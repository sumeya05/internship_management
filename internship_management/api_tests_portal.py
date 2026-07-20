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


def smoke_get_my_application_status():
	"""Smoke test for status endpoint.
	Requires a previously submitted Internship Application in DB.
	"""
	# This is intentionally manual.
	pass


def smoke_screening_decision_endpoints():
	"""Manual smoke test for screening decision endpoints."""
	# Intended manual calls:
	# - frappe.call('internship_management.api.get_screening_queue', {filters: {}})
	# - frappe.call('internship_management.api.get_application_for_screening', {'application_name': '...'} )
	# - frappe.call('internship_management.api.screen_application', {'application_name': '...', 'decision': 'Shortlisted', 'minimum_requirements_met': True, 'remarks': '...'})
	pass





