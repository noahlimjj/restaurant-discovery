import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def apply_filters(restaurants, filters, location=None):
    filtered = []
    print(f"Applying filters to {len(restaurants)} restaurants")
    
    for r in restaurants:
        # Price filter - be less restrictive
        if 'price' in filters and filters['price'] and r.get('price_level') is not None:
            price_map = {'$': 1, '$$': 2, '$$$': 3, '$$$$': 4}
            target_price = price_map.get(filters['price'], 0)
            if target_price != 0 and r['price_level'] != target_price:
                continue
        
        # Cuisine filter - be less restrictive
        if 'cuisine' in filters and filters['cuisine'] and filters['cuisine'].strip():
            cuisine_lower = filters['cuisine'].lower().strip()
            name_lower = r.get('name', '').lower()
            types_lower = [t.lower() for t in r.get('types', [])]
            
            # Check if cuisine appears in name or types
            if (cuisine_lower not in name_lower and 
                not any(cuisine_lower in t for t in types_lower)):
                continue
        
        # Dietary filter - be less restrictive
        if 'dietary' in filters and filters['dietary']:
            dietary_terms = [diet.lower().strip() for diet in filters['dietary'] if diet.strip()]
            if dietary_terms:
                name_lower = r.get('name', '').lower()
                types_text = ' '.join(r.get('types', [])).lower()
                
                # Check if any dietary term appears in name or types
                if not any(diet in name_lower or diet in types_text for diet in dietary_terms):
                    continue
        
        # Open now filter - only apply if specifically requested
        if filters.get('open_now') and r.get('open_now') is False:
            continue
        
        # Minimum rating filter - be less restrictive
        if 'min_rating' in filters and filters['min_rating'] > 0:
            rating = r.get('rating', 0)
            if rating < filters['min_rating']:
                continue
        
        # Distance filter - already calculated in Google Places API
        if location and 'radius' in filters and r.get('distance') is not None:
            if r['distance'] > filters['radius']:
                continue
        
        filtered.append(r)
    
    print(f"After filtering: {len(filtered)} restaurants")
    
    # Sort by rating desc, then distance asc - handle None values properly
    def sort_key(x):
        rating = x.get('rating', 0) or 0  # Convert None to 0
        distance = x.get('distance', float('inf')) or float('inf')  # Convert None to inf
        return (-rating, distance)
    
    filtered.sort(key=sort_key)
    return filtered 