import asyncio
from typing import List, Dict
from api.google_places import search_google_places

async def search_all_apis(location: Dict, filters: Dict) -> tuple[List[Dict], List[str]]:
    """
    Search using Google Places API only
    Returns: (results, search_log)
    """
    search_log = []
    
    # Search Google Places only
    results, google_log = await search_google_places(location, filters)
    search_log.extend(google_log)
    
    search_log.append(f"🔍 Found {len(results)} Google Places results")
    
    return results, search_log

def filter_results(results: List[Dict], filters: Dict) -> List[Dict]:
    """
    Apply filters to results
    """
    if not results:
        return []
    
    filtered = results.copy()
    
    # Filter by cuisine if specified
    if filters.get('cuisine'):
        cuisine = filters['cuisine'].lower()
        filtered = [r for r in filtered 
                   if cuisine in r['name'].lower() or 
                   any(cuisine in t.lower() for t in r.get('types', []))]
    
    # Filter by dietary if specified
    if filters.get('dietary'):
        dietary_terms = [d.lower() for d in filters['dietary']]
        filtered = [r for r in filtered 
                   if any(diet in r['name'].lower() or 
                         any(diet in t.lower() for t in r.get('types', [])) 
                         for diet in dietary_terms)]
    
    # Filter by open now if specified
    if filters.get('open_now'):
        filtered = [r for r in filtered if r.get('open_now') is True]
    
    # Filter by minimum rating if specified
    if filters.get('min_rating', 0) > 0:
        filtered = [r for r in filtered if r.get('rating', 0) >= filters['min_rating']]
    
    # Filter by distance (already done by APIs, but double-check)
    max_distance = filters.get('radius', 2000)
    filtered = [r for r in filtered if r.get('distance', float('inf')) <= max_distance]
    
    return filtered 