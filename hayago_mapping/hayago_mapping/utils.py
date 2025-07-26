# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import math
import json
from datetime import datetime, timedelta

def haversine_distance(lat1, lon1, lat2, lon2):
	"""
	Calculate the great circle distance between two points 
	on the earth (specified in decimal degrees)
	Returns distance in kilometers
	"""
	# Convert decimal degrees to radians
	lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
	
	# Haversine formula
	dlat = lat2 - lat1
	dlon = lon2 - lon1
	a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
	c = 2 * math.asin(math.sqrt(a))
	
	# Radius of earth in kilometers
	r = 6371
	
	return c * r

def calculate_bearing(lat1, lon1, lat2, lon2):
	"""
	Calculate the bearing between two points
	Returns bearing in degrees (0-360)
	"""
	lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
	
	dlon = lon2 - lon1
	
	y = math.sin(dlon) * math.cos(lat2)
	x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
	
	bearing = math.atan2(y, x)
	bearing = math.degrees(bearing)
	bearing = (bearing + 360) % 360
	
	return bearing

def create_geojson_point(longitude, latitude):
	"""Create a GeoJSON Point from coordinates"""
	return {
		"type": "Point",
		"coordinates": [float(longitude), float(latitude)]
	}

def create_geojson_linestring(coordinates):
	"""Create a GeoJSON LineString from a list of coordinates"""
	return {
		"type": "LineString",
		"coordinates": coordinates
	}

def create_geojson_feature(geometry, properties=None):
	"""Create a GeoJSON Feature"""
	feature = {
		"type": "Feature",
		"geometry": geometry
	}
	
	if properties:
		feature["properties"] = properties
	
	return feature

def create_geojson_feature_collection(features):
	"""Create a GeoJSON FeatureCollection"""
	return {
		"type": "FeatureCollection",
		"features": features
	}

def validate_coordinates(latitude, longitude):
	"""Validate latitude and longitude values"""
	try:
		lat = float(latitude)
		lon = float(longitude)
		
		if not (-90 <= lat <= 90):
			return False, "Latitude must be between -90 and 90 degrees"
		
		if not (-180 <= lon <= 180):
			return False, "Longitude must be between -180 and 180 degrees"
		
		return True, None
		
	except (ValueError, TypeError):
		return False, "Invalid coordinate format"

def get_module_settings():
	"""Get module settings with defaults"""
	try:
		settings = frappe.get_single("Module Settings")
		return settings
	except frappe.DoesNotExistError:
		# Return default settings if not configured
		return frappe._dict({
			'nominatim_url': 'https://nominatim.openstreetmap.org/',
			'graphhopper_url': 'https://graphhopper.com/api/1/route',
			'graphhopper_api_key': '',
			'tracking_api_endpoint': '',
			'nearby_driver_radius': 5.0,
			'cost_per_km': 1.0,
			'cost_per_minute': 0.2
		})

def cleanup_old_location_data(days=7):
	"""Clean up old driver location data older than specified days"""
	try:
		cutoff_date = datetime.now() - timedelta(days=days)
		
		# Delete old driver location records
		frappe.db.sql("""
			DELETE FROM `tabDriver Location`
			WHERE timestamp < %s
		""", (cutoff_date,))
		
		frappe.db.commit()
		
		frappe.logger().info(f"Cleaned up driver location data older than {days} days")
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Location Data Cleanup Error")

def get_trip_statistics(driver=None, date_range=30):
	"""Get trip statistics for a driver or all drivers"""
	try:
		conditions = []
		values = []
		
		if driver:
			conditions.append("driver = %s")
			values.append(driver)
		
		conditions.append("creation >= DATE_SUB(NOW(), INTERVAL %s DAY)")
		values.append(date_range)
		
		where_clause = " AND ".join(conditions) if conditions else "1=1"
		
		sql_query = f"""
			SELECT 
				COUNT(*) as total_trips,
				COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed_trips,
				COUNT(CASE WHEN status = 'Cancelled' THEN 1 END) as cancelled_trips,
				AVG(CASE WHEN status = 'Completed' THEN actual_distance END) as avg_distance,
				AVG(CASE WHEN status = 'Completed' THEN actual_duration END) as avg_duration,
				SUM(CASE WHEN status = 'Completed' THEN actual_cost END) as total_revenue
			FROM `tabTrip`
			WHERE {where_clause}
		"""
		
		result = frappe.db.sql(sql_query, values, as_dict=True)
		
		return result[0] if result else {}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Trip Statistics Error")
		return {}

def format_duration(minutes):
	"""Format duration in minutes to human readable format"""
	if not minutes:
		return "0 minutes"
	
	hours = int(minutes // 60)
	mins = int(minutes % 60)
	
	if hours > 0:
		return f"{hours}h {mins}m"
	else:
		return f"{mins}m"

def format_distance(kilometers):
	"""Format distance in kilometers to human readable format"""
	if not kilometers:
		return "0 km"
	
	if kilometers < 1:
		meters = int(kilometers * 1000)
		return f"{meters}m"
	else:
		return f"{kilometers:.1f}km"

def is_point_in_radius(center_lat, center_lon, point_lat, point_lon, radius_km):
	"""Check if a point is within a specified radius of a center point"""
	distance = haversine_distance(center_lat, center_lon, point_lat, point_lon)
	return distance <= radius_km

def get_bounding_box(latitude, longitude, radius_km):
	"""Get bounding box coordinates for a point and radius"""
	# Approximate degrees per kilometer
	lat_deg_per_km = 1 / 111.0
	lon_deg_per_km = 1 / (111.0 * math.cos(math.radians(latitude)))
	
	lat_offset = radius_km * lat_deg_per_km
	lon_offset = radius_km * lon_deg_per_km
	
	return {
		'min_lat': latitude - lat_offset,
		'max_lat': latitude + lat_offset,
		'min_lon': longitude - lon_offset,
		'max_lon': longitude + lon_offset
	}

