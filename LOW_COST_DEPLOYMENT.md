# Low-Cost Restaurant Discovery App Deployment

## Cost Analysis with Google Places API Only

### **API Costs:**
- **Google Places API**: $0.017 per request
- **Google Geocoding API**: $0.005 per request
- **Total per search**: ~$0.022

### **Cost Optimization Features:**
- ✅ **24-hour caching** (reduces API calls by ~80%)
- ✅ **Smart search strategies** (minimizes API calls)
- ✅ **Efficient pagination** (2 pages max)
- ✅ **Top 10 detailed results** only

### **Monthly Cost Estimates:**

| Users | Searches/Day | API Calls/Month | Monthly Cost |
|-------|-------------|-----------------|--------------|
| 50    | 1           | 1,500           | $33          |
| 100   | 1           | 3,000           | $66          |
| 200   | 2           | 12,000          | $264         |
| 500   | 3           | 45,000          | $990         |

## Free Deployment Options

### **1. Railway (Recommended) - FREE Tier**
```bash
# Deploy to Railway (free tier)
railway login
railway init
railway up
```

**Free Tier Includes:**
- 500 hours/month
- 1GB RAM
- Shared CPU
- Custom domains
- SSL certificates

### **2. Render - FREE Tier**
```bash
# Deploy to Render
# Connect your GitHub repo
# Set environment variables
```

**Free Tier Includes:**
- 750 hours/month
- 512MB RAM
- Shared CPU
- Custom domains
- SSL certificates

### **3. Heroku - FREE Alternative**
```bash
# Deploy to Heroku (limited free tier)
heroku create your-app-name
git push heroku main
```

**Free Tier Includes:**
- 550-1000 hours/month
- 512MB RAM
- Shared CPU

### **4. Vercel - FREE Tier**
```bash
# Deploy to Vercel
vercel --prod
```

**Free Tier Includes:**
- Unlimited deployments
- 100GB bandwidth
- Serverless functions
- Custom domains

## Production Deployment Steps

### **1. Prepare Your App**

```bash
# Create Procfile for production
echo "web: gunicorn app:app" > Procfile

# Add gunicorn to requirements
echo "gunicorn==20.1.0" >> requirements.txt

# Create runtime.txt
echo "python-3.11.7" > runtime.txt
```

### **2. Set Environment Variables**

```bash
# Production environment variables
GOOGLE_API_KEY=your_google_places_api_key_here
FLASK_ENV=production
```

### **3. Optimize for Production**

```python
# In app.py, add production optimizations
if os.environ.get('PORT'):
    # Production mode - disable debug
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT')))
```

### **4. Deploy to Railway (Recommended)**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables
railway variables set GOOGLE_API_KEY=your_key_here
```

## Cost Optimization Strategies

### **1. Aggressive Caching**
```python
# Extend cache duration to 48 hours
CACHE_DURATION_HOURS = 48

# Add cache warming for popular locations
def warm_cache_popular_locations():
    popular_locations = [
        {'lat': 1.2995, 'lng': 103.8499},  # Singapore
        {'lat': 37.7749, 'lng': -122.4194}, # San Francisco
        # Add more popular locations
    ]
```

### **2. User Quotas**
```python
# Implement daily search limits
MAX_SEARCHES_PER_DAY = 10
MAX_SEARCHES_PER_USER = 5
```

### **3. Smart Search Strategies**
```python
# Reduce API calls for small radius searches
if radius <= 1000:
    # Single search only
    search_strategy = 'minimal'
elif radius <= 3000:
    # Two searches max
    search_strategy = 'standard'
```

### **4. Mock Data for Development**
```python
# Use mock data when API key is not available
if not GOOGLE_API_KEY:
    return get_mock_restaurants(location, filters)
```

## Monitoring and Analytics

### **1. Track API Usage**
```python
# Log API calls for monitoring
import logging
logging.info(f"API call: {api_type} - {location}")

# Track costs
def track_api_cost(api_calls, cost_per_call):
    total_cost = api_calls * cost_per_call
    logging.info(f"API cost: ${total_cost:.4f}")
```

### **2. Set Up Alerts**
```bash
# Set up cost alerts in Google Cloud Console
# Alert when daily cost exceeds $5
# Alert when API quota reaches 80%
```

### **3. Monitor Performance**
```python
# Track response times
import time
start_time = time.time()
# ... API call ...
response_time = time.time() - start_time
logging.info(f"Response time: {response_time:.2f}s")
```

## Revenue Generation to Cover Costs

### **1. Premium Features**
- **Unlimited searches**: $5/month
- **Advanced filters**: $3/month
- **Export results**: $2/month

### **2. Restaurant Partnerships**
- **Featured listings**: $50/month per restaurant
- **Sponsored results**: $100/month
- **Menu integration**: $200/month

### **3. Affiliate Marketing**
- **Booking commissions**: 10-15% per booking
- **Delivery partnerships**: 5-10% per order
- **Review platform**: $1-2 per review

## Scaling Strategy

### **Phase 1: MVP (0-100 users)**
- **Cost**: $0-66/month
- **Platform**: Railway free tier
- **Features**: Basic search and filters

### **Phase 2: Growth (100-500 users)**
- **Cost**: $66-990/month
- **Platform**: Railway paid tier ($5/month)
- **Features**: Premium features, partnerships

### **Phase 3: Scale (500+ users)**
- **Cost**: $990+/month
- **Platform**: Dedicated hosting
- **Features**: Advanced analytics, ML recommendations

## Backup and Recovery

### **1. Data Backup**
```python
# Backup cache data
def backup_cache():
    import shutil
    shutil.make_archive('cache_backup', 'zip', 'cache/')
```

### **2. API Fallbacks**
```python
# Fallback to mock data if API fails
try:
    results = await search_google_places(location, filters)
except:
    results = get_mock_restaurants(location, filters)
```

### **3. Health Checks**
```python
@app.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'cache_size': get_cache_stats()['total_size_mb'],
        'api_key_configured': bool(os.getenv('GOOGLE_API_KEY'))
    })
```

## Security Considerations

### **1. API Key Protection**
```python
# Never expose API keys in client-side code
# Use environment variables only
# Rotate keys regularly
```

### **2. Rate Limiting**
```python
# Implement rate limiting
from flask_limiter import Limiter
limiter = Limiter(app, key_func=get_remote_address)

@app.route('/restaurants', methods=['POST'])
@limiter.limit("10 per minute")
async def get_restaurants():
    # ... existing code
```

### **3. Input Validation**
```python
# Validate all inputs
def validate_location(location):
    if not isinstance(location, dict):
        raise ValueError("Location must be a dictionary")
    if 'lat' not in location or 'lng' not in location:
        raise ValueError("Location must contain lat and lng")
    # ... more validation
```

## Conclusion

With these optimizations, you can run a production restaurant discovery app for **under $100/month** with 200+ users. The key is:

1. **Aggressive caching** (80% cost reduction)
2. **Smart search strategies** (minimize API calls)
3. **User quotas** (prevent abuse)
4. **Free hosting** (Railway/Render)
5. **Revenue generation** (premium features)

This approach allows you to start with minimal costs and scale as you grow your user base and revenue. 