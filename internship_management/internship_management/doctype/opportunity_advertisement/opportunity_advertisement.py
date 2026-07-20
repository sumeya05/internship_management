# Copyright (c) 2026,  KRCS and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class OpportunityAdvertisement(Document):
	def validate(self):
		# Keep advertisement data consistent with linked vacancy when fields
		# are left blank.
		self._populate_from_vacancy_if_missing()

		# When closing, ensure we don't accidentally leave a stale publish_date.
		# (No strict enforcement on publish_date value.)

	def _populate_from_vacancy_if_missing(self) -> None:
		"""Populate spec fields from linked Internship Vacancy if not set."""
		try:
			import frappe
			if not getattr(self, "vacancy", None):
				return
			vac = frappe.get_doc("Internship Vacancy", self.vacancy)
		except Exception:
			return

		if not getattr(self, "department", None):
			self.department = getattr(vac, "department", None)
		if not getattr(self, "location", None):
			self.location = getattr(vac, "location", None)
		if not getattr(self, "number_of_vacancies", None):
			self.number_of_vacancies = getattr(vac, "number_of_positions", None)
		if not getattr(self, "qualifications_required", None):
			self.qualifications_required = getattr(vac, "required_qualifications", None)
		if not getattr(self, "skills_required", None):
			self.skills_required = getattr(vac, "required_skills", None)
		if not getattr(self, "responsibilities", None):
			self.responsibilities = getattr(vac, "responsibilities", None)
		if not getattr(self, "duration", None):
			self.duration = getattr(vac, "duration", None)

	def _require_hr(self) -> None:
		import frappe
		from frappe import ValidationError

		# HR roles as per permissioning: HR Manager / HR Officer.
		user_roles = frappe.get_roles(frappe.session.user)
		if not ({"HR Manager", "HR Officer"} & set(user_roles)):
			raise ValidationError("Only HR can change advertisement status")

	def close_advertisement(self) -> None:
		"""HR closes the advertisement; portal should stop showing it."""
		self._require_hr()
		from frappe.utils import nowdate
		self.status = "Closed"
		# Keep application_deadline as-is.
		if not getattr(self, "publish_date", None):
			self.publish_date = nowdate()

	def extend_advertisement(self, *, new_deadline) -> None:
		"""HR extends the application deadline and re-opens for applicants."""
		self._require_hr()
		from frappe import ValidationError

		if not new_deadline:
			raise ValidationError("new_deadline is required")

		# If the new deadline is before or equal to the current deadline, keep it but
		# still mark Published as requested.
		self.application_deadline = new_deadline
		self.status = "Published"

	def publish_advertisement(self) -> None:
		"""HR publishes the advertisement."""
		self._require_hr()
		from frappe.utils import nowdate
		self.status = "Published"
		if not getattr(self, "publish_date", None):
			self.publish_date = nowdate()

