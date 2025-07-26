# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "hayago_mapping"
app_title = "Hayago Mapping"
app_publisher = "Manus AI"
app_description = "Comprehensive mapping and location-based services for ride-sharing and delivery platforms"
app_icon = "octicon octicon-location"
app_color = "blue"
app_email = "support@manus.ai"
app_license = "MIT"
app_version = app_version

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = "/assets/hayago_mapping/css/map_styles.css"
app_include_js = [
    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
    "/assets/hayago_mapping/js/map_controller.js"
]

# include js, css files in header of web template
web_include_css = [
    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css",
    "/assets/hayago_mapping/css/map_styles.css"
]
web_include_js = [
    "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js",
    "/assets/hayago_mapping/js/map_controller.js"
]

# include js in page
# page_js = {"page" : "public/js/page.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "hayago_mapping.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "hayago_mapping.install.before_install"
# after_install = "hayago_mapping.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "hayago_mapping.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"hayago_mapping.tasks.all"
# 	],
# 	"daily": [
# 		"hayago_mapping.tasks.daily"
# 	],
# 	"hourly": [
# 		"hayago_mapping.tasks.hourly"
# 	],
# 	"weekly": [
# 		"hayago_mapping.tasks.weekly"
# 	]
# 	"monthly": [
# 		"hayago_mapping.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "hayago_mapping.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "hayago_mapping.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "hayago_mapping.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Request Events
# ----------------
# before_request = ["hayago_mapping.utils.before_request"]
# after_request = ["hayago_mapping.utils.after_request"]

# Job Events
# ----------
# before_job = ["hayago_mapping.utils.before_job"]
# after_job = ["hayago_mapping.utils.after_job"]

# User Data Protection
# --------------------

user_data_fields = [
	{
		"doctype": "{doctype_1}",
		"filter_by": "{filter_by}",
		"redact_fields": ["{field_1}", "{field_2}"],
		"partial": 1,
	},
	{
		"doctype": "{doctype_2}",
		"filter_by": "{filter_by}",
		"partial": 1,
	},
	{
		"doctype": "{doctype_3}",
		"strict": False,
	},
	{
		"doctype": "{doctype_4}"
	}
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"hayago_mapping.auth.validate"
# ]


