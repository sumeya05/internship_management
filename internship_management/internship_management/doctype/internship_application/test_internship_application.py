# Copyright (c) 2026,  KRCS and Contributors
# See license.txt

import frappe
from unittest.mock import patch
from frappe.tests import IntegrationTestCase
from internship_management.internship_management.doctype.internship_application.internship_application import InternshipApplication
from internship_management.internship_management.doctype.internship_vacancy.internship_vacancy import InternshipVacancy


def _field_meta(doctype, fieldname):
	meta = frappe.get_meta(doctype)
	return next((field for field in meta.fields if field.fieldname == fieldname), None)


class TestInternshipWorkflow(IntegrationTestCase):
	def test_application_validation_checks_approved_vacancy_status(self):
		application = InternshipApplication()
		application.name = "APP-TEST-1"
		application.vacancy_applied_for = "VAC-001"
		application.email = "applicant@example.com"
		application.application_status = "Submitted"

		with patch("frappe.db.exists", return_value=False), patch(
			"frappe.db.get_value", return_value="Approved"
		) as mock_get_value, patch("frappe.get_all", return_value=[]):
			application.validate()

		mock_get_value.assert_any_call("Internship Vacancy", "VAC-001", "approval_status")

	def test_vacancy_validation_allows_expected_approval_transition(self):
		vacancy = InternshipVacancy()
		vacancy.name = "VAC-001"
		vacancy.approval_status = "Approved"

		with patch("frappe.db.exists", return_value=True), patch(
			"frappe.db.get_value", return_value="Pending Approval"
		):
			vacancy.validate()

	def test_location_fields_use_country_and_county_targets(self):
		nationality_field = _field_meta("Internship Application", "nationality")
		county_field = _field_meta("Internship Application", "county")
		sub_county_field = _field_meta("Internship Application", "sub_county")

		self.assertEqual(nationality_field.options, "Country")
		self.assertEqual(county_field.options, "County")
		self.assertEqual(sub_county_field.options, "Sub County")
