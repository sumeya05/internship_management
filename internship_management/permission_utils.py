# Copyright (c) 2026, KRCS and contributors
# For license information, please see license.txt

from __future__ import annotations

import frappe


def get_supervisor_department_for_user(user: str | None = None) -> str | None:
	"""Map the logged-in user to the Supervisor's Department.

	In this app, Supervisor DocType fields include:
	- employee (appears to store supervisor user/email)
	- department (Link to Department)
	"""
	user = user or frappe.session.user
	if not user or user == "Guest":
		return None

	dept = frappe.db.get_value("Supervisor", {"employee": user}, "department")
	if dept:
		return dept

	# Fallback: try matching supervisor by name
	dept = frappe.db.get_value("Supervisor", {"name": user}, "department")
	return dept


def build_department_permission_query(doctype: str, department_field: str = "department") -> str:
	"""Generic permission query condition by department.

	Returns a SQL snippet suitable for permission_query_conditions.

	Note: {table} is provided by Frappe.
	"""
	return (
		"exists (select 1 from `tab{doctype}` d "
		"where d.name = {table}.name and d.{department_field} = '{{department}}')"
	).format(doctype=doctype, table="{table}", department_field=department_field)

