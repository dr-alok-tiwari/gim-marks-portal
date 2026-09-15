# Security Notes

## Faculty password

The faculty password must be stored only in Streamlit Secrets as `FACULTY_PASSWORD`. Do not hard-code it into the public repository.

## Uploaded files

Course Profile and marksheet files are uploaded at runtime. The repository does not include the source files. Do not add real `.csv`, `.xlsx`, `.xls`, `.pdf`, `.db`, or `.streamlit/secrets.toml` files to GitHub.

## Multi-section data

All detected sections are published into one course record, with each student retaining their own section. The Student Portal asks for Programme + Term + Section + Roll Number. The backend filters on both roll number and section before returning marks.

This improves lookup precision and helps prevent accidental cross-section retrieval, but section selection is **not authentication**.

## Runtime persistence

The basic Streamlit Community Cloud version stores parsed published marks in SQLite on the running instance. Local cloud-instance storage can be reset during rebuilds/restarts. Do not treat it as a permanent institutional database.

## Student authentication limitation

Programme + Term + Section + Roll Number is not strong identity verification. Someone who knows another student's details could still attempt to query released marks. Add Microsoft SSO or institutional OTP before using the system for high-stakes production deployment.

## Public developer information

The About Developer page includes only public professional information and outbound links drawn from Dr. Alok Tiwari's public academic website/profile. No private credentials or student data are embedded there.
