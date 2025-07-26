# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import requests
from frappe import _

@frappe.whitelist(allow_guest=True)
def geocode_address(address):
	"""Geocode an address using Nominatim API"""
	try:
		settings = frappe.get_single("Module Settings")
		nominatim_url = settings.nominatim_url or "https://nominatim.openstreetmap.org/"
		
		# Ensure URL ends with /
		if not nominatim_url.endswith('/'):
			nominatim_url += '/'
		
		search_url = nominatim_url + "search"
		
		params = {
			'q': address,
			'format': 'json',
			'limit': 1,
			'addressdetails': 1
		}
		
		headers = {
			'User-Agent': 'Hayago Mapping Module/1.0 (Frappe Framework)'
		}
		
		response = requests.get(search_url, params=params, headers=headers, timeout=10)
		response.raise_for_status()
		
		results = response.json()
		
		if not results:
			return {
				"status": "error",
				"message": "Address not found"
			}
		
		result = results[0]
		
		return {
			"status": "success",
			"latitude": float(result['lat']),
			"longitude": float(result['lon']),
			"display_name": result['display_name'],
			"address_details": result.get('address', {})
		}
		
	except requests.RequestException as e:
		frappe.log_error(f"Nominatim API Error: {str(e)}", "Geocoding Error")
		return {
			"status": "error",
			"message": "Geocoding service unavailable"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Geocoding Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist(allow_guest=True)
def reverse_geocode(latitude, longitude):
	"""Reverse geocode coordinates to get address using Nominatim API"""
	try:
		settings = frappe.get_single("Module Settings")
		nominatim_url = settings.nominatim_url or "https://nominatim.openstreetmap.org/"
		
		# Ensure URL ends with /
		if not nominatim_url.endswith('/'):
			nominatim_url += '/'
		
		reverse_url = nominatim_url + "reverse"
		
		params = {
			'lat': latitude,
			'lon': longitude,
			'format': 'json',
			'addressdetails': 1
		}
		
		headers = {
			'User-Agent': 'Hayago Mapping Module/1.0 (Frappe Framework)'
		}
		
		response = requests.get(reverse_url, params=params, headers=headers, timeout=10)
		response.raise_for_status()
		
		result = response.json()
		
		if 'error' in result:
			return {
				"status": "error",
				"message": result['error']
			}
		
		return {
			"status": "success",
			"address": result['display_name'],
			"address_details": result.get('address', {})
		}
		
	except requests.RequestException as e:
		frappe.log_error(f"Nominatim API Error: {str(e)}", "Reverse Geocoding Error")
		return {
			"status": "error",
			"message": "Reverse geocoding service unavailable"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Reverse Geocoding Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def find_nearby_drivers(latitude, longitude, radius=None):
	"""Find drivers within a specified radius of a location"""
	try:
		settings = frappe.get_single("Module Settings")
		search_radius = float(radius) if radius else settings.nearby_driver_radius or 5.0
		
		# Get recent driver locations (within last 5 minutes)
		sql_query = """
			SELECT 
				dl.driver,
				dl.latitude,
				dl.longitude,
				dl.timestamp,
				dl.speed,
				u.full_name as driver_name,
				u.mobile_no as driver_mobile,
				(
					6371 * acos(
						cos(radians(%s)) * cos(radians(dl.latitude)) *
						cos(radians(dl.longitude) - radians(%s)) +
						sin(radians(%s)) * sin(radians(dl.latitude))
					)
				) AS distance
			FROM `tabDriver Location` dl
			LEFT JOIN `tabUser` u ON dl.driver = u.name
			WHERE dl.timestamp >= DATE_SUB(NOW(), INTERVAL 5 MINUTE)
			HAVING distance <= %s
			ORDER BY distance ASC
			LIMIT 20
		"""
		
		drivers = frappe.db.sql(sql_query, 
			(latitude, longitude, latitude, search_radius), 
			as_dict=True
		)
		
		# Check driver availability (not currently on a trip)
		available_drivers = []
		for driver in drivers:
			# Check if driver has any active trips
			active_trips = frappe.db.count("Trip", {
				"driver": driver.driver,
				"status": ["in", ["Accepted", "On Route"]]
			})
			
			if active_trips == 0:
				available_drivers.append(driver)
		
		return {
			"status": "success",
			"drivers": available_drivers,
			"count": len(available_drivers)
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Find Nearby Drivers Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def update_driver_location_api(driver, latitude, longitude, speed=None, heading=None, accuracy=None, is_offline=0, trip=None):
	"""API endpoint to update driver location - wrapper for the DocType method"""
	from hayago_mapping.hayago_mapping.doctype.driver_location.driver_location import update_driver_location
	
	return update_driver_location(
		driver=driver,
		latitude=latitude,
		longitude=longitude,
		speed=speed,
		heading=heading,
		accuracy=accuracy,
		is_offline=is_offline,
		trip=trip
	)

@frappe.whitelist()
def get_driver_location_history(driver, hours=24):
	"""Get driver location history for the specified number of hours"""
	try:
		sql_query = """
			SELECT 
				timestamp,
				latitude,
				longitude,
				speed,
				heading,
				accuracy,
				is_offline,
				trip
			FROM `tabDriver Location`
			WHERE driver = %s
			AND timestamp >= DATE_SUB(NOW(), INTERVAL %s HOUR)
			ORDER BY timestamp DESC
			LIMIT 1000
		"""
		
		locations = frappe.db.sql(sql_query, (driver, int(hours)), as_dict=True)
		
		return {
			"status": "success",
			"locations": locations,
			"count": len(locations)
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Driver Location History Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_active_trips():
	"""Get all active trips with driver and customer information"""
	try:
		sql_query = """
			SELECT 
				t.name,
				t.driver,
				t.customer,
				t.pickup_address,
				t.pickup_latitude,
				t.pickup_longitude,
				t.dropoff_address,
				t.dropoff_latitude,
				t.dropoff_longitude,
				t.start_time,
				t.estimated_distance,
				t.estimated_duration,
				t.estimated_cost,
				t.status,
				d.full_name as driver_name,
				d.mobile_no as driver_mobile,
				c.full_name as customer_name,
				c.mobile_no as customer_mobile
			FROM `tabTrip` t
			LEFT JOIN `tabUser` d ON t.driver = d.name
			LEFT JOIN `tabUser` c ON t.customer = c.name
			WHERE t.status IN ('Pending', 'Accepted', 'On Route')
			ORDER BY t.creation DESC
		"""
		
		trips = frappe.db.sql(sql_query, as_dict=True)
		
		return {
			"status": "success",
			"trips": trips,
			"count": len(trips)
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Get Active Trips Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def match_driver_to_trip(pickup_latitude, pickup_longitude, customer, pickup_address, dropoff_address, dropoff_latitude, dropoff_longitude):
	"""Complete driver matching workflow - find nearby drivers and create trip"""
	try:
		# Find nearby available drivers
		nearby_result = find_nearby_drivers(pickup_latitude, pickup_longitude)
		
		if nearby_result.get("status") != "success" or not nearby_result.get("drivers"):
			return {
				"status": "error",
				"message": "No available drivers found in the area"
			}
		
		# Select the closest driver
		closest_driver = nearby_result["drivers"][0]
		
		# Create trip with the matched driver
		from hayago_mapping.hayago_mapping.doctype.trip.trip import create_trip
		
		trip_result = create_trip(
			driver=closest_driver["driver"],
			customer=customer,
			pickup_address=pickup_address,
			pickup_lat=pickup_latitude,
			pickup_lng=pickup_longitude,
			dropoff_address=dropoff_address,
			dropoff_lat=dropoff_latitude,
			dropoff_lng=dropoff_longitude
		)
		
		if trip_result.get("status") == "success":
			trip_result["matched_driver"] = closest_driver
		
		return trip_result
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Driver Matching Error")
		return {
			"status": "error",
			"message": str(e)
		}

