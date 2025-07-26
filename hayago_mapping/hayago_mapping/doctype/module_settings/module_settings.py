# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ModuleSettings(Document):
	def validate(self):
		"""Validate module settings"""
		if self.nearby_driver_radius and self.nearby_driver_radius <= 0:
			frappe.throw("Nearby driver radius must be greater than 0")
		
		if self.cost_per_km and self.cost_per_km < 0:
			frappe.throw("Cost per kilometer cannot be negative")
		
		if self.cost_per_minute and self.cost_per_minute < 0:
			frappe.throw("Cost per minute cannot be negative")
		
		# Validate URLs
		if self.nominatim_url and not self.nominatim_url.startswith(('http://', 'https://')):
			frappe.throw("Nominatim URL must start with http:// or https://")
		
		if self.graphhopper_url and not self.graphhopper_url.startswith(('http://', 'https://')):
			frappe.throw("GraphHopper URL must start with http:// or https://")
		
		if self.tracking_api_endpoint and not self.tracking_api_endpoint.startswith(('http://', 'https://')):
			frappe.throw("Tracking API endpoint must start with http:// or https://")

