# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document

class DriverLocation(Document):
	def before_save(self):
		"""Generate GeoJSON point from latitude and longitude"""
		if self.latitude and self.longitude:
			geojson_point = {
				"type": "Point",
				"coordinates": [float(self.longitude), float(self.latitude)]
			}
			self.geojson_point = json.dumps(geojson_point)
	
	def validate(self):
		"""Validate location data"""
		if not (-90 <= self.latitude <= 90):
			frappe.throw("Latitude must be between -90 and 90 degrees")
		
		if not (-180 <= self.longitude <= 180):
			frappe.throw("Longitude must be between -180 and 180 degrees")
		
		if self.speed and self.speed < 0:
			frappe.throw("Speed cannot be negative")
		
		if self.heading and not (0 <= self.heading <= 360):
			frappe.throw("Heading must be between 0 and 360 degrees")

@frappe.whitelist()
def get_nearby_drivers(latitude, longitude, radius=5.0):
	"""Get drivers within a specified radius (in km) of a location"""
	# Using Haversine formula for distance calculation
	# This is a simplified implementation - in production, consider using spatial indexing
	
	sql_query = """
		SELECT 
			dl.driver,
			dl.latitude,
			dl.longitude,
			dl.timestamp,
			dl.speed,
			(
				6371 * acos(
					cos(radians(%s)) * cos(radians(dl.latitude)) *
					cos(radians(dl.longitude) - radians(%s)) +
					sin(radians(%s)) * sin(radians(dl.latitude))
				)
			) AS distance
		FROM `tabDriver Location` dl
		WHERE dl.timestamp >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
		HAVING distance <= %s
		ORDER BY distance ASC
	"""
	
	drivers = frappe.db.sql(sql_query, 
		(latitude, longitude, latitude, radius), 
		as_dict=True
	)
	
	return drivers

@frappe.whitelist()
def update_driver_location(driver, latitude, longitude, speed=None, heading=None, accuracy=None, is_offline=False, trip=None):
	"""API endpoint to update driver location"""
	try:
		doc = frappe.get_doc({
			"doctype": "Driver Location",
			"driver": driver,
			"timestamp": frappe.utils.now(),
			"latitude": float(latitude),
			"longitude": float(longitude),
			"speed": float(speed) if speed else None,
			"heading": float(heading) if heading else None,
			"accuracy": float(accuracy) if accuracy else None,
			"is_offline": int(is_offline),
			"trip": trip
		})
		doc.insert()
		frappe.db.commit()
		
		return {"status": "success", "name": doc.name}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Driver Location Update Error")
		return {"status": "error", "message": str(e)}

