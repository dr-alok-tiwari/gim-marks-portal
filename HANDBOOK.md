# GIM Marks Release Portal — Setup & Faculty Handbook

## 1. Purpose

This app is intentionally simple. Faculty keeps the source marksheet and Course Profile outside GitHub, logs into the live Streamlit app, uploads both files, chooses which evaluation components to release, and publishes them for student lookup.

The current version supports a single Excel workbook containing **multiple sections using the same GIM marksheet template**.

---

## 2. Repository privacy model

Your public GitHub repository contains only application code and documentation.

Do **not** upload any of the following to GitHub:

- real marksheets
- Course Profiles if they contain information you do not want public
- student data
- the faculty password
- the SQLite runtime database
- `.streamlit/secrets.toml`

The included `.gitignore` blocks common marksheet, PDF, database, and secret files.

---

## 3. Deploy on Streamlit Community Cloud

### Step 1 — Create the GitHub repository

Create a repository such as:

`gim-marks-portal`

Upload the contents of this project folder to the repository.

### Step 2 — Create the Streamlit app

In Streamlit Community Cloud:

1. Choose **Create app**.
2. Select your GitHub repository.
3. Select the correct branch, normally `main`.
4. Set the main file path to:

`app.py`

### Step 3 — Configure the faculty password

Open:

**App → Settings → Secrets**

Add:

```toml
FACULTY_PASSWORD = "<YOUR_PRIVATE_FACULTY_PASSWORD>"
```

For your deployment, set it to the password you have chosen for faculty access.

**Never put the real password in `app.py`, README, or a committed secrets file.**

### Step 4 — Deploy

Save the secrets and deploy/reboot the app if needed.

---

## 4. Faculty workflow

Open **Faculty Portal** and enter the faculty password.

### Upload files

Upload:

1. **Course Profile** — PDF
2. **Marksheet workbook** — XLSX/XLS, or a single-section CSV

For XLSX/XLS, upload the complete workbook, not an individual section exported separately.

---

## 5. How multi-section detection works

The app scans every worksheet in the uploaded workbook.

A worksheet is treated as a main marks sheet only when it contains the standard marks structure, including:

- `Roll No.`
- `Name of Student`
- `Name of Exam(...)`
- `Max Marks`

With your supplied workbook, the app detects:

| Worksheet | Detected section | Students |
|---|---:|---:|
| Section-A | A | 54 |
| Section-B | B | 55 |
| Section-C | C | 52 |

Total: **161 students**.

It ignores helper worksheets:

- `CP-Sec-A`
- `CP-Sec-B`
- `CP-Sec-C`

This means you upload the workbook **once** and do not need separate uploads for A, B, and C.

---

## 6. Course details

After parsing, verify:

- Programme
- Term
- Academic Year
- Course Name
- Faculty Name

The **Sections** field is automatically generated from the workbook and is not manually typed.

For the supplied workbook it displays:

`A, B, C`

---

## 7. Evaluation components

The app detects the standard evaluation components from the marks workbook and takes their course weights from the Course Profile when available.

For the supplied files it recognises:

| Component | Maximum marks |
|---|---:|
| Class Participation | 10 |
| Quiz | 15 |
| Mid-Term Examination | 60 |
| End-Term Examination | 90 |

The Course Profile provides the corresponding course weights.

### Important blank-mark handling

The workbook can contain Excel formulas such as `SUM(...)` in total columns. If all question-level marks for an exam are still blank, Excel may cache the total formula as `0`.

The app now checks the underlying question cells. If all exam question cells are blank, that exam is stored as **not entered**, not as a real zero.

---

## 8. Preview by section

Before publishing, the Faculty Portal shows:

- number of sections detected
- total students
- section-wise student counts
- ignored helper sheets

Use **Preview section** to select:

- All sections
- A
- B
- C

This makes it easy to verify each section before release.

---

## 9. Release marks

Choose the components students should be able to see.

Example:

- Class Participation — release
- Quiz — release
- Mid-Term — release
- End-Term — do not release yet

The same release selection applies to all detected sections in that workbook.

Click:

**Publish / Update All Sections**

The app stores all 161 students under one course record while retaining each student's actual section.

---

## 10. Student workflow

Students open **Student Portal** and enter:

1. Programme
2. Term
3. **Section**
4. Roll Number

The Section dropdown is populated from published data for the selected Programme and Term whenever sections are available. The backend matches both the selected section and the roll number before returning a result.

A student from Section B must select **B** and enter the matching roll number. Their own result card displays Section B rather than the combined `A, B, C` course label.

Only components selected by faculty are displayed.

If a released component has no mark entered yet, the portal displays **Not entered** rather than `0`.

---

## 11. Updating marks

When marks change:

1. Update the original Excel workbook on your computer.
2. Return to Faculty Portal.
3. Upload the Course Profile and revised workbook.
4. Verify the detected section counts.
5. Select the components to release.
6. Click **Publish / Update All Sections**.

Because the course identity is based on Programme + Term + Academic Year + Course Name, the multi-section upload updates the same course instead of creating separate A/B/C course entries.

---

## 12. Workbook template expectations

Continue using the same marksheet template structure.

Recommended main worksheet names:

- `Section-A`
- `Section-B`
- `Section-C`

The parser does not depend only on the worksheet name; it also checks the internal marksheet structure. This prevents helper worksheets from being interpreted as main marks sheets.

If more sections are added using the same template, such as `Section-D`, the app should detect them automatically.

---

## 13. Troubleshooting

### Only one section appears

Make sure you uploaded the full `.xlsx` workbook rather than a CSV exported from one section. A CSV contains only one sheet and therefore only one section.

### A helper sheet appears as a marks section

The current parser requires `Name of Student`, `Name of Exam`, and `Max Marks`, so CP helper sheets using `Roll No / Name / Certificates / Final` are intentionally excluded.

### Student count looks wrong

Check the section summary shown before publishing. In the supplied workbook the expected counts are:

- A = 54
- B = 55
- C = 52
- Total = 161

### End-Term shows Not entered

That is intentional when the End-Term question cells are blank. A cached Excel formula total of zero is not treated as an actual zero mark.

### Marks disappear after Streamlit restart

The basic version uses runtime SQLite storage on Streamlit Community Cloud. Re-upload and republish the workbook. For durable production storage, migrate the database to a managed service later.

---

## 14. Local testing

Create a Python environment, install dependencies, and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

For local secrets, copy:

`.streamlit/secrets.toml.example`

to:

`.streamlit/secrets.toml`

and set your private password there. Never commit that file.

Run tests with:

```bash
pytest -q
```

---

## 15. User interface

The current build includes a redesigned interactive interface:

- responsive gradient landing page
- styled sidebar navigation
- faculty and student workflow cards
- section-aware student search
- score cards with progress indicators
- weighted released-total display
- mobile-friendly spacing
- an **About Developer** page

The About Developer page is based on Dr. Alok Tiwari's public academic profile and links to:

- https://dr-alok-tiwari.github.io/
- https://github.com/dr-alok-tiwari
- https://www.linkedin.com/in/dr-alok-tiwari/

---

## 16. Recommended production improvement

This basic portal intentionally prioritises simplicity. Programme + Term + Section + Roll Number improves lookup accuracy but still does not establish identity. Before institution-wide use, the main recommended upgrade is student authentication using GIM Microsoft SSO or institutional email OTP.
