import frappe


def get_page_routes():
	# Optional helper; routes can also be defined directly via `hooks.py`.
	return {
		"internship-portal": {
			"template": "templates/pages/internship_portal.html",
		},
	}

