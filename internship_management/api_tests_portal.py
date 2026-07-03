"""Minimal smoke tests (manual use) for Internship Portal endpoints.

Run inside bench environment, e.g.:
	bench --site internship.localhost console <script>

This file is intentionally not hooked into pytest.
"""

import frappe


def smoke_get_vacancies():
	resp = frappe.call('internship_management.api.get_available_internships')
	assert 'vacancies' in resp
	return resp

