# 🚀 Deployment Steps for Restaurant Discovery App

## Step 1: Get Google Places API Key

1. **Go to Google Cloud Console:**
   - Visit [console.cloud.google.com](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable Required APIs:**
   - Go to "APIs & Services" > "Library"
   - Search and enable these APIs:
     - ✅ **Places API**
     - ✅ **Geocoding API**
     - ✅ **Maps JavaScript API**

3. **Create API Key:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "API Key"
   - **IMPORTANT:** Restrict the key to only the APIs you enabled above

4. **Copy your API key** - you'll need it for Step 3

## Step 2: Create GitHub Repository

1. **Go to GitHub:**
   - Visit [github.com](https://github.com/)
   - Sign up/login with your account

2. **Create New Repository:**
   - Click "New repository"
   - Name it: `restaurant-discovery-app`
   - Make it **Public** (for free Railway deployment)
   - Don't initialize with README (we already have files)

3. **Push Your Code:**
   ```bash
   # In your terminal, run these commands:
   git remote add origin https://github.com/YOUR_USERNAME/restaurant-discovery-app.git
   git branch -M main
   git push -u origin main
   ```

## Step 3: Deploy to Railway (FREE)

1. **Go to Railway:**
   - Visit [railway.app](https://railway.app/)
   - Sign up with your GitHub account

2. **Create New Project:**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your `restaurant-discovery-app` repository

3. **Set Environment Variables:**
   - In your Railway project dashboard
   - Go to "Variables" tab
   - Add these variables:
     ```
     GOOGLE_API_KEY=your_google_places_api_key_here
     FLASK_ENV=production
     ```

4. **Deploy:**
   - Railway will automatically deploy your app
   - Wait for deployment to complete (2-3 minutes)

## Step 4: Access Your Live App

1. **Get Your App URL:**
   - In Railway dashboard, click on your app
   - Copy the generated URL (e.g., `https://your-app-name.railway.app`)

2. **Test Your App:**
   - Visit the URL in your browser
   - Try searching for restaurants in different locations

## Step 5: Custom Domain (Optional)

1. **In Railway Dashboard:**
   - Go to "Settings" tab
   - Click "Custom Domains"
   - Add your domain (e.g., `restaurants.yourdomain.com`)

2. **Update DNS:**
   - Point your domain to Railway's servers
   - Follow Railway's DNS instructions

## 🎉 Your App is Live!

**Cost Breakdown:**
- ✅ **Hosting**: FREE (Railway free tier)
- ✅ **Domain**: FREE (Railway provides subdomain)
- ✅ **SSL**: FREE (automatic HTTPS)
- 💰 **API Costs**: ~$0.022 per search (with caching)

**Expected Monthly Costs:**
- 100 users, 1 search/day: ~$66/month
- 200 users, 2 searches/day: ~$264/month

## 🔧 Troubleshooting

### If deployment fails:
1. Check Railway logs for errors
2. Verify your API key is correct
3. Make sure all files are committed to GitHub

### If app doesn't work:
1. Check environment variables in Railway
2. Verify Google APIs are enabled
3. Check API key restrictions

### If you need help:
- Check Railway documentation
- Review Google Cloud Console setup
- Check the app logs in Railway dashboard

## 📈 Next Steps

1. **Monitor Usage:**
   - Check Railway dashboard for app performance
   - Monitor Google Cloud Console for API usage

2. **Optimize Costs:**
   - Implement user quotas if needed
   - Extend cache duration
   - Add premium features for revenue

3. **Scale Up:**
   - Add more features
   - Implement user accounts
   - Add restaurant partnerships

## 🎯 Success Metrics

Your app is successfully deployed when:
- ✅ App loads without errors
- ✅ Restaurant search works
- ✅ Photos load correctly
- ✅ Location detection works
- ✅ Filters work properly

**Your app URL will be:** `https://your-app-name.railway.app` 