#!/bin/bash

echo "🚀 Restaurant Discovery App - Deployment Setup"
echo "=============================================="
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
else
    echo "✅ Railway CLI is installed"
fi

echo ""
echo "📋 Next Steps:"
echo "=============="
echo ""
echo "1. 🔑 Get Google Places API Key:"
echo "   - Go to: https://console.cloud.google.com/"
echo "   - Create a new project"
echo "   - Enable: Places API, Geocoding API, Maps JavaScript API"
echo "   - Create API key and restrict it to these APIs"
echo ""
echo "2. 📝 Create GitHub Repository:"
echo "   - Go to: https://github.com/"
echo "   - Create new repository: restaurant-discovery-app"
echo "   - Make it PUBLIC"
echo ""
echo "3. 🔗 Connect to GitHub:"
echo "   Run these commands (replace YOUR_USERNAME):"
echo "   git remote add origin https://github.com/YOUR_USERNAME/restaurant-discovery-app.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "4. 🚂 Deploy to Railway:"
echo "   - Go to: https://railway.app/"
echo "   - Sign up with GitHub"
echo "   - Create new project from GitHub repo"
echo "   - Add environment variables:"
echo "     GOOGLE_API_KEY=your_api_key_here"
echo "     FLASK_ENV=production"
echo ""
echo "5. 🎉 Your app will be live at: https://your-app-name.railway.app"
echo ""
echo "💡 Need help? Check DEPLOYMENT_STEPS.md for detailed instructions"
echo "" 