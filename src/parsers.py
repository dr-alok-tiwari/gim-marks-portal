from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Any, BinaryIO

import pandas as pd

PROGRAMS = ["PGDM-BDA", "PGDM-Core", "PGDM-HCM", "PGDM-BIFS"]


@dataclass
class ParsedMarksheet:
    metadata: dict[str, Any]
    components: list[dict[str, Any]]
    students: pd.DataFrame
    warnings: list[str]


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass
    return re.sub(r"\s+", " ", str(value)).strip()


def parse_course_profile(uploaded_pdf: BinaryIO) -> dict[str, Any]:
    """Extract high-confidence metadata from a GIM-style Course Profile PDF."""
    try:
        import fitz  # PyMuPDF
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("PyMuPDF is required to read PDF course profiles.") from exc

    raw = uploaded_pdf.read()
    uploaded_pdf.seek(0)
    doc = fitz.open(stream=raw, filetype="pdf")
    text = "\n".join(page.get_text("text") for page in doc)
    flat = re.sub(r"[\t\r]+", " ", text)

    result: dict[str, Any] = {
        "programme": "",
        "academic_year": "",
        "term": None,
        "course_name": "",
        "faculty_name": "",
        "credits": None,
        "components": [],
        "raw_text": text,
    }

    patterns = {
        "programme": [
            r"Programme\s+((?:PGDM|FPM)[-–A-Za-z]*)",
            r"Program(?:me)?\s*[:\-]?\s*((?:PGDM|FPM)[-–A-Za-z]*)",
        ],
        "academic_year": [
            r"Academic\s+Year\s+(\d{4}\s*[–-]\s*\d{2,4})",
            r"AY\s*[:\-]?\s*(\d{4}\s*[–-]\s*\d{2,4})",
        ],
        "term": [r"Term\s+(\d)"],
        "credits": [r"Credits\s+(\d+(?:\.\d+)?)"],
        "course_name": [
            r"Course\s+Title\s+(.+?)\s+Mode\b",
            r"Course\s+Name\s*[:\-]?\s*(.+?)(?:\n|$)",
        ],
        "faculty_name": [
            r"Instructor\s+(.+?)(?:\s+Email|\n)",
            r"Faculty\s+Name\s*[:\-]?\s*(.+?)(?:\n|$)",
        ],
    }

    for key, candidates in patterns.items():
        for pattern in candidates:
            match = re.search(pattern, flat, flags=re.I | re.S)
            if not match:
                continue
            value = _clean(match.group(1)).replace("–", "-")
            if key in {"course_name", "faculty_name"}:
                value = re.sub(r"(?<=\w)-\s+(?=\w)", "", value)
            if key == "term":
                result[key] = int(value)
            elif key == "credits":
                result[key] = float(value)
            else:
                result[key] = value
            break

    component_pattern = re.compile(
        r"\d+\s+(.+?)\s+(\d+(?:\.\d+)?)%\s+(?:Throughout|After|Mid[- ]?course|End of course)",
        flags=re.I,
    )
    components: list[dict[str, Any]] = []
    for name, weight in component_pattern.findall(flat):
        name = _clean(name)
        if len(name) <= 60:
            components.append({"name": name, "weight": float(weight)})

    # Conservative fallback for the standard GIM evaluation table.
    if not components:
        known = [
            "Class participation",
            "Quiz",
            "Mid Term Examination",
            "End-Term Examination",
        ]
        for name in known:
            if not re.search(re.escape(name), flat, flags=re.I):
                continue
            match = re.search(
                re.escape(name) + r".{0,80}?(\d+(?:\.\d+)?)%",
                flat,
                flags=re.I | re.S,
            )
            if match:
                components.append({"name": name, "weight": float(match.group(1))})

    seen: set[str] = set()
    for component in components:
        key = component["name"].lower()
        if key not in seen:
            result["components"].append(component)
            seen.add(key)

    return result


