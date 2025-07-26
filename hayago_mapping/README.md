# Hayago Mapping - Frappe Module

A comprehensive mapping and location-based services module for Frappe Framework, designed for ride-sharing and delivery platforms.

## Features

✅ **Nearby Driver Matching** - Find drivers near pickup locations quickly and accurately  
✅ **Accurate Pre-trip Cost Estimation** - Calculate distance/time between pickup and dropoff  
✅ **Turn-by-turn Navigation** - Provide actual route guidance to drivers  
✅ **Route/Track Logging** - Save full trip routes and speed logs to database  
✅ **Offline Driver Location Updates** - Let drivers update locations even offline; sync later  

## Technology Stack

- **Frappe Framework** - Backend and business logic
- **Nominatim** - Open source geocoding service
- **GraphHopper** - Open source routing engine
- **Leaflet.js** - Interactive map UI
- **Custom Tracking API** - Lightweight Flask API for real-time location updates
- **Redis** - Caching and performance optimization

## Quick Start

### Prerequisites

- Frappe Framework v13.0+
- Python 3.8+
- Redis server
- MariaDB/MySQL database

### Installation

```bash
# Get the app
bench get-app hayago_mapping /path/to/hayago_mapping

# Install on your site
bench --site your-site-name install-app hayago_mapping

# Migrate database
bench --site your-site-name migrate
```

### Configuration

1. Go to **Hayago Mapping > Module Settings**
2. Configure API endpoints and pricing parameters
3. Deploy the tracking API (see installation guide)

## Documentation

- [Complete Documentation](module_documentation.md) - Comprehensive guide covering all aspects
- [Installation Guide](installation_guide.md) - Step-by-step installation instructions
- [Architecture Design](architecture_design.md) - Technical architecture overview

## Module Components

### DocTypes

- **Driver Location** - Real-time and historical driver location data
- **Trip** - Trip management with route planning and cost estimation
- **Route Log** - Detailed route tracking and logging
- **Module Settings** - Centralized configuration management

### API Endpoints

- Geocoding and reverse geocoding
- Driver matching and location services
- Route calculation and navigation
- Real-time location tracking

### User Interface

- Interactive maps with Leaflet.js integration
- Driver dashboard for real-time tracking
- Trip management forms with map visualization
- Mobile-optimized responsive design

## Key Features in Detail

### Driver Matching
- Configurable search radius
- Real-time availability checking
- Distance-based driver selection
- Status-aware matching (available, busy, offline)

### Cost Estimation
- Distance and time-based calculations
- Configurable pricing parameters
- Real-time route optimization
- Alternative route options

### Navigation
- Turn-by-turn instructions
- Voice-ready guidance text
- Real-time progress tracking
- Offline navigation support

### Location Tracking
- High-frequency location updates
- Offline data synchronization
- Speed and heading tracking
- Geofenced area monitoring

## Architecture

The module follows a modular architecture with clear separation of concerns:

- **Frappe Backend** - Business logic and data persistence
- **Tracking API** - High-performance location updates
- **Frontend UI** - Interactive maps and user interfaces
- **External Services** - Nominatim and GraphHopper integration

## Testing

The module includes comprehensive testing:

- Unit tests for all core functions
- Integration tests for external services
- Performance tests for high-load scenarios
- User acceptance testing procedures

## Contributing

We welcome contributions! Please see the [Contributing Guide](module_documentation.md#contributing) for details on:

- Development environment setup
- Code style and standards
- Feature development process
- Bug reporting guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Documentation**: Complete documentation available in `module_documentation.md`
- **Issues**: Report bugs and feature requests via GitHub issues
- **Community**: Join the Frappe community for general discussions

## Roadmap

- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Enhanced offline capabilities
- [ ] Integration with popular payment gateways
- [ ] Machine learning-based route optimization

## Acknowledgments

- Frappe Framework team for the excellent foundation
- OpenStreetMap community for mapping data
- GraphHopper team for routing services
- Leaflet.js contributors for mapping UI

---

**Version**: 1.0.0  
**Author**: Manus AI  
**Created**: July 26, 2025

