from __future__ import annotations

import frappe


# Website pages allowed for Guest users
PUBLIC_PAGE_ROUTES = {
    "internship-portal",
    "screening-queue",
}


# Public files allowed for Guest users
PUBLIC_ASSETS = {
    "website_script.js",
    "website_style.css",
    "website.bundle.css",
    "sw.js",
    "favicon.ico",
    "robots.txt",
}


def _is_guest() -> bool:
    """
    Check whether current session is Guest.
    """

    try:
        return frappe.session.user == "Guest"
    except Exception:
        return True


def fix_public_pages_for_app_prefix():
    """
    Allow public website pages to work through /app/<route>, normal website routes,
    and public assets.

    Examples:
        /
        /internship-portal
        /screening-queue
        /app/internship-portal
        /app/screening-queue
    """

    try:

        request = frappe.local.request

        if not request:
            return

        # Do not affect logged-in users
        if not _is_guest():
            return


        path = request.path.strip("/")


        # -----------------------------
        # Allow root URL (/) - set a generic public flag
        # -----------------------------

        if not path:
            frappe.local.flags.public_page = True
            return


        # -----------------------------
        # Allow public assets
        # -----------------------------

        if path in PUBLIC_ASSETS:
            frappe.local.flags.public_page = True
            return


        if path.startswith("assets/"):
            frappe.local.flags.public_page = True
            return


        # -----------------------------
        # Normal website routes
        # -----------------------------

        if path in PUBLIC_PAGE_ROUTES:
            frappe.local.flags.public_page = True
            return


        # -----------------------------
        # /app/<public route>
        # -----------------------------

        if path.startswith("app/"):

            route = path.replace("app/", "", 1)

            if route in PUBLIC_PAGE_ROUTES:
                frappe.local.flags.public_page = True
                frappe.local.flags.app_public_page = True
                return


    except Exception:

        # Never break Frappe requests
        frappe.log_error(
            frappe.get_traceback(),
            "Public Page Access Hook Error"
        )

