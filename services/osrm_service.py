import requests
import json

OSRM_BASE_URL = "http://router.project-osrm.org/route/v1/driving"

def get_osrm_route(coordinates):
    """
    coordinates: List of (lon, lat) tuples. NOTE: OSRM uses Lon,Lat order.
    Returns:
        {
            "geometry": str (encoded polyline),
            "duration": float (seconds),
            "distance": float (meters)
        }
    or None if failed.
    """
    if not coordinates or len(coordinates) < 2:
        return None

    # Format coords: "lon1,lat1;lon2,lat2"
    coord_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
    
    url = f"{OSRM_BASE_URL}/{coord_str}?overview=full&geometries=geojson"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 'Ok' and data['routes']:
                route = data['routes'][0]
                return {
                    "geometry": route['geometry'], # GeoJSON format
                    "duration": route['duration'],
                    "distance": route['distance'],
                    "legs": route['legs'] # Per step details
                }
    except Exception as e:
        print(f"OSRM Error: {e}")
        
    return None
