# Build Validation

The interactive multi-section build was validated against the supplied workbook:

`Marksheet-Storytelling using dataviz-Term-2-Batch-2026-28.xlsx`

## Detected main marks sheets

- Section-A — 54 students
- Section-B — 55 students
- Section-C — 52 students
- Total — 161 students

## Correctly ignored helper sheets

- CP-Sec-A
- CP-Sec-B
- CP-Sec-C

## Detected components

- Class Participation — max 10
- Quiz — max 15
- Mid-Term Examination — max 60
- End-Term Examination — max 90

## Blank grouped-exam correction

Blank End-Term question cells are retained as `Not entered`. The parser does not interpret a cached Excel `SUM(...) = 0` result as a genuine zero when no End-Term marks have been entered.

## Student section selection

The Student Portal now includes a Section dropdown. Published sections are discovered dynamically for the selected Programme and Term. Student retrieval is filtered by:

- Programme
- Term
- Section
- Roll Number

A roll number stored in Section A does not return a result when the user selects Section B.

## UI improvements

The app now includes:

- responsive custom visual theme
- redesigned landing page
- styled sidebar navigation
- interactive student score cards
- per-component progress bars
- released weighted-total visualization
- enhanced faculty upload/review workflow
- About Developer page with public professional links

## Automated checks

Included automated tests cover:

- multi-section workbook parsing
- section counts
- helper-sheet exclusion
- component maximum marks
- blank grouped-exam handling
- publishing records with blank component marks
- dynamic available-section discovery
- section-filtered student lookup

**All 5 included tests pass.**
