# GIM Marks Release Portal — Interactive Multi-Section Streamlit Edition

A lightweight Streamlit application for faculty-controlled release of student marks from the standard GIM marksheet workbook.

## What this version does

- Faculty login protected by a password stored in **Streamlit Secrets**.
- Faculty uploads a **Course Profile PDF** and the **complete marksheet workbook** at runtime.
- Source marksheets and Course Profiles are **not stored in the public GitHub repository**.
- Automatically detects and combines standard main section sheets such as:
  - `Section-A`
  - `Section-B`
  - `Section-C`
- Ignores helper sheets such as `CP-Sec-A`, `CP-Sec-B`, and `CP-Sec-C`.
- Faculty can preview marks for all sections or one section at a time.
- Faculty chooses which evaluation components are released.
- Students search using **Programme + Term + Section + Roll Number**.
- The student query verifies that the selected section matches the student's stored section.
- Results are shown as interactive score cards with progress indicators and released weighted totals.
- Includes an **About Developer** page for Dr. Alok Tiwari with links to his academic website, GitHub, and LinkedIn.
- Includes a redesigned responsive interface with a modern landing page, styled navigation, cards, metrics, and mobile-friendly spacing.

## Verified against the supplied workbook

The current parser detects:

| Worksheet | Section | Students |
|---|---:|---:|
| Section-A | A | 54 |
| Section-B | B | 55 |
| Section-C | C | 52 |
| **Total** | **A, B, C** | **161** |

It ignores the three CP calculation sheets and detects the four main evaluation components:

- Class Participation — maximum 10
- Quiz — maximum 15
- Mid-Term Examination — maximum 60
- End-Term Examination — maximum 90

Blank End-Term cells remain **blank / not entered** rather than being misread as zero when Excel has a cached `SUM(...) = 0` formula.

## Student lookup

The student portal asks for:

1. Programme
2. Term
3. Section
4. Roll Number

Available sections are read dynamically from published data for the selected Programme and Term. If no course has yet been published for that combination, the interface falls back to A/B/C so the page remains usable.

The backend checks both the Roll Number **and** Section before returning results.

## Quick deployment

1. Push this repository to GitHub.
2. Create a new app on Streamlit Community Cloud.
3. Set the main file to `app.py`.
4. Open **App settings → Secrets** and add:

```toml
FACULTY_PASSWORD = "<YOUR_PRIVATE_FACULTY_PASSWORD>"
```

For your deployment, use the private faculty password you chose. Do not commit it to GitHub.

5. Deploy the app.

For complete setup and operating instructions, read [`HANDBOOK.md`](HANDBOOK.md).

## Developer profile

The in-app **About Developer** page summarizes the public academic profile of **Dr. Alok Tiwari**, Assistant Professor, Big Data Analytics at Goa Institute of Management.

- Website: https://dr-alok-tiwari.github.io/
- GitHub: https://github.com/dr-alok-tiwari
- LinkedIn: https://www.linkedin.com/in/dr-alok-tiwari/

## Important storage note

Published parsed marks are stored in a local SQLite database inside the running Streamlit instance. This keeps them out of GitHub, but Streamlit Community Cloud local storage is not guaranteed to persist permanently across app rebuilds or restarts. For this basic version, faculty can re-upload and republish after a reset.

## Security note

Programme + Term + Section + Roll Number is more precise than roll-number-only lookup, but it is **not strong authentication**. A person who knows another student's details could still attempt to query released marks. Before institution-wide or high-stakes use, add GIM Microsoft SSO, institutional email OTP, or another identity-verification mechanism.
