from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__)

# Cache configuration
CACHE_DIR = 'cache'
CACHE_DURATION_HOURS = 24

# Manual restaurant database for restaurants not in Google Places
MANUAL_RESTAURANTS = {
    'domo': {
        'name': 'Domo Modern Japanese Restaurant',
        'address': '252 N Bridge Rd, #03-00 Fairmont Singapore, Singapore 179103',
        'lat': 1.2942831,
        'lng': 103.8529487,
        'rating': 4.5,
        'user_ratings_total': 150,
        'price_level': 3,
        'types': ['restaurant', 'japanese', 'fine_dining'],
        'cuisine': 'japanese',
        'description': 'Modern Japanese restaurant located in Fairmont Singapore',
        'source': 'manual'
    }
}

def ensure_cache_dir():
    """Ensure cache directory exists"""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)

def get_cache_key(location, filters):
    """Generate a cache key for the search parameters"""
    import hashlib
    cache_data = {
        'lat': round(location['lat'], 4),
        'lng': round(location['lng'], 4),
        'filters': filters
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
        pass

def search_google_places_sync(location, filters):
    """Search Google Places API using synchronous requests"""
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        return [], ['❌ Google API key not configured']
    
    # Check cache first
    ensure_cache_dir()
    cache_key = get_cache_key(location, filters)
    cache_file = get_cache_file(cache_key)
    
    if is_cache_valid(cache_file):
        cached_results = load_from_cache(cache_file)
        if cached_results:
            return cached_results, ['✅ Using cached results']
    
    # Search Google Places
    radius = filters.get('radius', 2000)
    search_log = []
    
    try:
        # Ensure location is properly formatted
        lat = float(location['lat'])
        lng = float(location['lng'])
        location_str = f"{lat},{lng}"
        
        results = []
        
        # 1. Nearby search for restaurants
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'key': google_api_key,
            'location': location_str,
            'radius': radius,
            'type': 'restaurant'
        }
        
        print(f"🔍 Making Google Places API request with params: {params}")
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        print(f"📊 Google Places API response status: {data.get('status')}")
        print(f"📊 Google Places API error message: {data.get('error_message', 'None')}")
        
        if data.get('status') == 'INVALID_REQUEST':
            search_log.append(f"❌ Google Places API not enabled. Please enable 'Places API' in your Google Cloud Console.")
            search_log.append(f"🔧 Go to: https://console.cloud.google.com/apis/library/places-backend.googleapis.com")
            return [], search_log
        elif data.get('status') != 'OK':
            search_log.append(f"❌ Google Places API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
            return [], search_log
        
        # Process nearby search results
        for place in data.get('results', []):
            result = process_place_result(place, lat, lng)
            results.append(result)
        
        # 2. Text search for specific restaurants if cuisine filter is applied
        if filters.get('cuisine'):
            cuisine = filters['cuisine'].lower()
            text_search_query = f"{cuisine} restaurant near {location_str}"
            
            text_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
            text_params = {
                'key': google_api_key,
                'query': text_search_query,
                'location': location_str,
                'radius': radius
            }
            
            print(f"🔍 Making text search request: {text_search_query}")
            text_response = requests.get(text_url, params=text_params, timeout=10)
            text_data = text_response.json()
            
            if text_data.get('status') == 'OK':
                for place in text_data.get('results', []):
                    result = process_place_result(place, lat, lng)
                    # Avoid duplicates
                    if not any(r['id'] == result['id'] for r in results):
                        results.append(result)
                search_log.append(f"✅ Text search found {len(text_data.get('results', []))} additional results")
        
        search_log.append(f"✅ Found {len(results)} total Google Places results")
        
        # Cache results
        save_to_cache(cache_file, results)
        search_log.append("💾 Results cached for 24 hours")
        
        return results, search_log
        
    except Exception as e:
        search_log.append(f"❌ Error searching Google Places: {str(e)}")
        return [], search_log

def process_place_result(place, lat, lng):
    """Process a single place result from Google Places API"""
    # Calculate distance
    from math import radians, cos, sin, asin, sqrt
    lat1, lon1 = lat, lng
    lat2, lon2 = place['geometry']['location']['lat'], place['geometry']['location']['lng']
    
    # Haversine formula
    R = 6371  # Earth's radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    distance = R * c * 1000  # Convert to meters
    
    return {
        'source': 'google',
        'id': place.get('place_id'),
        'name': place.get('name'),
        'address': place.get('vicinity') or place.get('formatted_address'),
        'rating': place.get('rating'),
        'user_ratings_total': place.get('user_ratings_total'),
        'distance': int(distance),
        'price_level': place.get('price_level'),
        'open_now': place.get('opening_hours', {}).get('open_now'),
        'photos': [],
        'types': place.get('types', []),
        'lat': place['geometry']['location']['lat'],
        'lng': place['geometry']['location']['lng']
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return jsonify({
        'status': 'success',
        'message': 'App is working!',
        'api_key_set': bool(os.getenv('GOOGLE_API_KEY')),
        'api_key_preview': os.getenv('GOOGLE_API_KEY', '')[:10] + '...' if os.getenv('GOOGLE_API_KEY') else 'Not set'
    })

@app.route('/test-api')
def test_api():
    """Test if Google API key is working"""
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        return jsonify({
            'status': 'error',
            'message': 'Google API key not configured',
            'suggestion': 'Set GOOGLE_API_KEY environment variable in Render'
        })
    
    try:
        # Test with a simple geocoding request
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'key': google_api_key,
            'address': 'San Francisco, CA'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') == 'OK':
            return jsonify({
                'status': 'success',
                'message': 'Google API key is working!',
                'test_result': f"Found {len(data.get('results', []))} results for 'San Francisco, CA'",
                'api_status': data.get('status')
            })
        else:
            return jsonify({
                'status': 'error',
                'message': f'Google API error: {data.get("status")}',
                'error_message': data.get('error_message', 'Unknown error'),
                'suggestion': 'Check your API key and enabled APIs'
            })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'API test failed: {str(e)}',
            'suggestion': 'Check your internet connection and API key'
        })

