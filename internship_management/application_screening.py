# Copyright (c) 2026, KRCS and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime


def _get_application_status_to_decision_map() -> dict[str, str]:
	# Maps screening decision -> Internship Application fields.
	# We try to keep compatibility with existing schema by setting both:
	# - `screening_decision` (if present)
	# - `application_status` (if present)
	# - `recommendation` (if present)
	return {
		"Pending": "Under Review",
		"Shortlisted": "Shortlisted",
		"Rejected": "Rejected",
		"Reserved": "Reserved",
	}


def _decision_to_recommendation(decision: str) -> str | None:
	# Heuristic recommendation values used by the app.
	# If your Internship Application doctype uses different values,
	# adjust here.
	m = {
		"Pending": "Proceed to Interview",
		"Shortlisted": "Proceed to Interview",
		"Reserved": "Keep in Reserve",
		"Rejected": "Reject",
	}
	return m.get(decision)


def _safe_get_application_fields(app_doc: Document) -> dict:
	fields = {
		"name": app_doc.name,

		"applicant_name": (

			getattr(app_doc, "first_name", "")
			+ (
				" " + getattr(app_doc, "last_name", "")
				if getattr(app_doc, "last_name", None)
				else ""
			)
		),


		"email": getattr(app_doc, "email", None),
		"department": (
			getattr(app_doc, "preferred_department", None)
			or getattr(app_doc, "department", None)
		),

		"vacancy_applied_for": getattr(app_doc, "vacancy_applied_for", None),
		"level_of_study": getattr(app_doc, "level_of_study", None),
		"application_status": getattr(app_doc, "application_status", None) or getattr(app_doc, "status", None),
		"submission_date": getattr(app_doc, "creation", None) or getattr(app_doc, "date", None),
	}
	fields["screening_decision"] = getattr(app_doc, "screening_decision", None)
	fields["recommendation"] = getattr(app_doc, "recommendation", None)
	fields["meets_minimum_requirements"] = getattr(app_doc, "meets_minimum_requirements", None)
	fields["screening_remarks"] = getattr(app_doc, "screening_remarks", None)
	return fields


def _send_regret_email_if_needed(app_doc: Document, *, decision: str) -> None:
	# Regret notifications are only for unsuccessful applicants.
	if decision not in ("Rejected", "Reserved"):
		return

	# Convention: mark fields if present.
	already_sent = bool(getattr(app_doc, "regret_email_sent", 0) or getattr(app_doc, "regret_notification_sent", 0))
	if already_sent:
		return

	email = getattr(app_doc, "email", None)
	if not email:
		return

	vacancy = None
	if getattr(app_doc, "vacancy_applied_for", None):
		try:
			vacancy = frappe.get_doc("Internship Vacancy", app_doc.vacancy_applied_for)
		except Exception:
			vacancy = None

	vacancy_title = getattr(vacancy, "vacancy_title", None) if vacancy else None
	subject = _("Internship Application Update")
	body = _(
		"Dear {first_name} {last_name},\n\n"
		"Thank you for applying for {vacancy}. After screening, we regret to inform you that your application is {decision}.\n\n"
		"Regards,\n"
		"Internship Management Team"
	).format(
		first_name=getattr(app_doc, "first_name", ""),
		last_name=getattr(app_doc, "last_name", ""),
		vacancy=vacancy_title or getattr(app_doc, "vacancy_applied_for", ""),
		decision=decision,
	)

	# Use Frappe mail sending (system email settings should be configured).
	try:
		frappe.sendmail(
			recipients=[email],
			subject=subject,
			message=body,
		)
	except Exception:
		# Fail-safe: don't block screening decision.
		return

	# Persist flags.
	if hasattr(app_doc, "regret_email_sent"):
		app_doc.regret_email_sent = 1
	if hasattr(app_doc, "notification_date"):
		app_doc.notification_date = now_datetime()
	if hasattr(app_doc, "regret_notification_sent"):
		app_doc.regret_notification_sent = 1
	

