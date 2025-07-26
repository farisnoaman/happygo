// Trip DocType JavaScript
// Copyright (c) 2025, Manus AI

frappe.ui.form.on('Trip', {
    refresh: function(frm) {
        // Add custom buttons
        if (frm.doc.status === 'Pending') {
            frm.add_custom_button(__('Find Driver'), function() {
                find_nearby_driver(frm);
            }, __('Actions'));
        }
        
        if (frm.doc.status === 'Accepted') {
            frm.add_custom_button(__('Start Trip'), function() {
                start_trip_navigation(frm);
            }, __('Actions'));
        }
        
        if (frm.doc.status === 'On Route') {
            frm.add_custom_button(__('Complete Trip'), function() {
                complete_trip(frm);
            }, __('Actions'));
        }
        
        // Add map view button
        frm.add_custom_button(__('View on Map'), function() {
            show_trip_on_map(frm);
        });
        
        // Initialize map if coordinates are available
        if (frm.doc.pickup_latitude && frm.doc.pickup_longitude) {
            setTimeout(() => {
                initialize_trip_map(frm);
            }, 500);
        }
    },
    
    pickup_address: function(frm) {
        if (frm.doc.pickup_address) {
            geocode_address(frm.doc.pickup_address, (result) => {
                if (result) {
                    frm.set_value('pickup_latitude', result.lat);
                    frm.set_value('pickup_longitude', result.lng);
                    update_trip_map(frm);
                }
            });
        }
    },
    
    dropoff_address: function(frm) {
        if (frm.doc.dropoff_address) {
            geocode_address(frm.doc.dropoff_address, (result) => {
                if (result) {
                    frm.set_value('dropoff_latitude', result.lat);
                    frm.set_value('dropoff_longitude', result.lng);
                    update_trip_map(frm);
                    
                    // Calculate route and cost if both addresses are set
                    if (frm.doc.pickup_latitude && frm.doc.pickup_longitude) {
                        calculate_trip_estimate(frm);
                    }
                }
            });
        }
    },
    
    pickup_latitude: function(frm) {
        update_trip_map(frm);
    },
    
    pickup_longitude: function(frm) {
        update_trip_map(frm);
    },
    
    dropoff_latitude: function(frm) {
        update_trip_map(frm);
        if (frm.doc.pickup_latitude && frm.doc.pickup_longitude) {
            calculate_trip_estimate(frm);
        }
    },
    
    dropoff_longitude: function(frm) {
        update_trip_map(frm);
        if (frm.doc.pickup_latitude && frm.doc.pickup_longitude) {
            calculate_trip_estimate(frm);
        }
    }
});

function initialize_trip_map(frm) {
    // Create map container
    const mapHtml = `
        <div class="row">
            <div class="col-md-12">
                <div class="form-group">
                    <label class="control-label">Trip Route Map</label>
                    <div id="trip-map" class="hayago-map" style="height: 400px; margin-top: 10px;"></div>
                </div>
            </div>
        </div>
    `;
    
    // Insert map after the route section
    const routeSection = frm.fields_dict.route_section.$wrapper;
    if (routeSection && !document.getElementById('trip-map')) {
        routeSection.after(mapHtml);
        
        // Initialize map controller
        setTimeout(() => {
            if (!frm.trip_map) {
                frm.trip_map = new hayago_mapping.MapController({
                    container: 'trip-map',
                    center: [frm.doc.pickup_latitude, frm.doc.pickup_longitude],
                    zoom: 13,
                    height: '400px'
                });
                
                update_trip_map(frm);
            }
        }, 100);
    }
}

