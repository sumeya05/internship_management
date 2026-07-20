app_name = "internship_management"
app_title = "Internship Management"
app_publisher = "KRCS"
app_description = "Internship Information Management System"
app_email = "sumeyabishar70@gmail.com"
app_license = "mit"

fixtures = [
    {
        "dt": "Workspace",
        "filters": [["module", "=", "Internship Management"]],
    },
    {
        "dt": "Dashboard Chart",
        "filters": [["module", "=", "Internship Management"]],
    },
    {
        "dt": "Number Card",
        "filters": [["module", "=", "Internship Management"]],
    },
    {
        "dt": "Report",
        "filters": [["module", "=", "Internship Management"]],
    },
    {
        "dt": "Print Format",
        "filters": [["module", "=", "Internship Management"]],
    },
]

page_js = {}

# NOTE: For these to be accessible publicly (Guest users) we use
# `page_routes` with `public: true` so Frappe treats them as website/public
# pages instead of desk-only pages.
page_routes = {
    "internship-portal": {
        "route": "internship-portal",
        "template": "templates/pages/internship_portal.html",
        "public": True,
    },
    "screening-queue": {
        "route": "screening-queue",
        "template": "templates/pages/screening_queue.html",
        "public": True,
    },
}


# Make /app/<public_page> accessible for Guest users (avoid redirect to /desk/...).
# This enables public templates to render without authentication.


# Public page redirect rules.
# Frappe's /app/<page> gets redirected to /desk/<page> by default.
# Map /app paths to the corresponding public website routes instead.
website_redirects = [
    {"source": "/app/internship-portal", "target": "/internship-portal", "redirect_http_status": 302},
    {"source": "/app/screening-queue", "target": "/screening-queue", "redirect_http_status": 302},
]







permission_query_conditions = {
    "Intern Profile": "internship_management.permissioning.get_permission_query_conditions",
    "Intern Attendance": "internship_management.permissioning.get_permission_query_conditions",
    "Intern Progress Log": "internship_management.permissioning.get_permission_query_conditions",
    "Extension Request": "internship_management.permissioning.get_permission_query_conditions",
    "Intern Onboarding": "internship_management.permissioning.get_permission_query_conditions",
    "Intern Exit Clearance": "internship_management.permissioning.get_permission_query_conditions",
    "Internship Vacancy": "internship_management.permissioning.get_permission_query_conditions",
    "Application Screening Record": "internship_management.permissioning.get_conditions_application_screening_record",
}

has_permission = {
    "Intern Profile": "internship_management.permissioning.has_permission",
    "Intern Attendance": "internship_management.permissioning.has_permission",
    "Intern Progress Log": "internship_management.permissioning.has_permission",
    "Extension Request": "internship_management.permissioning.has_permission",
    "Intern Onboarding": "internship_management.permissioning.has_permission",
    "Intern Exit Clearance": "internship_management.permissioning.has_permission",
    "Internship Vacancy": "internship_management.permissioning.has_permission",
    "Application Screening Record": "internship_management.permissioning.has_permission",
}

# Ensure public `/app/<route>` pages render for Guest users instead of redirecting to Desk.
# This is implemented in `hooks_public_pages_fix.py`.
# Hook name uses Frappe's request hook mechanism.
request_hooks = [
    "internship_management.hooks_public_pages_fix.fix_public_pages_for_app_prefix",
]



