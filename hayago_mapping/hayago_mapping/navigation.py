# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
import math
from .routing import get_route
from .utils import haversine_distance, calculate_bearing

@frappe.whitelist()
def get_navigation_instructions(trip_id):
	"""Get turn-by-turn navigation instructions for a trip"""
	try:
		trip = frappe.get_doc("Trip", trip_id)
		
		# Get route with instructions
		route_result = get_route(
			trip.pickup_latitude,
			trip.pickup_longitude,
			trip.dropoff_latitude,
			trip.dropoff_longitude,
			vehicle="car",
			alternatives=False
		)
		
		if route_result.get("status") != "success":
			return route_result
		
		instructions = route_result.get("instructions", [])
		
		# Process instructions for better navigation display
		processed_instructions = []
		for i, instruction in enumerate(instructions):
			processed_instruction = {
				"step": i + 1,
				"text": instruction.get("text", ""),
				"distance": instruction.get("distance", 0),
				"time": instruction.get("time", 0),
				"sign": instruction.get("sign", 0),
				"direction": get_direction_text(instruction.get("sign", 0)),
				"maneuver": get_maneuver_type(instruction.get("sign", 0))
			}
			
			# Add coordinate information if available
			if "interval" in instruction and len(instruction["interval"]) >= 2:
				start_idx = instruction["interval"][0]
				end_idx = instruction["interval"][1]
				
				# Extract coordinates from route if available
				if trip.route_geojson:
					route_data = json.loads(trip.route_geojson)
					if "coordinates" in route_data and len(route_data["coordinates"]) > end_idx:
						processed_instruction["start_coordinate"] = route_data["coordinates"][start_idx]
						processed_instruction["end_coordinate"] = route_data["coordinates"][end_idx]
			
			processed_instructions.append(processed_instruction)
		
		return {
			"status": "success",
			"trip_id": trip_id,
			"instructions": processed_instructions,
			"total_distance": route_result.get("distance_km", 0),
			"total_duration": route_result.get("duration_minutes", 0)
		}
		
	except frappe.DoesNotExistError:
		return {
			"status": "error",
			"message": "Trip not found"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Navigation Instructions Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def get_next_instruction(trip_id, current_lat, current_lng):
	"""Get the next navigation instruction based on current location"""
	try:
		trip = frappe.get_doc("Trip", trip_id)
		
		# Get all navigation instructions
		nav_result = get_navigation_instructions(trip_id)
		if nav_result.get("status") != "success":
			return nav_result
		
		instructions = nav_result.get("instructions", [])
		
		if not instructions:
			return {
				"status": "error",
				"message": "No navigation instructions available"
			}
		
		# Find the closest instruction based on current location
		min_distance = float('inf')
		next_instruction = instructions[0]
		instruction_index = 0
		
		for i, instruction in enumerate(instructions):
			if "start_coordinate" in instruction:
				coord = instruction["start_coordinate"]
				distance = haversine_distance(
					current_lat, current_lng,
					coord[1], coord[0]  # GeoJSON uses [lng, lat]
				)
				
				if distance < min_distance:
					min_distance = distance
					next_instruction = instruction
					instruction_index = i
		
		# Calculate bearing to next instruction
		if "start_coordinate" in next_instruction:
			coord = next_instruction["start_coordinate"]
			bearing = calculate_bearing(
				current_lat, current_lng,
				coord[1], coord[0]  # GeoJSON uses [lng, lat]
			)
			next_instruction["bearing"] = bearing
		
		# Calculate distance to destination
		dest_distance = haversine_distance(
			current_lat, current_lng,
			trip.dropoff_latitude, trip.dropoff_longitude
		)
		
		return {
			"status": "success",
			"current_instruction": next_instruction,
			"instruction_index": instruction_index,
			"total_instructions": len(instructions),
			"distance_to_destination": dest_distance,
			"distance_to_next_turn": min_distance
		}
		
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Next Instruction Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def log_route_point(trip_id, latitude, longitude, speed=None, timestamp=None):
	"""Log a route point for trip tracking"""
	try:
		trip = frappe.get_doc("Trip", trip_id)
		
		# Validate coordinates
		if not (-90 <= float(latitude) <= 90):
			return {"status": "error", "message": "Invalid latitude"}
		
		if not (-180 <= float(longitude) <= 180):
			return {"status": "error", "message": "Invalid longitude"}
		
		# Add route log entry
		route_log = {
			"timestamp": timestamp or frappe.utils.now(),
			"latitude": float(latitude),
			"longitude": float(longitude),
			"speed": float(speed) if speed else None
		}
		
		trip.append("route_logs", route_log)
		trip.save()
		
		# Also update driver location
		from .api import update_driver_location_api
		update_driver_location_api(
			driver=trip.driver,
			latitude=latitude,
			longitude=longitude,
			speed=speed,
			trip=trip_id
		)
		
		return {
			"status": "success",
			"message": "Route point logged successfully"
		}
		
	except frappe.DoesNotExistError:
		return {
			"status": "error",
			"message": "Trip not found"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Route Point Logging Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def start_trip_navigation(trip_id):
	"""Start navigation for a trip"""
	try:
		trip = frappe.get_doc("Trip", trip_id)
		
		if trip.status not in ["Accepted", "Pending"]:
			return {
				"status": "error",
				"message": "Trip cannot be started in current status"
			}
		
		# Update trip status and start time
		trip.status = "On Route"
		trip.start_time = frappe.utils.now()
		trip.save()
		
		# Get navigation instructions
		nav_result = get_navigation_instructions(trip_id)
		
		return {
			"status": "success",
			"message": "Trip navigation started",
			"trip": {
				"id": trip.name,
				"status": trip.status,
				"start_time": trip.start_time,
				"pickup_address": trip.pickup_address,
				"dropoff_address": trip.dropoff_address,
				"estimated_distance": trip.estimated_distance,
				"estimated_duration": trip.estimated_duration
			},
			"navigation": nav_result
		}
		
	except frappe.DoesNotExistError:
		return {
			"status": "error",
			"message": "Trip not found"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Start Trip Navigation Error")
		return {
			"status": "error",
			"message": str(e)
		}

@frappe.whitelist()
def complete_trip(trip_id, end_latitude=None, end_longitude=None):
	"""Complete a trip and calculate final metrics"""
	try:
		trip = frappe.get_doc("Trip", trip_id)
		
		if trip.status != "On Route":
			return {
				"status": "error",
				"message": "Trip is not currently on route"
			}
		
		# Update trip status and end time
		trip.status = "Completed"
		trip.end_time = frappe.utils.now()
		
		# Log final location if provided
		if end_latitude and end_longitude:
			log_route_point(trip_id, end_latitude, end_longitude)
		
		# Calculate final cost (this will be done in the trip's before_save method)
		trip.save()
		
		return {
			"status": "success",
			"message": "Trip completed successfully",
			"trip": {
				"id": trip.name,
				"status": trip.status,
				"start_time": trip.start_time,
				"end_time": trip.end_time,
				"actual_distance": trip.actual_distance,
				"actual_duration": trip.actual_duration,
				"actual_cost": trip.actual_cost
			}
		}
		
	except frappe.DoesNotExistError:
		return {
			"status": "error",
			"message": "Trip not found"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Complete Trip Error")
		return {
			"status": "error",
			"message": str(e)
		}

def get_direction_text(sign_code):
	"""Convert GraphHopper sign code to human-readable direction"""
	direction_map = {
		0: "Continue",
		1: "Turn slight right",
		2: "Turn right",
		3: "Turn sharp right",
		-1: "Turn slight left",
		-2: "Turn left",
		-3: "Turn sharp left",
		4: "Arrive at destination",
		5: "Via point reached",
		6: "Enter roundabout",
		7: "Exit roundabout",
		8: "U-turn"
	}
	
	return direction_map.get(sign_code, "Continue")

def get_maneuver_type(sign_code):
	"""Convert GraphHopper sign code to maneuver type"""
	maneuver_map = {
		0: "straight",
		1: "slight-right",
		2: "right",
		3: "sharp-right",
		-1: "slight-left",
		-2: "left",
		-3: "sharp-left",
		4: "arrive",
		5: "via",
		6: "roundabout-enter",
		7: "roundabout-exit",
		8: "u-turn"
	}
	
	return maneuver_map.get(sign_code, "straight")

@frappe.whitelist()
def get_trip_progress(trip_id):
	"""Get current progress of a trip"""
	try:
		trip = frappe.get_doc("Trip", trip_id)
		
		if not trip.route_logs:
			return {
				"status": "success",
				"progress": 0,
				"distance_covered": 0,
				"estimated_remaining": trip.estimated_distance or 0
			}
		
		# Calculate distance covered from route logs
		total_distance = 0
		for i in range(1, len(trip.route_logs)):
			prev_log = trip.route_logs[i-1]
			curr_log = trip.route_logs[i]
			
			distance = haversine_distance(
				prev_log.latitude, prev_log.longitude,
				curr_log.latitude, curr_log.longitude
			)
			total_distance += distance
		
		# Calculate progress percentage
		estimated_distance = trip.estimated_distance or 0
		progress_percentage = 0
		if estimated_distance > 0:
			progress_percentage = min((total_distance / estimated_distance) * 100, 100)
		
		# Calculate remaining distance to destination
		if trip.route_logs:
			last_log = trip.route_logs[-1]
			remaining_distance = haversine_distance(
				last_log.latitude, last_log.longitude,
				trip.dropoff_latitude, trip.dropoff_longitude
			)
		else:
			remaining_distance = estimated_distance
		
		return {
			"status": "success",
			"progress": progress_percentage,
			"distance_covered": total_distance,
			"estimated_remaining": remaining_distance,
			"total_route_points": len(trip.route_logs)
		}
		
	except frappe.DoesNotExistError:
		return {
			"status": "error",
			"message": "Trip not found"
		}
	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "Trip Progress Error")
		return {
			"status": "error",
			"message": str(e)
		}

