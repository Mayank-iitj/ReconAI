# Deploy SmartRecon-AI to Railway

This guide will help you deploy SmartRecon-AI to Railway for free (with $5 monthly credit).

## Prerequisites

- GitHub account
- Railway account (sign up at https://railway.app)
- Push your code to GitHub

## Deployment Steps

### Method 1: Deploy via Railway Dashboard (Recommended)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/smartrecon-ai.git
   git push -u origin main
   ```

2. **Connect to Railway**
   - Go to https://railway.app
   - Click "Start a New Project"
   - Select "Deploy from GitHub repo"
   - Authorize Railway to access your GitHub
   - Select your `smartrecon-ai` repository

3. **Add Services**

   Railway will automatically detect your `docker-compose.yml` and create services. Configure each:

   #### A. PostgreSQL Database
   - Click "+ New" → "Database" → "PostgreSQL"
   - Railway will auto-provision it
   - Note: Connection variables are auto-injected

   #### B. Redis
   - Click "+ New" → "Database" → "Redis"
   - Railway will auto-provision it
   - Connection variables auto-injected

   #### C. API Service
   - Railway auto-detects from `docker-compose.yml`
   - Click on "api" service
   - Go to "Settings" → "Environment"
   - Add variables:
     ```
     PORT=8000
     JWT_SECRET=<generate-with-openssl-rand-hex-32>
     ADMIN_EMAIL=admin@smartrecon.local
     ADMIN_PASSWORD=<your-secure-password>
     OPENAI_API_KEY=<your-key-optional>
     ```
   - Go to "Settings" → "Deploy"
   - Set Custom Start Command: `sh railway-start.sh`
   - Click "Deploy"

   #### D. Worker Service
   - Click on "worker" service
   - Environment variables are shared from project
   - Click "Deploy"

   #### E. Frontend (Optional)
   - Click on "frontend" service
   - Go to "Settings" → "Environment"
   - Add:
     ```
     NEXT_PUBLIC_API_URL=<your-api-url-from-railway>
     ```
   - Click "Deploy"

4. **Generate Domain**
   - Click on "api" service
   - Go to "Settings" → "Networking"
   - Click "Generate Domain"
   - Copy the URL (e.g., `smartrecon-api-production.up.railway.app`)

5. **Update Frontend API URL**
   - Go to "frontend" service settings
   - Update `NEXT_PUBLIC_API_URL` with the API domain
   - Redeploy frontend

6. **Test Deployment**
   - Visit: `https://your-api-domain.up.railway.app/health`
   - Visit: `https://your-api-domain.up.railway.app/docs`
   - Login with your admin credentials

### Method 2: Deploy via Railway CLI

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Link to your project (or create new)
railway link

# Add PostgreSQL
railway add --database postgresql

# Add Redis
railway add --database redis

# Set environment variables
railway variables set JWT_SECRET=$(openssl rand -hex 32)
railway variables set ADMIN_PASSWORD=YourSecurePassword123
railway variables set PORT=8000

# Deploy
railway up

# Deploy specific service
railway up --service api
railway up --service worker
railway up --service frontend

# Open in browser
railway open
```

## Environment Variables Configuration

Add these to your Railway project settings:

### Required Variables:
```bash
# Application
PORT=8000
ENVIRONMENT=production

# Database (auto-injected by Railway)
DATABASE_URL=${DATABASE_URL}

# Redis (auto-injected by Railway)
REDIS_URL=${REDIS_URL}

# Security
JWT_SECRET=<generate-random-string>
JWT_EXPIRATION_HOURS=24
ADMIN_EMAIL=admin@smartrecon.local
ADMIN_PASSWORD=<strong-password>

# CORS (use your Railway domains)
CORS_ORIGINS=["https://your-frontend.railway.app"]

# Optional: LLM APIs
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=...
ANTHROPIC_API_KEY=...
GROQ_API_KEY=...
```

### Generate Secrets:
```bash
# JWT Secret
openssl rand -hex 32

# Admin Password
openssl rand -base64 16
```

## Railway-Specific Configuration

### Service Configuration

#### API Service
- **Build Command**: Auto-detected from Dockerfile
- **Start Command**: `sh railway-start.sh`
- **Health Check**: `https://$RAILWAY_PUBLIC_DOMAIN/health`
- **Port**: 8000

#### Worker Service
- **Build Command**: Auto-detected
- **Start Command**: `celery -A app.worker.tasks worker --loglevel=info`
- **No public port needed**

#### Frontend Service
- **Build Command**: `npm run build`
- **Start Command**: `npm start`
- **Port**: 3000

### Database Migration

Railway automatically handles database provisioning. The `railway-start.sh` script:
1. Waits for database to be ready
2. Creates all tables
3. Seeds admin user
4. Starts the API

## Cost & Limits

### Free Tier ($5 credit/month):
- ~140 hours of usage
- Suitable for:
  - Development/testing
  - Light personal use
  - Demos

### Usage Tips:
- Enable "Sleep on idle" to save credits
- Monitor usage in Railway dashboard
- Upgrade to Hobby plan ($5/month) for 24/7 uptime

## Monitoring

### View Logs:
```bash
# Via CLI
railway logs

# Via Dashboard
Go to service → "Deployments" → Click on deployment → "View Logs"
```

### Check Status:
```bash
railway status
```

### Restart Services:
```bash
railway restart
```

## Troubleshooting

### Database Not Connecting
```bash
# Check DATABASE_URL is set
railway variables

# Test connection
railway run python -c "
from app.core.database import engine
with engine.connect() as conn:
    print('✅ Database connected!')
"
```

### Worker Not Processing Tasks
```bash
# Check Redis connection
railway logs --service worker

# Restart worker
railway restart --service worker
```

### API Returns 500 Error
```bash
# Check logs
railway logs --service api

# Run database init manually
railway run python -c "
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
"
```

## Upgrading to Production

For production use (24/7 uptime):

1. **Upgrade to Hobby Plan** ($5/month per service)
2. **Add Custom Domain**:
   - Go to Settings → Networking → Custom Domain
   - Add your domain
   - Update DNS records as shown

3. **Enable Monitoring**:
   ```bash
   # Add Sentry for error tracking
   railway variables set SENTRY_DSN=<your-sentry-dsn>
   ```

4. **Setup Backups**:
   - Railway PostgreSQL includes daily backups
   - Export manually: `railway run pg_dump > backup.sql`

5. **Scale Resources** (if needed):
   - Go to Settings → Resources
   - Increase RAM/CPU limits

## Alternative: Deploy Individual Services

If you want to use Railway's free PostgreSQL + Redis but deploy API elsewhere:

```bash
# Create Railway project with just databases
railway init
railway add --database postgresql
railway add --database redis

# Get connection strings
railway variables

# Use these URLs in your external deployment
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
```

## Support

- Railway Docs: https://docs.railway.app
- SmartRecon-AI Issues: https://github.com/yourusername/smartrecon-ai/issues
- Railway Discord: https://discord.gg/railway

---

## Quick Reference Commands

```bash
# Deploy all services
railway up

# Deploy specific service
railway up --service api

# View logs
railway logs --service api

# Open dashboard
railway open

# SSH into container
railway shell

# Run one-off command
railway run python manage.py

# Check variables
railway variables

# Set variable
railway variables set KEY=value

# Delete variable
railway variables delete KEY

# Restart service
railway restart --service api

# View status
railway status
```

---

**🎉 Your SmartRecon-AI is now deployed on Railway!**

Access your deployment:
- API: `https://your-project.up.railway.app`
- Docs: `https://your-project.up.railway.app/docs`
- Frontend: `https://your-frontend.up.railway.app`
