# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class RouteLog(Document):
	def validate(self):
		"""Validate route log data"""
		if not (-90 <= self.latitude <= 90):
			frappe.throw("Latitude must be between -90 and 90 degrees")
		
		if not (-180 <= self.longitude <= 180):
			frappe.throw("Longitude must be between -180 and 180 degrees")
		
		if self.speed and self.speed < 0:
			frappe.throw("Speed cannot be negative")

