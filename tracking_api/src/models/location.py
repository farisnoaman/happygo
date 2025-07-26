from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class DriverLocation(db.Model):
    __tablename__ = 'driver_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.String(100), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float, nullable=True)
    heading = db.Column(db.Float, nullable=True)
    accuracy = db.Column(db.Float, nullable=True)
    is_offline = db.Column(db.Boolean, default=False, nullable=False)
    trip_id = db.Column(db.String(100), nullable=True, index=True)
    synced_to_frappe = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DriverLocation {self.driver_id} at {self.timestamp}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'driver_id': self.driver_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'speed': self.speed,
            'heading': self.heading,
            'accuracy': self.accuracy,
            'is_offline': self.is_offline,
            'trip_id': self.trip_id,
            'synced_to_frappe': self.synced_to_frappe,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def to_geojson_feature(self):
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": {
                "driver_id": self.driver_id,
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "speed": self.speed,
                "heading": self.heading,
                "accuracy": self.accuracy,
                "is_offline": self.is_offline,
                "trip_id": self.trip_id
            }
        }

class OfflineLocationQueue(db.Model):
    __tablename__ = 'offline_location_queue'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.String(100), nullable=False, index=True)
    location_data = db.Column(db.Text, nullable=False)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed = db.Column(db.Boolean, default=False, nullable=False)
    
    def __repr__(self):
        return f'<OfflineLocationQueue {self.driver_id} - {self.id}>'
    
    def get_location_data(self):
        try:
            return json.loads(self.location_data)
        except json.JSONDecodeError:
            return {}
    
    def set_location_data(self, data):
        self.location_data = json.dumps(data)

class SyncStatus(db.Model):
    __tablename__ = 'sync_status'
    
    id = db.Column(db.Integer, primary_key=True)
    driver_id = db.Column(db.String(100), nullable=False, unique=True, index=True)
    last_sync_timestamp = db.Column(db.DateTime, nullable=True)
    pending_locations = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SyncStatus {self.driver_id}>'
    
    def to_dict(self):
        return {
            'driver_id': self.driver_id,
            'last_sync_timestamp': self.last_sync_timestamp.isoformat() if self.last_sync_timestamp else None,
            'pending_locations': self.pending_locations,
            'last_error': self.last_error,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

