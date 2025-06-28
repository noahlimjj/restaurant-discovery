import os
import aiohttp
import ssl
import random
import json
import hashlib
import time
from datetime import datetime, timedelta

GOOGLE_API_KEY = os.getenv('GOOGLE_PLACES_API_KEY')
GOOGLE_PLACES_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
GOOGLE_TEXT_SEARCH_URL = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
GOOGLE_PLACE_DETAILS_URL = 'https://maps.googleapis.com/maps/api/place/details/json'

# Cache configuration
CACHE_DIR = 'cache'
CACHE_DURATION_HOURS = 24  # Cache results for 24 hours

def ensure_cache_dir():
    """Ensure cache directory exists"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_key(location, filters, search_type):
    """Generate a cache key for the search parameters"""
    # Create a hash of the search parameters
    cache_data = {
        'lat': round(location['lat'], 4),  # Round to reduce cache fragmentation
        'lng': round(location['lng'], 4),
        'filters': filters,
        'search_type': search_type
    }
    cache_string = json.dumps(cache_data, sort_keys=True)
    return hashlib.md5(cache_string.encode()).hexdigest()

def get_cache_file(cache_key):
    """Get the cache file path for a given key"""
    return os.path.join(CACHE_DIR, f"{cache_key}.json")

def is_cache_valid(cache_file):
    """Check if cache file exists and is still valid"""
    if not os.path.exists(cache_file):
        return False
    
    # Check if cache is expired
    file_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    return datetime.now() - file_time < timedelta(hours=CACHE_DURATION_HOURS)

def load_from_cache(cache_file):
    """Load results from cache file"""
    try:
        with open(cache_file, 'r') as f:
            return json.load(f)
    except:
        return None

def save_to_cache(cache_file, results):
    """Save results to cache file"""
    try:
        with open(cache_file, 'w') as f:
            json.dump(results, f)
    except:
        pass  # Silently fail if cache save fails

def should_use_cached_results(filters):
    """Determine if we should use cached results based on filters"""
    # Don't cache if open_now is True (results change frequently)
    if filters.get('open_now'):
        return False
    
    # Don't cache if radius is very small (user might want fresh results)
    if filters.get('radius', 2000) < 1000:
        return False
    
    return True

# Cuisine-specific keywords for better search results
CUISINE_KEYWORDS = {
    'japanese': ['sushi', 'ramen', 'tempura', 'udon', 'soba', 'yakitori', 'izakaya', 'bento', 'teppanyaki', 'sashimi'],
    'chinese': ['dim sum', 'peking duck', 'kung pao', 'szechuan', 'cantonese', 'hot pot', 'dumplings', 'noodles'],
    'italian': ['pizza', 'pasta', 'risotto', 'osso buco', 'bruschetta', 'tiramisu', 'gelato', 'prosciutto'],
    'mexican': ['tacos', 'burritos', 'enchiladas', 'guacamole', 'quesadilla', 'mole', 'ceviche', 'tamales'],
    'indian': ['curry', 'tandoori', 'naan', 'biryani', 'dal', 'samosa', 'kebab', 'masala'],
    'thai': ['pad thai', 'tom yum', 'green curry', 'massaman', 'som tam', 'larb', 'satay'],
    'korean': ['bbq', 'bibimbap', 'bulgogi', 'kimchi', 'japchae', 'tteokbokki', 'samgyeopsal'],
    'vietnamese': ['pho', 'banh mi', 'spring rolls', 'bun cha', 'com tam', 'cao lau'],
    'mediterranean': ['hummus', 'falafel', 'shawarma', 'kebab', 'tabbouleh', 'baklava'],
    'french': ['croissant', 'escargot', 'coq au vin', 'ratatouille', 'quiche', 'creme brulee'],
    'greek': ['gyro', 'moussaka', 'souvlaki', 'spanakopita', 'baklava', 'tzatziki'],
    'spanish': ['paella', 'tapas', 'gazpacho', 'chorizo', 'jamón', 'sangria'],
    'american': ['burger', 'steak', 'bbq', 'hot dog', 'mac and cheese', 'apple pie'],
    'seafood': ['lobster', 'crab', 'shrimp', 'oysters', 'salmon', 'tuna', 'mussels'],
    'vegetarian': ['vegan', 'plant-based', 'vegetarian', 'tofu', 'tempeh', 'quinoa'],
    'dessert': ['ice cream', 'cake', 'pastry', 'donuts', 'cookies', 'chocolate']
}

def get_cuisine_keywords(cuisine):
    """Get relevant keywords for a cuisine type"""
    cuisine_lower = cuisine.lower()
    
    # Direct match
    if cuisine_lower in CUISINE_KEYWORDS:
        return [cuisine] + CUISINE_KEYWORDS[cuisine_lower]
    
    # Partial matches
    keywords = [cuisine]
    for cuisine_type, words in CUISINE_KEYWORDS.items():
        if cuisine_lower in cuisine_type or cuisine_type in cuisine_lower:
            keywords.extend(words)
    
    return list(set(keywords))  # Remove duplicates

def get_mock_restaurants(location, filters):
    """Return mock restaurant data for testing when API key is not available"""
    mock_restaurants = [
        {
            'source': 'google',
            'id': 'mock_1',
            'name': 'Pizza Palace',
            'address': '123 Main St',
            'rating': 4.5,
            'user_ratings_total': 234,
            'distance': 500,
            'price_level': 2,
            'open_now': True,
            'photos': [
                {
                    'url': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                },
                {
                    'url': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                }
            ],
            'types': ['restaurant', 'food', 'pizza', 'italian'],
            'lat': location['lat'] + 0.001,
            'lng': location['lng'] + 0.001,
        },
        {
            'source': 'google',
            'id': 'mock_2',
            'name': 'Sushi Express',
            'address': '456 Oak Ave',
            'rating': 4.2,
            'user_ratings_total': 156,
            'distance': 800,
            'price_level': 3,
            'open_now': True,
            'photos': [
                {
                    'url': 'https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                }
            ],
            'types': ['restaurant', 'food', 'sushi', 'japanese'],
            'lat': location['lat'] - 0.002,
            'lng': location['lng'] + 0.002,
        },
        {
            'source': 'google',
            'id': 'mock_3',
            'name': 'Burger Joint',
            'address': '789 Pine St',
            'rating': 3.8,
            'user_ratings_total': 89,
            'distance': 1200,
            'price_level': 1,
            'open_now': False,
            'photos': [
                {
                    'url': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                }
            ],
            'types': ['restaurant', 'food', 'burger', 'american'],
            'lat': location['lat'] + 0.003,
            'lng': location['lng'] - 0.001,
        },
        {
            'source': 'google',
            'id': 'mock_4',
            'name': 'Thai Spice',
            'address': '321 Elm Rd',
            'rating': 4.7,
            'user_ratings_total': 312,
            'distance': 1500,
            'price_level': 2,
            'open_now': True,
            'photos': [
                {
                    'url': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                },
                {
                    'url': 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                }
            ],
            'types': ['restaurant', 'food', 'thai', 'asian'],
            'lat': location['lat'] - 0.001,
            'lng': location['lng'] - 0.003,
        },
        {
            'source': 'google',
            'id': 'mock_5',
            'name': 'Seafood Grill',
            'address': '654 Maple Dr',
            'rating': 4.1,
            'user_ratings_total': 178,
            'distance': 2000,
            'price_level': 3,
            'open_now': True,
            'photos': [
                {
                    'url': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                }
            ],
            'types': ['restaurant', 'food', 'seafood', 'grill'],
            'lat': location['lat'] + 0.002,
            'lng': location['lng'] + 0.003,
        },
        {
            'source': 'google',
            'id': 'mock_6',
            'name': 'Pasta House',
            'address': '987 Cedar Ln',
            'rating': 4.3,
            'user_ratings_total': 145,
            'distance': 2500,
            'price_level': 2,
            'open_now': True,
            'photos': [
                {
                    'url': 'https://images.unsplash.com/photo-1621996346565-e3dbc353d2e5?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                }
            ],
            'types': ['restaurant', 'food', 'italian', 'pasta'],
            'lat': location['lat'] - 0.003,
            'lng': location['lng'] + 0.004,
        },
        {
            'source': 'google',
            'id': 'mock_7',
            'name': 'Mexican Cantina',
            'address': '147 Birch Rd',
            'rating': 3.9,
            'user_ratings_total': 78,
            'distance': 3000,
            'price_level': 1,
            'open_now': False,
            'photos': [
                {
                    'url': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                }
            ],
            'types': ['restaurant', 'food', 'mexican', 'tacos'],
            'lat': location['lat'] + 0.004,
            'lng': location['lng'] - 0.003,
        },
        {
            'source': 'google',
            'id': 'mock_8',
            'name': 'Chinese Palace',
            'address': '258 Spruce Ave',
            'rating': 4.0,
            'user_ratings_total': 156,
            'distance': 3500,
            'price_level': 2,
            'open_now': True,
            'photos': [
                {
                    'url': 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=400&h=300&fit=crop',
                    'width': 400,
                    'height': 300
                }
            ],
            'types': ['restaurant', 'food', 'chinese', 'asian'],
            'lat': location['lat'] - 0.004,
            'lng': location['lng'] - 0.004,
        }
    ]
    
    # Don't pre-filter by radius - let the main filtering handle it
    # Filter by cuisine if specified
    if 'cuisine' in filters and filters['cuisine']:
        cuisine_lower = filters['cuisine'].lower()
        mock_restaurants = [r for r in mock_restaurants 
                          if cuisine_lower in r['name'].lower() or 
                          any(cuisine_lower in t.lower() for t in r['types'])]
    
    # Filter by dietary if specified
    if 'dietary' in filters and filters['dietary']:
        dietary_terms = [d.lower() for d in filters['dietary']]
        mock_restaurants = [r for r in mock_restaurants 
                          if any(diet in r['name'].lower() or 
                                any(diet in t.lower() for t in r['types']) 
                                for diet in dietary_terms)]
    
    # Filter by open now if specified
    if filters.get('open_now'):
        mock_restaurants = [r for r in mock_restaurants if r['open_now']]
    
    # Filter by minimum rating if specified
    if 'min_rating' in filters and filters['min_rating'] > 0:
        mock_restaurants = [r for r in mock_restaurants if r['rating'] >= filters['min_rating']]
    
    return mock_restaurants

async def get_place_details(session, place_id, search_log):
    """Get detailed information for a specific place"""
    try:
        # Create a new session for this request to avoid session closed errors
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async with aiohttp.ClientSession(connector=connector) as detail_session:
            params = {
                'key': GOOGLE_API_KEY,
                'place_id': place_id,
                'fields': 'photos,formatted_phone_number,website,opening_hours,reviews,price_level,rating,user_ratings_total'
            }
            
            async with detail_session.get(GOOGLE_PLACE_DETAILS_URL, params=params) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if data.get('status') == 'OK':
                        result = data.get('result', {})
                        
                        # Extract photos
                        photos = []
                        if 'photos' in result:
                            for photo in result['photos'][:3]:  # Limit to 3 photos
                                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photoreference={photo['photo_reference']}&key={GOOGLE_API_KEY}"
                                photos.append({
                                    'url': photo_url,
                                    'width': photo.get('width', 400),
                                    'height': photo.get('height', 300)
                                })
                        
                        # Extract reviews
                        reviews = []
                        if 'reviews' in result:
                            for review in result['reviews'][:3]:  # Limit to 3 reviews
                                reviews.append({
                                    'author_name': review.get('author_name', 'Anonymous'),
                                    'rating': review.get('rating', 0),
                                    'text': review.get('text', '')[:200] + '...' if len(review.get('text', '')) > 200 else review.get('text', ''),
                                    'time': review.get('time', 0)
                                })
                        
                        return {
                            'photos': photos,
                            'formatted_phone_number': result.get('formatted_phone_number'),
                            'website': result.get('website'),
                            'opening_hours': result.get('opening_hours', {}).get('weekday_text', []),
                            'reviews': reviews,
                            'price_level': result.get('price_level'),
                            'rating': result.get('rating'),
                            'user_ratings_total': result.get('user_ratings_total')
                        }
                    else:
                        search_log.append(f"  ❌ Details API error: {data.get('status')}")
                else:
                    search_log.append(f"  ❌ Details HTTP error: {resp.status}")
                    
    except Exception as e:
        search_log.append(f"  ❌ Exception getting details for {place_id}: {str(e)}")
    
    return {}

async def search_google_places(location, filters):
    # Check if API key is available
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'your_google_places_api_key_here':
        print("No Google Places API key found, using mock data")
        return get_mock_restaurants(location, filters), []
    
    # Initialize cache
    ensure_cache_dir()
    
    # Check if we should use cached results
    if should_use_cached_results(filters):
        cache_key = get_cache_key(location, filters, 'comprehensive')
        cache_file = get_cache_file(cache_key)
        
        if is_cache_valid(cache_file):
            cached_results = load_from_cache(cache_file)
            if cached_results:
                print(f"Using cached results: {len(cached_results)} restaurants")
                return cached_results, ["📋 Using cached results (24h cache)"]
    
    search_log = []
    all_results = []
    seen_place_ids = set()
    
    # Create SSL context to handle certificate issues
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    # Cost optimization: Determine search strategy based on filters
    search_strategy = determine_search_strategy(filters)
    search_log.append(f"💰 Using search strategy: {search_strategy['name']}")
    
    async with aiohttp.ClientSession(connector=connector) as session:
        # Strategy 1: Smart radius searches based on user's requested radius
        user_radius = filters.get('radius', 2000)
        radius_values = get_optimized_radius_values(user_radius)
        
        for radius in radius_values:
            basic_params = {
                'key': GOOGLE_API_KEY,
                'location': f"{location['lat']},{location['lng']}",
                'radius': radius,
                'type': 'restaurant',
            }
            
            if filters.get('open_now'):
                basic_params['opennow'] = 'true'
            
            search_log.append(f"🔍 Radius search: {radius}m")
            basic_results = await perform_search_with_pagination(session, GOOGLE_PLACES_URL, basic_params, search_log)
            
            # Add only new results
            new_results = [r for r in basic_results if r['id'] not in seen_place_ids]
            all_results.extend(new_results)
            seen_place_ids.update(r['id'] for r in new_results if r['id'])
        
        # Strategy 2: Cuisine-specific searches (only if cuisine is specified)
        if 'cuisine' in filters and filters['cuisine'] and len(filters['cuisine'].strip()) > 2:
            cuisine = filters['cuisine'].strip()
            keywords = get_cuisine_keywords(cuisine)
            
            search_log.append(f"🍽️ Cuisine search for '{cuisine}' with keywords: {', '.join(keywords[:3])}")
            
            for keyword in keywords[:3]:  # Limit to 3 keywords to reduce costs
                if keyword.lower() != cuisine.lower():
                    for radius in [2000, 5000]:  # Reduced radius values
                        keyword_params = {
                            'key': GOOGLE_API_KEY,
                            'location': f"{location['lat']},{location['lng']}",
                            'radius': radius,
                            'type': 'restaurant',
                            'keyword': keyword
                        }
                        
                        if filters.get('open_now'):
                            keyword_params['opennow'] = 'true'
                        
                        search_log.append(f"  🔎 Keyword search: '{keyword}' (radius: {radius}m)")
                        keyword_results = await perform_search_with_pagination(session, GOOGLE_PLACES_URL, keyword_params, search_log)
                        
                        # Add only new results
                        new_results = [r for r in keyword_results if r['id'] not in seen_place_ids]
                        all_results.extend(new_results)
                        seen_place_ids.update(r['id'] for r in new_results if r['id'])
        
        # Strategy 3: Fallback searches (only for larger radius searches)
        if user_radius >= 3000:
            fallback_keywords = ['seafood', 'chinese', 'japanese', 'italian', 'mexican', 'thai', 'indian', 'american', 'pizza', 'burger']
            for keyword in fallback_keywords:
                for radius in [5000]:  # Single radius to reduce costs
                    fallback_params = {
                        'key': GOOGLE_API_KEY,
                        'query': f"{keyword} restaurant",
                        'type': 'restaurant',
                        'location': f"{location['lat']},{location['lng']}",
                        'radius': radius
                    }
                    
                    search_log.append(f"🎯 Fallback search: '{keyword}' (radius: {radius}m)")
                    fallback_results = await perform_search_with_pagination(session, GOOGLE_TEXT_SEARCH_URL, fallback_params, search_log)
                    
                    # Add only new results
                    new_results = [r for r in fallback_results if r['id'] not in seen_place_ids]
                    all_results.extend(new_results)
                    seen_place_ids.update(r['id'] for r in new_results if r['id'])
    
    # Remove duplicates and process results
    unique_results = []
    seen_names = set()
    
    for result in all_results:
        if result['name'] not in seen_names:
            unique_results.append(result)
            seen_names.add(result['name'])
    
    # Get additional details for top results (limit to first 10 to save API calls)
    search_log.append("📸 Fetching additional details for top results...")
    detailed_results = []
    
    for i, result in enumerate(unique_results[:10]):
        if result.get('id'):
            details = await get_place_details(session, result['id'], search_log)
            if details:
                result.update(details)
            detailed_results.append(result)
        else:
            detailed_results.append(result)
    
    # Add remaining results without details
    detailed_results.extend(unique_results[10:])
    
    search_log.append(f"✅ Total unique results found: {len(detailed_results)}")
    print(f"Processed {len(detailed_results)} Google Places results")
    
    # Cache the results if appropriate
    if should_use_cached_results(filters):
        cache_key = get_cache_key(location, filters, 'comprehensive')
        cache_file = get_cache_file(cache_key)
        save_to_cache(cache_file, detailed_results)
        search_log.append("💾 Results cached for 24 hours")
    
    return detailed_results, search_log

def determine_search_strategy(filters):
    """Determine the optimal search strategy based on filters to minimize API costs"""
    radius = filters.get('radius', 2000)
    cuisine = filters.get('cuisine', '')
    
    if radius <= 1000:
        return {'name': 'minimal', 'description': 'Small radius, minimal searches'}
    elif radius <= 3000 and not cuisine:
        return {'name': 'standard', 'description': 'Medium radius, standard searches'}
    elif radius <= 5000:
        return {'name': 'comprehensive', 'description': 'Large radius, comprehensive searches'}
    else:
        return {'name': 'extensive', 'description': 'Very large radius, extensive searches'}

def get_optimized_radius_values(user_radius):
    """Get optimized radius values based on user's requested radius to minimize API calls"""
    if user_radius <= 1000:
        return [user_radius]  # Single search for small radius
    elif user_radius <= 3000:
        return [1000, user_radius]  # Two searches
    elif user_radius <= 5000:
        return [2000, user_radius]  # Two searches
    else:
        return [2000, 5000, user_radius]  # Three searches for large radius

