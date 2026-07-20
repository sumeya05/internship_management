app_name = "internship_management"
app_title = "Internship Management"
app_publisher = "KRCS"
app_description = "Internship Information Management System"
app_email = "sumeyabishar70@gmail.com"
app_license = "MIT"


# ---------------------------------------------------------
# Fixtures
# ---------------------------------------------------------

fixtures = [
    {
        "dt": "Workspace",
        "filters": [
            ["module", "=", "Internship Management"]
        ],
    },
    {
        "dt": "Dashboard Chart",
        "filters": [
            ["module", "=", "Internship Management"]
        ],
    },
    {
        "dt": "Number Card",
        "filters": [
            ["module", "=", "Internship Management"]
        ],
    },
    {
        "dt": "Report",
        "filters": [
            ["module", "=", "Internship Management"]
        ],
    },
    {
        "dt": "Print Format",
        "filters": [
            ["module", "=", "Internship Management"]
        ],
    },
]


# ---------------------------------------------------------
# Website Routes
# ---------------------------------------------------------

# Frappe automatically maps:
#
# www/internship_portal.html
#       ↓
# /internship-portal
#
# These rules are only needed for custom routing.

website_route_rules = [
    {
        "from_route": "/internship-portal",
        "to_route": "internship-portal",
    },
    {
        "from_route": "/screening-queue",
        "to_route": "screening-queue",
    },
]


# ---------------------------------------------------------
# Permission Query Conditions
# ---------------------------------------------------------

permission_query_conditions = {

    "Intern Profile":
        "internship_management.permissioning.get_conditions_intern_profile",

    "Intern Attendance":
        "internship_management.permissioning.get_conditions_intern_attendance",

    "Intern Progress Log":
        "internship_management.permissioning.get_conditions_intern_progress_log",

    "Extension Request":
        "internship_management.permissioning.get_conditions_extension_request",

    "Intern Onboarding":
        "internship_management.permissioning.get_conditions_intern_onboarding",

    "Intern Exit Clearance":
        "internship_management.permissioning.get_conditions_intern_exit_clearance",

    "Internship Vacancy":
        "internship_management.permissioning.get_conditions_internship_vacancy",

    "Application Screening Record":
        "internship_management.permissioning.get_conditions_application_screening_record",
}


# ---------------------------------------------------------
# Permission Hooks
# ---------------------------------------------------------

has_permission = {

    "Intern Profile":
        "internship_management.permissioning.has_general_permission",

    "Intern Attendance":
        "internship_management.permissioning.has_general_permission",

    "Intern Progress Log":
        "internship_management.permissioning.has_general_permission",

    "Extension Request":
        "internship_management.permissioning.has_general_permission",

    "Intern Onboarding":
        "internship_management.permissioning.has_general_permission",

    "Intern Exit Clearance":
        "internship_management.permissioning.has_general_permission",

    "Internship Vacancy":
        "internship_management.permissioning.has_general_permission",

    "Application Screening Record":
        "internship_management.permissioning.has_general_permission",
}


# ---------------------------------------------------------
# Request Hooks
# ---------------------------------------------------------
#
# Allows Guest users to access:
#   /app/internship-portal
#   /app/screening-queue
#
# and required public assets.
#

before_request = [
    "internship_management.public_page_helper.fix_public_pages_for_app_prefix"
]


# ---------------------------------------------------------
# Document Events
# ---------------------------------------------------------

# Add future automation here:
#
# doc_events = {
#     "Internship Application": {
#         "after_insert":
#             "internship_management.events.application_created"
#     }
# }


# ---------------------------------------------------------
# Developer Settings
# ---------------------------------------------------------

developer_mode = True