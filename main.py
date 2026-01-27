from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import shutil
import os
import json
from services.parser import parse_pdf
from services.geocoder import geocode_addresses
from services.optimizer import optimize_route

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "online", "message": "Delivery Route Optimizer API is running"}

class Location(BaseModel):
    id: int
    name: str
    address: str
    lat: float
    lon: float
    distance_stop: float = 0.0 # km from previous
    duration_stop: float = 0.0 # seconds from previous

class SkippedItem(BaseModel):
    name: str
    address: str
    error: str

class OptimizedRoute(BaseModel):
    locations: List[Location]
    skipped: List[SkippedItem]
    total_distance: float = 0.0
    total_duration: float = 0.0 # seconds
    geometry: str = None # Encoded polyline or GeoJSON string

@app.post("/api/optimize-route", response_model=OptimizedRoute)
async def optimize_route_endpoint(
    file: UploadFile = File(...),
    start_address: str = Form(None),
    max_distance: float = Form(None),
    excel_start_row: int = Form(1),
    excel_address_col: str = Form("A"),
    round_trip: bool = Form(False),
    strategy: str = Form("nearest")
):
    is_pdf = file.filename.lower().endswith('.pdf')
    is_excel = file.filename.lower().endswith(('.xlsx', '.xls'))

    if not (is_pdf or is_excel):
        raise HTTPException(status_code=400, detail="File must be PDF or Excel (.xlsx)")
    
    temp_file = f"temp_{file.filename}"
    try:
        with open(temp_file, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        raw_addresses = []
        
        # 1. Parse File based on type
        if is_pdf:
             raw_addresses = parse_pdf(temp_file)
        elif is_excel:
             from services.excel_parser import parse_excel
             raw_addresses = parse_excel(temp_file, excel_start_row, excel_address_col)

        if not raw_addresses:
            raise HTTPException(status_code=400, detail="No addresses found in file")

        # 2. Geocode Start Address FIRST to get Context
        start_location = None
        region_bias = "Argentina" # Default bias
        
        if start_address:
            # Import here to avoid circular dependencies if any, or just use the geocoder import
            from services.geocoder import geocode_single
            result = geocode_single(start_address)
            
            if result:
                lat, lon, details = result
                start_location = {
                    "id": 0,
                    "name": "DEPÓSITO / INICIO",
                    "address": start_address,
                    "lat": lat,
                    "lon": lon
                }
                
                # Extract context from details
                components = []
                if 'city' in details: components.append(details['city'])
                elif 'town' in details: components.append(details['town'])
                
                if 'state' in details: components.append(details['state'])
                if 'country' in details: components.append(details['country'])
                
                if components:
                    region_bias = ", ".join(components)
                    print(f"Detected Region Bias: {region_bias}")
                    
            else:
                 raise HTTPException(status_code=400, detail=f"Could not geocode start address: {start_address}")
        
        # If max_distance is set, we really need a start location.
        if max_distance and not start_location:
            raise HTTPException(status_code=400, detail="Start address is required when using Max Distance filter.")

        # 3. Geocode Deliveries using Region Bias
        geocode_result = geocode_addresses(raw_addresses, region_bias)
        locations = geocode_result["found"]
        skipped = geocode_result["not_found"]

        # 4. Optimize
        optimized_locations = optimize_route(locations, start_location, max_distance, round_trip, strategy)
        
        # Check against original locations to assume which were filtered by distance
        opt_ids = {loc["id"] for loc in optimized_locations}
        for loc in locations:
            if loc["id"] not in opt_ids:
                 skipped.append({
                     "name": loc["name"],
                     "address": loc["address"],
                     "error": f"Distance > {max_distance}km"
                 })

        # 5. Get OSRM Data (Real Path & Duration)
        total_dist = 0.0
        total_time = 0.0
        route_geometry = None
        
        # Prepare Coords for OSRM: List of (lon, lat)
        path_coords = [(loc['lon'], loc['lat']) for loc in optimized_locations]
        
        if len(path_coords) >= 2:
            from services.osrm_service import get_osrm_route
            osrm_data = get_osrm_route(path_coords)
            
            if osrm_data:
                 route_geometry = json.dumps(osrm_data['geometry'])
                 total_time = osrm_data['duration'] # seconds
                 total_dist = osrm_data['distance'] / 1000.0 # meters to km (OSRM returns meters)
                 
                 # Assign stats per leg
                 legs = osrm_data.get('legs', [])
                 # Legs connect points. Leg 0 connects Point 0 (Start) to Point 1.
                 # So Optimized Location 1 (index 1) gets stats from Leg 0.
                 # Start location (index 0) has 0 dist/time.
                 
                 for i, leg in enumerate(legs):
                     # Guard against index out of bounds
                     if i + 1 < len(optimized_locations):
                         opt_loc = optimized_locations[i+1]
                         # Convert OSRM meters/seconds to km/seconds for consistency
                         opt_loc['distance_stop'] = leg['distance'] / 1000.0
                         opt_loc['duration_stop'] = leg['duration']
                         
            else:
                 # Fallback: Calculate straight line distance
                 from services.optimizer import calculate_distance
                 for i in range(len(optimized_locations) - 1):
                     l1 = optimized_locations[i]
                     l2 = optimized_locations[i+1]
                     dist_km = calculate_distance(l1['lat'], l1['lon'], l2['lat'], l2['lon'])
                     total_dist += dist_km
                     
                     # Est time
                     time_s = (dist_km / 30.0) * 3600
                     
                     optimized_locations[i+1]['distance_stop'] = dist_km
                     optimized_locations[i+1]['duration_stop'] = time_s
                     
                 total_time = (total_dist / 30.0) * 3600

        return OptimizedRoute(
            locations=optimized_locations, 
            skipped=skipped,
            total_distance=total_dist,
            total_duration=total_time,
            geometry=route_geometry
        )

    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
