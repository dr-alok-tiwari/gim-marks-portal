from __future__ import annotations

import json
import math
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

DB_PATH = os.getenv("GIM_MARKS_DB", "data/portal.db")


def _ensure_parent() -> None:
    parent = os.path.dirname(DB_PATH)
    if parent:
        os.makedirs(parent, exist_ok=True)


@contextmanager
def connection():
    _ensure_parent()
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connection() as conn:
        conn.executescript(
            """
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_key TEXT NOT NULL UNIQUE,
                course_name TEXT NOT NULL,
                programme TEXT NOT NULL,
                term INTEGER NOT NULL,
                academic_year TEXT,
                faculty_name TEXT,
                section TEXT,
                components_json TEXT NOT NULL,
                released_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL,
                roll_no TEXT NOT NULL,
                student_name TEXT NOT NULL,
                section TEXT,
                marks_json TEXT NOT NULL,
                UNIQUE(course_id, roll_no),
                FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE
            );
            """
        )


def make_course_key(
    programme: str,
    term: int,
    academic_year: str,
    course_name: str,
    section: str = "",
) -> str:
    """Stable key for a course instance.

    Section is deliberately not part of the key: one uploaded workbook can contain
    Section A/B/C together, and later section-list changes should update the same course.
    """
    del section
    return "|".join(
        [
            programme.strip().upper(),
            str(term),
            academic_year.strip().upper(),
            course_name.strip().upper(),
        ]
    )


def _is_missing(value) -> bool:
    if value is None:
        return True
    try:
        return bool(math.isnan(float(value)))
    except (TypeError, ValueError):
        return False


def publish_course(*, metadata: dict, components: list[dict], released: list[str], students) -> int:
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    key = make_course_key(
        metadata["programme"],
        int(metadata["term"]),
        metadata.get("academic_year", ""),
        metadata["course_name"],
        metadata.get("section", ""),
    )
    serialisable_components = [
        {"name": c["name"], "max_marks": c.get("max_marks"), "weight": c.get("weight")}
        for c in components
    ]

    with connection() as conn:
        row = conn.execute("SELECT id FROM courses WHERE course_key=?", (key,)).fetchone()
        if row:
            course_id = int(row["id"])
            conn.execute(
                """
                UPDATE courses
                SET course_name=?, programme=?, term=?, academic_year=?, faculty_name=?,
                    section=?, components_json=?, released_json=?, updated_at=?
                WHERE id=?
                """,
                (
                    metadata["course_name"],
                    metadata["programme"],
                    int(metadata["term"]),
                    metadata.get("academic_year", ""),
                    metadata.get("faculty_name", ""),
                    metadata.get("section", ""),
                    json.dumps(serialisable_components),
                    json.dumps(released),
                    now,
                    course_id,
                ),
            )
            conn.execute("DELETE FROM marks WHERE course_id=?", (course_id,))
        else:
            cur = conn.execute(
                """
                INSERT INTO courses(
                    course_key, course_name, programme, term, academic_year, faculty_name,
                    section, components_json, released_json, created_at, updated_at
                ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    key,
                    metadata["course_name"],
                    metadata["programme"],
                    int(metadata["term"]),
                    metadata.get("academic_year", ""),
                    metadata.get("faculty_name", ""),
                    metadata.get("section", ""),
                    json.dumps(serialisable_components),
                    json.dumps(released),
                    now,
                    now,
                ),
            )
            course_id = int(cur.lastrowid)

        for _, row_data in students.iterrows():
            marks = {}
            for component in components:
                value = row_data.get(component["name"])
                marks[component["name"]] = None if _is_missing(value) else float(value)
            conn.execute(
                "INSERT INTO marks(course_id, roll_no, student_name, section, marks_json) VALUES (?,?,?,?,?)",
                (
                    course_id,
                    str(row_data["roll_no"]).strip().upper(),
                    str(row_data["student_name"]).strip(),
                    str(row_data.get("section", "")).strip(),
                    json.dumps(marks),
                ),
            )
    return course_id


def get_available_sections(programme: str, term: int) -> list[str]:
    """Return distinct published student sections for a programme and term."""
    init_db()
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT DISTINCT TRIM(m.section) AS section
            FROM courses c
            JOIN marks m ON c.id=m.course_id
            WHERE UPPER(c.programme)=UPPER(?)
              AND c.term=?
              AND TRIM(COALESCE(m.section, '')) <> ''
            ORDER BY section
            """,
            (programme.strip(), int(term)),
        ).fetchall()
    return [str(row["section"]).strip().upper() for row in rows if str(row["section"] or "").strip()]


def get_student_courses(programme: str, term: int, roll_no: str, section: str | None = None) -> list[dict]:
    init_db()
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT c.*, m.student_name, m.section AS student_section, m.marks_json
            FROM courses c
            JOIN marks m ON c.id=m.course_id
            WHERE UPPER(c.programme)=UPPER(?)
              AND c.term=?
              AND UPPER(m.roll_no)=UPPER(?)
              AND (? IS NULL OR UPPER(TRIM(m.section))=UPPER(TRIM(?)))
            ORDER BY c.course_name
            """,
            (
                programme.strip(),
                int(term),
                roll_no.strip(),
                section.strip() if section else None,
                section.strip() if section else None,
            ),
        ).fetchall()

    output = []
    for row in rows:
        item = dict(row)
        item["components"] = json.loads(item.pop("components_json"))
        item["released"] = json.loads(item.pop("released_json"))
        item["marks"] = json.loads(item.pop("marks_json"))
        output.append(item)
    return output


def list_courses() -> list[dict]:
    init_db()
    with connection() as conn:
        rows = conn.execute("SELECT * FROM courses ORDER BY updated_at DESC").fetchall()
    return [dict(row) for row in rows]


def delete_course(course_id: int) -> None:
    init_db()
    with connection() as conn:
        conn.execute("DELETE FROM courses WHERE id=?", (int(course_id),))
