#!/bin/bash

# Restaurant Discovery App Deployment Script
echo "🚀 Deploying Restaurant Discovery App..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway..."
    railway login
fi

# Deploy to Railway
echo "📦 Deploying to Railway..."
railway up

# Set environment variables
echo "🔧 Setting environment variables..."
echo "Please set your GOOGLE_API_KEY in Railway dashboard:"
echo "1. Go to your project in Railway"
echo "2. Click on 'Variables' tab"
echo "3. Add: GOOGLE_API_KEY=your_google_places_api_key_here"
echo "4. Add: FLASK_ENV=production"

echo "✅ Deployment complete!"
echo "🌐 Your app should be live at: https://your-app-name.railway.app" 