def cleanup_expired_cache():
    """Remove expired cache files to save disk space"""
    if not os.path.exists(CACHE_DIR):
        return
    
    current_time = datetime.now()
    expired_count = 0
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(CACHE_DIR, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if current_time - file_time > timedelta(hours=CACHE_DURATION_HOURS):
                try:
                    os.remove(file_path)
                    expired_count += 1
                except:
                    pass
    
    if expired_count > 0:
        print(f"Cleaned up {expired_count} expired cache files")

def get_cache_stats():
    """Get cache statistics"""
    if not os.path.exists(CACHE_DIR):
        return {'total_files': 0, 'total_size_mb': 0}
    
    total_files = 0
    total_size = 0
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(CACHE_DIR, filename)
            total_files += 1
            total_size += os.path.getsize(file_path)
    
    return {
        'total_files': total_files,
        'total_size_mb': round(total_size / (1024 * 1024), 2)
    }

async def perform_search_with_pagination(session, url, params, search_log):
    """Perform a search with pagination to get more results"""
    all_results = []
    next_page_token = None
    max_pages = 2  # Reduced from 3 to 2 to save costs
    
    for page in range(max_pages):
        if next_page_token:
            params['pagetoken'] = next_page_token
            # Google requires a short delay between pagination requests
            import asyncio
            await asyncio.sleep(2)
        
        try:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
                status = data.get('status')
                results_count = len(data.get('results', []))
                
                search_log.append(f"  📊 Page {page + 1}: Status: {status}, Results: {results_count}")
                
                if status not in ['OK', 'ZERO_RESULTS']:
                    search_log.append(f"  ❌ Error: {data}")
                    break
                
                if results_count == 0:
                    break
                
                results = []
                for place in data.get('results', []):
                    from filters import haversine
                    distance = haversine(
                        float(params['location'].split(',')[0]), 
                        float(params['location'].split(',')[1]),
                        place['geometry']['location']['lat'],
                        place['geometry']['location']['lng']
                    )
                    
                    # Process photos to add URLs
                    photos = []
                    if 'photos' in place and place['photos']:
                        for photo in place['photos'][:3]:  # Limit to 3 photos
                            photo_url = f"https://maps.googleapis.com/maps/api/place/photo?key={GOOGLE_API_KEY}&photoreference={photo['photo_reference']}&maxwidth=400"
                            photos.append({
                                'url': photo_url,
                                'width': photo.get('width'),
                                'height': photo.get('height')
                            })
                    
                    # Don't filter by distance here - let the main filtering handle it
                    # Google Places API already respects the radius parameter
                    results.append({
                        'source': 'google',
                        'id': place.get('place_id'),
                        'name': place.get('name'),
                        'address': place.get('vicinity'),
                        'rating': place.get('rating', 0),
                        'user_ratings_total': place.get('user_ratings_total', 0),
                        'distance': distance,
                        'price_level': place.get('price_level', 0),
                        'open_now': place.get('opening_hours', {}).get('open_now') if place.get('opening_hours') else None,
                        'photos': photos,
                        'types': place.get('types', []),
                        'lat': place['geometry']['location']['lat'],
                        'lng': place['geometry']['location']['lng'],
                    })
                
                all_results.extend(results)
                
                # Check for next page token
                next_page_token = data.get('next_page_token')
                if not next_page_token:
                    break
                    
        except Exception as e:
            search_log.append(f"  ❌ Exception on page {page + 1}: {str(e)}")
            break
    
    return all_results

async def perform_search(session, url, params, search_log):
    """Perform a single search and return results"""
    try:
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            status = data.get('status')
            results_count = len(data.get('results', []))
            
            search_log.append(f"  📊 Status: {status}, Results: {results_count}")
            
            if status not in ['OK', 'ZERO_RESULTS']:
                search_log.append(f"  ❌ Error: {data}")
                return []
            
            results = []
            for place in data.get('results', []):
                from filters import haversine
                distance = haversine(
                    float(params['location'].split(',')[0]), 
                    float(params['location'].split(',')[1]),
                    place['geometry']['location']['lat'],
                    place['geometry']['location']['lng']
                )
                
                # Process photos to add URLs
                photos = []
                if 'photos' in place and place['photos']:
                    for photo in place['photos'][:3]:  # Limit to 3 photos
                        photo_url = f"https://maps.googleapis.com/maps/api/place/photo?key={GOOGLE_API_KEY}&photoreference={photo['photo_reference']}&maxwidth=400"
                        photos.append({
                            'url': photo_url,
                            'width': photo.get('width'),
                            'height': photo.get('height')
                        })
                
                # Don't filter by distance here - let the main filtering handle it
                # Google Places API already respects the radius parameter
                results.append({
                    'source': 'google',
                    'id': place.get('place_id'),
                    'name': place.get('name'),
                    'address': place.get('vicinity'),
                    'rating': place.get('rating', 0),
                    'user_ratings_total': place.get('user_ratings_total', 0),
                    'distance': distance,
                    'price_level': place.get('price_level', 0),
                    'open_now': place.get('opening_hours', {}).get('open_now') if place.get('opening_hours') else None,
                    'photos': photos,
                    'types': place.get('types', []),
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng'],
                })
            
            return results
            
    except Exception as e:
        search_log.append(f"  ❌ Exception: {str(e)}")
        return [] 