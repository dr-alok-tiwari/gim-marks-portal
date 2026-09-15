import os
from pathlib import Path

import pandas as pd


def test_publish_accepts_blank_component_marks(tmp_path, monkeypatch):
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("GIM_MARKS_DB", str(db_path))

    # Reload module so DB_PATH picks up the temporary environment variable.
    import importlib
    import src.db as db
    importlib.reload(db)

    students = pd.DataFrame([
        {
            "section": "A",
            "roll_no": "B2026001",
            "student_name": "Student One",
            "Quiz": 12.0,
            "End-Term Examination": None,
        }
    ])
    components = [
        {"name": "Quiz", "max_marks": 15, "weight": 15},
        {"name": "End-Term Examination", "max_marks": 90, "weight": 40},
    ]
    metadata = {
        "course_name": "Test Course",
        "programme": "PGDM-BDA",
        "term": 1,
        "academic_year": "2026-27",
        "faculty_name": "Faculty",
        "section": "A, B, C",
    }

    course_id = db.publish_course(
        metadata=metadata,
        components=components,
        released=["Quiz", "End-Term Examination"],
        students=students,
    )
    assert course_id > 0
    courses = db.get_student_courses("PGDM-BDA", 1, "B2026001")
    assert len(courses) == 1
    assert courses[0]["marks"]["Quiz"] == 12.0
    assert courses[0]["marks"]["End-Term Examination"] is None


def test_student_lookup_can_require_matching_section(tmp_path, monkeypatch):
    db_path = tmp_path / "section_test.db"
    monkeypatch.setenv("GIM_MARKS_DB", str(db_path))

    import importlib
    import src.db as db
    importlib.reload(db)

    students = pd.DataFrame([
        {"section": "A", "roll_no": "B2026001", "student_name": "Student A", "Quiz": 11.0},
        {"section": "B", "roll_no": "B2026002", "student_name": "Student B", "Quiz": 13.0},
    ])
    components = [{"name": "Quiz", "max_marks": 15, "weight": 15}]
    metadata = {
        "course_name": "Section Test",
        "programme": "PGDM-BDA",
        "term": 1,
        "academic_year": "2026-27",
        "faculty_name": "Faculty",
        "section": "A, B",
    }
    db.publish_course(
        metadata=metadata,
        components=components,
        released=["Quiz"],
        students=students,
    )

    assert db.get_available_sections("PGDM-BDA", 1) == ["A", "B"]
    assert len(db.get_student_courses("PGDM-BDA", 1, "B2026001", section="A")) == 1
    assert db.get_student_courses("PGDM-BDA", 1, "B2026001", section="B") == []
