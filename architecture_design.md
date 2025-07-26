# Hayago Mapping Frappe Module: Architecture Design

## 1. Introduction

This document outlines the architectural design and database schema for the `hayago_mapping` Frappe module. The module aims to provide comprehensive mapping and location-based services for a ride-sharing or delivery platform, including nearby driver matching, pre-trip cost estimation, navigation, route/track logging, and offline driver location updates. It will leverage open-source services like Nominatim for geocoding, GraphHopper for routing, and a custom lightweight API for real-time tracking, with Leaflet for the map user interface.

## 2. Overall Architecture

The `hayago_mapping` module will be integrated into the existing Frappe framework as a custom application. It will consist of several key components, each responsible for a specific set of functionalities:

*   **Frappe Backend (Python):** This will handle the core business logic, data storage, and integration with external APIs (Nominatim, GraphHopper). It will manage DocTypes for drivers, trips, locations, and settings.
*   **Frappe Frontend (JavaScript/Jinja):** This will provide the user interface for interacting with the mapping functionalities, including displaying maps, driver locations, and trip routes. Leaflet.js will be the primary library for map rendering.
*   **Custom Lightweight Tracking API (Python/Flask/FastAPI):** A separate, optimized API will be developed to handle high-frequency, real-time location and speed updates from driver devices. This API will be designed for efficiency and to support offline synchronization.
*   **Nominatim (External Service/Self-hosted):** Used for geocoding (address to coordinates) and reverse geocoding (coordinates to address) functionalities.
*   **GraphHopper (External Service/Self-hosted):** Used for calculating routes, distances, travel times, and providing turn-by-turn navigation instructions.
*   **Redis (Frappe's Built-in):** Utilized for caching, real-time updates, and potentially for managing job queues related to location processing.
*   **MariaDB (Frappe's Built-in):** The primary database for persistent storage of all module-related data.

The interaction flow will generally involve the Frappe frontend making requests to the Frappe backend, which in turn will interact with external services (Nominatim, GraphHopper) or the custom tracking API. The custom tracking API will directly receive data from driver devices and store it, with the Frappe backend periodically synchronizing or querying this data.

## 3. Database Schema Design

The following DocTypes and their fields are proposed for the `hayago_mapping` module. These will be implemented within Frappe to manage the module's data.

### 3.1. Driver Location (DocType)

This DocType will store the real-time and historical location data of drivers. It will be frequently updated by the custom tracking API.

| Field Name        | Type       | Description                                       | Constraints/Notes                                   |
| :---------------- | :--------- | :------------------------------------------------ | :-------------------------------------------------- |
| `driver`          | Link       | Link to the `Driver` DocType (or `User` DocType)  | Mandatory, Index                                    |
| `timestamp`       | Datetime   | Time of the location update                       | Mandatory, Index                                    |
| `latitude`        | Float      | Latitude coordinate                               | Mandatory                                           |
| `longitude`       | Float      | Longitude coordinate                              | Mandatory                                           |
| `speed`           | Float      | Current speed of the driver (km/h or mph)         | Optional                                            |
| `heading`         | Float      | Direction of travel (degrees from North)          | Optional                                            |
| `accuracy`        | Float      | Accuracy of the GPS reading (meters)              | Optional                                            |
| `is_offline`      | Check      | Indicates if the update was received offline      | Default: 0 (False)                                  |
| `trip`            | Link       | Link to the `Trip` DocType (if part of a trip)    | Optional, Index                                     |
| `geojson_point`   | Data       | GeoJSON representation of the point               | Stored as string, for map display                   |

### 3.2. Trip (DocType)

This DocType will store details about each trip, including pickup, dropoff, route, and cost estimations.

| Field Name        | Type       | Description                                       | Constraints/Notes                                   |
| :---------------- | :--------- | :------------------------------------------------ | :-------------------------------------------------- |
| `name`            | Data       | Unique Trip ID (auto-generated by Frappe)         | Primary Key                                         |
| `driver`          | Link       | Link to the `Driver` DocType                      | Mandatory, Index                                    |
| `customer`        | Link       | Link to the `Customer` DocType (or `User` DocType)| Mandatory, Index                                    |
| `pickup_address`  | Small Text | Full pickup address                               | Mandatory                                           |
| `pickup_latitude` | Float      | Pickup latitude                                   | Mandatory                                           |
| `pickup_longitude`| Float      | Pickup longitude                                  | Mandatory                                           |
| `dropoff_address` | Small Text | Full dropoff address                              | Mandatory                                           |
| `dropoff_latitude`| Float      | Dropoff latitude                                  | Mandatory                                           |
| `dropoff_longitude`| Float      | Dropoff longitude                                 | Mandatory                                           |
| `start_time`      | Datetime   | Actual trip start time                            | Optional (set when trip starts)                     |
| `end_time`        | Datetime   | Actual trip end time                              | Optional (set when trip ends)                       |
| `estimated_distance`| Float    | Estimated distance of the trip (km)               | Calculated via GraphHopper                          |
| `estimated_duration`| Float    | Estimated duration of the trip (minutes)          | Calculated via GraphHopper                          |
| `estimated_cost`  | Currency   | Estimated cost of the trip                        | Calculated based on distance/duration               |
| `actual_distance` | Float      | Actual distance traveled (km)                     | Calculated from logged route                        |
| `actual_duration` | Float      | Actual duration of the trip (minutes)             | Calculated from logged route                        |
| `actual_cost`     | Currency   | Actual cost of the trip                           | Final cost                                          |
| `status`          | Select     | Current status of the trip                        | Options: `Pending`, `Accepted`, `On Route`, `Completed`, `Cancelled` |
| `route_geojson`   | Long Text  | GeoJSON representation of the planned route       | Stored as string, for map display                   |
| `logged_route_geojson`| Long Text| GeoJSON representation of the actual logged route | Stored as string, for map display                   |

### 3.3. Module Settings (DocType)

This will be a Singleton DocType to store global settings for the `hayago_mapping` module.

| Field Name        | Type       | Description                                       | Constraints/Notes                                   |
| :---------------- | :--------- | :------------------------------------------------ | :-------------------------------------------------- |
| `nominatim_url`   | Data       | URL for Nominatim API                             | Default: `https://nominatim.openstreetmap.org/`     |
| `graphhopper_url` | Data       | URL for GraphHopper API                           | Default: `https://graphhopper.com/api/1/route`      |
| `graphhopper_api_key`| Password | API Key for GraphHopper                           | Encrypted                                           |
| `tracking_api_endpoint`| Data    | Endpoint for the custom tracking API              |                                                     |
| `nearby_driver_radius`| Float   | Radius for nearby driver matching (km)            | Default: 5.0                                        |
| `cost_per_km`     | Currency   | Cost per kilometer for estimation                 | Default: 1.0                                        |
| `cost_per_minute` | Currency   | Cost per minute for estimation                    | Default: 0.2                                        |

### 3.4. Route Log (Child DocType of Trip)

This DocType will store individual points of the logged route for a trip. It will be a child table of the `Trip` DocType.

| Field Name        | Type       | Description                                       | Constraints/Notes                                   |
| :---------------- | :--------- | :------------------------------------------------ | :-------------------------------------------------- |
| `parent`          | Link       | Link to the `Trip` DocType                        | Mandatory                                           |
| `parentfield`     | Data       | Field name in parent DocType (e.g., `route_logs`)| Mandatory                                           |
| `parenttype`      | Data       | Parent DocType name (`Trip`)                      | Mandatory                                           |
| `idx`             | Int        | Index of the log point in the sequence            | Mandatory, for ordering                             |
| `timestamp`       | Datetime   | Time of the log point                             | Mandatory                                           |
| `latitude`        | Float      | Latitude coordinate                               | Mandatory                                           |
| `longitude`       | Float      | Longitude coordinate                              | Mandatory                                           |
| `speed`           | Float      | Speed at this point                               | Optional                                            |

## 4. Key Functionalities and Their Interaction with Architecture

### 4.1. Nearby Driver Matching

1.  **User Request:** A customer requests a ride, providing pickup location (address/coordinates).
2.  **Frappe Backend:** Receives the request. Queries the `Driver Location` DocType to find active drivers within a configurable radius (`nearby_driver_radius` from `Module Settings`).
3.  **Geospatial Query:** This will likely involve a database query that leverages spatial indexing (if available in MariaDB/Frappe) or a simple distance calculation based on latitude/longitude.
4.  **Driver Selection:** Based on availability, proximity, and other criteria, a suitable driver is matched.

### 4.2. Accurate Pre-trip Cost Estimation

1.  **User Input:** Customer provides pickup and dropoff locations.
2.  **Frappe Backend:** Calls the GraphHopper API (using `graphhopper_url` and `graphhopper_api_key` from `Module Settings`) with pickup and dropoff coordinates.
3.  **GraphHopper Response:** Receives estimated distance and duration for the optimal route.
4.  **Cost Calculation:** Calculates `estimated_cost` using `estimated_distance`, `estimated_duration`, `cost_per_km`, and `cost_per_minute` from `Module Settings`.
5.  **Store Trip Data:** Saves the estimated details and the `route_geojson` (planned route) to the `Trip` DocType.

### 4.3. Navigation and Route/Track Logging

1.  **Trip Acceptance:** Once a trip is accepted by a driver.
2.  **Frappe Frontend (Driver App):** Displays the planned route (`route_geojson` from `Trip` DocType) on the Leaflet map. Provides turn-by-turn instructions (parsed from GraphHopper response, potentially stored in `Trip` or fetched on demand).
3.  **Custom Tracking API (Driver Device):** The driver's mobile application (not part of this module's direct scope, but assumed to exist) will periodically send location, speed, and timestamp data to the `tracking_api_endpoint`.
4.  **Custom Tracking API Backend:** Receives these updates and stores them in the `Driver Location` DocType and, if a trip is active, also as `Route Log` entries linked to the `Trip` DocType.
5.  **Frappe Backend:** Can query `Driver Location` and `Route Log` to display the driver's current position and the actual route taken on the customer's map.

### 4.4. Offline Driver Location Updates

1.  **Driver Device (Offline):** When the driver's device is offline, location updates are temporarily stored locally on the device.
2.  **Custom Tracking API (Driver Device):** Once connectivity is restored, the stored offline updates are sent to the `tracking_api_endpoint`.
3.  **Custom Tracking API Backend:** Receives these updates. The `is_offline` flag in the `Driver Location` DocType can be used to distinguish these updates. The `timestamp` will ensure correct chronological order.

## 5. Technology Stack Summary

*   **Framework:** Frappe Framework (Python, JavaScript, Jinja)
*   **Database:** MariaDB
*   **Caching/Realtime:** Redis
*   **Geocoding:** Nominatim API
*   **Routing:** GraphHopper API
*   **Mapping UI:** Leaflet.js
*   **Real-time Tracking API:** Custom (e.g., Flask/FastAPI)

This design provides a robust and scalable foundation for the `hayago_mapping` module, leveraging Frappe's capabilities and integrating with powerful open-source geospatial services. The next phase will involve implementing this design by creating the Frappe module structure and core DocTypes.

