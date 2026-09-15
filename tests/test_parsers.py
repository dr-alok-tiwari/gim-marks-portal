from pathlib import Path

import pandas as pd

from src.parsers import parse_marksheet


class UploadLike:
    def __init__(self, path: Path):
        self._file = open(path, "rb")

    def read(self, *args):
        return self._file.read(*args)

    def seek(self, *args):
        return self._file.seek(*args)

    def close(self):
        self._file.close()


def _parse(path: Path):
    upload = UploadLike(path)
    try:
        return parse_marksheet(upload, path.name)
    finally:
        upload.close()


def test_supplied_single_section_csv_if_present():
    path = Path("/mnt/data/Marksheet-Storytelling using dataviz-Term-2-Batch-2026-28(Section-A)(1).csv")
    if not path.exists():
        return
    parsed = _parse(path)
    assert parsed.metadata["programme"] == "PGDM-BDA"
    assert parsed.metadata["term"] == 1
    assert len(parsed.students) == 54
    assert parsed.metadata["sections"] == ["A"]
    names = [component["name"] for component in parsed.components]
    assert "Class Participation" in names
    assert "Mid-Term Examination" in names


def test_supplied_multisection_workbook_if_present():
    path = Path("/mnt/data/Marksheet-Storytelling using dataviz-Term-2-Batch-2026-28.xlsx")
    if not path.exists():
        return
    parsed = _parse(path)

    assert parsed.metadata["programme"] == "PGDM-BDA"
    assert parsed.metadata["term"] == 1
    assert parsed.metadata["sections"] == ["A", "B", "C"]
    assert parsed.metadata["source_sheets"] == ["Section-A", "Section-B", "Section-C"]
    assert set(parsed.metadata["ignored_sheets"]) == {"CP-Sec-A", "CP-Sec-B", "CP-Sec-C"}
    assert len(parsed.students) == 161

    counts = parsed.students.groupby("section").size().to_dict()
    assert counts == {"A": 54, "B": 55, "C": 52}

    first = parsed.students.loc[parsed.students["roll_no"] == "B2026001"].iloc[0]
    assert first["section"] == "A"
    assert first["Mid-Term Examination"] == 42

    # End-term question cells are blank in the supplied workbook. A cached Excel SUM=0
    # must not be interpreted as an actual zero mark.
    assert pd.isna(first["End-Term Examination"])

    b_student = parsed.students.loc[parsed.students["roll_no"] == "B2026056"].iloc[0]
    c_student = parsed.students.loc[parsed.students["roll_no"] == "B2026110"].iloc[0]
    assert b_student["section"] == "B"
    assert c_student["section"] == "C"


def test_component_maxima_for_multisection_workbook_if_present():
    path = Path("/mnt/data/Marksheet-Storytelling using dataviz-Term-2-Batch-2026-28.xlsx")
    if not path.exists():
        return
    parsed = _parse(path)
    maxima = {c["name"]: c["max_marks"] for c in parsed.components}
    assert maxima["Class Participation"] == 10
    assert maxima["Quiz"] == 15
    assert maxima["Mid-Term Examination"] == 60
    assert maxima["End-Term Examination"] == 90
