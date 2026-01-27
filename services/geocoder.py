from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
import json
import os

# User agent is required by Nominatim policy
geolocator = Nominatim(user_agent="delivery_route_optimizer_v1")

# Persistent cache path
CACHE_PATH = os.path.join("/tmp", "geocoding_cache.json") if os.path.exists("/tmp") else "geocoding_cache.json"

def load_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
    except:
        pass

# Initialize cache
persistent_cache = load_cache()

def geocode_single(address, region_bias=None):
    """
    Geocodes a single address string with persistent caching and multi-region strategy.
    """
    if not address:
        return None

    clean_addr = address.strip()
    
    # Check cache first
    if clean_addr in persistent_cache:
        return persistent_cache[clean_addr]

    # Pre-processing
    search_addr = clean_addr.replace("AV ", "Avenida ").replace("Av. ", "Avenida ").replace("Gral. ", "General ")
    search_addr = search_addr.replace("C.A.B.A.", "CABA").replace("Ciudad Autónoma de Buenos Aires", "CABA")

    attempts = []
    
    # Strategy 1: The address exactly as provided (with bias if any)
    if region_bias and region_bias.lower() not in search_addr.lower():
        attempts.append(f"{search_addr}, {region_bias}")
    attempts.append(search_addr)
    
    # Strategy 2: Explicit Argentina context (Covers whole country)
    if "argentina" not in search_addr.lower():
        attempts.append(f"{search_addr}, Argentina")

    # Strategy 3: Priority Contexts (If CABA or GBA bias)
    if not any(x in search_addr.lower() for x in ["caba", "buenos aires", "provincia"]):
        attempts.append(f"{search_addr}, CABA, Argentina")
    
    # Deduplicate attempts while preserving order
    unique_attempts = []
    for a in attempts:
        if a not in unique_attempts: unique_attempts.append(a)

    for query in unique_attempts:
        try:
            # Respect policy - Minimum 1s wait
            time.sleep(1.05)
            location = geolocator.geocode(query, addressdetails=True)
            
            if location:
                result = (location.latitude, location.longitude, location.raw.get('address', {}))
                # Store in persistent cache
                persistent_cache[clean_addr] = result
                save_cache(persistent_cache)
                return result
        except GeocoderTimedOut:
            continue
        except Exception as e:
            print(f"Error for {query}: {e}")
            continue
            
    return None

def geocode_addresses(raw_data, region_bias=None):
    """
    Geocodes a list of addresses with deduplication to speed up processing.
    """
    # 1. Deduplicate by address string
    unique_addresses = {}
    for item in raw_data:
        addr = item["address"]
        if addr not in unique_addresses:
            unique_addresses[addr] = item["name"]

    # 2. Geocode unique ones
    results_map = {}
    for addr, name in unique_addresses.items():
        results_map[addr] = geocode_single(addr, region_bias)

    # 3. Rebuild original list with geocoded data
    found = []
    not_found = []
    
    for idx, item in enumerate(raw_data):
        addr = item["address"]
        name = item["name"]
        result = results_map.get(addr)
        
        if result:
            lat, lon, _ = result
            found.append({
                "id": idx + 1,
                "name": name,
                "address": addr,
                "lat": lat,
                "lon": lon
            })
        else:
            not_found.append({
                "name": name,
                "address": addr,
                "error": "Not Found"
            })
        
    return {"found": found, "not_found": not_found}

