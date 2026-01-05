#!/bin/bash
# Quick Railway deployment script

set -e

echo "🚂 Deploying SmartRecon-AI to Railway..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Login to Railway
echo "📝 Logging in to Railway..."
railway login

# Initialize project
echo "🎯 Initializing Railway project..."
railway init

# Add databases
echo "🗄️  Adding PostgreSQL..."
railway add --database postgresql

echo "📦 Adding Redis..."
railway add --database redis

# Generate secrets
echo "🔐 Generating secure secrets..."
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -base64 16)

echo ""
echo "Generated credentials (SAVE THESE!):"
echo "  Admin Password: $ADMIN_PASSWORD"
echo "  JWT Secret: $JWT_SECRET"
echo ""
read -p "Press Enter to continue..."

# Set environment variables
echo "⚙️  Setting environment variables..."
railway variables set PORT=8000
railway variables set ENVIRONMENT=production
railway variables set JWT_SECRET="$JWT_SECRET"
railway variables set ADMIN_PASSWORD="$ADMIN_PASSWORD"
railway variables set ADMIN_EMAIL=admin@smartrecon.local
railway variables set ADMIN_USERNAME=admin
railway variables set JWT_ALGORITHM=HS256
railway variables set JWT_EXPIRATION_HOURS=24

echo ""
echo "🚀 Deploying services..."

# Deploy API service
echo "  → Deploying API..."
railway up --service api

# Deploy Worker service  
echo "  → Deploying Worker..."
railway up --service worker

# Deploy Frontend (optional)
read -p "Deploy Frontend? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  → Deploying Frontend..."
    railway up --service frontend
fi

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "  1. Get your API URL: railway open"
echo "  2. Test API: https://your-domain.railway.app/health"
echo "  3. View logs: railway logs"
echo "  4. Monitor: railway dashboard"
echo ""
echo "🔗 Useful commands:"
echo "  • View all variables: railway variables"
echo "  • View logs: railway logs --service api"
echo "  • Restart: railway restart --service api"
echo "  • Open dashboard: railway open"
echo ""
