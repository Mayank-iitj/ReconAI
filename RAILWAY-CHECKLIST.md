# Railway Deployment Checklist

## Pre-Deployment

- [ ] Code pushed to GitHub
- [ ] Railway account created (https://railway.app)
- [ ] Railway CLI installed: `npm install -g @railway/cli`

## Deployment Steps

### 1. Quick Deploy (Automatic)
```bash
# Login to Railway
railway login

# Initialize and deploy
railway init

# Add PostgreSQL
railway add --database postgresql

# Add Redis  
railway add --database redis

# Generate and set secrets
railway variables set JWT_SECRET=$(openssl rand -hex 32)
railway variables set ADMIN_PASSWORD=$(openssl rand -base64 16)
railway variables set PORT=8000

# Deploy all services
railway up
```

### 2. Dashboard Deploy (Visual)
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your `smartrecon-ai` repository
4. Railway auto-detects docker-compose.yml
5. Add PostgreSQL database (+ New → Database → PostgreSQL)
6. Add Redis (+ New → Database → Redis)
7. Configure environment variables in each service
8. Deploy!

## Required Environment Variables

Copy these to Railway project settings (replace placeholders):

```bash
PORT=8000
ENVIRONMENT=production
JWT_SECRET=<generate-with-openssl-rand-hex-32>
ADMIN_PASSWORD=<your-strong-password>
ADMIN_EMAIL=admin@smartrecon.local
ADMIN_USERNAME=admin
```

## Post-Deployment

- [ ] Get API domain from Railway dashboard
- [ ] Test health endpoint: `https://your-app.railway.app/health`
- [ ] Test API docs: `https://your-app.railway.app/docs`
- [ ] Login with admin credentials
- [ ] Update frontend `NEXT_PUBLIC_API_URL` with API domain
- [ ] Test creating a target
- [ ] Test creating a scan

## Monitoring

```bash
# View logs
railway logs

# Check status
railway status

# Open dashboard
railway open

# Restart if needed
railway restart
```

## Cost Management

- Free tier: $5 credit/month (~140 hours)
- Enable sleep mode to save credits
- Upgrade to Hobby ($5/month) for 24/7 uptime

## Troubleshooting

### Database not connecting
```bash
railway variables  # Check DATABASE_URL is set
railway logs --service api  # Check connection errors
```

### Worker not processing
```bash
railway logs --service worker
railway restart --service worker
```

### API returns errors
```bash
railway logs --service api
railway run python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

## Files Created for Railway

✅ `railway.json` - Service configuration
✅ `.railwayignore` - Files to exclude
✅ `railway-start.sh` - Initialization script
✅ `.env.railway` - Environment variable template
✅ `RAILWAY-DEPLOY.md` - Complete deployment guide
✅ `deploy-railway.sh` - Automated deployment script

## Quick Commands

```bash
# Deploy specific service
railway up --service api

# View service logs
railway logs --service api

# SSH into container
railway shell

# Run database migration
railway run python -c "from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)"

# Restart service
railway restart --service api

# Open in browser
railway open
```

## Success Criteria

✅ API returns 200 on `/health`
✅ Swagger docs accessible at `/docs`
✅ Can login with admin credentials
✅ Can create targets via API
✅ Worker processes background tasks
✅ Frontend connects to API

---

**Ready to deploy!** Run `bash deploy-railway.sh` or see [RAILWAY-DEPLOY.md](RAILWAY-DEPLOY.md) for detailed instructions.
