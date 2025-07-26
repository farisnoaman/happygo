# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import requests
from frappe import _
from .utils import get_module_settings, validate_coordinates

@frappe.whitelist()
def get_route(pickup_lat, pickup_lng, dropoff_lat, dropoff_lng, vehicle="car", alternatives=False):
	"""Get route information from GraphHopper API"""
	try:
		# Validate coordinates
		valid_pickup, pickup_error = validate_coordinates(pickup_lat, pickup_lng)
		if not valid_pickup:
			return {"status": "error", "message": f"Invalid pickup coordinates: {pickup_error}"}
		
		valid_dropoff, dropoff_error = validate_coordinates(dropoff_lat, dropoff_lng)
		if not valid_dropoff:
			return {"status": "error", "message": f"Invalid dropoff coordinates: {dropoff_error}"}
		
		settings = get_module_settings()
		
		# Prepare GraphHopper API request
		url = settings.graphhopper_url or "https://graphhopper.com/api/1/route"
		
		params = {
			"point": [f"{pickup_lat},{pickup_lng}", f"{dropoff_lat},{dropoff_lng}"],
			"vehicle": vehicle,
			"locale": "en",
			"calc_points": "true",
			"debug": "true",
			"elevation": "false",
			"points_encoded": "false",
			"instructions": "true",
			"alternative_route.max_paths": "3" if alternatives else "1"
		}
		
		if settings.graphhopper_api_key:
			params["key"] = settings.graphhopper_api_key
		
		headers = {
			'User-Agent': 'Hayago Mapping Module/1.0 (Frappe Framework)'
		}
		
		response = requests.get(url, params=params, headers=headers, timeout=30)
		response.raise_for_status()
		
		route_data = response.json()
		
		if "paths" not in route_data or not route_data["paths"]:
			return {
				"status": "error",
				"message": "No route found between the specified points"
			}
		
		# Process the main route
		main_path = route_data["paths"][0]
		
		# Extract route information
		distance_km = main_path.get("distance", 0) / 1000.0
		duration_minutes = main_path.get("time", 0) / 60000.0
		
		# Create GeoJSON for the route
		route_geojson = None
		if "points" in main_path and "coordinates" in main_path["points"]:
			route_geojson = {
				"type": "LineString",
				"coordinates": main_path["points"]["coordinates"]
			}
		
		# Extract turn-by-turn instructions
		instructions = []
		if "instructions" in main_path:
			for instruction in main_path["instructions"]:
				instructions.append({
					"text": instruction.get("text", ""),
					"distance": instruction.get("distance", 0),
					"time": instruction.get("time", 0),
					"sign": instruction.get("sign", 0),
					"interval": instruction.get("interval", [])
				})
		
		# Calculate estimated cost
		cost_per_km = settings.cost_per_km or 1.0
		cost_per_minute = settings.cost_per_minute or 0.2
		estimated_cost = (distance_km * cost_per_km) + (duration_minutes * cost_per_minute)
		
		result = {
			"status": "success",
			"distance_km": distance_km,
			"duration_minutes": duration_minutes,
			"estimated_cost": estimated_cost,
			"route_geojson": route_geojson,
			"instructions": instructions
		}
		
		# Add alternative routes if requested
		if alternatives and len(route_data["paths"]) > 1:
			alternative_routes = []
			for alt_path in route_data["paths"][1:]:
				alt_distance_km = alt_path.get("distance", 0) / 1000.0
				alt_duration_minutes = alt_path.get("time", 0) / 60000.0
				alt_cost = (alt_distance_km * cost_per_km) + (alt_duration_minutes * cost_per_minute)
				
				alt_geojson = None
				if "points" in alt_path and "coordinates" in alt_path["points"]:
					alt_geojson = {
						"type": "LineString",
						"coordinates": alt_path["points"]["coordinates"]
					}
				
				alternative_routes.append({
					"distance_km": alt_distance_km,
					"duration_minutes": alt_duration_minutes,
					"estimated_cost": alt_cost,
					"route_geojson": alt_geojson
				})
			
			result["alternatives"] = alternative_routes
		
		return result
		
	except requests.RequestException as e:
		frappe.log_error(f"GraphHopper API Error: {str(e)}", "Routing Error")
		return {
			"status": "error",
			"message": "Routing service unavailable"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Routing Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_isochrone(latitude, longitude, time_limit=600, vehicle="car"):
	"""Get isochrone (reachable area) from GraphHopper API"""
	try:
		# Validate coordinates
		valid_coords, coord_error = validate_coordinates(latitude, longitude)
		if not valid_coords:
			return {"status": "error", "message": f"Invalid coordinates: {coord_error}"}
		
		settings = get_module_settings()
		
		# Check if GraphHopper supports isochrone (usually a premium feature)
		base_url = settings.graphhopper_url or "https://graphhopper.com/api/1"
		if not base_url.endswith('/'):
			base_url += '/'
		
		isochrone_url = base_url.replace('/route', '/isochrone')
		
		params = {
			"point": f"{latitude},{longitude}",
			"time_limit": time_limit,
			"vehicle": vehicle
		}
		
		if settings.graphhopper_api_key:
			params["key"] = settings.graphhopper_api_key
		
		headers = {
			'User-Agent': 'Hayago Mapping Module/1.0 (Frappe Framework)'
		}
		
		response = requests.get(isochrone_url, params=params, headers=headers, timeout=30)
		response.raise_for_status()
		
		isochrone_data = response.json()
		
		return {
			"status": "success",
			"isochrone": isochrone_data
		}
		
	except requests.RequestException as e:
		frappe.log_error(f"GraphHopper Isochrone API Error: {str(e)}", "Isochrone Error")
		return {
			"status": "error",
			"message": "Isochrone service unavailable or not supported"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Isochrone Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def optimize_route(points, vehicle="car", optimize=True):
	"""Optimize route for multiple points using GraphHopper Route Optimization API"""
	try:
		if len(points) < 2:
			return {
				"status": "error",
				"message": "At least 2 points are required for route optimization"
			}
		
		# Validate all coordinates
		for i, point in enumerate(points):
			if len(point) != 2:
				return {
					"status": "error",
					"message": f"Point {i+1} must have exactly 2 coordinates [lat, lng]"
				}
			
			valid_coords, coord_error = validate_coordinates(point[0], point[1])
			if not valid_coords:
				return {
					"status": "error",
					"message": f"Invalid coordinates for point {i+1}: {coord_error}"
				}
		
		settings = get_module_settings()
		
		# Use GraphHopper Route Optimization API
		base_url = settings.graphhopper_url or "https://graphhopper.com/api/1"
		if not base_url.endswith('/'):
			base_url += '/'
		
		optimization_url = base_url.replace('/route', '/optimize')
		
		# Prepare optimization request
		optimization_request = {
			"vehicles": [{
				"vehicle_id": "vehicle1",
				"start_address": {
					"location_id": "start",
					"lat": points[0][0],
					"lon": points[0][1]
				},
				"end_address": {
					"location_id": "end",
					"lat": points[-1][0],
					"lon": points[-1][1]
				}
			}],
			"services": []
		}
		
		# Add intermediate points as services
		for i, point in enumerate(points[1:-1], 1):
			optimization_request["services"].append({
				"id": f"service{i}",
				"address": {
					"location_id": f"point{i}",
					"lat": point[0],
					"lon": point[1]
				}
			})
		
		params = {}
		if settings.graphhopper_api_key:
			params["key"] = settings.graphhopper_api_key
		
		headers = {
			'Content-Type': 'application/json',
			'User-Agent': 'Hayago Mapping Module/1.0 (Frappe Framework)'
		}
		
		response = requests.post(
			optimization_url,
			json=optimization_request,
			params=params,
			headers=headers,
			timeout=60
		)
		response.raise_for_status()
		
		optimization_result = response.json()
		
		return {
			"status": "success",
			"optimization": optimization_result
		}
		
	except requests.RequestException as e:
		frappe.log_error(f"GraphHopper Optimization API Error: {str(e)}", "Route Optimization Error")
		return {
			"status": "error",
			"message": "Route optimization service unavailable"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Route Optimization Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def calculate_matrix(origins, destinations, vehicle="car"):
	"""Calculate distance/time matrix between multiple origins and destinations"""
	try:
		if not origins or not destinations:
			return {
				"status": "error",
				"message": "Origins and destinations are required"
			}
		
		# Validate coordinates
		all_points = origins + destinations
		for i, point in enumerate(all_points):
			if len(point) != 2:
				return {
					"status": "error",
					"message": f"Point {i+1} must have exactly 2 coordinates [lat, lng]"
				}
			
			valid_coords, coord_error = validate_coordinates(point[0], point[1])
			if not valid_coords:
				return {
					"status": "error",
					"message": f"Invalid coordinates for point {i+1}: {coord_error}"
				}
		
		settings = get_module_settings()
		
		# Use GraphHopper Matrix API
		base_url = settings.graphhopper_url or "https://graphhopper.com/api/1"
		if not base_url.endswith('/'):
			base_url += '/'
		
		matrix_url = base_url.replace('/route', '/matrix')
		
		# Prepare all points for the matrix request
		all_points_formatted = []
		for point in origins + destinations:
			all_points_formatted.append(f"{point[0]},{point[1]}")
		
		params = {
			"point": all_points_formatted,
			"vehicle": vehicle,
			"out_array": ["times", "distances"]
		}
		
		if settings.graphhopper_api_key:
			params["key"] = settings.graphhopper_api_key
		
		headers = {
			'User-Agent': 'Hayago Mapping Module/1.0 (Frappe Framework)'
		}
		
		response = requests.get(matrix_url, params=params, headers=headers, timeout=60)
		response.raise_for_status()
		
		matrix_result = response.json()
		
		# Extract relevant submatrix (origins to destinations)
		num_origins = len(origins)
		num_destinations = len(destinations)
		
		times_matrix = []
		distances_matrix = []
		
		if "times" in matrix_result:
			for i in range(num_origins):
				times_row = []
				for j in range(num_origins, num_origins + num_destinations):
					times_row.append(matrix_result["times"][i][j])
				times_matrix.append(times_row)
		
		if "distances" in matrix_result:
			for i in range(num_origins):
				distances_row = []
				for j in range(num_origins, num_origins + num_destinations):
					distances_row.append(matrix_result["distances"][i][j])
				distances_matrix.append(distances_row)
		
		return {
			"status": "success",
			"times": times_matrix,  # in milliseconds
			"distances": distances_matrix,  # in meters
			"origins": origins,
			"destinations": destinations
		}
		
	except requests.RequestException as e:
		frappe.log_error(f"GraphHopper Matrix API Error: {str(e)}", "Matrix Calculation Error")
		return {
			"status": "error",
			"message": "Matrix calculation service unavailable"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Matrix Calculation Error")
		return {
			"status": "error",
			"message": str(e)
		}