def _read_csv(raw: bytes) -> pd.DataFrame:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin1"):
        try:
            return pd.read_csv(io.BytesIO(raw), header=None, encoding=encoding)
        except Exception as exc:  # pragma: no cover - depends on source encoding
            last_error = exc
    raise ValueError(f"Could not read CSV: {last_error}")


def _find_header_row(df: pd.DataFrame, *, strict_student_name: bool = False) -> int:
    for idx in range(min(len(df), 50)):
        cells = [_clean(v).lower() for v in df.iloc[idx].tolist()]
        has_roll = any("roll" in cell and ("no" in cell or "number" in cell) for cell in cells)
        if strict_student_name:
            has_name = any("name of student" in cell or cell == "student name" for cell in cells)
        else:
            has_name = any(
                "name of student" in cell or cell == "student name" or cell == "name"
                for cell in cells
            )
        if has_roll and has_name:
            return idx
    raise ValueError("Could not detect the student header row (Roll No. / Name of Student).")


def _is_main_marks_sheet(df: pd.DataFrame) -> bool:
    """Return True for the course marks sheets, excluding helper/CP calculation sheets."""
    try:
        header_idx = _find_header_row(df, strict_student_name=True)
    except ValueError:
        return False

    top_text = "\n".join(
        " | ".join(_clean(v) for v in df.iloc[i].tolist())
        for i in range(min(header_idx + 1, len(df)))
    ).lower()
    # The standard template has both an exam-definition row and a max-marks row.
    return "name of exam" in top_text and "max marks" in top_text


def _find_col(row: pd.Series, predicates: list[str]) -> int | None:
    for col, value in enumerate(row.tolist()):
        text = _clean(value).lower()
        if any(predicate in text for predicate in predicates):
            return col
    return None


def _safe_num(value: Any) -> float | None:
    if value is None or _clean(value) == "":
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalise_component_name(value: str) -> str:
    value = _clean(value)
    lower = value.lower().replace("–", "-")
    if "class participation" in lower or lower == "cp":
        return "Class Participation"
    if "quiz" in lower:
        return "Quiz"
    if "mid term" in lower or "mid-term" in lower or lower == "mt":
        return "Mid-Term Examination"
    if "end term" in lower or "end-term" in lower or lower == "et":
        return "End-Term Examination"
    return value


def _infer_section_from_sheet_name(sheet_name: str) -> str:
    match = re.search(r"(?:section|sec)[\s_\-]*([A-Za-z0-9]+)", sheet_name, flags=re.I)
    return match.group(1).upper() if match else ""


def _metadata_from_top(df: pd.DataFrame, header_idx: int) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "course_name": "",
        "faculty_name": "",
        "programme": "",
        "term": None,
        "academic_year": "",
        "section": "",
    }
    top_text = "\n".join(
        " | ".join(_clean(v) for v in df.iloc[i].tolist())
        for i in range(header_idx)
    )

    for line in top_text.splitlines():
        if "Course Name:" in line:
            metadata["course_name"] = _clean(line.split("Course Name:", 1)[1].split("|")[0])
        if "Faculty Name:" in line:
            metadata["faculty_name"] = _clean(line.split("Faculty Name:", 1)[1].split("|")[0])

    match = re.search(r"\b(PGDM-(?:BDA|Core|HCM|BIFS))\b", top_text, re.I)
    if match:
        programme = match.group(1)
        metadata["programme"] = next(
            (p for p in PROGRAMS if p.lower() == programme.lower()),
            programme,
        )
    match = re.search(r"\bTerm\s*:?\s*([1-6])\b", top_text, re.I)
    if match:
        metadata["term"] = int(match.group(1))
    match = re.search(
        r"\b(?:AY|Academic Year)\s*:?\s*(\d{4}\s*[-–]\s*\d{2,4})",
        top_text,
        re.I,
    )
    if match:
        metadata["academic_year"] = match.group(1).replace("–", "-").replace(" ", "")
    return metadata


