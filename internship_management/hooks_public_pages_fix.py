# Helper module to make public pages accessible from `/app/*` routes.
#
# Problem observed:
#   GET /app/internship-portal  -> 301 to /desk/internship-portal
# For Guest users, we want the public page (render template) instead.
#
# This module patches Frappe's request handling so that routes defined in
# `hooks.py::page_routes` are treated as public/guest pages when coming from
# the `/app/` prefix.

from __future__ import annotations

import frappe


# Keep this list in sync with `hooks.py::page_routes` keys.
PUBLIC_PAGE_ROUTES = {
	"internship-portal": "internship-portal",
	"screening-queue": "screening-queue",
}


def _is_guest_request() -> bool:
	try:
		return frappe.session.user == "Guest"
	except Exception:
		return True


def fix_public_pages_for_app_prefix() -> None:
	"""Request hook.

	For Guest users hitting exact `/app/<public-route>` paths defined in
	`hooks.py::page_routes`, mark the request as public for this request.

	Also allow Guest users to fetch public website assets that are required
	by website templates (e.g. `/website_script.js` and app static assets).

	IMPORTANT: do NOT rewrite request path/url_rule/path_info here. Only set
	request-scoped `frappe.flags`.
	"""

	try:
		req = getattr(frappe, "request", None)
		if not req:
			return

		if not _is_guest_request():
			return

		path = (getattr(req, "path", "") or "").lstrip("/")
		if not path:
			return

		# ---- Guest public asset allowlist ----
		# Keep this minimal; only add paths that must be accessible for public
		# rendering.
		public_asset_paths = {
			"website_script.js",
			"sw.js",
			"krcs-brand.css",
			"assets/internship_management/krcs-brand.css",
			"assets/internship_management/krce-logo.png",
		}
		if path in public_asset_paths:
			frappe.flags.internship_management_public_page = True
			frappe.flags.public_page_route = "__assets__"
			frappe.flags.internship_management_app_prefix_public = True
			return

		# ---- Guest public page allowlist ----
		# Expected shape after stripping leading slash: `app/<route>`.
		if not path.startswith("app/"):
			return

		parts = path.split("/", 2)
		if len(parts) != 2:
			return

		route = parts[1]
		if route not in PUBLIC_PAGE_ROUTES:
			return

		frappe.flags.internship_management_public_page = True
		frappe.flags.public_page_route = route
		frappe.flags.internship_management_app_prefix_public = True

	except Exception:
		# Never break request handling.
		return