function update_trip_map(frm) {
    if (!frm.trip_map) return;
    
    // Clear existing markers and routes
    Object.keys(frm.trip_map.markers).forEach(id => {
        frm.trip_map.removeMarker(id);
    });
    Object.keys(frm.trip_map.routes).forEach(id => {
        frm.trip_map.removeRoute(id);
    });
    
    // Add pickup marker
    if (frm.doc.pickup_latitude && frm.doc.pickup_longitude) {
        frm.trip_map.addMarker('pickup', frm.doc.pickup_latitude, frm.doc.pickup_longitude, {
            title: 'Pickup Location',
            popup: `<strong>Pickup:</strong><br>${frm.doc.pickup_address || 'Pickup Location'}`,
            icon: L.divIcon({
                className: 'pickup-marker',
                html: '<div style="background: #28a745; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">P</div>',
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            })
        });
    }
    
    // Add dropoff marker
    if (frm.doc.dropoff_latitude && frm.doc.dropoff_longitude) {
        frm.trip_map.addMarker('dropoff', frm.doc.dropoff_latitude, frm.doc.dropoff_longitude, {
            title: 'Dropoff Location',
            popup: `<strong>Dropoff:</strong><br>${frm.doc.dropoff_address || 'Dropoff Location'}`,
            icon: L.divIcon({
                className: 'dropoff-marker',
                html: '<div style="background: #dc3545; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 6px rgba(0,0,0,0.3);">D</div>',
                iconSize: [28, 28],
                iconAnchor: [14, 14]
            })
        });
    }
    
    // Add planned route if available
    if (frm.doc.route_geojson) {
        try {
            const routeData = JSON.parse(frm.doc.route_geojson);
            if (routeData.coordinates) {
                const coordinates = routeData.coordinates.map(coord => [coord[1], coord[0]]); // Convert [lng, lat] to [lat, lng]
                frm.trip_map.addRoute('planned', coordinates, {
                    color: '#007bff',
                    weight: 4,
                    opacity: 0.7,
                    popup: `<strong>Planned Route</strong><br>Distance: ${frm.doc.estimated_distance || 'N/A'} km<br>Duration: ${frm.doc.estimated_duration || 'N/A'} min`
                });
            }
        } catch (e) {
            console.error('Error parsing route GeoJSON:', e);
        }
    }
    
    // Add logged route if available
    if (frm.doc.logged_route_geojson) {
        try {
            const loggedRouteData = JSON.parse(frm.doc.logged_route_geojson);
            if (loggedRouteData.coordinates) {
                const coordinates = loggedRouteData.coordinates.map(coord => [coord[1], coord[0]]); // Convert [lng, lat] to [lat, lng]
                frm.trip_map.addRoute('logged', coordinates, {
                    color: '#28a745',
                    weight: 5,
                    opacity: 0.8,
                    popup: `<strong>Actual Route</strong><br>Distance: ${frm.doc.actual_distance || 'N/A'} km<br>Duration: ${frm.doc.actual_duration || 'N/A'} min`
                });
            }
        } catch (e) {
            console.error('Error parsing logged route GeoJSON:', e);
        }
    }
    
    // Fit map to show all markers
    const bounds = [];
    if (frm.doc.pickup_latitude && frm.doc.pickup_longitude) {
        bounds.push([frm.doc.pickup_latitude, frm.doc.pickup_longitude]);
    }
    if (frm.doc.dropoff_latitude && frm.doc.dropoff_longitude) {
        bounds.push([frm.doc.dropoff_latitude, frm.doc.dropoff_longitude]);
    }
    
    if (bounds.length > 0) {
        if (bounds.length === 1) {
            frm.trip_map.setView(bounds[0][0], bounds[0][1], 15);
        } else {
            frm.trip_map.fitBounds(bounds, {padding: [20, 20]});
        }
    }
}

function geocode_address(address, callback) {
    frappe.call({
        method: 'hayago_mapping.api.geocode_address',
        args: {
            address: address
        },
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                callback({
                    lat: response.message.latitude,
                    lng: response.message.longitude,
                    display_name: response.message.display_name
                });
            } else {
                frappe.msgprint(__('Could not geocode address: ') + address);
                callback(null);
            }
        }
    });
}

function calculate_trip_estimate(frm) {
    if (!frm.doc.pickup_latitude || !frm.doc.pickup_longitude || 
        !frm.doc.dropoff_latitude || !frm.doc.dropoff_longitude) {
        return;
    }
    
    frappe.call({
        method: 'hayago_mapping.hayago_mapping.doctype.trip.trip.estimate_trip_cost',
        args: {
            pickup_lat: frm.doc.pickup_latitude,
            pickup_lng: frm.doc.pickup_longitude,
            dropoff_lat: frm.doc.dropoff_latitude,
            dropoff_lng: frm.doc.dropoff_longitude
        },
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                const result = response.message;
                
                frm.set_value('estimated_distance', result.estimated_distance);
                frm.set_value('estimated_duration', result.estimated_duration);
                frm.set_value('estimated_cost', result.estimated_cost);
                frm.set_value('route_geojson', result.route_geojson);
                
                // Update map with new route
                update_trip_map(frm);
                
                frappe.show_alert({
                    message: __('Trip estimate updated'),
                    indicator: 'green'
                });
            } else {
                frappe.msgprint(__('Could not calculate trip estimate'));
            }
        }
    });
}

