# Copyright (c) 2026,  KRCS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document



class InternshipOffer(Document):
	def validate(self):
		# Keep derived/display fields in sync.
		# Candidate name from linked Internship Application.
		if getattr(self, "applicant", None):
			first = frappe.db.get_value("Internship Application", self.applicant, "first_name")
			last = frappe.db.get_value("Internship Application", self.applicant, "last_name")
			if first or last:
				self.candidate_name = f"{(first or '').strip()} {(last or '').strip()}".strip()

			# Preferred location from application if vacancy doesn't provide it.
			preferred_location = frappe.db.get_value(
				"Internship Application", self.applicant, "preferred_location"
			)
			if preferred_location and not getattr(self, "location", None):
				self.location = preferred_location

			# Fill department from application if missing.
			if not getattr(self, "department", None):
				dept = frappe.db.get_value("Internship Application", self.applicant, "department")
				if dept:
					self.department = dept

		if getattr(self, "vacancy", None):
			# Location and duration from vacancy.
			if not getattr(self, "location", None):
				loc = frappe.db.get_value("Internship Vacancy", self.vacancy, "location")
				if loc:
					self.location = loc

			if not getattr(self, "internship_duration", None):
				dur = frappe.db.get_value("Internship Vacancy", self.vacancy, "duration")
				if dur:
					self.internship_duration = dur

	def on_update(self):
		# When candidate response is set, mirror into the overall status.
		if getattr(self, "applicant_response", None):
			if self.applicant_response == "Accepted":
				self.status = "Accepted"
				self.offer_date = self.offer_date or frappe.utils.nowdate()
			elif self.applicant_response == "Declined":
				self.status = "Declined"
				self.response_date = self.response_date or frappe.utils.nowdate()
			elif self.applicant_response == "Pending":
				# Keep Sent/Draft as-is; don't force.
				if not getattr(self, "status", None):
					self.status = "Sent"

	def before_save(self):
		# If acceptance deadline passed and still not accepted/declined/withdrawn, mark as Expired.
		if getattr(self, "status", None) not in {"Accepted", "Declined", "Withdrawn"}:
			if getattr(self, "acceptance_deadline", None):
				from frappe.utils import nowdate
				dl = self.acceptance_deadline
				# acceptance_deadline is a Date; compare using nowdate.
				if dl < nowdate():
					self.status = "Expired"