def screen_application(
	*,
		application_name: str,
		decision: str,
		minimum_requirements_met: bool,
		remarks: str | None = None,
		send_regret_if_rejected: bool = True,
) -> Document:
	app_doc = frappe.get_doc("Internship Application", application_name)

	decision_norm = (decision or "").strip()
	if decision_norm not in ("Pending", "Shortlisted", "Rejected", "Reserved"):
		raise frappe.ValidationError("Invalid screening decision")

	allowed_transitions = {
		# Allow reviewers to move from Pending/Under Review to any terminal state.
		"Pending": ["Pending", "Shortlisted", "Rejected", "Reserved"],
		"Under Review": ["Pending", "Shortlisted", "Rejected", "Reserved"],
		"Shortlisted": ["Shortlisted", "Reserved"],
		"Reserved": ["Reserved"],
		"Rejected": ["Rejected"],
	}
	current_status = getattr(app_doc, "application_status", None) or getattr(app_doc, "status", None) or ""
	# Normalize current_status to our decision keys if possible.
	current_key = current_status
	if current_status in ("Under Review", "Submitted"):
		current_key = "Pending"
	if current_key not in allowed_transitions:
		current_key = "Pending"

	if current_key in allowed_transitions and decision_norm not in allowed_transitions[current_key]:
		raise frappe.ValidationError("Decision transition not allowed")

	# Determine mapping.
	status_value = _get_application_status_to_decision_map().get(decision_norm)
	recommendation_value = _decision_to_recommendation(decision_norm)

	# Persist on Internship Application (only if fields exist).
	if hasattr(app_doc, "screening_decision"):
		app_doc.screening_decision = decision_norm
	if hasattr(app_doc, "application_status") and status_value:
		app_doc.application_status = status_value
	if hasattr(app_doc, "status") and status_value:
		# Some doctypes may use `status` for workflow.
		app_doc.status = status_value
	if hasattr(app_doc, "recommendation") and recommendation_value:
		app_doc.recommendation = recommendation_value
	if hasattr(app_doc, "meets_minimum_requirements"):
		app_doc.meets_minimum_requirements = 1 if minimum_requirements_met else 0
	if hasattr(app_doc, "screening_remarks"):
		app_doc.screening_remarks = remarks
	if hasattr(app_doc, "screened_on"):
		app_doc.screened_on = now_datetime()

	# Create audit record.
	from frappe.utils import now_datetime as _nd
	checklist_snapshot = {
		"minimum_requirements_met": bool(minimum_requirements_met),
		"remarks": remarks or "",
	}
	record = frappe.get_doc(
		{
			"doctype": "Application Screening Record",
			"application": app_doc.name,
			"vacancy_applied_for": getattr(app_doc, "vacancy_applied_for", None),
			"reviewer": frappe.session.user,
			"department": getattr(app_doc, "preferred_department", None)
				or getattr(app_doc, "department", None),
			"screening_decision": decision_norm,
			"minimum_requirements_met": 1 if minimum_requirements_met else 0,
			"checklist_snapshot": checklist_snapshot,
			"remarks": remarks or "",
			"screening_date": _nd(),
			"recommendation": recommendation_value,
		}
	)
	record.insert(ignore_permissions=True)

	app_doc.flags.ignore_validate_update_after_submit = True
	app_doc.save(ignore_permissions=True)

	if send_regret_if_rejected and decision_norm in ("Rejected", "Reserved"):
		_send_regret_email_if_needed(app_doc, decision=decision_norm)
		# save updated flags after email
		app_doc.save(ignore_permissions=True)

	return app_doc


def get_screening_queue(*, filters: dict | None = None, limit: int = 50) -> dict:
	filters = filters or {}

	# Build query with best-effort field names.
	app_filters = {}
	if filters.get("department"):
		app_filters["preferred_department"] = filters["department"]
	if filters.get("vacancy_applied_for"):
		app_filters["vacancy_applied_for"] = filters["vacancy_applied_for"]
	if filters.get("qualification"):
		# Level of study stored in level_of_study
		app_filters["level_of_study"] = ("like", f"%{filters['qualification']}%")
	if filters.get("institution_name"):
		app_filters["institution_name"] = filters["institution_name"]
	if filters.get("status"):
		# application_status OR status
		app_filters["application_status"] = filters["status"]

	if filters.get("submission_date_from"):
		app_filters["creation"] = (">=", filters["submission_date_from"])
	if filters.get("submission_date_to"):
		app_filters.setdefault("creation", ("<=", filters["submission_date_to"]))

	items = frappe.get_all(
		"Internship Application",
		filters=app_filters,
		fields=[
			"name",
			"first_name",
			"last_name",
			"preferred_department",
			"vacancy_applied_for",
			"level_of_study",
			"application_status",
			"status",
			"meets_minimum_requirements",
			"screening_decision",
		],
		limit_page_length=limit,
		order_by="creation desc",
	)

	# Normalize key fields so the frontend contract stays stable even if
	# the underlying doctype uses alternate field names.








	for it in items:

		it["applicant_name"] = ((it.get("first_name") or "") + " " + (it.get("last_name") or "")).strip()
		it["department"] = it.pop("preferred_department", None)

		it["application_status"] = it.get("application_status") or it.get("status")

	return {"items": items}


def get_application_for_screening(application_name: str) -> dict:
	if not application_name or not str(application_name).strip():
		raise frappe.ValidationError("application_name is required")
	application_name = str(application_name).strip()
	app_doc = frappe.get_doc("Internship Application", application_name)
	data = _safe_get_application_fields(app_doc)

	# Add vacancy title if possible
	if data.get("vacancy_applied_for"):
		try:
			vac = frappe.get_doc("Internship Vacancy", data["vacancy_applied_for"])
			data["vacancy_title"] = getattr(vac, "vacancy_title", None)
		except Exception:
			pass
	return {"application": data}

