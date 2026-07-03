# Copyright (c) 2026, KRCS and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import ValidationError


def _parse_level(value: str | None) -> str | None:
	if not value:
		return None
	return str(value).strip().lower()


def _normalize_course(value: str | None) -> str | None:
	if not value:
		return None
	return str(value).strip().lower()


def validate_application_against_vacancy(*, vacancy_id: str, applicant_payload: dict) -> None:
	"""Server-side screening rules for public portal submissions.

	Rules (Phase 5 screening):
	- Minimum qualification rule (best-effort substring match)
	- Course match rule (case-insensitive substring match)
	- Required documents uploaded rule

	Note: current Vacancy doctype stores required_qualifications (Small Text)
	and required_skills (Data) and does not explicitly store course/program lists.
	This validator is intentionally best-effort and will pass if the vacancy fields
	are empty.
	"""

	vac = frappe.get_doc("Internship Vacancy", vacancy_id)

	# 1) Qualification rule (best-effort)
	req_qual = (getattr(vac, "required_qualifications", None) or "").strip().lower()
	app_level = _parse_level(applicant_payload.get("level_of_study") or applicant_payload.get("qualification"))

	if req_qual:
		if not app_level:
			raise ValidationError("Qualification/level of study is required")
		# Accept if applicant level contains any word/phrase from required_qualifications.
		# This is simplistic due to current schema.
		if req_qual not in app_level and app_level not in req_qual:
			raise ValidationError("Minimum qualification requirement not met")

	# 2) Course match rule (best-effort)
	req_course = (getattr(vac, "required_skills", None) or "").strip().lower()
	app_course = _normalize_course(applicant_payload.get("course"))

	# The current vacancy schema uses `required_skills`; we treat it as course/program requirement
	# to enable basic filtering until the schema is extended.
	if req_course:
		if not app_course:
			raise ValidationError("Course is required")
		if req_course not in app_course and app_course not in req_course:
			raise ValidationError("Required course/program does not match")

	# 3) Required documents uploaded rule
	# Vacancy requirements in the Phase description are ID, CV, recommendation letter, school letter, certificates.
	# Current portal template enforces CV required, others optional. We enforce at least:
	# - CV file provided
	# - ID/NID file optional (only required if provided by vacancy's schema later)
	# We'll require `cv_file` present in payload.
	cv = applicant_payload.get("cv_file") or applicant_payload.get("cv")
	if not cv:
		raise ValidationError("CV upload is required")

	# If frontend provided file IDs under `file_ids` we could check them, but this app currently
	# accepts simplified payload.
	return

