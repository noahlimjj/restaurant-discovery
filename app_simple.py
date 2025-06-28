from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/test')
def test():
    return jsonify({
        'status': 'success',
        'message': 'App is working!',
        'api_key_set': bool(os.getenv('GOOGLE_API_KEY'))
    })

@app.route('/restaurants', methods=['POST'])
def get_restaurants():
    try:
        data = request.get_json()
        location = data.get('location')
        filters = data.get('filters', {})
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        # Return mock data for testing
        mock_results = [
            {
                'source': 'google',
                'id': 'test_1',
                'name': 'Test Restaurant',
                'address': '123 Test St',
                'rating': 4.5,
                'user_ratings_total': 100,
                'distance': 500,
                'price_level': 2,
                'open_now': True,
                'photos': [],
                'types': ['restaurant', 'food'],
                'lat': location['lat'] + 0.001,
                'lng': location['lng'] + 0.001,
            }
        ]
        
        return jsonify({
            'results': mock_results,
            'search_log': ['Test mode - using mock data'],
            'total_found': 1,
            'total_filtered': 1
        })
        
    except Exception as e:
        print(f"❌ Error in restaurant search: {str(e)}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

if __name__ == "__main__":
    import os
    
    # Get port from environment variable (for production) or use default
    port = int(os.environ.get("PORT", 5001))
    
    print(f"Starting Flask app on port {port}...")
    app.run(host="0.0.0.0", port=port, debug=False) 