def _parse_marks_sheet(df: pd.DataFrame, sheet_name: str) -> ParsedMarksheet:
    warnings: list[str] = []
    header_idx = _find_header_row(df, strict_student_name=True)
    header = df.iloc[header_idx]

    roll_col = _find_col(header, ["roll no", "roll number"])
    name_col = _find_col(header, ["name of student", "student name"])
    section_col = _find_col(header, ["sec", "section"])
    if roll_col is None or name_col is None:
        raise ValueError(f"{sheet_name}: could not identify Roll No. and Name of Student columns.")

    metadata = _metadata_from_top(df, header_idx)
    inferred_section = _infer_section_from_sheet_name(sheet_name)

    records: list[dict[str, Any]] = []
    for idx in range(header_idx + 1, len(df)):
        roll = _clean(df.iat[idx, roll_col])
        if not roll or "roll" in roll.lower():
            continue
        name = _clean(df.iat[idx, name_col])
        if not name:
            continue
        section = _clean(df.iat[idx, section_col]) if section_col is not None else ""
        if not section:
            section = inferred_section
        records.append(
            {
                "section": section.upper(),
                "roll_no": roll.upper(),
                "student_name": name,
                "_row": idx,
            }
        )

    if not records:
        raise ValueError(f"{sheet_name}: no student records were detected.")

    sections = sorted({r["section"] for r in records if r["section"]})
    metadata["section"] = ", ".join(sections)

    # Standard template rows are relative to the student header:
    # exam names = header - 3, max marks = header - 1.
    exam_row_idx = max(0, header_idx - 3)
    max_row_idx = max(0, header_idx - 1)
    exam_row = df.iloc[exam_row_idx]
    max_row = df.iloc[max_row_idx]

    # Total columns are explicitly labelled in the rows above the student header.
    total_map: dict[str, int] = {}
    for row_idx in range(max(0, header_idx - 10), header_idx):
        for col_idx, value in enumerate(df.iloc[row_idx].tolist()):
            text = _clean(value).lower().replace("–", "-")
            if "mid term total" in text or "mid-term total" in text:
                total_map["Mid-Term Examination"] = col_idx
            elif "end term total" in text or "end-term total" in text:
                total_map["End-Term Examination"] = col_idx

    components: list[dict[str, Any]] = []
    used_cols: set[int] = {roll_col, name_col}
    if section_col is not None:
        used_cols.add(section_col)

    # Direct columns such as Class Participation and Quiz.
    for col_idx in range(df.shape[1]):
        label = _clean(exam_row.iloc[col_idx])
        if not label:
            continue
        component_name = _normalise_component_name(label)
        if component_name in {"Class Participation", "Quiz"}:
            components.append(
                {
                    "name": component_name,
                    "source_col": col_idx,
                    "max_marks": _safe_num(max_row.iloc[col_idx]),
                    "kind": "direct",
                }
            )
            used_cols.add(col_idx)

    # Grouped exams such as Mid-Term and End-Term.
    for target in ("Mid-Term Examination", "End-Term Examination"):
        total_col = total_map.get(target)
        exam_start: int | None = None
        for col_idx in range(df.shape[1]):
            if _normalise_component_name(_clean(exam_row.iloc[col_idx])) == target:
                exam_start = col_idx
                break

        if exam_start is None:
            continue

        question_cols: list[int] = []
        if total_col is not None and total_col > exam_start:
            question_cols = list(range(exam_start, total_col))
        else:
            # Fallback: walk across merged-header blanks until another labelled exam/total.
            col_idx = exam_start
            while col_idx < df.shape[1]:
                label = _clean(exam_row.iloc[col_idx])
                normalised = _normalise_component_name(label) if label else ""
                if col_idx != exam_start and label and normalised != target:
                    break
                question_cols.append(col_idx)
                col_idx += 1

        max_values = [_safe_num(max_row.iloc[c]) for c in question_cols]
        max_marks = sum(value for value in max_values if value is not None) or None
        components.append(
            {
                "name": target,
                "source_col": total_col,
                "question_cols": question_cols,
                "max_marks": max_marks,
                "kind": "total" if total_col is not None else "sum_questions",
            }
        )
        if total_col is not None:
            used_cols.add(total_col)
        used_cols.update(question_cols)

    if not components:
        # Fallback for a simpler sheet using component names directly as headers.
        for col_idx, value in enumerate(header.tolist()):
            if col_idx in used_cols:
                continue
            label = _clean(value)
            if not label or re.search(r"final|total", label, re.I):
                continue
            components.append(
                {
                    "name": _normalise_component_name(label),
                    "source_col": col_idx,
                    "max_marks": None,
                    "kind": "direct",
                }
            )

    out_rows: list[dict[str, Any]] = []
    for record in records:
        row = df.iloc[record["_row"]]
        result = {k: v for k, v in record.items() if k != "_row"}
        for component in components:
            question_cols = component.get("question_cols") or []
            question_values = [_safe_num(row.iloc[c]) for c in question_cols]
            question_present = [v for v in question_values if v is not None]

            if question_cols and not question_present:
                # Critical: blank exam questions must remain blank. Excel SUM formulas often
                # cache a numeric 0 even when no marks have been entered yet.
                value = None
            else:
                source_col = component.get("source_col")
                value = _safe_num(row.iloc[source_col]) if source_col is not None else None
                if value is None and question_present:
                    value = sum(question_present)
            result[component["name"]] = value
        out_rows.append(result)

    students = pd.DataFrame(out_rows)
    if students["roll_no"].duplicated().any():
        warnings.append(f"{sheet_name}: duplicate roll numbers were detected.")

    for component in components:
        max_marks = component.get("max_marks")
        if max_marks is None:
            continue
        values = pd.to_numeric(students[component["name"]], errors="coerce")
        if (values > float(max_marks)).any():
            warnings.append(
                f"{sheet_name}: some {component['name']} marks exceed the detected maximum of {max_marks:g}."
            )
        if (values < 0).any():
            warnings.append(f"{sheet_name}: some {component['name']} marks are negative.")

    metadata["source_sheet"] = sheet_name
    return ParsedMarksheet(
        metadata=metadata,
        components=components,
        students=students,
        warnings=warnings,
    )


