# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import requests
from frappe.model.document import Document
from frappe.utils import now, time_diff_in_seconds

class Trip(Document):
	def validate(self):
		"""Validate trip data"""
		if not (-90 <= self.pickup_latitude <= 90):
			frappe.throw("Pickup latitude must be between -90 and 90 degrees")
		
		if not (-180 <= self.pickup_longitude <= 180):
			frappe.throw("Pickup longitude must be between -180 and 180 degrees")
		
		if not (-90 <= self.dropoff_latitude <= 90):
			frappe.throw("Dropoff latitude must be between -90 and 90 degrees")
		
		if not (-180 <= self.dropoff_longitude <= 180):
			frappe.throw("Dropoff longitude must be between -180 and 180 degrees")
		
		if self.start_time and self.end_time:
			if self.start_time >= self.end_time:
				frappe.throw("End time must be after start time")
	
	def before_save(self):
		"""Calculate actual duration and distance if trip is completed"""
		if self.status == "Completed" and self.start_time and self.end_time:
			# Calculate actual duration in minutes
			duration_seconds = time_diff_in_seconds(self.end_time, self.start_time)
			self.actual_duration = duration_seconds / 60.0
			
			# Calculate actual distance from route logs if available
			if self.route_logs:
				self.actual_distance = self.calculate_distance_from_logs()
			
			# Generate logged route GeoJSON from route logs
			if self.route_logs:
				self.logged_route_geojson = self.generate_logged_route_geojson()
	
	def calculate_distance_from_logs(self):
		"""Calculate total distance from route log points using Haversine formula"""
		if not self.route_logs or len(self.route_logs) < 2:
			return 0.0
		
		total_distance = 0.0
		
		for i in range(1, len(self.route_logs)):
			prev_log = self.route_logs[i-1]
			curr_log = self.route_logs[i]
			
			distance = self.haversine_distance(
				prev_log.latitude, prev_log.longitude,
				curr_log.latitude, curr_log.longitude
			)
			total_distance += distance
		
		return total_distance
	
	def haversine_distance(self, lat1, lon1, lat2, lon2):
		"""Calculate distance between two points using Haversine formula"""
		import math
		
		# Convert latitude and longitude from degrees to radians
		lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
		
		# Haversine formula
		dlat = lat2 - lat1
		dlon = lon2 - lon1
		a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
		c = 2 * math.asin(math.sqrt(a))
		
		# Radius of earth in kilometers
		r = 6371
		
		return c * r
	
	def generate_logged_route_geojson(self):
		"""Generate GeoJSON LineString from route logs"""
		if not self.route_logs:
			return None
		
		coordinates = []
		for log in self.route_logs:
			coordinates.append([float(log.longitude), float(log.latitude)])
		
		geojson = {
			"type": "LineString",
			"coordinates": coordinates
		}
		
		return json.dumps(geojson)

@frappe.whitelist()
def estimate_trip_cost(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng):
	"""Estimate trip cost using GraphHopper API"""
	try:
		settings = frappe.get_single("Module Settings")
		
		# Get route from GraphHopper
		route_data = get_route_from_graphhopper(
			pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, settings
		)
		
		if not route_data:
			return {"status": "error", "message": "Could not calculate route"}
		
		# Extract distance (in meters) and time (in milliseconds)
		distance_km = route_data.get("distance", 0) / 1000.0
		duration_minutes = route_data.get("time", 0) / 60000.0
		
		# Calculate cost
		cost = (distance_km * settings.cost_per_km) + (duration_minutes * settings.cost_per_minute)
		
		# Generate route GeoJSON
		route_geojson = None
		if "paths" in route_data and route_data["paths"]:
			points = route_data["paths"][0].get("points", {})
			if "coordinates" in points:
				route_geojson = json.dumps({
					"type": "LineString",
					"coordinates": points["coordinates"]
				})
		
		return {
			"status": "success",
			"estimated_distance": distance_km,
			"estimated_duration": duration_minutes,
			"estimated_cost": cost,
			"route_geojson": route_geojson
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Trip Cost Estimation Error")
		return {"status": "error", "message": str(e)}

def get_route_from_graphhopper(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, settings):
	"""Get route data from GraphHopper API"""
	try:
		url = settings.graphhopper_url
		
		params = {
			"point": [f"{pickup_lat},{pickup_lng}", f"{dropoff_lat},{dropoff_lng}"],
			"vehicle": "car",
			"locale": "en",
			"calc_points": "true",
			"debug": "true",
			"elevation": "false",
			"points_encoded": "false"
		}
		
		if settings.graphhopper_api_key:
			params["key"] = settings.graphhopper_api_key
		
		response = requests.get(url, params=params, timeout=30)
		response.raise_for_status()
		
		return response.json()
		
	except Exception as e:
		frappe.log_error(f"GraphHopper API Error: {str(e)}", "GraphHopper API Error")
		return None

@frappe.whitelist()
def create_trip(driver, customer, pickup_address, pickup_lat, pickup_lng, 
               dropoff_address, dropoff_lat, dropoff_lng):
	"""Create a new trip with cost estimation"""
	try:
		# Get cost estimation
		estimation = estimate_trip_cost(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
		
		if estimation.get("status") != "success":
			return estimation
		
		# Create trip document
		trip = frappe.get_doc({
			"doctype": "Trip",
			"driver": driver,
			"customer": customer,
			"pickup_address": pickup_address,
			"pickup_latitude": float(pickup_lat),
			"pickup_longitude": float(pickup_lng),
			"dropoff_address": dropoff_address,
			"dropoff_latitude": float(dropoff_lat),
			"dropoff_longitude": float(dropoff_lng),
			"estimated_distance": estimation.get("estimated_distance"),
			"estimated_duration": estimation.get("estimated_duration"),
			"estimated_cost": estimation.get("estimated_cost"),
			"route_geojson": estimation.get("route_geojson"),
			"status": "Pending"
		})
		
		trip.insert()
		frappe.db.commit()
		
		return {"status": "success", "trip_id": trip.name, "estimation": estimation}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Trip Creation Error")
		return {"status": "error", "message": str(e)}

