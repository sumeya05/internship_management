from __future__ import annotations

import frappe


# Fraction core system routes/paths that must NEVER be intercepted.
# The before_request hook returns immediately for these.
PUBLIC_SYSTEM_ROUTES = {
    "",
    "/",
    "/login",
    "/desk",
    "/api",
    "/assets",
}


# System routes that Frappe handles natively — must not be intercepted
IGNORE_ROUTES = {
    "login",
    "logout",
    "desk",
    "api",
    "assets",
    "update",
    "files",
    "private",
    "app",
}


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


def before_request():
    """
    Top-level before_request hook.

    Never interfere with Frappe core routes.  Return immediately for:
        /, /api/*, /assets/*, /login, /desk.

    Public assets (.js, .css, /website_script.js, /sw.js, favicon.ico,
    robots.txt etc.) are forwarded to fix_public_pages_for_app_prefix()
    so the public_page flag can be set for Guest users, preventing 403 errors.
    """

    path = frappe.local.request.path

    # Never interfere with Frappe core routes — but let .js/.css and
    # public asset paths through so fix_public_pages_for_app_prefix()
    # can set the public_page flag for Guest users.
    if (
        path.startswith("/api")
        or path.startswith("/assets")
        or path.startswith("/login")
        or path.startswith("/desk")
        or path in PUBLIC_SYSTEM_ROUTES
    ):
        return

    fix_public_pages_for_app_prefix()


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


        # --------------------------------------------------
        # Skip system routes completely — let Frappe handle them natively
        # Do NOT modify any flags; just return immediately.
        # --------------------------------------------------

        if path in IGNORE_ROUTES:
            return

        for prefix in ("api/", "assets/", "files/", "private/", "update/"):
            if path.startswith(prefix):
                return

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

