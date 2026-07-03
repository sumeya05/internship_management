# Copyright (c) 2026, KRCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from internship_management.portal_validations import (
	validate_application_against_vacancy,
)


def _get_approved_vacancies(filters=None):
	filters = filters or {}
	filters = {**filters}

	# Vacancy is considered public when HR approved.
	filters.setdefault("approval_status", "Approved")

	return frappe.get_all(
		"Internship Vacancy",
		filters={k: v for k, v in filters.items()},
		fields=[
			"name",
			"vacancy_title",
			"department",
			"location",
			"number_of_positions",
			"duration",
			"application_deadline",
		],
		order_by="creation desc",
		limit_page_length=50,
	)


@frappe.whitelist(allow_guest=True)
def get_available_internships():
	"""Public endpoint used by the applicant portal to list approved vacancies."""
	return {"vacancies": _get_approved_vacancies()}


@frappe.whitelist(allow_guest=True)
def submit_internship_application(**data):
	"""Create Internship Application from public form submission.

	Expected keys (best-effort, based on current doctype validation):
	- vacancy_applied_for
	- first_name, last_name, dob, gender, national_id, email, phone
	- institution, course, qualification, year_of_study (may vary depending on your form)
	- county, sub_county (optional)

	Server sets initial workflow state to "Received".

	NOTE: This portal currently submits fields only.
	File uploads require uploading to Frappe's File Manager first to obtain file IDs.
	If `file_ids` (or `attachments`) are provided, we attach them to an `attachments` table
	(if the doctype has such a field).
	"""
	from frappe import ValidationError
	from frappe.utils.data import strip

	vacancy = data.get("vacancy_applied_for")
	if not vacancy:
		raise ValidationError("Vacancy is required")

	email = strip(data.get("email") or "")
	if not email:
		raise ValidationError("Email is required")

	approval_status = frappe.db.get_value(
		"Internship Vacancy", vacancy, "approval_status"
	)
	if approval_status != "Approved":
		raise ValidationError("Vacancy must be Approved to submit an application")

	# Apply server-side screening rules before creating the application.
	validate_application_against_vacancy(vacancy_id=vacancy, applicant_payload=data)

	# Create application.
	doc = frappe.get_doc(
		{
			"doctype": "Internship Application",
			"vacancy_applied_for": vacancy,
			"email": email,
			"first_name": data.get("first_name"),
			"last_name": data.get("last_name"),
			"date_of_birth": data.get("dob"),
			"gender": data.get("gender"),
			"national_id": data.get("national_id"),
			"phone": data.get("phone"),
			"county": data.get("county"),
			"sub_county": data.get("sub_county"),
			"institution_name": data.get("institution"),
			"course": data.get("course"),
			"level_of_study": data.get("level_of_study") or data.get("qualification"),
			"year_of_study": data.get("year_of_study"),
			"status": "Received",
		}
	)

	# Attach files if frontend provides IDs.
	file_ids = data.get("file_ids") or data.get("attachments") or []
	if isinstance(file_ids, str):
		file_ids = [x.strip() for x in file_ids.split(",") if x.strip()]
	for fid in file_ids:
		try:
			doc.append("attachments", {"file": fid})
		except Exception:
			pass

	doc.flags.ignore_validate_update_after_submit = True
	doc.insert(ignore_permissions=True)

	return {"name": doc.name, "status": doc.status, "message": _("Application submitted successfully")}

