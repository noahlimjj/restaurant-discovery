from flask import Flask, render_template, request, jsonify
import os
import ssl
from merge import search_all_apis, filter_results
from filters import haversine
import json
from datetime import datetime, timedelta
import asyncio
from dotenv import load_dotenv
import subprocess
import aiohttp
from api.google_places import search_google_places, cleanup_expired_cache, get_cache_stats

load_dotenv()

app = Flask(__name__)

# SSL context for HTTPS
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/geocode', methods=['POST'])
def geocode():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        print(f"🔍 Geocoding request for: {query}")
        
        # Check if Google API key is available
        google_api_key = os.getenv('GOOGLE_API_KEY')
        if not google_api_key or google_api_key == 'your_google_places_api_key_here':
            return jsonify({
                'error': 'Google Geocoding API is not configured. Please set GOOGLE_API_KEY environment variable.',
                'suggestion': 'You can manually enter coordinates or use "Use My Location" instead.'
            }), 400
        
        # Create SSL context
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        
        async def geocode_async():
            async with aiohttp.ClientSession(connector=connector) as session:
                params = {
                    'key': google_api_key,
                    'address': query,
                    'components': 'country:SG'  # Focus on Singapore
                }
                
                async with session.get('https://maps.googleapis.com/maps/api/geocode/json', params=params) as resp:
                    data = await resp.json()
                    status = data.get('status')
                    
                    print(f"📊 Geocoding response status: {status}")
                    
                    if status == 'REQUEST_DENIED':
                        error_msg = data.get('error_message', 'Unknown error')
                        print(f"❌ Geocoding API error: {error_msg}")
                        return {
                            'error': f'API access denied: {error_msg}. Please check your Google API key configuration.',
                            'suggestion': 'You can manually enter coordinates or use "Use My Location" instead.'
                        }
                    
                    if status != 'OK':
                        print(f"❌ Geocoding error: {status}")
                        return {'error': f'Geocoding failed: {status}'}
                    
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
                    
                    return {'results': formatted_results}
        
        # Run async function
        result = asyncio.run(geocode_async())
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Geocoding error: {str(e)}")
        return jsonify({
            'error': f'Geocoding failed: {str(e)}',
            'suggestion': 'You can manually enter coordinates or use "Use My Location" instead.'
        }), 400

@app.route('/restaurants', methods=['POST'])
def get_restaurants():
    try:
        data = request.get_json()
        location = data.get('location')
        filters = data.get('filters', {})
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        print(f"🔍 Searching for restaurants at {location['lat']}, {location['lng']}")
        
        # Search using Google Places API only
        async def fetch_results():
            return await search_all_apis(location, filters)
        
        results, search_log = asyncio.run(fetch_results())
        
        # Apply additional filters
        filtered_results = filter_results(results, filters)
        
        print(f"Processed {len(results)} Google Places results")
        print(f"Applying filters to {len(results)} restaurants")
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

@app.route('/restaurants/test', methods=['GET'])
def test_restaurants():
    # Mock location and filters
    location = {'lat': 37.7749, 'lng': -122.4194}
    filters = {'radius': 2000, 'min_rating': 0}
    
    # Mock results for testing
    google_results = [
        {
            'source': 'google',
            'id': 'g1',
            'name': 'Sushi Place',
            'address': '123 Market St',
            'rating': 4.5,
            'user_ratings_total': 120,
            'distance': None,
            'price_level': 2,
            'open_now': True,
            'photos': [],
            'types': ['Japanese', 'vegetarian'],
            'lat': 37.7750,
            'lng': -122.4195,
        },
        {
            'source': 'google',
            'id': 'g2',
            'name': 'Ramen House',
            'address': '456 Mission St',
            'rating': 4.2,
            'user_ratings_total': 80,
            'distance': None,
            'price_level': 2,
            'open_now': True,
            'photos': [],
            'types': ['Japanese'],
            'lat': 37.7760,
            'lng': -122.4180,
        },
    ]
    
    # Use new functions
    filtered = filter_results(google_results, filters)
    return jsonify({'results': filtered})