@app.route('/test-places')
def test_places():
    """Test Google Places API specifically"""
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        return jsonify({
            'status': 'error',
            'message': 'Google API key not configured'
        })
    
    try:
        # Test Places API directly
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'key': google_api_key,
            'location': '37.7749,-122.4194',  # San Francisco
            'radius': 1000,
            'type': 'restaurant'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        return jsonify({
            'status': 'success',
            'places_api_status': data.get('status'),
            'error_message': data.get('error_message'),
            'results_count': len(data.get('results', [])),
            'raw_response': data
        })
            
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Places API test failed: {str(e)}'
        })

@app.route('/test-all-apis')
def test_all_apis():
    """Test all Google APIs and provide setup instructions"""
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        return jsonify({
            'status': 'error',
            'message': 'Google API key not configured',
            'setup_instructions': [
                '1. Go to Google Cloud Console: https://console.cloud.google.com/',
                '2. Create a new project or select existing one',
                '3. Go to APIs & Services > Credentials',
                '4. Create an API key',
                '5. Set it as GOOGLE_API_KEY environment variable in Render'
            ]
        })
    
    results = {
        'api_key_configured': True,
        'api_key_preview': google_api_key[:10] + '...',
        'apis': {}
    }
    
    # Test Geocoding API
    try:
        geocode_url = 'https://maps.googleapis.com/maps/api/geocode/json'
        geocode_params = {
            'key': google_api_key,
            'address': 'San Francisco, CA'
        }
        response = requests.get(geocode_url, params=geocode_params, timeout=5)
        data = response.json()
        results['apis']['geocoding'] = {
            'status': data.get('status'),
            'enabled': data.get('status') == 'OK',
            'error_message': data.get('error_message')
        }
    except Exception as e:
        results['apis']['geocoding'] = {
            'status': 'error',
            'enabled': False,
            'error_message': str(e)
        }
    
    # Test Places API
    try:
        places_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        places_params = {
            'key': google_api_key,
            'location': '37.7749,-122.4194',
            'radius': 1000,
            'type': 'restaurant'
        }
        response = requests.get(places_url, params=places_params, timeout=5)
        data = response.json()
        results['apis']['places'] = {
            'status': data.get('status'),
            'enabled': data.get('status') == 'OK',
            'error_message': data.get('error_message'),
            'results_count': len(data.get('results', []))
        }
    except Exception as e:
        results['apis']['places'] = {
            'status': 'error',
            'enabled': False,
            'error_message': str(e)
        }
    
    # Generate setup instructions
    setup_instructions = []
    if not results['apis'].get('geocoding', {}).get('enabled'):
        setup_instructions.append('Enable Geocoding API: https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com')
    if not results['apis'].get('places', {}).get('enabled'):
        setup_instructions.append('Enable Places API: https://console.cloud.google.com/apis/library/places-backend.googleapis.com')
    
    if setup_instructions:
        results['setup_instructions'] = setup_instructions
        results['status'] = 'needs_setup'
    else:
        results['status'] = 'all_working'
    
    return jsonify(results)

