# Copyright (c) 2026, KRCS and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe

from internship_management.permission_utils import get_supervisor_department_for_user


def get_permission_query_conditions(user: str) -> str:

	"""Permission query conditions for supervisor dashboard visibility.

	Implementation strategy (Option 1 + guard for assignment):
	- Department is taken from Supervisor where employee == user (see permission_utils).
	- Records are filtered to department via Linked Intern Profile.
	- For Extension Request / Progress Log where there is no department field, we filter by
	  the intern's department from Intern Profile.

	Field mapping used by this app:
	- Intern Profile: department
	- Intern Attendance: intern (Link -> Intern Profile)
	- Intern Progress Log: intern (Link -> Intern Profile) and supervisor (read_only User)
	- Extension Request: intern (Link -> Intern Profile)
	- Intern Onboarding / Intern Exit Clearance: intern (Link -> Intern Profile)
	- Internship Vacancy: department

	This function is intended to be referenced by hooks.py as a scripted permission
	for the above doctypes.
	"""
	dept = get_supervisor_department_for_user(user)
	if not dept:
		# If not a supervisor, return a condition that yields no rows for list/desk.
		return "1=0"

	# hooks framework injects {table} placeholder.
	# We filter by department through Intern Profile where possible.
	# Also handle doctypes that directly have department.
	# Assigned relationship (supervisor) filtering is enforced on Extension Request and Intern Progress Log
	# using their `supervisor` or `approved_by`/supervisor read-only logic.

	return (
		"("
		"  (exists (select 1 from `tabIntern Profile` ip where ip.name = {table}.intern and ip.department = '{dept}'))"
		"  OR ( {table}.department = '{dept}' )"
		" )"
	).format(dept=dept, table="{table}")



