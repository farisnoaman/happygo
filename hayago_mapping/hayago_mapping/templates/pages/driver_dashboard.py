# -*- coding: utf-8 -*-
# Copyright (c) 2025, Manus AI and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def get_context(context):
    """Get context for driver dashboard page"""
    
    # Check if user is logged in
    if frappe.session.user == 'Guest':
        frappe.throw("Please login to access the driver dashboard", frappe.PermissionError)
    
    context.no_cache = 1
    context.show_sidebar = False
    
    # Get driver information
    user = frappe.get_doc("User", frappe.session.user)
    context.driver_name = user.full_name or user.name
    context.driver_email = user.email
    
    # Get current active trip for the driver
    active_trips = frappe.get_all("Trip", 
        filters={
            "driver": frappe.session.user,
            "status": ["in", ["Accepted", "On Route"]]
        },
        fields=["name", "pickup_address", "dropoff_address", "status", "customer"],
        limit=1
    )
    
    context.current_trip = active_trips[0] if active_trips else None
    
    # Get driver statistics
    context.driver_stats = get_driver_statistics(frappe.session.user)
    
    return context

def get_driver_statistics(driver):
    """Get driver statistics"""
    from hayago_mapping.hayago_mapping.utils import get_trip_statistics
    
    stats = get_trip_statistics(driver=driver, date_range=30)
    
    return {
        'total_trips': stats.get('total_trips', 0),
        'completed_trips': stats.get('completed_trips', 0),
        'cancelled_trips': stats.get('cancelled_trips', 0),
        'total_revenue': stats.get('total_revenue', 0),
        'avg_distance': stats.get('avg_distance', 0),
        'avg_duration': stats.get('avg_duration', 0)
    }