def _component_public(component: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": component["name"],
        "max_marks": component.get("max_marks"),
    }


def _merge_section_parses(parsed_sheets: list[ParsedMarksheet]) -> ParsedMarksheet:
    if not parsed_sheets:
        raise ValueError("No valid marks sheets were detected in the workbook.")

    warnings: list[str] = []
    base = dict(parsed_sheets[0].metadata)
    students = pd.concat([p.students for p in parsed_sheets], ignore_index=True)

    # Warn on inconsistent course-level metadata; keep the first non-empty detected value.
    fields = ["course_name", "faculty_name", "programme", "term", "academic_year"]
    for field in fields:
        values = []
        for parsed in parsed_sheets:
            value = parsed.metadata.get(field)
            if value not in (None, "") and value not in values:
                values.append(value)
        if len(values) > 1:
            warnings.append(
                f"Different {field.replace('_', ' ')} values were detected across section sheets: "
                + ", ".join(str(v) for v in values)
                + ". Please verify before publishing."
            )
        if values:
            base[field] = values[0]

    sections = sorted({str(v).strip().upper() for v in students["section"] if str(v).strip()})
    base["sections"] = sections
    base["section"] = ", ".join(sections)
    base["source_sheets"] = [p.metadata.get("source_sheet", "") for p in parsed_sheets]

    section_summary: list[dict[str, Any]] = []
    for parsed in parsed_sheets:
        detected_sections = sorted(
            {str(v).strip().upper() for v in parsed.students["section"] if str(v).strip()}
        )
        section_summary.append(
            {
                "sheet": parsed.metadata.get("source_sheet", ""),
                "section": ", ".join(detected_sections),
                "students": int(len(parsed.students)),
            }
        )
    base["section_summary"] = section_summary

    # Merge component definitions by name and preserve the order of the first section.
    components_by_name: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for parsed in parsed_sheets:
        for component in parsed.components:
            name = component["name"]
            public = _component_public(component)
            if name not in components_by_name:
                components_by_name[name] = public
                order.append(name)
            else:
                old_max = components_by_name[name].get("max_marks")
                new_max = public.get("max_marks")
                if old_max is None and new_max is not None:
                    components_by_name[name]["max_marks"] = new_max
                elif (
                    old_max is not None
                    and new_max is not None
                    and abs(float(old_max) - float(new_max)) > 1e-9
                ):
                    warnings.append(
                        f"Component {name} has different maximum marks across section sheets "
                        f"({old_max:g} vs {new_max:g})."
                    )

    component_sets = [{c["name"] for c in p.components} for p in parsed_sheets]
    if any(component_set != component_sets[0] for component_set in component_sets[1:]):
        warnings.append("Evaluation component sets differ across section sheets. Please verify before publishing.")

    components = [components_by_name[name] for name in order]

    warnings.extend(w for parsed in parsed_sheets for w in parsed.warnings)
    duplicated = students[students["roll_no"].duplicated(keep=False)]
    if not duplicated.empty:
        rolls = sorted(set(duplicated["roll_no"].astype(str)))
        warnings.append(
            "Duplicate roll numbers were detected across the combined sections: "
            + ", ".join(rolls[:10])
            + (" …" if len(rolls) > 10 else "")
        )

    return ParsedMarksheet(
        metadata=base,
        components=components,
        students=students,
        warnings=warnings,
    )


