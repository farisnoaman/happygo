// Hayago Mapping - Leaflet Map Controller
// Copyright (c) 2025, Manus AI

frappe.provide('hayago_mapping');

hayago_mapping.MapController = class {
    constructor(options) {
        this.options = Object.assign({
            container: 'map',
            center: [37.7749, -122.4194], // Default to San Francisco
            zoom: 13,
            height: '400px',
            enableGeolocation: true,
            enableRouting: true,
            enableDriverTracking: true
        }, options);
        
        this.map = null;
        this.markers = {};
        this.routes = {};
        this.driverMarkers = {};
        this.currentLocationMarker = null;
        this.trackingInterval = null;
        
        this.init();
    }
    
    init() {
        this.createMapContainer();
        this.initializeMap();
        this.setupEventHandlers();
        
        if (this.options.enableGeolocation) {
            this.getCurrentLocation();
        }
    }
    
    createMapContainer() {
        const container = document.getElementById(this.options.container);
        if (!container) {
            console.error('Map container not found:', this.options.container);
            return;
        }
        
        container.style.height = this.options.height;
        container.style.width = '100%';
        container.style.position = 'relative';
        container.style.borderRadius = '8px';
        container.style.overflow = 'hidden';
        container.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
    }
    
    initializeMap() {
        // Initialize Leaflet map
        this.map = L.map(this.options.container, {
            center: this.options.center,
            zoom: this.options.zoom,
            zoomControl: true,
            attributionControl: true
        });
        
        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 19
        }).addTo(this.map);
        
        // Add custom controls
        this.addCustomControls();
        
        console.log('Map initialized successfully');
    }
    
    addCustomControls() {
        // Add location control
        if (this.options.enableGeolocation) {
            const locationControl = L.control({position: 'topright'});
            locationControl.onAdd = () => {
                const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
                div.innerHTML = '<a href="#" title="Get Current Location"><i class="fa fa-location-arrow"></i></a>';
                div.style.backgroundColor = 'white';
                div.style.width = '30px';
                div.style.height = '30px';
                div.style.cursor = 'pointer';
                
                L.DomEvent.on(div, 'click', (e) => {
                    L.DomEvent.stopPropagation(e);
                    this.getCurrentLocation();
                });
                
                return div;
            };
            locationControl.addTo(this.map);
        }
        
        // Add fullscreen control
        const fullscreenControl = L.control({position: 'topright'});
        fullscreenControl.onAdd = () => {
            const div = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom');
            div.innerHTML = '<a href="#" title="Toggle Fullscreen"><i class="fa fa-expand"></i></a>';
            div.style.backgroundColor = 'white';
            div.style.width = '30px';
            div.style.height = '30px';
            div.style.cursor = 'pointer';
            
            L.DomEvent.on(div, 'click', (e) => {
                L.DomEvent.stopPropagation(e);
                this.toggleFullscreen();
            });
            
            return div;
        };
        fullscreenControl.addTo(this.map);
    }
    
    setupEventHandlers() {
        // Map click handler
        this.map.on('click', (e) => {
            this.onMapClick(e);
        });
        
        // Map move handler
        this.map.on('moveend', () => {
            this.onMapMove();
        });
    }
    
    onMapClick(e) {
        const {lat, lng} = e.latlng;
        
        // Trigger custom event
        if (this.options.onMapClick) {
            this.options.onMapClick(lat, lng);
        }
        
        // Reverse geocode the clicked location
        this.reverseGeocode(lat, lng).then(address => {
            if (address) {
                this.showPopup(lat, lng, `<strong>Location:</strong><br>${address}`);
            }
        });
    }
    
    onMapMove() {
        const center = this.map.getCenter();
        const zoom = this.map.getZoom();
        
        if (this.options.onMapMove) {
            this.options.onMapMove(center.lat, center.lng, zoom);
        }
    }
    
    getCurrentLocation() {
        if (!navigator.geolocation) {
            frappe.msgprint('Geolocation is not supported by this browser.');
            return;
        }
        
        navigator.geolocation.getCurrentPosition(
            (position) => {
                const lat = position.coords.latitude;
                const lng = position.coords.longitude;
                
                this.setCurrentLocation(lat, lng);
                this.map.setView([lat, lng], 15);
            },
            (error) => {
                console.error('Geolocation error:', error);
                frappe.msgprint('Unable to get your location.');
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 60000
            }
        );
    }
    
    setCurrentLocation(lat, lng) {
        if (this.currentLocationMarker) {
            this.map.removeLayer(this.currentLocationMarker);
        }
        
        this.currentLocationMarker = L.marker([lat, lng], {
            icon: L.divIcon({
                className: 'current-location-marker',
                html: '<div style="background: #007bff; width: 12px; height: 12px; border-radius: 50%; border: 3px solid white; box-shadow: 0 0 10px rgba(0,123,255,0.5);"></div>',
                iconSize: [18, 18],
                iconAnchor: [9, 9]
            })
        }).addTo(this.map);
        
        this.currentLocationMarker.bindPopup('Your current location').openPopup();
    }
    
    addMarker(id, lat, lng, options = {}) {
        const markerOptions = Object.assign({
            title: 'Marker',
            popup: null,
            icon: null,
            draggable: false
        }, options);
        
        let marker;
        
        if (markerOptions.icon) {
            marker = L.marker([lat, lng], {
                title: markerOptions.title,
                draggable: markerOptions.draggable,
                icon: markerOptions.icon
            });
        } else {
            marker = L.marker([lat, lng], {
                title: markerOptions.title,
                draggable: markerOptions.draggable
            });
        }
        
        marker.addTo(this.map);
        
        if (markerOptions.popup) {
            marker.bindPopup(markerOptions.popup);
        }
        
        if (markerOptions.draggable) {
            marker.on('dragend', (e) => {
                const position = e.target.getLatLng();
                if (markerOptions.onDragEnd) {
                    markerOptions.onDragEnd(position.lat, position.lng);
                }
            });
        }
        
        this.markers[id] = marker;
        return marker;
    }
    
    removeMarker(id) {
        if (this.markers[id]) {
            this.map.removeLayer(this.markers[id]);
            delete this.markers[id];
        }
    }
    
    addDriverMarker(driverId, lat, lng, options = {}) {
        const driverOptions = Object.assign({
            name: `Driver ${driverId}`,
            status: 'available',
            speed: null,
            heading: null
        }, options);
        
        // Create custom driver icon
        const iconHtml = this.createDriverIconHtml(driverOptions);
        const driverIcon = L.divIcon({
            className: 'driver-marker',
            html: iconHtml,
            iconSize: [30, 30],
            iconAnchor: [15, 15]
        });
        
        // Remove existing driver marker if it exists
        if (this.driverMarkers[driverId]) {
            this.map.removeLayer(this.driverMarkers[driverId]);
        }
        
        // Create new marker
        const marker = L.marker([lat, lng], {
            icon: driverIcon,
            title: driverOptions.name
        }).addTo(this.map);
        
        // Create popup content
        const popupContent = this.createDriverPopupContent(driverId, driverOptions);
        marker.bindPopup(popupContent);
        
        this.driverMarkers[driverId] = marker;
        return marker;
    }
    
    createDriverIconHtml(options) {
        const statusColor = {
            'available': '#28a745',
            'busy': '#ffc107',
            'offline': '#6c757d'
        }[options.status] || '#28a745';
        
        return `
            <div style="
                background: ${statusColor};
                width: 24px;
                height: 24px;
                border-radius: 50%;
                border: 3px solid white;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3);
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 12px;
                font-weight: bold;
            ">
                🚗
            </div>
        `;
    }
    
    createDriverPopupContent(driverId, options) {
        return `
            <div style="min-width: 200px;">
                <h6 style="margin: 0 0 8px 0; color: #333;">${options.name}</h6>
                <div style="font-size: 12px; color: #666;">
                    <div><strong>Status:</strong> ${options.status}</div>
                    ${options.speed ? `<div><strong>Speed:</strong> ${options.speed} km/h</div>` : ''}
                    ${options.heading ? `<div><strong>Heading:</strong> ${options.heading}°</div>` : ''}
                </div>
                <div style="margin-top: 8px;">
                    <button onclick="hayago_mapping.selectDriver('${driverId}')" 
                            class="btn btn-sm btn-primary">
                        Select Driver
                    </button>
                </div>
            </div>
        `;
    }
    
    updateDriverLocation(driverId, lat, lng, options = {}) {
        if (this.driverMarkers[driverId]) {
            const marker = this.driverMarkers[driverId];
            
            // Animate movement
            const currentLatLng = marker.getLatLng();
            const newLatLng = L.latLng(lat, lng);
            
            // Simple animation by updating position
            marker.setLatLng(newLatLng);
            
            // Update popup content if options provided
            if (Object.keys(options).length > 0) {
                const popupContent = this.createDriverPopupContent(driverId, options);
                marker.getPopup().setContent(popupContent);
            }
        } else {
            // Create new marker if it doesn't exist
            this.addDriverMarker(driverId, lat, lng, options);
        }
    }
    
    addRoute(routeId, coordinates, options = {}) {
        const routeOptions = Object.assign({
            color: '#007bff',
            weight: 4,
            opacity: 0.7,
            smoothFactor: 1
        }, options);
        
        // Remove existing route if it exists
        if (this.routes[routeId]) {
            this.map.removeLayer(this.routes[routeId]);
        }
        
        // Create polyline
        const route = L.polyline(coordinates, routeOptions).addTo(this.map);
        
        if (options.popup) {
            route.bindPopup(options.popup);
        }
        
        this.routes[routeId] = route;
        
        // Fit map to route bounds
        if (options.fitBounds !== false) {
            this.map.fitBounds(route.getBounds(), {padding: [20, 20]});
        }
        
        return route;
    }
    
    removeRoute(routeId) {
        if (this.routes[routeId]) {
            this.map.removeLayer(this.routes[routeId]);
            delete this.routes[routeId];
        }
    }
    
    showPopup(lat, lng, content) {
        L.popup()
            .setLatLng([lat, lng])
            .setContent(content)
            .openOn(this.map);
    }
    
    fitBounds(bounds, options = {}) {
        this.map.fitBounds(bounds, options);
    }
    
    setView(lat, lng, zoom) {
        this.map.setView([lat, lng], zoom);
    }
    
    toggleFullscreen() {
        const container = document.getElementById(this.options.container);
        
        if (!document.fullscreenElement) {
            container.requestFullscreen().then(() => {
                setTimeout(() => {
                    this.map.invalidateSize();
                }, 100);
            });
        } else {
            document.exitFullscreen();
        }
    }
    
    startDriverTracking(interval = 30000) {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
        }
        
        this.trackingInterval = setInterval(() => {
            this.updateNearbyDrivers();
        }, interval);
        
        // Initial update
        this.updateNearbyDrivers();
    }
    
    stopDriverTracking() {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
            this.trackingInterval = null;
        }
    }
    
    updateNearbyDrivers() {
        const center = this.map.getCenter();
        
        frappe.call({
            method: 'hayago_mapping.api.find_nearby_drivers',
            args: {
                latitude: center.lat,
                longitude: center.lng,
                radius: 10 // 10km radius
            },
            callback: (response) => {
                if (response.message && response.message.status === 'success') {
                    const drivers = response.message.drivers || [];
                    
                    // Clear existing driver markers
                    Object.keys(this.driverMarkers).forEach(driverId => {
                        this.map.removeLayer(this.driverMarkers[driverId]);
                    });
                    this.driverMarkers = {};
                    
                    // Add new driver markers
                    drivers.forEach(driver => {
                        this.addDriverMarker(driver.driver, driver.latitude, driver.longitude, {
                            name: driver.driver_name || driver.driver,
                            status: 'available',
                            speed: driver.speed
                        });
                    });
                }
            }
        });
    }
    
    async reverseGeocode(lat, lng) {
        try {
            const response = await frappe.call({
                method: 'hayago_mapping.api.reverse_geocode',
                args: {
                    latitude: lat,
                    longitude: lng
                }
            });
            
            if (response.message && response.message.status === 'success') {
                return response.message.address;
            }
        } catch (error) {
            console.error('Reverse geocoding error:', error);
        }
        
        return null;
    }
    
    async geocodeAddress(address) {
        try {
            const response = await frappe.call({
                method: 'hayago_mapping.api.geocode_address',
                args: {
                    address: address
                }
            });
            
            if (response.message && response.message.status === 'success') {
                return {
                    lat: response.message.latitude,
                    lng: response.message.longitude,
                    display_name: response.message.display_name
                };
            }
        } catch (error) {
            console.error('Geocoding error:', error);
        }
        
        return null;
    }
    
    destroy() {
        if (this.trackingInterval) {
            clearInterval(this.trackingInterval);
        }
        
        if (this.map) {
            this.map.remove();
        }
    }
};

// Global helper functions
hayago_mapping.selectDriver = function(driverId) {
    frappe.msgprint(`Driver ${driverId} selected!`);
    // Implement driver selection logic here
};

// Initialize map when DOM is ready
$(document).ready(function() {
    // Auto-initialize maps with class 'hayago-map'
    $('.hayago-map').each(function() {
        const container = $(this);
        const mapId = container.attr('id') || 'map-' + Math.random().toString(36).substr(2, 9);
        container.attr('id', mapId);
        
        const options = {
            container: mapId,
            height: container.data('height') || '400px',
            center: container.data('center') ? container.data('center').split(',').map(Number) : [37.7749, -122.4194],
            zoom: container.data('zoom') || 13
        };
        
        new hayago_mapping.MapController(options);
    });
});