function find_nearby_driver(frm) {
    if (!frm.doc.pickup_latitude || !frm.doc.pickup_longitude) {
        frappe.msgprint(__('Please set pickup location first'));
        return;
    }
    
    frappe.call({
        method: 'hayago_mapping.api.match_driver_to_trip',
        args: {
            pickup_latitude: frm.doc.pickup_latitude,
            pickup_longitude: frm.doc.pickup_longitude,
            customer: frm.doc.customer,
            pickup_address: frm.doc.pickup_address,
            dropoff_address: frm.doc.dropoff_address,
            dropoff_latitude: frm.doc.dropoff_latitude,
            dropoff_longitude: frm.doc.dropoff_longitude
        },
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                frappe.msgprint(__('Driver matched successfully!'));
                frm.reload_doc();
            } else {
                frappe.msgprint(__('No available drivers found in the area'));
            }
        }
    });
}

function start_trip_navigation(frm) {
    frappe.call({
        method: 'hayago_mapping.navigation.start_trip_navigation',
        args: {
            trip_id: frm.doc.name
        },
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                frappe.show_alert({
                    message: __('Trip navigation started'),
                    indicator: 'green'
                });
                frm.reload_doc();
            } else {
                frappe.msgprint(__('Could not start trip navigation'));
            }
        }
    });
}

function complete_trip(frm) {
    frappe.call({
        method: 'hayago_mapping.navigation.complete_trip',
        args: {
            trip_id: frm.doc.name
        },
        callback: function(response) {
            if (response.message && response.message.status === 'success') {
                frappe.show_alert({
                    message: __('Trip completed successfully'),
                    indicator: 'green'
                });
                frm.reload_doc();
            } else {
                frappe.msgprint(__('Could not complete trip'));
            }
        }
    });
}

function show_trip_on_map(frm) {
    // Open a modal with a larger map view
    const dialog = new frappe.ui.Dialog({
        title: __('Trip Map View'),
        size: 'extra-large',
        fields: [
            {
                fieldtype: 'HTML',
                fieldname: 'map_html',
                options: '<div id="trip-map-modal" class="hayago-map" style="height: 500px;"></div>'
            }
        ]
    });
    
    dialog.show();
    
    // Initialize map in modal
    setTimeout(() => {
        const modalMap = new hayago_mapping.MapController({
            container: 'trip-map-modal',
            center: [frm.doc.pickup_latitude || 37.7749, frm.doc.pickup_longitude || -122.4194],
            zoom: 13,
            height: '500px',
            enableDriverTracking: true
        });
        
        // Add trip markers and routes
        if (frm.doc.pickup_latitude && frm.doc.pickup_longitude) {
            modalMap.addMarker('pickup', frm.doc.pickup_latitude, frm.doc.pickup_longitude, {
                title: 'Pickup Location',
                popup: `<strong>Pickup:</strong><br>${frm.doc.pickup_address || 'Pickup Location'}`
            });
        }
        
        if (frm.doc.dropoff_latitude && frm.doc.dropoff_longitude) {
            modalMap.addMarker('dropoff', frm.doc.dropoff_latitude, frm.doc.dropoff_longitude, {
                title: 'Dropoff Location',
                popup: `<strong>Dropoff:</strong><br>${frm.doc.dropoff_address || 'Dropoff Location'}`
            });
        }
        
        // Start driver tracking if trip is active
        if (frm.doc.status === 'On Route') {
            modalMap.startDriverTracking(10000); // Update every 10 seconds
        }
        
        // Clean up when dialog is closed
        dialog.onhide = () => {
            modalMap.destroy();
        };
    }, 200);
}

