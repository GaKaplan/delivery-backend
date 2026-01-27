from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time

# User agent is required by Nominatim policy
geolocator = Nominatim(user_agent="delivery_route_optimizer_v1")

# Simple in-memory cache
cache = {}

def geocode_single(address, region_bias=None):
    """
    Geocodes a single address string. 
    Returns (lat, lon, details_dict) or None.
    Retry Strategy:
    1. Address + Region Bias (if provided)
    2. Address + ", Argentina" (Standard)
    3. Address (Clean)
    4. Address + ", Buenos Aires Province" (Context specific fallback)
    """
    if not address:
        return None

    clean_addr = address.strip()
    
    # 1. Expand abbreviations & Standardize
    clean_addr = clean_addr.replace("AV ", "Avenida ")
    clean_addr = clean_addr.replace("Av. ", "Avenida ")
    clean_addr = clean_addr.replace("Gral. ", "General ")
    
    # Heuristic: Add accents to common names if missing (Nominatim is usually fuzzy but helps)
    # San Martin -> San Martín
    if "San Martin" in clean_addr and "Martín" not in clean_addr:
        clean_addr = clean_addr.replace("San Martin", "San Martín")

    # Heuristic: Known Avenues that might lack prefix
    # "Cordoba 4001" -> "Avenida Cordoba 4001"
    known_avenues = ["Cordoba", "Córdoba", "San Martin", "San Martín", "Rivadavia", "Corrientes", "Santa Fe", "Cabildo", "Libertador"]
    
    # Check if address starts with one of these (case insensitive)
    upper_addr = clean_addr.upper()
    for av in known_avenues:
        if upper_addr.startswith(av.upper() + " "):
            # Don't add if it already has Avenida
            clean_addr = f"Avenida {clean_addr}"
            break

    # Prioritize CABA explicitly
    clean_addr = clean_addr.replace("C.A.B.A.", "Ciudad Autónoma de Buenos Aires")
    clean_addr = clean_addr.replace("CABA", "Ciudad Autónoma de Buenos Aires")
    
    attempts = []
    
    # Strategy 1: Use Region Bias if available
    # Force CABA context if bias seems to be BA city
    if region_bias:
        if "Autónoma" in region_bias or "Capital Federal" in region_bias:
             attempts.append(f"{clean_addr}, Ciudad Autónoma de Buenos Aires")
        elif region_bias.lower() not in clean_addr.lower():
            attempts.append(f"{clean_addr}, {region_bias}")
            
    # Strategy 2: Explicit CABA attempt (High confidence for this project)
    attempts.append(f"{clean_addr}, Ciudad Autónoma de Buenos Aires, Argentina")

    # Strategy 3: Standard Argentina
    if "argentina" not in clean_addr.lower():
         attempts.append(f"{clean_addr}, Argentina")
    else:
         attempts.append(clean_addr)
    
    # Strategy 4: Try adding "Calle" prefix (fixes Sarmiento 4062 -> Calle Sarmiento 4062)
    attempts.append(f"Calle {clean_addr}, Ciudad Autónoma de Buenos Aires")

    # Strategy 5: Special Handling for San Martín (Border case)
    # 7170 is high number, might be province.
    if "San Martín" in clean_addr or "San Martin" in clean_addr:
         attempts.append(f"{clean_addr}, General San Martín, Buenos Aires")
         attempts.append(f"{clean_addr}, Villa Devoto, Buenos Aires")

    # Strategy 6: Fallback Clean
    attempts.append(clean_addr)

    # Deduplicate attempts while preserving order
    unique_attempts = []
    for a in attempts:
        if a not in unique_attempts:
            unique_attempts.append(a)

    for query in unique_attempts:
        if query in cache:
            return cache[query]
        
        try:
            # Respect policy
            time.sleep(1.1)
            location = geolocator.geocode(query, addressdetails=True)
            
            if location:
                # Store full details
                result = (location.latitude, location.longitude, location.raw.get('address', {}))
                
                # Cache successful query
                cache[query] = result
                # Cache original input too if it was the first attempt or successful match
                if address not in cache:
                    cache[address] = result
                    
                return result
        except GeocoderTimedOut:
            print(f"Timeout for {query}")
            continue
        except Exception as e:
            print(f"Error for {query}: {e}")
            continue
            
    print(f"Could not geocode: {address} after trying: {unique_attempts}")
    return None

def geocode_addresses(raw_data, region_bias=None):
    """
    Takes a list of {"name": str, "address": str}
    Returns a dict with:
      - "found": list of dicts {id, name, address, lat, lon}
      - "not_found": list of dicts {name, address, error}
    """
    found = []
    not_found = []
    
    for idx, item in enumerate(raw_data):
        address = item["address"]
        name = item["name"]
        
        # Pass region_bias to the single geocoder
        result = geocode_single(address, region_bias)
        
        if result:
            lat, lon, _ = result
            found.append({
                "id": idx + 1,
                "name": name,
                "address": address,
                "lat": lat,
                "lon": lon
            })
        else:
            not_found.append({
                "name": name,
                "address": address,
                "error": "Could not geocode"
            })
        
    return {"found": found, "not_found": not_found}