@app.route('/restaurants/sf', methods=['GET'])
def test_sf_restaurants():
    """Test endpoint using San Francisco location to verify API works"""
    try:
        # Use San Francisco location
        location = {'lat': 37.7749, 'lng': -122.4194}  # San Francisco
        filters = {
            'radius': 5000,  # 5km radius
            'min_rating': 0  # No minimum rating to get more results
        }

        print(f"Testing SF restaurants with location: {location}, filters: {filters}")

        async def fetch_all():
            print("Searching Google Places...")
            results, search_log = await search_all_apis(location, filters)
            print(f"Got {len(results)} Google results")
            print("Applying filters...")
            filtered = filter_results(results, filters)
            print(f"Filtered to {len(filtered)} results")
            return filtered, search_log

        results, search_log = asyncio.run(fetch_all())
        print(f"Final result count: {len(results)}")
        return jsonify({
            'results': results,
            'count': len(results),
            'location': location,
            'filters': filters,
            'search_log': search_log
        })
    except Exception as e:
        print(f"Error in /restaurants/sf: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'results': [], 'search_log': []}), 500

@app.route('/cache/stats')
def cache_stats():
    """Get cache statistics"""
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        return jsonify({'total_files': 0, 'total_size_mb': 0})
    
    total_files = 0
    total_size = 0
    
    for filename in os.listdir(cache_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(cache_dir, filename)
            total_files += 1
            total_size += os.path.getsize(file_path)
    
    return jsonify({
        'total_files': total_files,
        'total_size_mb': round(total_size / (1024 * 1024), 2)
    })

@app.route('/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cache files"""
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        return jsonify({'message': 'No cache to clear'})
    
    cleared_count = 0
    for filename in os.listdir(cache_dir):
        if filename.endswith('.json'):
            try:
                os.remove(os.path.join(cache_dir, filename))
                cleared_count += 1
            except:
                pass
    
    return jsonify({'message': f'Cleared {cleared_count} cache files'})

@app.route('/cache/cleanup', methods=['POST'])
def cleanup_cache():
    """Remove expired cache files"""
    cache_dir = 'cache'
    if not os.path.exists(cache_dir):
        return jsonify({'message': 'No cache to cleanup'})
    
    current_time = datetime.now()
    expired_count = 0
    
    for filename in os.listdir(cache_dir):
        if filename.endswith('.json'):
            file_path = os.path.join(cache_dir, filename)
            file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            
            if current_time - file_time > timedelta(hours=24):
                try:
                    os.remove(file_path)
                    expired_count += 1
                except:
                    pass
    
    return jsonify({'message': f'Cleaned up {expired_count} expired cache files'})

def create_self_signed_cert():
    """Create a self-signed certificate using OpenSSL"""
    try:
        # Generate private key
        subprocess.run([
            'openssl', 'genrsa', '-out', 'key.pem', '2048'
        ], check=True, capture_output=True)
        
        # Generate certificate
        subprocess.run([
            'openssl', 'req', '-new', '-x509', '-key', 'key.pem', 
            '-out', 'cert.pem', '-days', '365',
            '-subj', '/C=US/ST=CA/L=San Francisco/O=Food Recommendation App/CN=localhost'
        ], check=True, capture_output=True)
        
        return "cert.pem", "key.pem"
    except subprocess.CalledProcessError as e:
        print(f"Error creating SSL certificate: {e}")
        return None, None
    except FileNotFoundError:
        print("OpenSSL not found. Please install OpenSSL or use HTTP instead.")
        return None, None

if __name__ == "__main__":
    import os
    
    # Get port from environment variable (for production) or use default
    port = int(os.environ.get("PORT", 5001))
    
    # Check if we're in production (Render, Railway, etc.)
    is_production = os.environ.get("RENDER") or os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT")
    
    if is_production:
        # Production: no SSL context, bind to all interfaces
        print(f"Starting Flask app in production mode on port {port}...")
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        # Development: use SSL context
        print("Starting Flask app with HTTPS...")
        print(f"Access the app at: https://127.0.0.1:{port}")
        print(f"Test API with: https://127.0.0.1:{port}/restaurants/sf")
        print("Note: You may see a security warning in your browser. Click 'Advanced' and 'Proceed to localhost' to continue.")
        
        # Create SSL context for development
        cert_file = "cert.pem"
        key_file = "key.pem"
        
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            print("Creating self-signed SSL certificate...")
            cert_file, key_file = create_self_signed_cert()
            if cert_file and key_file:
                print("SSL certificate created successfully!")
            else:
                print("Failed to create SSL certificate. Starting with HTTP...")
                app.run(debug=True, host="0.0.0.0", port=port)
                exit()
        
        app.run(debug=True, host="0.0.0.0", port=port, ssl_context=(cert_file, key_file)) 