# Deploy to Render - Free Alternative to Railway

## Why Render?
- **Free tier**: 750 hours/month (enough for 24/7)
- **Easy deployment**: Connect GitHub repo
- **Automatic HTTPS**: No SSL configuration needed
- **Custom domains**: Free subdomain included
- **Sleep after inactivity**: Free tier sleeps after 15 minutes (wakes up on first request)

## Step-by-Step Deployment

### 1. Prepare Your Code
✅ Your code is already prepared with:
- `requirements.txt` - Dependencies
- `render.yaml` - Render configuration
- `app.py` - Updated for production
- `Procfile` - Alternative start command

### 2. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub (recommended)
3. Verify your email

### 3. Deploy Your App
1. **Click "New +" → "Web Service"**
2. **Connect your GitHub repository**
3. **Configure the service:**
   - **Name**: `food-recommendation-app`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`
   - **Plan**: `Free`

### 4. Set Environment Variables
In the Render dashboard, go to your service → Environment:
- **Key**: `GOOGLE_API_KEY`
- **Value**: Your Google Places API key
- **Click "Save Changes"**

### 5. Deploy
- Click "Create Web Service"
- Wait for build to complete (2-3 minutes)
- Your app will be available at: `https://your-app-name.onrender.com`

## Environment Variables
Set these in Render dashboard:
```
GOOGLE_API_KEY=your_actual_google_api_key_here
```

## Troubleshooting

### Build Fails
- Check that `requirements.txt` is in the root directory
- Ensure all dependencies are listed
- Check build logs for specific errors

### App Won't Start
- Verify the start command in `render.yaml`
- Check that `app.py` has the correct Flask app instance
- Look at logs for Python errors

### API Key Issues
- Ensure `GOOGLE_API_KEY` is set in environment variables
- Verify the API key is valid and has Places API enabled
- Check that billing is enabled on Google Cloud

### App Sleeps
- Free tier sleeps after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up
- Consider upgrading to paid plan for always-on service

## Monitoring
- **Logs**: Available in Render dashboard
- **Metrics**: Basic metrics included
- **Health checks**: Automatic health checks

## Custom Domain (Optional)
1. Go to your service → Settings → Custom Domains
2. Add your domain
3. Update DNS records as instructed

## Cost Comparison
- **Render Free**: $0/month (750 hours)
- **Railway**: $5/month minimum
- **Heroku**: $5/month minimum
- **DigitalOcean**: $5/month minimum

## Next Steps
1. Deploy to Render
2. Test your app
3. Set up monitoring
4. Consider custom domain
5. Monitor usage to stay within free tier

## Support
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Python on Render](https://render.com/docs/deploy-python) 