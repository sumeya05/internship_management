# Copyright (c) 2026, KRCS and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe


ROLE_NAMES = [
	"Applicant",
	"HR Officer",
	"Department Representative",
	"Supervisor",
	"Interview Panel Member",
	"System Administrator",
]


def _ensure_role(role_name: str) -> None:
	if frappe.db.exists("Role", role_name):
		return
	frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(ignore_permissions=True)


def _set_permissions_for_doctype(doctype: str, permissions: list[dict]) -> None:
	"""Upsert role permissions for a doctype.

	Instead of overwriting `meta.permissions` for all roles (which can remove
	permissions provided by Frappe or other apps), we only update the rows for
	this app's roles.

	permissions item format:
	{
		"role": "Role Name",
		"perm": {"read": 1, "write": 1, "create": 1, ...}
	}
	"""
	meta = frappe.get_meta(doctype)

	# Index existing rows by role.
	existing_by_role: dict[str, frappe._dict] = {}
	for row in (meta.permissions or []):
		role_name = row.get("role") if isinstance(row, dict) else getattr(row, "role", None)
		if role_name:
			existing_by_role[role_name] = row

	# Upsert only the provided roles.
	for p in permissions:
		role_name = p["role"]
		perm_map = p.get("perm", {})

		if role_name in existing_by_role:
			row = existing_by_role[role_name]
			row.update(perm_map)
		else:
			row = frappe._dict({"role": role_name})
			row.update(perm_map)
			existing_by_role[role_name] = row

	# Preserve any roles that weren't mentioned.
	meta.permissions = list(existing_by_role.values())
	meta.save()




def _apply_role_permission_matrix() -> None:
	# Internship Vacancy
	_set_permissions_for_doctype(
		"Internship Vacancy",
		[
			{"role": "Department Representative", "perm": {"read": 1, "write": 1, "create": 1, "submit": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1, "approve": 1, "reject": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "approve": 1, "reject": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Internship Application
	_set_permissions_for_doctype(
		"Internship Application",
		[
			# Ownership should be enforced by Frappe's ownership rules; leaving `read/write` as allowed.
			{"role": "Applicant", "perm": {"create": 1, "read": 1, "write": 1, "submit": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1}},
			{"role": "Department Representative", "perm": {"read": 1}},
			{"role": "Interview Panel Member", "perm": {"read": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Intern (Intern Profile)
	_set_permissions_for_doctype(
		"Intern Profile",
		[
			{"role": "Supervisor", "perm": {"read": 1, "write": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "share": 1, "email": 1, "export": 1, "print": 1, "report": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Intern Progress Log
	_set_permissions_for_doctype(
		"Intern Progress Log",
		[
			{"role": "Supervisor", "perm": {"read": 1, "write": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "share": 1, "email": 1, "export": 1, "print": 1, "report": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Extension Request
	_set_permissions_for_doctype(
		"Extension Request",
		[
			{"role": "Supervisor", "perm": {"read": 1, "write": 1}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1, "approve": 1, "reject": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "approve": 1, "reject": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Ensure Interview Panel + Interview Evaluation have base read for panel members
	_set_permissions_for_doctype(
		"Interview Schedule",
		[
			{"role": "Interview Panel Member", "perm": {"read": 1, "write": 0, "create": 0}},
			{"role": "HR Officer", "perm": {"read": 1, "write": 1}},
			{"role": "System Administrator", "perm": {"read": 1, "write": 1, "create": 1, "delete": 1, "submit": 1, "cancel": 1, "email": 1, "export": 1, "print": 1, "report": 1, "share": 1}},
		],
	)

	# Interview Panel doctype is a child table (istable=1); usually not needed in Desk permissions.


def execute() -> None:
	for r in ROLE_NAMES:
		_ensure_role(r)
	_apply_role_permission_matrix()

