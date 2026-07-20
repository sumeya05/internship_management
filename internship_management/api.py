# Copyright (c) 2026, KRCS and contributors
# For license information, please see license.txt

import frappe
from frappe import _

from internship_management.portal_validations import (
	validate_application_against_vacancy,
	validate_advertisement_is_open_for_application,
)






def _get_published_opportunity_advertisements(filters=None):
	"""Return published opportunity advertisements for applicant portal."""
	filters = filters or {}
	filters = {**filters}

	filters.setdefault("status", "Published")

	from frappe.utils import nowdate
	# Hide ads whose deadline has passed.
	filters.setdefault("application_deadline", (">=", nowdate()))

	# We join to the linked Internship Vacancy (field: vacancy) to expose location/duration/etc.
	# Note: Vacancy `location` is Data in schema; leave as-is.
	rows = frappe.get_all(
		"Opportunity Advertisement",
		filters={k: v for k, v in filters.items()},
		fields=[
			"name",
			"department",
			"location",
			"number_of_vacancies",
			"qualifications_required",
			"skills_required",
			"responsibilities",
			"duration",
			"required_documents",
			"application_deadline",
			"special_instructions",
			"vacancy",
			"publish_date",
			"status",
		],

		order_by="publish_date desc, creation desc",
		limit_page_length=50,
	)

	# Enrich with vacancy details (location, duration, responsibilities, skills, etc.)
	for r in rows:
		if not r.get("vacancy"):
			continue
		v = frappe.db.get_value(
			"Internship Vacancy",
			r["vacancy"],
			[
				"vacancy_title",
				"location",
				"number_of_positions",
				"duration",
				"responsibilities",
				"required_skills",
				"required_qualifications",
			],
			as_dict=True,
		)
		r["vacancy_title"] = (v or {}).get("vacancy_title")
		# Only enrich if vacancy fields are not already present on the advertisement.
		r["location"] = r.get("location") or (v or {}).get("location")
		r["duration"] = r.get("duration") or (v or {}).get("duration")
		r["responsibilities"] = r.get("responsibilities") or (v or {}).get("responsibilities")
		# Vacancy schema uses required_skills/required_qualifications; map to advertisement keys.
		r["skills_required"] = r.get("skills_required") or (v or {}).get("required_skills")
		r["qualifications_required"] = r.get("qualifications_required") or (v or {}).get("required_qualifications")
		r["number_of_vacancies"] = r.get("number_of_vacancies") or (v or {}).get("number_of_positions")


	return rows


