# Internship Management System (KRCS) — Setup & Usage

**App:** `internship_management`

This document is a focused onboarding package for tomorrow’s delivery. It includes:
- prerequisites
- installation and migration steps
- how to use the public applicant portal
- how to use the HR screening queue

---

## 1) Prerequisites

- A working **Frappe/ERPNext bench**
- Access to the bench directory where apps are installed
- A target Frappe site (example: `your-site.local`)
- Node/JS build tooling is handled by bench when running `bench build`.

---

## 2) Install the app

From your bench directory:

```bash
cd /home/sumeya/frappe/my-bench
bench get-app internship_management --branch version-16
bench install-app internship_management
```

If the app is already present locally:

```bash
cd /home/sumeya/frappe/my-bench
bench install-app apps/internship_management
```

---

## 3) Migrate, build, restart

```bash
bench --site <your-site> migrate
bench --site <your-site> build
bench --site <your-site> restart
```

Start services (if needed):

```bash
bench start
```

---

## 4) Access the pages

### 4.1 Applicant portal (Guest)
- **URL:** `https://<your-site>/internship-portal`
- **Template:** `internship_management/templates/pages/internship_portal.html`

What you can do:
- view published opportunities
- submit an internship application
- check your application status by reference number or email

### 4.2 Screening queue (Reviewer/HR)
- **URL:** `https://<your-site>/screening-queue`
- **Template:** `internship_management/templates/pages/screening_queue.html`

What you can do:
- load applications pending screening
- open details for screening
- save screening decisions

---

## 5) Guest/Public API usage (portal-backed)

These endpoints are whitelisted for guest access and are used by the applicant portal.

### 5.1 List available internships
- Function: `internship_management.api.get_available_internships`
- Output: `{ "vacancies": [ ... ] }`

Business rules enforced:
- `status = "Published"`
- `application_deadline >= today`

### 5.2 Submit an internship application
- Function: `internship_management.api.submit_internship_application`

Required input (high level):
- `vacancy_applied_for` (Opportunity Advertisement id)
- applicant personal fields: `first_name`, `last_name`, `dob`, `gender`, `national_id`, `email`, `phone`
- education fields: `institution`, `course`, `level_of_study`, `year_of_study`
- location fields: `county`, `sub_county`
- `preferred_department`
- internship period fields: `internship_start_date`, `internship_end_date`
- attachments: `cv_file` (required) and `school_letter_file` (required)

Output on success:
- `reference_number` (internship application docname)

### 5.3 Track application status
- Function: `internship_management.api.get_my_application_status`
- Parameters: `reference_number` OR `email`

Output:
- `{ found: bool, status, reference_number, vacancy_applied_for }`

---

## 6) Troubleshooting (quick)

### 6.1 “Opportunity advertisement is not open”
- Verify the **Opportunity Advertisement** status is `Published`
- Verify `application_deadline` has not passed

### 6.2 “CV attachment is required” / “School letter … is required”
- Ensure the payload keys are exactly:
  - `cv_file`
  - `school_letter_file`

### 6.3 “Application deadline has passed”
- The backend compares the advertisement vacancy deadline against `nowdate()`.

---

## 7) Where to look in the codebase

- Applicant portal API: `internship_management/api.py`
- Screening queue logic: `internship_management/application_screening.py`
- Portal validation helpers: `internship_management/portal_validations.py`
- Hooks/routes: `internship_management/hooks.py`, `internship_management/page_routes.py`
- Page templates:
  - `templates/pages/internship_portal.html`
  - `templates/pages/screening_queue.html`

---

## 8) Notes

This document matches what is currently implemented in the repository. If you extend onboarding/HR workflows tomorrow, update this file to include the new entry points.

