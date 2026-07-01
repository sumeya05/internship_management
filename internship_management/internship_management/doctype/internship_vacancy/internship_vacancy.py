# Copyright (c) 2026,  KRCS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class InternshipVacancy(Document):
	def validate(self):
		# Enforce allowed status transitions (server-side guard)
		import frappe
		if not self.name:
			return

		# When updating an existing doc, block illegal status changes


		if frappe.db.exists("Internship Vacancy", self.name):
			old_status = frappe.db.get_value("Internship Vacancy", self.name, "status")
		else:
			old_status = None

		if old_status and old_status != self.status:
			allowed = {
				"Draft": ["Pending HR Approval"],
				"Pending HR Approval": ["Approved", "Rejected"],
				"Approved": ["Rejected"],  # per existing workflow revoke
				"Rejected": [],
			}
			if self.status not in allowed.get(old_status, []):
				raise frappe.ValidationError(f"Invalid status transition from {old_status} to {self.status}")

