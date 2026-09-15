from __future__ import annotations

import hmac
from html import escape
from typing import Any

import pandas as pd
import streamlit as st

from src.db import (
    delete_course,
    get_available_sections,
    get_student_courses,
    init_db,
    list_courses,
    publish_course,
)
from src.parsers import PROGRAMS, parse_course_profile, parse_marksheet

st.set_page_config(
    page_title="GIM Marks Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)
init_db()


DEVELOPER_SITE = "https://dr-alok-tiwari.github.io/"
DEVELOPER_GITHUB = "https://github.com/dr-alok-tiwari"
DEVELOPER_LINKEDIN = "https://www.linkedin.com/in/dr-alok-tiwari/"


def apply_theme() -> None:
    """Apply lightweight styling without relying on external CSS or JavaScript."""
    st.markdown(
        """
        <style>
        :root {
            --portal-navy: #14213d;
            --portal-blue: #3157d5;
            --portal-indigo: #5b5bd6;
            --portal-ink: #172033;
            --portal-muted: #657085;
            --portal-soft: #f4f7ff;
            --portal-border: rgba(49, 87, 213, 0.14);
        }

        .stApp {
            background:
                radial-gradient(circle at 90% 5%, rgba(91,91,214,.08), transparent 28rem),
                radial-gradient(circle at 5% 18%, rgba(49,87,213,.07), transparent 24rem),
                #fbfcff;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #111a31 0%, #162445 55%, #1a2b52 100%);
        }
        [data-testid="stSidebar"] * {
            color: #f7f9ff;
        }
        [data-testid="stSidebar"] [data-baseweb="radio"] label {
            border-radius: 12px;
            padding: .34rem .45rem;
        }
        [data-testid="stSidebar"] hr {
            border-color: rgba(255,255,255,.14);
        }

        .block-container {
            max-width: 1240px;
            padding-top: 2.1rem;
            padding-bottom: 4rem;
        }

        .portal-hero {
            background: linear-gradient(120deg, #14213d 0%, #273f82 52%, #5b5bd6 100%);
            color: white;
            border-radius: 24px;
            padding: 2.0rem 2.2rem;
            box-shadow: 0 18px 45px rgba(20, 33, 61, .18);
            margin-bottom: 1.35rem;
            overflow: hidden;
            position: relative;
        }
        .portal-hero::after {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            border-radius: 50%;
            right: -95px;
            top: -95px;
            background: rgba(255,255,255,.10);
        }
        .portal-hero h1 {
            color: white !important;
            font-size: clamp(2rem, 4vw, 3.35rem) !important;
            line-height: 1.03;
            margin: 0 0 .6rem 0 !important;
        }
        .portal-hero p {
            font-size: 1.05rem;
            max-width: 800px;
            color: rgba(255,255,255,.88) !important;
            margin: 0;
        }
        .hero-kicker {
            display: inline-block;
            font-size: .76rem;
            font-weight: 700;
            letter-spacing: .08em;
            text-transform: uppercase;
            background: rgba(255,255,255,.14);
            border: 1px solid rgba(255,255,255,.18);
            padding: .35rem .65rem;
            border-radius: 999px;
            margin-bottom: .85rem;
        }

        .portal-card {
            background: rgba(255,255,255,.93);
            border: 1px solid var(--portal-border);
            border-radius: 18px;
            padding: 1.1rem 1.2rem;
            box-shadow: 0 8px 26px rgba(25, 45, 90, .06);
            min-height: 100%;
        }
        .portal-card h3 {
            margin: .15rem 0 .45rem 0;
            color: var(--portal-ink);
        }
        .portal-card p {
            color: var(--portal-muted);
            margin-bottom: .25rem;
        }

        .mini-icon {
            width: 42px;
            height: 42px;
            border-radius: 13px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 1.25rem;
            background: linear-gradient(135deg, rgba(49,87,213,.12), rgba(91,91,214,.12));
            margin-bottom: .5rem;
        }

        .soft-panel {
            border: 1px solid var(--portal-border);
            background: linear-gradient(135deg, #ffffff 0%, #f7f9ff 100%);
            border-radius: 18px;
            padding: 1rem 1.1rem;
            margin-bottom: .9rem;
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 750;
            color: var(--portal-ink);
            margin-top: .3rem;
            margin-bottom: .5rem;
        }

        .pill-row { margin-top: .8rem; }
        .pill {
            display: inline-block;
            padding: .32rem .62rem;
            border-radius: 999px;
            background: rgba(49,87,213,.10);
            color: #2747b8;
            font-size: .78rem;
            font-weight: 650;
            margin: 0 .35rem .35rem 0;
        }

        .result-course {
            border-radius: 20px;
            border: 1px solid rgba(49,87,213,.14);
            padding: 1.1rem 1.2rem .75rem 1.2rem;
            background: linear-gradient(180deg,#fff 0%,#fbfcff 100%);
            box-shadow: 0 9px 28px rgba(28,48,91,.06);
            margin: .5rem 0 1.15rem 0;
        }
        .result-course-title {
            font-size: 1.25rem;
            font-weight: 760;
            color: var(--portal-ink);
            margin-bottom: .15rem;
        }
        .result-meta {
            color: var(--portal-muted);
            font-size: .9rem;
        }

        [data-testid="stMetric"] {
            background: rgba(255,255,255,.78);
            border: 1px solid var(--portal-border);
            padding: .8rem .9rem;
            border-radius: 15px;
        }

        div.stButton > button,
        div.stDownloadButton > button,
        a[data-testid="stBaseButton-secondary"] {
            border-radius: 12px !important;
            font-weight: 650 !important;
        }
        div.stButton > button[kind="primary"] {
            box-shadow: 0 7px 18px rgba(49,87,213,.20);
        }

        [data-testid="stFileUploader"] {
            background: rgba(255,255,255,.68);
            border-radius: 16px;
            padding: .35rem .55rem;
        }

        .dev-avatar {
            width: 82px;
            height: 82px;
            border-radius: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.6rem;
            font-weight: 800;
            background: linear-gradient(135deg, #3157d5, #5b5bd6);
            box-shadow: 0 10px 25px rgba(49,87,213,.24);
        }
        .footer-note {
            text-align: center;
            color: #7d8798;
            font-size: .78rem;
            padding-top: 1rem;
        }

        @media (max-width: 780px) {
            .block-container { padding-top: 1rem; }
            .portal-hero { padding: 1.45rem 1.25rem; border-radius: 18px; }
            .portal-hero h1 { font-size: 2rem !important; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="portal-hero">
            <div class="hero-kicker">{kicker}</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def secret_password() -> str:
    try:
        return str(st.secrets["FACULTY_PASSWORD"])
    except Exception:
        return ""


def faculty_authenticated() -> bool:
    return bool(st.session_state.get("faculty_authenticated", False))


def login_box() -> bool:
    with st.container(border=True):
        st.markdown("### 🔐 Faculty Login")
        st.caption("The faculty password is stored in Streamlit Secrets and is never exposed in the public repository.")
        password = st.text_input("Password", type="password", key="faculty_password_input")
        if st.button("Login to Faculty Portal", type="primary", use_container_width=True):
            configured = secret_password()
            if not configured:
                st.error("Faculty password is not configured. Add FACULTY_PASSWORD in Streamlit Secrets.")
            elif hmac.compare_digest(password, configured):
                st.session_state.faculty_authenticated = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    return faculty_authenticated()


def component_weight(profile_components: list[dict[str, Any]], name: str) -> float | None:
    norm = name.lower().replace("-", " ")
    aliases = {
        "class participation": ["class participation"],
        "quiz": ["quiz"],
        "mid term examination": ["mid term"],
        "end term examination": ["end term"],
    }
    for profile_component in profile_components:
        profile_name = str(profile_component.get("name", "")).lower().replace("-", " ")
        for key, words in aliases.items():
            if key in norm and any(word in profile_name for word in words):
                return float(profile_component["weight"])
        if profile_name == norm:
            return float(profile_component["weight"])
    return None


def home_page() -> None:
    hero(
        "GIM Academic Portal",
        "Marks, released with clarity.",
        "A lightweight faculty-controlled portal for publishing selected evaluation components across multiple sections while keeping source files out of the public GitHub repository.",
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """<div class="portal-card"><div class="mini-icon">🔒</div><h3>Faculty controlled</h3><p>Faculty decides exactly which evaluation components are visible to students.</p></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """<div class="portal-card"><div class="mini-icon">📚</div><h3>Multi-section ready</h3><p>One standard workbook can publish Sections A, B, C and future matching section sheets together.</p></div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """<div class="portal-card"><div class="mini-icon">🛡️</div><h3>GitHub-safe workflow</h3><p>Course profiles and marksheets are uploaded at runtime rather than committed to the public code repository.</p></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("### How the portal works")
    a, b = st.columns([1.15, 1])
    with a:
        with st.container(border=True):
            st.markdown("#### 👨‍🏫 Faculty")
            st.markdown(
                "**Login → Upload Course Profile → Upload complete marksheet workbook → Review detected sections → Select components → Publish.**"
            )
            st.caption("Re-upload a revised workbook and publish again whenever marks are updated.")
    with b:
        with st.container(border=True):
            st.markdown("#### 🎓 Student")
            st.markdown(
                "**Select Programme → Term → Section → Enter Roll Number → View only the marks released by faculty.**"
            )
            st.caption("The selected section is checked along with the roll number before results are returned.")

    st.info(
        "Pilot privacy note: Programme + Term + Section + Roll Number improves lookup accuracy, but roll numbers are not a strong authentication method. For institution-wide deployment, add GIM Microsoft SSO or institutional email OTP."
    )


def _student_component_cards(course: dict[str, Any]) -> tuple[float, float]:
    component_lookup = {component["name"]: component for component in course["components"]}
    weighted_total = 0.0
    released_weight_with_marks = 0.0

    released_components = [
        (name, component_lookup.get(name), course["marks"].get(name))
        for name in course["released"]
        if component_lookup.get(name)
    ]

    for start in range(0, len(released_components), 2):
        cols = st.columns(2)
        for col, entry in zip(cols, released_components[start : start + 2]):
            name, component, mark = entry
            max_marks = component.get("max_marks")
            weight = component.get("weight")
            weighted = None
            progress = 0.0
            if mark is not None and max_marks not in (None, 0):
                progress = min(max(float(mark) / float(max_marks), 0.0), 1.0)
                if weight is not None:
                    weighted = float(mark) / float(max_marks) * float(weight)
                    weighted_total += weighted
                    released_weight_with_marks += float(weight)

            with col:
                with st.container(border=True):
                    st.markdown(f"**{name}**")
                    if mark is None:
                        st.metric("Score", "Not entered")
                        st.caption(
                            f"Maximum: {float(max_marks):g}" if max_marks is not None else "Maximum: —"
                        )
                    else:
                        max_label = "—" if max_marks is None else f"{float(max_marks):g}"
                        st.metric("Score", f"{float(mark):g} / {max_label}")
                        if max_marks not in (None, 0):
                            st.progress(progress)
                            st.caption(f"{progress * 100:.1f}% of raw maximum")
                    if weight is not None:
                        weighted_label = "—" if weighted is None else f"{weighted:.2f} / {float(weight):g}"
                        st.caption(f"Course weight: {float(weight):g}% · Weighted contribution: {weighted_label}")
    return weighted_total, released_weight_with_marks


def student_page() -> None:
    hero(
        "Student Access",
        "Your released marks, in one place.",
        "Choose your programme, term and section, then enter your roll number. Only evaluation components released by faculty are displayed.",
    )

    with st.container(border=True):
        st.markdown("#### 🔎 Find my marks")
        c1, c2, c3 = st.columns(3)
        programme = c1.selectbox("Programme", PROGRAMS, key="student_programme")
        term = c2.selectbox("Term", list(range(1, 7)), key="student_term")

        available_sections = get_available_sections(programme, term)
        section_options = available_sections if available_sections else ["A", "B", "C"]
        section = c3.selectbox(
            "Section",
            section_options,
            help="Select the section in which you are enrolled.",
            key="student_section",
        )
        roll = st.text_input(
            "Roll Number",
            placeholder="e.g., B2026001",
            key="student_roll",
        ).strip().upper()

        search = st.button("View My Released Marks", type="primary", use_container_width=True)

    if not search:
        st.caption("Your section and roll number are matched together before any result is displayed.")
        return
    if not roll:
        st.warning("Enter your roll number.")
        return

    courses = get_student_courses(programme, term, roll, section=section)
    visible = [course for course in courses if course["released"]]
    if not visible:
        st.warning("No released marks are currently available for the information entered.")
        return

    st.success(
        f"Welcome, {visible[0]['student_name']} · Section {visible[0].get('student_section') or section}"
    )

    for course in visible:
        meta_parts = [course["programme"], f"Term {course['term']}"]
        if course.get("academic_year"):
            meta_parts.append(f"AY {course['academic_year']}")
        if course.get("student_section"):
            meta_parts.append(f"Section {course['student_section']}")

        safe_course_name = escape(str(course['course_name']))
        safe_meta = escape(' · '.join(meta_parts))
        st.markdown(
            f"""
            <div class="result-course">
                <div class="result-course-title">{safe_course_name}</div>
                <div class="result-meta">{safe_meta}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        weighted_total, released_weight_with_marks = _student_component_cards(course)

        if released_weight_with_marks:
            m1, m2 = st.columns([1, 1.5])
            with m1:
                st.metric(
                    "Released weighted total",
                    f"{weighted_total:.2f} / {released_weight_with_marks:g}",
                )
            with m2:
                attainment = min(weighted_total / released_weight_with_marks, 1.0)
                st.caption("Performance across entered and released components")
                st.progress(attainment)
                st.caption(f"{attainment * 100:.1f}% of the currently released weighted maximum")
            if released_weight_with_marks < 100:
                st.info(
                    "This is a **partial course total** based only on released components that currently have marks entered. It is not the final course score."
                )
        st.divider()


def _section_summary_frame(parsed) -> pd.DataFrame:
    summary = parsed.metadata.get("section_summary", [])
    if summary:
        return pd.DataFrame(summary).rename(
            columns={"sheet": "Worksheet", "section": "Section", "students": "Students"}
        )
    counts = (
        parsed.students.groupby("section", dropna=False)
        .size()
        .reset_index(name="Students")
        .rename(columns={"section": "Section"})
    )
    counts["Worksheet"] = ""
    return counts[["Worksheet", "Section", "Students"]]


def render_publish_tab() -> None:
    st.markdown("### 1 · Upload source files")
    st.caption("Upload the files only inside the live faculty session. They are not added to your GitHub repository.")
    left, right = st.columns(2)
    with left:
        course_pdf = st.file_uploader(
            "Course Profile (PDF)",
            type=["pdf"],
            key="course_profile",
        )
    with right:
        marks_file = st.file_uploader(
            "Complete marksheet workbook",
            type=["csv", "xlsx", "xls"],
            key="marksheet",
            help=(
                "For XLSX/XLS, upload the complete workbook. The app automatically detects all main "
                "Section sheets and ignores helper sheets such as CP-Sec-A."
            ),
        )

    if not (course_pdf and marks_file):
        st.info("Upload both the Course Profile and marksheet to continue.")
        return

    try:
        profile = parse_course_profile(course_pdf)
        parsed = parse_marksheet(marks_file, marks_file.name)
    except Exception as exc:
        st.error(f"Could not parse the uploaded files: {exc}")
        return

    st.markdown("### 2 · Sections detected")
    sections = parsed.metadata.get("sections") or sorted(
        set(parsed.students["section"].dropna().astype(str))
    )
    summary_df = _section_summary_frame(parsed)
    m1, m2, m3 = st.columns(3)
    m1.metric("Sections detected", len(sections))
    m2.metric("Students detected", len(parsed.students))
    m3.metric("Section list", ", ".join(sections) if sections else "—")
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

    ignored = parsed.metadata.get("ignored_sheets", [])
    if ignored:
        st.caption("Helper/non-marks worksheets ignored: " + ", ".join(ignored))

    st.markdown("### 3 · Verify course details")
    detected_programme = parsed.metadata.get("programme") or profile.get("programme") or PROGRAMS[0]
    detected_programme = detected_programme if detected_programme in PROGRAMS else PROGRAMS[0]
    c1, c2, c3 = st.columns(3)
    programme = c1.selectbox("Programme", PROGRAMS, index=PROGRAMS.index(detected_programme))
    detected_term = parsed.metadata.get("term") or profile.get("term") or 1
    term = c2.selectbox(
        "Term",
        list(range(1, 7)),
        index=max(0, min(5, int(detected_term) - 1)),
    )
    academic_year = c3.text_input(
        "Academic Year",
        value=parsed.metadata.get("academic_year") or profile.get("academic_year") or "",
    )
    course_name = st.text_input(
        "Course Name",
        value=parsed.metadata.get("course_name") or profile.get("course_name") or "",
    )
    faculty_name = st.text_input(
        "Faculty Name",
        value=parsed.metadata.get("faculty_name") or profile.get("faculty_name") or "",
    )
    st.text_input("Sections (automatically detected)", value=", ".join(sections), disabled=True)

    for warning in parsed.warnings:
        st.warning(warning)

    st.markdown("### 4 · Evaluation components")
    enriched: list[dict[str, Any]] = []
    for component in parsed.components:
        item = dict(component)
        item["weight"] = component_weight(profile.get("components", []), item["name"])
        enriched.append(item)

    component_df = pd.DataFrame(
        [
            {
                "Component": component["name"],
                "Maximum marks": component.get("max_marks"),
                "Course weight %": component.get("weight"),
            }
            for component in enriched
        ]
    )
    st.dataframe(component_df, use_container_width=True, hide_index=True)

    st.markdown("### 5 · Preview student marks")
    filter_options = ["All sections"] + sections
    section_filter = st.selectbox("Preview section", filter_options)
    preview = parsed.students
    if section_filter != "All sections":
        preview = preview[preview["section"].astype(str).str.upper() == section_filter.upper()]
    preview_cols = ["section", "roll_no", "student_name"] + [c["name"] for c in enriched]
    st.caption(f"Showing {len(preview)} of {len(parsed.students)} students.")
    st.dataframe(preview[preview_cols], use_container_width=True, height=420, hide_index=True)

    st.markdown("### 6 · Choose what students can see")
    default_release = [component["name"] for component in enriched]
    released = st.multiselect(
        "Released components",
        options=default_release,
        default=default_release,
        help="The same release selection applies to every detected section in this workbook.",
    )

    if not st.button("Publish / Update All Sections", type="primary", use_container_width=True):
        return
    if not course_name.strip():
        st.error("Course name is required.")
        return
    if not released:
        st.warning("Select at least one component to release.")
        return

    duplicate_rolls = parsed.students[parsed.students["roll_no"].duplicated(keep=False)]
    if not duplicate_rolls.empty:
        st.error(
            "Publishing stopped because duplicate roll numbers exist across the detected sections. "
            "Correct the workbook and upload it again."
        )
        return

    metadata = {
        "course_name": course_name.strip(),
        "programme": programme,
        "term": term,
        "academic_year": academic_year.strip(),
        "faculty_name": faculty_name.strip(),
        "section": ", ".join(sections),
    }
    publish_course(
        metadata=metadata,
        components=enriched,
        released=released,
        students=parsed.students,
    )
    st.success(
        f"Published successfully for {len(sections)} section(s) and {len(parsed.students)} students. "
        "Students can now select their section and view the components you released."
    )
    st.balloons()


def render_manage_tab() -> None:
    st.markdown("### Published courses")
    courses = list_courses()
    if not courses:
        st.info("No courses have been published in this running app instance.")
        return

    for course in courses:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            section_text = course.get("section", "") or "—"
            c1.markdown(
                f"**{course['course_name']}**  \n"
                f"{course['programme']} · Term {course['term']} · "
                f"{course.get('academic_year','')} · Sections {section_text}"
            )
            if c2.button("Delete", key=f"delete_{course['id']}"):
                delete_course(course["id"])
                st.rerun()


def faculty_page() -> None:
    hero(
        "Faculty Workspace",
        "Upload once. Review clearly. Release selectively.",
        "The workbook parser detects all main section sheets in the standard template, combines them safely, and lets you control which evaluation components students can see.",
    )
    if not faculty_authenticated():
        login_box()
        return

    col_a, col_b = st.columns([5, 1])
    col_a.success("Faculty access authenticated")
    if col_b.button("Logout", use_container_width=True):
        st.session_state.faculty_authenticated = False
        st.rerun()

    tab_publish, tab_manage = st.tabs(["📤 Upload & Publish", "📚 Published Courses"])
    with tab_publish:
        render_publish_tab()
    with tab_manage:
        render_manage_tab()


def about_developer_page() -> None:
    hero(
        "About the Developer",
        "Dr. Alok Tiwari",
        "Assistant Professor, Big Data Analytics at Goa Institute of Management · AI researcher · educator · builder of applied academic and decision-support tools.",
    )

    left, right = st.columns([1, 3])
    with left:
        st.markdown('<div class="dev-avatar">AT</div>', unsafe_allow_html=True)
        st.markdown("#### Dr. Alok Tiwari")
        st.caption("PhD · Biomedical Engineering · IIT (BHU), Varanasi")
    with right:
        st.markdown(
            "Dr. Alok Tiwari works at the intersection of **machine learning, medical imaging, explainable AI, healthcare analytics, MLOps and management-focused data science**. His academic work combines research, teaching and implementation, with a focus on translating rigorous analytics into useful decisions and learning experiences."
        )
        st.markdown(
            '<div class="pill-row"><span class="pill">Healthcare AI</span><span class="pill">Medical Imaging</span><span class="pill">Explainable AI</span><span class="pill">Data Science</span><span class="pill">MLOps</span><span class="pill">GenAI & Pedagogy</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("### Focus areas")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            """<div class="portal-card"><div class="mini-icon">🏥</div><h3>Responsible AI for healthcare</h3><p>Medical imaging, clinical decision support, transfer learning and explainable AI systems.</p></div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """<div class="portal-card"><div class="mini-icon">🧑‍🏫</div><h3>Teaching innovation</h3><p>Analytics, GenAI-enabled pedagogy, faculty development and management-oriented technical learning.</p></div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            """<div class="portal-card"><div class="mini-icon">⚙️</div><h3>Applied AI systems</h3><p>Production-ready workflows, MLOps, data products and practical decision-support applications.</p></div>""",
            unsafe_allow_html=True,
        )

    st.markdown("### Explore more")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.link_button("🌐 Academic Website", DEVELOPER_SITE, use_container_width=True)
    with b2:
        st.link_button("💻 GitHub", DEVELOPER_GITHUB, use_container_width=True)
    with b3:
        st.link_button("💼 LinkedIn", DEVELOPER_LINKEDIN, use_container_width=True)

    st.caption("Developer profile information is summarized from the public academic website linked above.")


def sidebar_brand() -> None:
    st.sidebar.markdown("## 🎓 GIM Marks Portal")
    st.sidebar.caption("Faculty-controlled academic marks release")
    st.sidebar.divider()


def footer() -> None:
    st.markdown(
        f'<div class="footer-note">GIM Marks Portal · Developed by Dr. Alok Tiwari · <a href="{DEVELOPER_SITE}" target="_blank">Academic Website</a></div>',
        unsafe_allow_html=True,
    )


def main() -> None:
    apply_theme()
    sidebar_brand()
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Home", "🎓 Student Portal", "🔐 Faculty Portal", "👨‍💻 About Developer"],
        key="main_nav",
    )
    st.sidebar.divider()
    st.sidebar.caption("Multi-Section Streamlit Edition")
    st.sidebar.caption("Runtime uploads · Selective release · Section-aware student lookup")

    if page == "🏠 Home":
        home_page()
    elif page == "🎓 Student Portal":
        student_page()
    elif page == "🔐 Faculty Portal":
        faculty_page()
    else:
        about_developer_page()
    footer()


if __name__ == "__main__":
    main()