@frappe.whitelist(allow_guest=True)
def get_available_internships():
	"""Public endpoint used by the applicant portal to list published opportunity advertisements."""
	return {"vacancies": _get_published_opportunity_advertisements()}



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

	# The portal submits `vacancy_applied_for` but we now treat it as an
	# Opportunity Advertisement id.
	advertisement_id = data.get("vacancy_applied_for")
	if not advertisement_id:
		raise ValidationError("Opportunity advertisement is required")

	email = strip(data.get("email") or "")
	if not email:
		raise ValidationError("Email is required")

	ad_doc = frappe.get_doc("Opportunity Advertisement", advertisement_id)
	validate_advertisement_is_open_for_application(advertisement=ad_doc)

	vacancy_id = getattr(ad_doc, "vacancy", None)
	if not vacancy_id:
		raise ValidationError("Linked vacancy is missing")

	# Best-effort screening against the linked vacancy.
	validate_application_against_vacancy(vacancy_id=vacancy_id, applicant_payload=data)

	# --- Mandatory field validation (Section 6.4) ---
	mandatory_fields = {
		"first_name": "First name",
		"last_name": "Last name",
		"dob": "Date of birth",
		"gender": "Gender",
		"national_id": "National ID",
		"institution": "School/Institution name",
		"course": "Course/Programme",
		"email": "Email",
		"phone": "Contact phone",
		"vacancy_applied_for": "Opportunity/Vacancy",
		"county": "County",
		"sub_county": "Sub County",
		"level_of_study": "Level of study",
		"year_of_study": "Year of study",
		# internship period required (in this portal template we don't collect it,
		# but the backend schema has internship_start_date/internship_end_date).
		"internship_start_date": "Internship start date",
		"internship_end_date": "Internship end date",
		"preferred_department": "Preferred department",
	}

	# Map portal payload keys to the mandatory schema keys we expect.
	# Current portal uses: vacancy_applied_for, first_name, last_name, dob, gender, national_id,
	# institution, course, county, sub_county, level_of_study, year_of_study, email, phone.
	# We'll also accept alternate keys if provided.
	if "level_of_study" not in data and data.get("qualification"):
		data["level_of_study"] = data.get("qualification")

	missing = []
	for k, label in mandatory_fields.items():
		if k == "internship_start_date":
			v = data.get("internship_start_date")
		elif k == "internship_end_date":
			v = data.get("internship_end_date")
		elif k == "preferred_department":
			v = data.get("preferred_department")
		else:
			v = data.get(k)
		if not v and v != 0:
			missing.append(label)

	if missing:
		raise ValidationError(
			"Missing mandatory fields: " + ", ".join(missing)
		)

	# Required attachments (CV + School Letter per user confirmation)
	cv_payload = data.get("cv_file") or data.get("curriculum_vitae_cv") or data.get("cv")
	school_letter_payload = data.get("school_letter_file") or data.get("school_letter")
	if not cv_payload:
		raise ValidationError("CV attachment is required")
	if not school_letter_payload:
		raise ValidationError("School letter/recommendation attachment is required")

	# Create application.
	doc = frappe.get_doc(
		{
			"doctype": "Internship Application",
			"vacancy_applied_for": vacancy_id,

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
			"level_of_study": data.get("level_of_study"),
			"year_of_study": data.get("year_of_study"),

			"preferred_department": data.get("preferred_department"),
			"preferred_location": data.get("preferred_location") or data.get("county"),

			"internship_start_date": data.get("internship_start_date"),
			"internship_end_date": data.get("internship_end_date"),
			"internship_duration": data.get("internship_duration"),

			"status": "Received",
			# Keep submit date for reference.
			"date": frappe.utils.nowdate(),
		}
	)

	# Attach files if frontend provides IDs.
	# NOTE: Current portal submits raw file objects; we cannot reliably map them to File IDs.
	# This code still supports the app's expected payload format:
	# - file_ids / attachments: list of File IDs to append to an attachments child table.
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

	# Application reference number requirement: return doc.name
	return {
		"reference_number": doc.name,
		"name": doc.name,
		"status": doc.status,
		"message": _("Application submitted successfully"),
	}


from internship_management.application_screening import (
	get_application_for_screening as _get_application_for_screening,
	get_screening_queue as _get_screening_queue,
	screen_application as _screen_application,
)


@frappe.whitelist()
def get_screening_queue(filters: dict | None = None, limit: int = 50):
	"""Reviewer endpoint: fetch applications for screening queue."""
	if filters is not None and not isinstance(filters, dict):
		raise frappe.ValidationError("filters must be a dict")
	limit = int(limit) if limit is not None else 50
	limit = max(1, min(limit, 200))
	return _get_screening_queue(filters=filters, limit=limit)



@frappe.whitelist()
def get_application_for_screening(application_name: str):
	"""Reviewer endpoint: fetch application details for decision UI."""
	return _get_application_for_screening(application_name=application_name)


@frappe.whitelist()
def screen_application(payload: dict):
	"""Reviewer endpoint: persist screening decision and audit record."""
	return _screen_application(
		application_name=payload.get("application_name"),
		decision=payload.get("decision"),
		minimum_requirements_met=bool(payload.get("minimum_requirements_met")),
		remarks=payload.get("remarks"),
		send_regret_if_rejected=payload.get("send_regret_if_rejected", True),
	)



@frappe.whitelist(allow_guest=True)
def get_my_application_status(reference_number: str = None, email: str = None):

	"""Allow applicants to view status of their submitted internship applications."""

	from frappe import ValidationError

	reference_number = (reference_number or "").strip()
	email = (email or "").strip()
	if not reference_number and not email:
		raise ValidationError("Reference number or email is required")

	filters = {}
	if reference_number:
		filters["name"] = reference_number
	if email:
		filters["email"] = email

	app = frappe.get_all(
		"Internship Application",
		filters=filters,
		fields=["name", "status", "vacancy_applied_for", "first_name", "last_name", "email"],
		limit_page_length=1,
	)
	if not app:
		return {"found": False, "message": "No application found"}

	row = app[0]
	return {
		"found": True,
		"reference_number": row["name"],
		"status": row["status"],
		"vacancy_applied_for": row.get("vacancy_applied_for"),
	}


