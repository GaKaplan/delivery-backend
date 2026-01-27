import math

def calculate_distance(lat1, lon1, lat2, lon2):
    # Haversine formula
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def optimize_route(locations, start_location=None, max_distance_km=None, round_trip=False, strategy="nearest"):
    """
    Optimizes the route based on strategy.
    strategy: "nearest" (default) or "furthest".
    round_trip: If True, adds the start location as the final destination.
    """
    if not locations:
        return []
    
    # Make a copy to not mutate original list
    pending = locations.copy()
    route = []
    
    # Determine the starting point
    current = None
    start_node = None
    
    if start_location:
        current = start_location
        start_node = start_location # Keep reference for return trip
        route.append(current)
        
        # Filter by max_distance if set
        if max_distance_km is not None and max_distance_km > 0:
            filtered_pending = []
            for point in pending:
                dist = calculate_distance(current['lat'], current['lon'], point['lat'], point['lon'])
                if dist <= max_distance_km:
                    filtered_pending.append(point)
            pending = filtered_pending
            
    else:
        # If no start location, just pick the first one from the list (only for nearest)
        # For 'furthest', we theoretically need a start node context, but if none, we just pick textually first.
        if pending:
            current = pending.pop(0)
            route.append(current)
            start_node = current # Approx start
    
    if not current:
         return route

    # Strategy Implementation
    if strategy == "furthest" and start_node and pending:
        # 1. Find the point furthest from start
        furthest_idx = -1
        max_dist = -1
        
        for i, point in enumerate(pending):
            dist = calculate_distance(start_node['lat'], start_node['lon'], point['lat'], point['lon'])
            if dist > max_dist:
                max_dist = dist
                furthest_idx = i
                
        if furthest_idx != -1:
            # Move to furthest first
            next_point = pending.pop(furthest_idx)
            route.append(next_point)
            current = next_point
            
            # Continue with Nearest Neighbor from there (essentially working backwards)
            # This works well for "Go far, deliver on way back"
            
    # Standard Nearest Neighbor Loop (greedy)
    while pending:
        nearest_idx = -1
        min_dist = float('inf')
        
        for i, point in enumerate(pending):
            dist = calculate_distance(current['lat'], current['lon'], point['lat'], point['lon'])
            if dist < min_dist:
                min_dist = dist
                nearest_idx = i
        
        if nearest_idx != -1:
            next_point = pending.pop(nearest_idx)
            route.append(next_point)
            current = next_point
        else:
            break
            
    # Round Trip: Return to start
    if round_trip and start_node:
        # We append a COPY of start node so it appears as a distinct stop in the list
        # Or just reference it.
        # Ideally, generate a new id or flag 'is_return'
        return_stop = start_node.copy()
        return_stop['id'] = 9999 # Special ID or just re-use
        return_stop['name'] = "RETORNO A DEPÓSITO"
        route.append(return_stop)
        
    return route
