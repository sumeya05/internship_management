# Copyright (c) 2026, KRCS and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe

from internship_management.permission_utils import get_supervisor_department_for_user


# ---------------------------------------------------------------------------
# Permission query conditions
# ---------------------------------------------------------------------------
#
# Frappe's `permission_query_conditions` hook calls the registered function
# with only `user` as an argument — it does NOT pass the doctype/table name,
# and it does NOT do any template substitution on the returned SQL string.
# Whatever string the function returns is ANDed into the query verbatim.
#
# Because of that, a single shared function can't safely reference `{table}`
# as a placeholder — there is no second pass that fills it in. Each doctype
# needs its own function (or closure) that already knows its real table name.
#
# This module builds one such function per doctype via `_conditions_for`,
# and hooks.py should point each entry in `permission_query_conditions` at
# its own dedicated function (see mapping at the bottom of this file).


def _department_condition(table: str, dept: str) -> str:
	"""Build the department-scoping SQL fragment for a given table.

	`table` is a literal table name (e.g. "tabIntern Profile") supplied by us,
	never derived from user input, so it's safe to interpolate directly.
	`dept` is escaped via frappe.db.escape before interpolation.
	"""
	safe_dept = frappe.db.escape(dept)  # includes surrounding quotes

	return (
		"("
		"  (exists ("
		"    select 1 from `tabIntern Profile` ip"
		"    where ip.name = `{table}`.intern and ip.department = {dept}"
		"  ))"
		"  OR (`{table}`.department = {dept})"
		")"
	).format(table=table, dept=safe_dept)


def _conditions_for(table: str):
	"""Return a permission_query_conditions function bound to a specific table.

	Visibility rules:
	- System Administrator: unrestricted.
	- HR Officer / Management/Approver: unrestricted read across these doctypes,
	  matching the broad "read" grants given in the role permission matrix below.
	  (Tighten this per-doctype if any of these roles should actually be scoped.)
	- Supervisor: restricted to their own department, via Intern Profile linkage
	  or a direct `department` field on the table itself.
	- Everyone else: no rows.
	"""

	def _inner(user: str) -> str:
		if user == "Administrator":
			return ""

		roles = frappe.get_roles(user)

		if "System Administrator" in roles:
			return ""

		if any(r in roles for r in ("HR Officer", "Management/Approver")):
			return ""

		dept = get_supervisor_department_for_user(user)
		if not dept:
			# Not a supervisor and not covered by a broader role above:
			# no visibility into this doctype.
			return "1=0"

		return _department_condition(table, dept)

	return _inner


# One bound function per doctype. Register each of these individually in
# hooks.py's permission_query_conditions dict — do NOT reuse a single shared
# function across doctypes, since the table name must be baked in per-function.
get_conditions_intern_profile = _conditions_for("tabIntern Profile")
get_conditions_intern_attendance = _conditions_for("tabIntern Attendance")
get_conditions_intern_progress_log = _conditions_for("tabIntern Progress Log")
get_conditions_extension_request = _conditions_for("tabExtension Request")
get_conditions_intern_onboarding = _conditions_for("tabIntern Onboarding")
get_conditions_intern_exit_clearance = _conditions_for("tabIntern Exit Clearance")
get_conditions_internship_vacancy = _conditions_for("tabInternship Vacancy")
get_conditions_application_screening_record = _conditions_for(
	"tabApplication Screening Record"
)


# ---- Role bootstrap for this app ----


ROLE_NAMES = [
	"Applicant",
	"HR Officer",
	"Department Representative",
	"Supervisor",
	"Interview Panel Member",
	"System Administrator",
	"Management/Approver",
]


def _ensure_role(role_name: str) -> None:
	if frappe.db.exists("Role", role_name):
		return
	frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def _set_permissions_for_doctype(doctype: str, permissions: list[dict]) -> None:
	"""Upsert role permissions for a doctype using Frappe's permission APIs.

	Rather than mutating a cached Meta object and calling meta.save() (which is
	not a reliable way to persist DocPerm rows), this uses
	frappe.permissions.add_permission / update_permission_property, which write
	proper Custom DocPerm rows and clear the relevant caches for us.

	permissions item format:
	{
		"role": "Role Name",
		"perm": {"read": 1, "write": 1, "create": 1, ...}
	}
	"""
	from frappe.permissions import add_permission, update_permission_property

	for p in permissions:
		role_name = p["role"]
		perm_map = p.get("perm", {})

		# Ensure a permission row exists for this role/doctype (permlevel 0).
		if not frappe.db.exists(
			"Custom DocPerm", {"parent": doctype, "role": role_name, "permlevel": 0}
		):
			add_permission(doctype, role_name, permlevel=0)

		for prop, value in perm_map.items():
			update_permission_property(doctype, role_name, permlevel=0, ptype=prop, value=value)

	frappe.clear_cache(doctype=doctype)


def _apply_role_permission_matrix() -> None:
	# Internship Vacancy
	_set_permissions_for_doctype(
		"Internship Vacancy",
		[
			{"role": "Department Representative", "perm": {"read": 1, "write": 1, "create": 1, "submit": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1, "approve": 1, "reject": 1}},
			{"role": "Management/Approver", "perm": {"read": 1, "write": 1, "approve": 1, "reject": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "approve": 1, "reject": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Internship Application
	_set_permissions_for_doctype(
		"Internship Application",
		[
			{"role": "Applicant", "perm": {"create": 1, "read": 1, "write": 1, "submit": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1}},
			{"role": "Department Representative", "perm": {"read": 1}},
			{"role": "Interview Panel Member", "perm": {"read": 1}},
			{"role": "Management/Approver", "perm": {"read": 1, "write": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Intern (Intern Profile)
	_set_permissions_for_doctype(
		"Intern Profile",
		[
			{"role": "Supervisor", "perm": {"read": 1, "write": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "share": 1, "email": 1, "export": 1, "print": 1, "report": 1}},
			{"role": "Management/Approver", "perm": {"read": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Intern Progress Log
	_set_permissions_for_doctype(
		"Intern Progress Log",
		[
			{"role": "Supervisor", "perm": {"read": 1, "write": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "share": 1, "email": 1, "export": 1, "print": 1, "report": 1}},
			{"role": "Management/Approver", "perm": {"read": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Extension Request
	_set_permissions_for_doctype(
		"Extension Request",
		[
			{"role": "Supervisor", "perm": {"read": 1, "write": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1, "approve": 1, "reject": 1}},
			{"role": "Management/Approver", "perm": {"read": 1, "write": 1, "approve": 1, "reject": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "approve": 1, "reject": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Ensure Interview Panel + Interview Evaluation have base read for panel members
	_set_permissions_for_doctype(
		"Interview Schedule",
		[
			{"role": "Interview Panel Member", "perm": {"read": 1, "write": 0, "create": 0}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1}},
			{"role": "Management/Approver", "perm": {"read": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)


def execute() -> None:
	for r in ROLE_NAMES:
		_ensure_role(r)
	_apply_role_permission_matrix()

