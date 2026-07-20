from __future__ import annotations

import frappe


def fix_public_pages_for_app_prefix():
	"""Backward-compatible re-export.

	If anything references `hooks_public_pages_fix.fix_public_pages_for_app_prefix`
	directly, this delegates to the consolidated implementation in
	`public_page_helper`.
	"""

	try:
		from internship_management.public_page_helper import (
			fix_public_pages_for_app_prefix as _impl,
		)

		_impl()
		return
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hooks_public_pages_fix delegation failed")
		return
