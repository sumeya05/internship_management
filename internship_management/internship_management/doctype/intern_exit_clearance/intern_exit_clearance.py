# Copyright (c) 2026,  KRCS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class InternExitClearance(Document):
	def validate(self):
		import frappe

		# Guard allowed status transitions
		if not frappe.db.exists("Intern Exit Clearance", self.name):
			return

		old_status = frappe.db.get_value("Intern Exit Clearance", self.name, "status")
		new_status = self.status
		if not old_status or old_status == new_status:
			return

		allowed = {
			"Pending Clearance": ["Cleared", "Closed"],
			"Cleared": ["Closed"],
			"Closed": [],
		}
		if new_status not in allowed.get(old_status, []):
			raise frappe.ValidationError(
				f"Invalid status transition from {old_status} to {new_status}"
			)