def parse_marksheet(uploaded_file: BinaryIO, filename: str) -> ParsedMarksheet:
    """Parse one CSV marks sheet or all main section sheets from an Excel workbook.

    For the standard workbook template, all sheets containing the main marks structure
    (e.g. Section-A, Section-B, Section-C) are detected and combined automatically.
    Helper sheets such as CP-Sec-A are deliberately ignored.
    """
    raw = uploaded_file.read()
    uploaded_file.seek(0)
    lower = filename.lower()

    if lower.endswith(".csv"):
        df = _read_csv(raw)
        parsed = _parse_marks_sheet(df, "CSV")
        parsed.metadata["source_sheets"] = ["CSV"]
        parsed.metadata["sections"] = sorted(
            {str(v).strip().upper() for v in parsed.students["section"] if str(v).strip()}
        )
        parsed.metadata["section_summary"] = [
            {
                "sheet": "CSV",
                "section": parsed.metadata.get("section", ""),
                "students": int(len(parsed.students)),
            }
        ]
        return parsed

    if lower.endswith((".xlsx", ".xls")):
        try:
            excel = pd.ExcelFile(io.BytesIO(raw))
        except Exception as exc:
            raise ValueError(f"Could not open Excel workbook: {exc}") from exc

        parsed_sheets: list[ParsedMarksheet] = []
        ignored_sheets: list[str] = []
        for sheet_name in excel.sheet_names:
            df = excel.parse(sheet_name=sheet_name, header=None)
            if not _is_main_marks_sheet(df):
                ignored_sheets.append(sheet_name)
                continue
            parsed_sheets.append(_parse_marks_sheet(df, sheet_name))

        if not parsed_sheets:
            raise ValueError(
                "No main marks sheets were detected. The workbook should contain the standard "
                "GIM template with Roll No., Name of Student, Name of Exam and Max Marks rows."
            )

        merged = _merge_section_parses(parsed_sheets)
        merged.metadata["ignored_sheets"] = ignored_sheets
        return merged

    raise ValueError("Unsupported marksheet format. Use CSV, XLSX or XLS.")
