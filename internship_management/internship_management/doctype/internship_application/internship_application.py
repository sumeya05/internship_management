# Copyright (c) 2026,  KRCS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class InternshipApplication(Document):
	def validate(self):
		# Required vacancy link
		if not getattr(self, "vacancy_applied_for", None):
			from frappe import ValidationError
			raise ValidationError("Vacancy is required")

		self._validate_vacancy_is_approved()
		self._validate_no_duplicate_application()
		self._validate_status_transition()

	def _validate_status_transition(self) -> None:
		import frappe

		# Determine previous status from DB (ignore new docs)
		if not frappe.db.exists("Internship Application", self.name):
			return

		old_status = frappe.db.get_value("Internship Application", self.name, "status")
		new_status = self.status
		if not old_status or old_status == new_status:
			return

		allowed = {
			"Received": ["Shortlisted", "Rejected"],
			"Shortlisted": ["Interview Scheduled", "Rejected"],
			"Interview Scheduled": ["Offered", "Rejected"],
			"Offered": ["Accepted", "Rejected", "Regret Sent"],
			"Accepted": [],
			"Rejected": [],
			"Regret Sent": [],
		}
		if new_status not in allowed.get(old_status, []):
			raise frappe.ValidationError(
				f"Invalid status transition from {old_status} to {new_status}"
			)

	def _validate_vacancy_is_approved(self) -> None:
		import frappe
		vacancy_status = frappe.db.get_value(
			"Internship Vacancy", self.vacancy_applied_for, "approval_status"
		)
		if not vacancy_status:
			from frappe import ValidationError
			raise ValidationError("Selected vacancy is invalid")
		if vacancy_status != "Approved":
			from frappe import ValidationError
			raise ValidationError("Vacancy must be Approved to submit an application")

	def _validate_no_duplicate_application(self) -> None:
		import frappe
		if not self.email:
			from frappe import ValidationError
			raise ValidationError("Email is required")

		# Enforce uniqueness on (vacancy, email)
		dupes = frappe.get_all(
			"Internship Application",
			filters={
				"vacancy_applied_for": self.vacancy_applied_for,
				"email": self.email,
				"name": ["!=", self.name],
			},
			limit=1,
			pluck="name",
		)
		if dupes:
			from frappe import ValidationError
			raise ValidationError("Duplicate application for this vacancy and email")





