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
        # Nearby search
        url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'
        params = {
            'key': google_api_key,
            'location': f"{location['lat']},{location['lng']}",
            'radius': radius,
            'type': 'restaurant',
            'rankby': 'distance'
        }
        
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if data.get('status') != 'OK':
            search_log.append(f"❌ Google Places API error: {data.get('status')}")
            return [], search_log
        
        results = []
        for place in data.get('results', []):
            # Calculate distance
            from math import radians, cos, sin, asin, sqrt
            lat1, lon1 = location['lat'], location['lng']
            lat2, lon2 = place['geometry']['location']['lat'], place['geometry']['location']['lng']
            
            # Haversine formula
            R = 6371  # Earth's radius in kilometers
            dlat = radians(lat2 - lat1)
            dlon = radians(lon2 - lon1)
            a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            distance = R * c * 1000  # Convert to meters
            
            result = {
                'source': 'google',
                'id': place.get('place_id'),
                'name': place.get('name'),
                'address': place.get('vicinity'),
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
            results.append(result)
        
        search_log.append(f"✅ Found {len(results)} Google Places results")
        
        # Cache results
        save_to_cache(cache_file, results)
        search_log.append("💾 Results cached for 24 hours")
        
        return results, search_log
        
    except Exception as e:
        search_log.append(f"❌ Error searching Google Places: {str(e)}")
        return [], search_log

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

@app.route('/restaurants', methods=['POST'])
def get_restaurants():
    try:
        data = request.get_json()
        location = data.get('location')
        filters = data.get('filters', {})
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        print(f"🔍 Searching for restaurants at {location['lat']}, {location['lng']}")
        
        # Search using Google Places API
        results, search_log = search_google_places_sync(location, filters)
        
        # Apply basic filters
        filtered_results = results.copy()
        
        # Filter by minimum rating
        if filters.get('min_rating', 0) > 0:
            filtered_results = [r for r in filtered_results if r.get('rating', 0) >= filters['min_rating']]
        
        # Filter by open now
        if filters.get('open_now'):
            filtered_results = [r for r in filtered_results if r.get('open_now') is True]
        
        # Filter by cuisine
        if filters.get('cuisine'):
            cuisine = filters['cuisine'].lower()
            filtered_results = [r for r in filtered_results 
                              if cuisine in r['name'].lower() or 
                              any(cuisine in t.lower() for t in r.get('types', []))]
        
        print(f"Processed {len(results)} Google Places results")
        print(f"After filtering: {len(filtered_results)} restaurants")
        
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
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

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

if __name__ == "__main__":
    import os
    
    # Get port from environment variable (for production) or use default
    port = int(os.environ.get("PORT", 5001))
    
    print(f"Starting Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False) 