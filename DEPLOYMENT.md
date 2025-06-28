# 🚀 Deployment Guide - Restaurant Finder App

## Free Hosting Options

### Option 1: Heroku (Recommended - Free)
**Cost**: $0/month for basic usage
**Limitations**: App sleeps after 30 minutes of inactivity

#### Steps:
1. **Install Heroku CLI**
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Or download from: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login to Heroku**
   ```bash
   heroku login
   ```

3. **Create Heroku App**
   ```bash
   heroku create your-restaurant-finder
   ```

4. **Set Environment Variables**
   ```bash
   heroku config:set GOOGLE_PLACES_API_KEY=your_api_key_here
   ```

5. **Deploy**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

6. **Open App**
   ```bash
   heroku open
   ```

### Option 2: Railway ($5/month)
**Cost**: $5/month (includes $5 credit)
**Benefits**: No sleep, better performance

#### Steps:
1. Go to [railway.app](https://railway.app)
2. Connect your GitHub repository
3. Set environment variables in Railway dashboard
4. Deploy automatically

### Option 3: Render ($7/month)
**Cost**: $7/month for web services
**Benefits**: Reliable, good performance

## API Cost Management

### Google Places API Costs:
- **Free tier**: $200/month credit
- **Nearby Search**: $17 per 1000 requests
- **Text Search**: $32 per 1000 requests
- **With $200 credit**: ~11,700 searches/month

### Cost Reduction Strategies:

1. **Implement Caching**
   ```python
   # Cache results for 1 hour
   from functools import lru_cache
   import time
   
   @lru_cache(maxsize=1000)
   def cached_search(location, filters):
       # Your search logic here
       pass
   ```

2. **Add Rate Limiting**
   ```python
   # Limit users to 10 searches per day
   from flask_limiter import Limiter
   
   limiter = Limiter(app, key_func=get_remote_address)
   
   @app.route('/restaurants', methods=['POST'])
   @limiter.limit("10 per day")
   def get_restaurants():
       # Your code here
   ```

3. **Use Mock Data for Development**
   - Keep mock data for testing
   - Only use real API in production

## Environment Variables

Set these in your hosting platform:

```bash
GOOGLE_PLACES_API_KEY=your_google_api_key
FLASK_ENV=production
```

## Free Alternative APIs

If Google Places becomes too expensive:

1. **OpenTripMap**: 5000 requests/month free
2. **Foursquare Places**: 950 requests/day free
3. **Here Places**: 250,000 transactions/month free

## Monitoring Usage

Add usage tracking:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/restaurants', methods=['POST'])
def get_restaurants():
    logger.info(f"API request from {request.remote_addr}")
    # Your code here
```

## Cost Estimates

### Low Usage (Personal/Small Group):
- **Hosting**: $0 (Heroku free tier)
- **APIs**: $0-20/month
- **Total**: $0-20/month

### Medium Usage (100 users/day):
- **Hosting**: $7/month (Render)
- **APIs**: $50-100/month
- **Total**: $57-107/month

### High Usage (1000+ users/day):
- **Hosting**: $25/month (Heroku paid)
- **APIs**: $200-500/month
- **Total**: $225-525/month

## Scaling Tips

1. **Start with free tier**
2. **Monitor usage closely**
3. **Implement caching early**
4. **Add rate limiting**
5. **Consider alternative APIs**
6. **Optimize search strategies**

## Security Considerations

1. **Never commit API keys to Git**
2. **Use environment variables**
3. **Implement rate limiting**
4. **Validate user input**
5. **Use HTTPS in production** 