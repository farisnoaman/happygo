from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.location import db, DriverLocation, OfflineLocationQueue, SyncStatus
import requests
import os
import json

tracking_bp = Blueprint('tracking', __name__)

# Configuration - these should be environment variables in production
FRAPPE_BASE_URL = os.getenv('FRAPPE_BASE_URL', 'http://localhost:8000')
FRAPPE_API_KEY = os.getenv('FRAPPE_API_KEY', '')
FRAPPE_API_SECRET = os.getenv('FRAPPE_API_SECRET', '')

@tracking_bp.route('/location', methods=['POST'])
def update_location():
    """Update driver location - supports both online and offline updates"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['driver_id', 'latitude', 'longitude']
        for field in required_fields:
            if field not in data:
                return jsonify({'status': 'error', 'message': f'Missing required field: {field}'}), 400
        
        # Validate coordinate ranges
        try:
            lat = float(data['latitude'])
            lng = float(data['longitude'])
            
            if not (-90 <= lat <= 90):
                return jsonify({'status': 'error', 'message': 'Invalid latitude range'}), 400
            
            if not (-180 <= lng <= 180):
                return jsonify({'status': 'error', 'message': 'Invalid longitude range'}), 400
                
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Invalid coordinate format'}), 400
        
        # Parse timestamp
        timestamp = datetime.utcnow()
        if 'timestamp' in data:
            try:
                timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
            except ValueError:
                # Use current time if timestamp parsing fails
                pass
        
        # Create location record
        location = DriverLocation(
            driver_id=data['driver_id'],
            timestamp=timestamp,
            latitude=lat,
            longitude=lng,
            speed=float(data.get('speed')) if data.get('speed') is not None else None,
            heading=float(data.get('heading')) if data.get('heading') is not None else None,
            accuracy=float(data.get('accuracy')) if data.get('accuracy') is not None else None,
            is_offline=bool(data.get('is_offline', False)),
            trip_id=data.get('trip_id')
        )
        
        db.session.add(location)
        db.session.commit()
        
        # Update sync status
        sync_status = SyncStatus.query.filter_by(driver_id=data['driver_id']).first()
        if not sync_status:
            sync_status = SyncStatus(driver_id=data['driver_id'])
            db.session.add(sync_status)
        
        sync_status.pending_locations += 1
        db.session.commit()
        
        # Try to sync to Frappe immediately if online
        if not data.get('is_offline', False):
            try:
                sync_result = sync_location_to_frappe(location)
                if sync_result:
                    location.synced_to_frappe = True
                    sync_status.pending_locations = max(0, sync_status.pending_locations - 1)
                    sync_status.last_sync_timestamp = datetime.utcnow()
                    db.session.commit()
            except Exception as e:
                # Log error but don't fail the request
                print(f"Sync error: {str(e)}")
        
        return jsonify({
            'status': 'success',
            'message': 'Location updated successfully',
            'location_id': location.id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@tracking_bp.route('/location/batch', methods=['POST'])
def update_locations_batch():
    """Update multiple driver locations in batch - useful for offline sync"""
    try:
        data = request.get_json()
        
        if not data or 'locations' not in data:
            return jsonify({'status': 'error', 'message': 'No locations provided'}), 400
        
        locations = data['locations']
        if not isinstance(locations, list):
            return jsonify({'status': 'error', 'message': 'Locations must be a list'}), 400
        
        processed_locations = []
        failed_locations = []
        
        for i, loc_data in enumerate(locations):
            try:
                # Validate required fields
                required_fields = ['driver_id', 'latitude', 'longitude']
                for field in required_fields:
                    if field not in loc_data:
                        failed_locations.append({'index': i, 'error': f'Missing required field: {field}'})
                        continue
                
                # Validate coordinates
                lat = float(loc_data['latitude'])
                lng = float(loc_data['longitude'])
                
                if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                    failed_locations.append({'index': i, 'error': 'Invalid coordinates'})
                    continue
                
                # Parse timestamp
                timestamp = datetime.utcnow()
                if 'timestamp' in loc_data:
                    try:
                        timestamp = datetime.fromisoformat(loc_data['timestamp'].replace('Z', '+00:00'))
                    except ValueError:
                        pass
                
                # Create location record
                location = DriverLocation(
                    driver_id=loc_data['driver_id'],
                    timestamp=timestamp,
                    latitude=lat,
                    longitude=lng,
                    speed=float(loc_data.get('speed')) if loc_data.get('speed') is not None else None,
                    heading=float(loc_data.get('heading')) if loc_data.get('heading') is not None else None,
                    accuracy=float(loc_data.get('accuracy')) if loc_data.get('accuracy') is not None else None,
                    is_offline=bool(loc_data.get('is_offline', False)),
                    trip_id=loc_data.get('trip_id')
                )
                
                db.session.add(location)
                processed_locations.append(location)
                
            except Exception as e:
                failed_locations.append({'index': i, 'error': str(e)})
        
        # Commit all successful locations
        db.session.commit()
        
        # Update sync status for each driver
        driver_counts = {}
        for location in processed_locations:
            driver_counts[location.driver_id] = driver_counts.get(location.driver_id, 0) + 1
        
        for driver_id, count in driver_counts.items():
            sync_status = SyncStatus.query.filter_by(driver_id=driver_id).first()
            if not sync_status:
                sync_status = SyncStatus(driver_id=driver_id)
                db.session.add(sync_status)
            
            sync_status.pending_locations += count
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Processed {len(processed_locations)} locations',
            'processed_count': len(processed_locations),
            'failed_count': len(failed_locations),
            'failed_locations': failed_locations
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@tracking_bp.route('/location/<driver_id>', methods=['GET'])
def get_driver_locations(driver_id):
    """Get location history for a specific driver"""
    try:
        # Get query parameters
        hours = request.args.get('hours', 24, type=int)
        limit = request.args.get('limit', 1000, type=int)
        
        # Calculate time threshold
        time_threshold = datetime.utcnow() - timedelta(hours=hours)
        
        # Query locations
        locations = DriverLocation.query.filter(
            DriverLocation.driver_id == driver_id,
            DriverLocation.timestamp >= time_threshold
        ).order_by(DriverLocation.timestamp.desc()).limit(limit).all()
        
        return jsonify({
            'status': 'success',
            'driver_id': driver_id,
            'locations': [loc.to_dict() for loc in locations],
            'count': len(locations)
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@tracking_bp.route('/location/<driver_id>/latest', methods=['GET'])
def get_latest_location(driver_id):
    """Get the latest location for a specific driver"""
    try:
        location = DriverLocation.query.filter_by(driver_id=driver_id).order_by(
            DriverLocation.timestamp.desc()
        ).first()
        
        if not location:
            return jsonify({
                'status': 'error',
                'message': 'No location found for driver'
            }), 404
        
        return jsonify({
            'status': 'success',
            'location': location.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@tracking_bp.route('/sync/<driver_id>', methods=['POST'])
def sync_driver_locations(driver_id):
    """Manually trigger sync for a specific driver"""
    try:
        # Get unsynced locations
        unsynced_locations = DriverLocation.query.filter(
            DriverLocation.driver_id == driver_id,
            DriverLocation.synced_to_frappe == False
        ).order_by(DriverLocation.timestamp.asc()).limit(100).all()
        
        if not unsynced_locations:
            return jsonify({
                'status': 'success',
                'message': 'No locations to sync',
                'synced_count': 0
            }), 200
        
        synced_count = 0
        failed_count = 0
        
        for location in unsynced_locations:
            try:
                if sync_location_to_frappe(location):
                    location.synced_to_frappe = True
                    synced_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                failed_count += 1
                print(f"Sync error for location {location.id}: {str(e)}")
        
        # Update sync status
        sync_status = SyncStatus.query.filter_by(driver_id=driver_id).first()
        if sync_status:
            sync_status.pending_locations = max(0, sync_status.pending_locations - synced_count)
            if synced_count > 0:
                sync_status.last_sync_timestamp = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Synced {synced_count} locations',
            'synced_count': synced_count,
            'failed_count': failed_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(e)}), 500

@tracking_bp.route('/sync/status', methods=['GET'])
def get_sync_status():
    """Get sync status for all drivers"""
    try:
        sync_statuses = SyncStatus.query.all()
        
        return jsonify({
            'status': 'success',
            'sync_statuses': [status.to_dict() for status in sync_statuses]
        }), 200
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@tracking_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Get some basic stats
        total_locations = DriverLocation.query.count()
        active_drivers = db.session.query(DriverLocation.driver_id).distinct().count()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'total_locations': total_locations,
            'active_drivers': active_drivers,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

def sync_location_to_frappe(location):
    """Sync a location record to Frappe"""
    try:
        if not FRAPPE_BASE_URL:
            return False
        
        # Prepare data for Frappe API
        frappe_data = {
            'driver': location.driver_id,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'timestamp': location.timestamp.isoformat(),
            'speed': location.speed,
            'heading': location.heading,
            'accuracy': location.accuracy,
            'is_offline': location.is_offline,
            'trip': location.trip_id
        }
        
        # Remove None values
        frappe_data = {k: v for k, v in frappe_data.items() if v is not None}
        
        # Make API request to Frappe
        url = f"{FRAPPE_BASE_URL}/api/method/hayago_mapping.api.update_driver_location_api"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Add authentication if available
        if FRAPPE_API_KEY and FRAPPE_API_SECRET:
            headers['Authorization'] = f'token {FRAPPE_API_KEY}:{FRAPPE_API_SECRET}'
        
        response = requests.post(url, json=frappe_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('message', {}).get('status') == 'success'
        
        return False
        
    except Exception as e:
        print(f"Frappe sync error: {str(e)}")
        return False