@app.route('/restaurants', methods=['POST'])
def restaurants():
    try:
        data = request.get_json()
        location = data.get('location')
        filters = data.get('filters', {})
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        print(f"🔍 Searching for restaurants at {location['lat']}, {location['lng']}")
        print(f"📋 Filters: {filters}")
        
        # Search using Google Places API
        results, search_log = search_google_places_sync(location, filters)
        
        # Add manual restaurants
        manual_results = search_manual_restaurants(location, filters)
        if manual_results:
            results.extend(manual_results)
            search_log.append(f"✅ Added {len(manual_results)} manual restaurants")
        
        # Apply filters
        filtered_results = results.copy()
        
        # Filter by minimum rating
        if filters.get('min_rating', 0) > 0:
            filtered_results = [r for r in filtered_results if r.get('rating', 0) >= filters['min_rating']]
        
        # Filter by open now
        if filters.get('open_now'):
            filtered_results = [r for r in filtered_results if r.get('open_now') is True]
        
        # Filter by cuisine type
        if filters.get('cuisine'):
            cuisine = filters['cuisine'].lower()
            cuisine_keywords = {
                'japanese': ['japanese', 'sushi', 'ramen', 'tempura', 'bento', 'izakaya', 'teppanyaki'],
                'chinese': ['chinese', 'dim sum', 'szechuan', 'cantonese', 'peking'],
                'italian': ['italian', 'pizza', 'pasta', 'ristorante', 'trattoria'],
                'indian': ['indian', 'curry', 'tandoori', 'biryani', 'masala'],
                'thai': ['thai', 'pad thai', 'tom yum', 'green curry'],
                'korean': ['korean', 'bbq', 'bibimbap', 'kimchi', 'bulgogi'],
                'mexican': ['mexican', 'taco', 'burrito', 'enchilada', 'quesadilla'],
                'american': ['american', 'burger', 'steak', 'bbq', 'diner'],
                'french': ['french', 'bistro', 'brasserie', 'crepe', 'croissant'],
                'mediterranean': ['mediterranean', 'greek', 'lebanese', 'turkish', 'falafel']
            }
            
            keywords = cuisine_keywords.get(cuisine, [cuisine])
            filtered_results = [r for r in filtered_results 
                              if any(keyword in r['name'].lower() or 
                                    any(keyword in t.lower() for t in r.get('types', []))
                                    for keyword in keywords)]
        
        # Filter by price level
        if filters.get('price_level') is not None:
            filtered_results = [r for r in filtered_results 
                              if r.get('price_level') == filters['price_level']]
        
        print(f"Processed {len(results)} Google Places results")
        print(f"After filtering: {len(filtered_results)} restaurants")
        
        # Get photos for top results (temporarily disabled to prevent crashes)
        # if filtered_results:
        #     filtered_results = get_restaurant_photos(filtered_results[:20])  # Limit to top 20 for photos
        
        # Log search details
        for log_entry in search_log:
            print(log_entry)
        
        return jsonify({
            'results': filtered_results,
            'search_log': search_log,
            'total_found': len(results),
            'total_filtered': len(filtered_results)
        })
        
    except Exception as e:
        print(f"❌ Error in restaurant search: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

def get_restaurant_photos(restaurants, max_photos=3):
    """Get photos for restaurants using Google Places Photo API"""
    google_api_key = os.getenv('GOOGLE_API_KEY')
    if not google_api_key:
        print("❌ No Google API key available for photos")
        return restaurants
    
    print(f"📸 Fetching photos for {len(restaurants)} restaurants...")
    
    for i, restaurant in enumerate(restaurants):
        if not restaurant.get('id'):
            continue
            
        try:
            # Get place details to get photo references
            details_url = 'https://maps.googleapis.com/maps/api/place/details/json'
            details_params = {
                'key': google_api_key,
                'place_id': restaurant['id'],
                'fields': 'photos'
            }
            
            response = requests.get(details_url, params=details_params, timeout=5)
            data = response.json()
            
            if data.get('status') == 'OK' and data.get('result', {}).get('photos'):
                photos = []
                for photo in data['result']['photos'][:max_photos]:
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo"
                    photo_params = {
                        'key': google_api_key,
                        'photoreference': photo['photo_reference'],
                        'maxwidth': 400,
                        'maxheight': 300
                    }
                    photos.append({
                        'url': photo_url,
                        'params': photo_params,
                        'width': photo.get('width'),
                        'height': photo.get('height')
                    })
                restaurant['photos'] = photos
                print(f"✅ Got {len(photos)} photos for {restaurant.get('name', 'Unknown')}")
            else:
                restaurant['photos'] = []
                print(f"ℹ️ No photos available for {restaurant.get('name', 'Unknown')}")
                
        except Exception as e:
            print(f"❌ Error getting photos for {restaurant.get('name', 'Unknown')}: {str(e)}")
            restaurant['photos'] = []
    
    return restaurants

@app.route('/geocode', methods=['POST'])
def geocode():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        print(f"🔍 Geocoding request for: {query}")
        
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            return jsonify({
                'error': 'Google Geocoding API is not configured. Please set GOOGLE_API_KEY environment variable.',
                'suggestion': 'You can manually enter coordinates or use "Use My Location" instead.'
            }), 400
        
        url = 'https://maps.googleapis.com/maps/api/geocode/json'
        params = {
            'key': google_api_key,
            'address': query,
            'components': 'country:SG'  # Focus on Singapore
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        status = data.get('status')
        print(f"📊 Geocoding response status: {status}")
        
        if status == 'REQUEST_DENIED':
            error_msg = data.get('error_message', 'Unknown error')
            print(f"❌ Geocoding API error: {error_msg}")
            return jsonify({
                'error': f'API access denied: {error_msg}. Please check your Google API key configuration.',
                'suggestion': 'You can manually enter coordinates or use "Use My Location" instead.'
            }), 400
        
        if status != 'OK':
            print(f"❌ Geocoding error: {status}")
            return jsonify({'error': f'Geocoding failed: {status}'}), 400
        
        results = data.get('results', [])
        print(f"✅ Found {len(results)} geocoding results")
        
        formatted_results = []
        for result in results[:5]:  # Limit to 5 results
            location = result['geometry']['location']
            formatted_results.append({
                'formatted_address': result['formatted_address'],
                'lat': location['lat'],
                'lng': location['lng']
            })
        
        return jsonify({'results': formatted_results})
        
    except Exception as e:
        print(f"❌ Geocoding error: {str(e)}")
        return jsonify({
            'error': f'Geocoding failed: {str(e)}',
            'suggestion': 'You can manually enter coordinates or use "Use My Location" instead.'
        }), 400

@app.route('/cache/stats')
def cache_stats():
    """Get cache statistics"""
    if not os.path.exists(CACHE_DIR):
        return jsonify({'total_files': 0, 'total_size_mb': 0})
    
    total_files = 0
    total_size = 0
    
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            file_path = os.path.join(CACHE_DIR, filename)
            total_files += 1
            total_size += os.path.getsize(file_path)
    
    return jsonify({
        'total_files': total_files,
        'total_size_mb': round(total_size / (1024 * 1024), 2)
    })

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cache files"""
    if not os.path.exists(CACHE_DIR):
        return jsonify({'message': 'No cache to clear'})
    
    cleared_count = 0
    for filename in os.listdir(CACHE_DIR):
        if filename.endswith('.json'):
            try:
                os.remove(os.path.join(CACHE_DIR, filename))
                cleared_count += 1
            except:
                pass
    
    return jsonify({'message': f'Cleared {cleared_count} cache files'})

@app.route('/search-restaurant', methods=['POST'])
def search_restaurant_by_name():
    """Search for a specific restaurant by name"""
    try:
        data = request.get_json()
        restaurant_name = data.get('name', '').strip()
        location = data.get('location')
        
        if not restaurant_name:
            return jsonify({'error': 'Restaurant name is required'}), 400
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key:
            return jsonify({'error': 'Google API key not configured'}), 400
        
        # Text search for the specific restaurant
        text_url = 'https://maps.googleapis.com/maps/api/place/textsearch/json'
        text_params = {
            'key': google_api_key,
            'query': f"{restaurant_name} restaurant",
            'location': f"{location['lat']},{location['lng']}",
            'radius': 5000  # 5km radius
        }
        
        print(f"🔍 Searching for restaurant: {restaurant_name}")
        response = requests.get(text_url, params=text_params, timeout=10)
        data = response.json()
        
        if data.get('status') != 'OK':
            return jsonify({
                'error': f'Search failed: {data.get("status")}',
                'error_message': data.get('error_message', 'Unknown error')
            }), 400
        
        results = []
        for place in data.get('results', []):
            result = process_place_result(place, location['lat'], location['lng'])
            results.append(result)
        
        return jsonify({
            'results': results,
            'total_found': len(results),
            'search_query': restaurant_name
        })
        
    except Exception as e:
        print(f"❌ Error in restaurant name search: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

def search_manual_restaurants(location, filters):
    """Search manual restaurant database"""
    results = []
    lat = float(location['lat'])
    lng = float(location['lng'])
    radius = filters.get('radius', 2000)
    
    for key, restaurant in MANUAL_RESTAURANTS.items():
        # Calculate distance
        from math import radians, cos, sin, asin, sqrt
        lat1, lon1 = lat, lng
        lat2, lon2 = restaurant['lat'], restaurant['lng']
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distance = R * c * 1000  # Convert to meters
        
        # Check if within radius
        if distance <= radius:
            # Apply filters
            if filters.get('cuisine') and restaurant.get('cuisine') != filters['cuisine']:
                continue
            if filters.get('min_rating', 0) > 0 and restaurant.get('rating', 0) < filters['min_rating']:
                continue
            if filters.get('price_level') is not None and restaurant.get('price_level') != filters['price_level']:
                continue
            
            result = {
                'source': 'manual',
                'id': f"manual_{key}",
                'name': restaurant['name'],
                'address': restaurant['address'],
                'rating': restaurant.get('rating'),
                'user_ratings_total': restaurant.get('user_ratings_total'),
                'distance': int(distance),
                'price_level': restaurant.get('price_level'),
                'open_now': None,  # Manual entries don't have real-time data
                'photos': [],
                'types': restaurant.get('types', []),
                'lat': restaurant['lat'],
                'lng': restaurant['lng'],
                'description': restaurant.get('description')
            }
            results.append(result)
    
    return results

if __name__ == "__main__":
    import os
    
    # Get port from environment variable (for production) or use default
    port = int(os.environ.get("PORT", 5001))
    
    print(f"Starting Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False) 