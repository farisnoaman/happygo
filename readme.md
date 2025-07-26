# Hayago Mapping Module - Quick Installation Guide

## Prerequisites

- Frappe Framework v13.0 or higher
- Python 3.8+
- Redis server
- MariaDB/MySQL database

## Installation Steps

### 1. Install the Frappe App

```bash
# Navigate to your Frappe bench directory
cd /path/to/frappe-bench

# Get the app
bench get-app hayago_mapping /path/to/hayago_mapping

# Install on your site
bench --site your-site-name install-app hayago_mapping

# Migrate the database
bench --site your-site-name migrate
```

### 2. Configure Module Settings

1. Login to your Frappe site
2. Go to **Hayago Mapping > Module Settings**
3. Configure the following:
   - **Nominatim URL**: `https://nominatim.openstreetmap.org/`
   - **GraphHopper URL**: `https://graphhopper.com/api/1/`
   - **GraphHopper API Key**: (Get from GraphHopper)
   - **Cost per KM**: Set your pricing (e.g., 2.0)
   - **Cost per Minute**: Set your pricing (e.g., 0.5)
   - **Driver Matching Radius**: Set radius in KM (e.g., 5.0)

### 3. Deploy the Tracking API

```bash
# Navigate to the tracking API directory
cd /path/to/hayago_mapping/tracking_api

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FRAPPE_BASE_URL="http://your-site-name"
export FRAPPE_API_KEY="your-api-key"
export FRAPPE_API_SECRET="your-api-secret"

# Run the tracking API
python src/main.py
```

### 4. Update Module Settings with Tracking API URL

1. Go back to **Module Settings**
2. Set **Tracking API Endpoint**: `http://localhost:5000`

### 5. Test the Installation

```bash
# Test the tracking API
curl http://localhost:5000/api/health

# Test location update
curl -X POST http://localhost:5000/api/location \
  -H "Content-Type: application/json" \
  -d '{
    "driver_id": "test_driver",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "speed": 25.5
  }'
```

### 6. Create Test Data

1. Create a **User** for testing (driver role)
2. Create a **Trip** record
3. Test the map interface in the Trip form

## Production Deployment

For production, consider:

- Using a proper WSGI server (Gunicorn/uWSGI) for the tracking API
- Setting up SSL certificates
- Configuring proper firewall rules
- Using a process manager (systemd/supervisor)
- Setting up monitoring and logging

## Troubleshooting

**Common Issues:**

1. **Map not loading**: Check that Leaflet.js is loading correctly
2. **Location updates failing**: Verify tracking API is running and accessible
3. **Geocoding errors**: Check Nominatim service availability
4. **Route calculation fails**: Verify GraphHopper API key and quota

**Getting Help:**

- Check the full documentation in `module_documentation.md`
- Review log files in Frappe and tracking API
- Test external services directly using curl

## Next Steps

- Configure user permissions for drivers and dispatchers
- Set up the driver dashboard page
- Customize cost calculation parameters
- Configure monitoring and alerting
- Set up data backup procedures

For detailed information, refer to the complete documentation.

