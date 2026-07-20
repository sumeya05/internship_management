# Copyright (c) 2026,  KRCS and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe
from frappe.model.document import Document


class InternshipVacancy(Document):
	def _require_field_for_status_change(self, *, fieldname: str, message: str) -> None:
		val = (getattr(self, fieldname, None) or "").strip() if fieldname else ""
		if not val:
			raise frappe.ValidationError(message)

	def _assert_hr_action_allowed(self) -> None:
		if not (
			frappe.has_role("HR Officer")
			or frappe.has_role("HR Manager")
			or frappe.has_role("Management/Approver")
			or frappe.has_role("System Administrator")
		):
			raise frappe.ValidationError("Only HR can perform this action")

	def _validate_requirements_for_approval(self) -> None:
		missing = []
		if not (self.vacancy_title or "").strip():
			missing.append("Vacancy Title")
		if not getattr(self, "department", None):
			missing.append("Department")
		if not getattr(self, "number_of_positions", None):
			missing.append("Number of Positions")
		if not (self.required_skills or "").strip():
			missing.append("Required Skills")
		if not (self.required_qualifications or "").strip():
			missing.append("Required Qualifications")
		if not getattr(self, "start_date", None) or not getattr(self, "end_date", None):
			missing.append("Start Date / End Date")

		if missing:
			raise frappe.ValidationError("Missing required fields: " + ", ".join(missing))

	def _validate_department_capacity(self) -> None:
		capacity_field = None
		try:
			from frappe import get_meta

			meta = get_meta("Department")
			for f in (meta.fields or []):
				if getattr(f, "fieldname", None) in {"capacity", "max_positions", "intern_capacity"}:
					capacity_field = f.fieldname
					break
		except Exception:
			capacity_field = None

		if not capacity_field:
			return

		cap = frappe.db.get_value("Department", self.department, capacity_field)
		if cap is None:
			return

		active_filters = {"department": self.department}
		for status_field in ("status", "employment_status", "intern_status"):
			if frappe.db.has_column("tabIntern Profile", status_field):
				active_filters[status_field] = ("Active", "active")
				break

		current_active = (
			frappe.db.count("Intern Profile", active_filters)
			if active_filters
			else frappe.db.count("Intern Profile", {"department": self.department})
		)

		if (current_active + int(self.number_of_positions or 0)) > int(cap):
			raise frappe.ValidationError(
				f"Department capacity exceeded. Current interns: {current_active}, requested: {self.number_of_positions}, capacity: {cap}"
			)

	def _append_approval_history(self) -> None:
		if not getattr(self, "name", None):
			return

		action_map = {
			"Approved": ("Approved", None),
			"Rejected": ("Rejected", "hr_rejection_reason"),
			"Returned for Clarification": ("Returned for Clarification", "hr_clarification_request"),
		}
		if self.approval_status not in action_map:
			return

		action_taken, comment_field = action_map[self.approval_status]
		comments = (getattr(self, comment_field, None) if comment_field else None) or ""
		comments = comments.strip()

		if frappe.db.exists(
			"Internship Vacancy Approval History",
			{
				"vacancy": self.name,
				"reviewer": frappe.session.user,
				"action_taken": action_taken,
				"comments": comments,
			},
		):
			return

		h = frappe.get_doc(
			{
				"doctype": "Internship Vacancy Approval History",
				"vacancy": self.name,
				"reviewer": frappe.session.user,
				"action_taken": action_taken,
				"comments": comments,
			}
		)
		h.insert(ignore_permissions=True)

	def validate(self):
		if not self.name:
			return

		old_status = frappe.db.get_value("Internship Vacancy", self.name, "approval_status")
		if old_status and old_status != self.approval_status:
			allowed = {
				"Draft": ["Submitted"],
				"Submitted": ["Approved", "Rejected", "Returned for Clarification"],
				"Returned for Clarification": ["Submitted"],
				"Approved": ["Rejected"],
				"Rejected": [],
			}
			if self.approval_status not in allowed.get(old_status, []):
				raise frappe.ValidationError(
					f"Invalid status transition from {old_status} to {self.approval_status}"
				)

			if self.approval_status == "Approved":
				self._assert_hr_action_allowed()
				self._validate_department_capacity()
				self._validate_requirements_for_approval()
				if not getattr(self, "approved_by", None):
					self.approved_by = frappe.session.user
				self.hr_rejection_reason = None
				self.hr_clarification_request = None

			elif self.approval_status == "Rejected":
				self._assert_hr_action_allowed()
				self._require_field_for_status_change(
					fieldname="hr_rejection_reason",
					message="HR Rejection Reason is required when rejecting a vacancy",
				)
				if not getattr(self, "approved_by", None):
					self.approved_by = frappe.session.user
				self.hr_clarification_request = None

			elif self.approval_status == "Returned for Clarification":
				self._assert_hr_action_allowed()
				self._require_field_for_status_change(
					fieldname="hr_clarification_request",
					message="HR Clarification Request is required when returning a vacancy for clarification",
				)
				self.hr_rejection_reason = None

			self._append_approval_history()

