# Free Deployment Guide for SmartRecon-AI

## Option 1: Oracle Cloud Always Free (RECOMMENDED) ⭐

**Why Oracle Cloud?**
- ✅ **FREE FOREVER** (not a trial!)
- ✅ **4 CPU cores + 24GB RAM** (on ARM VM)
- ✅ **200GB storage + 10TB transfer/month**
- ✅ **No credit card charges** (after initial verification)
- ✅ **Runs entire Docker Compose stack**

### Setup Steps:

#### 1. Create Oracle Cloud Account
1. Go to: https://cloud.oracle.com/free
2. Sign up (requires credit card for verification, but won't be charged)
3. Wait for account activation (5-10 minutes)

#### 2. Create VM Instance
1. Go to: **Compute** → **Instances** → **Create Instance**
2. **Name**: smartrecon-ai
3. **Image**: Ubuntu 22.04 (minimal)
4. **Shape**: 
   - Click "Change Shape"
   - Select **Ampere (ARM)** → **VM.Standard.A1.Flex**
   - Set: **4 OCPUs, 24GB RAM** (all free!)
5. **Networking**: 
   - Create new VCN (default settings)
   - Assign public IP: ✅ Yes
6. **SSH Keys**: Upload your public key or generate new
7. Click **Create**

#### 3. Configure Firewall
1. Go to **Virtual Cloud Networks** → Your VCN → **Security Lists**
2. Click **Default Security List** → **Add Ingress Rules**:
   - **CIDR**: 0.0.0.0/0
   - **Destination Port**: 22 (SSH)
   - Add more rules for: 80, 443, 8000, 3000

#### 4. Deploy SmartRecon-AI
```bash
# SSH into your VM
ssh ubuntu@<your-vm-public-ip>

# Download and run deployment script
curl -o deploy.sh https://raw.githubusercontent.com/yourusername/smartrecon-ai/main/deploy-oracle-free.sh
chmod +x deploy.sh
./deploy.sh
```

**Or deploy manually:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Clone repo
git clone https://github.com/yourusername/smartrecon-ai.git
cd smartrecon-ai

# Configure
cp .env.example .env
nano .env  # Update secrets and set HOST=0.0.0.0

# Deploy
docker-compose up -d

# Initialize database
docker-compose exec api python -c "
from app.core.database import SessionLocal, Base, engine
Base.metadata.create_all(bind=engine)
"

# Create admin user
docker-compose exec api python -c "
from app.core.database import SessionLocal
from app.models import User, Role
from app.core.security import get_password_hash
db = SessionLocal()
role = Role(name='admin', description='Admin', permissions={'all': True})
db.add(role)
db.commit()
user = User(email='admin@smartrecon.local', username='admin', hashed_password=get_password_hash('changeme123'), role_id=role.id, is_active=True)
db.add(user)
db.commit()
"
```

#### 5. Access Your Deployment
```
API: http://<your-vm-ip>:8000
Swagger: http://<your-vm-ip>:8000/docs
Frontend: http://<your-vm-ip>:3000
```

---

## Option 2: Fly.io (Limited but Easy)

**Limitations**: 
- Only 256MB RAM per VM (can run API only)
- Need external database (use Supabase free PostgreSQL)

### Setup:
```powershell
# Install Fly CLI
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"

# Login
fly auth login

# Create fly.toml
fly launch --no-deploy

# Deploy
fly deploy
```

**fly.toml:**
```toml
app = "smartrecon-api"
primary_region = "iad"

[build]
  dockerfile = "backend/Dockerfile"

[env]
  PORT = "8000"
  DATABASE_URL = "your-external-db-url"
  REDIS_URL = "your-external-redis-url"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

**Free External Services:**
- PostgreSQL: https://supabase.com (500MB free)
- Redis: https://upstash.com (10K commands/day free)

---

## Option 3: Render.com

**Limitations**: 
- Services spin down after 15 min inactivity (slow cold starts)
- PostgreSQL expires after 90 days (need to migrate)

### Setup:
1. Push code to GitHub
2. Go to: https://render.com
3. **New** → **Web Service**
4. Connect GitHub repo
5. Configure:
   - **Name**: smartrecon-api
   - **Runtime**: Docker
   - **Dockerfile Path**: backend/Dockerfile
   - **Plan**: Free
6. Add **PostgreSQL** database (free tier)
7. Use Upstash for Redis

---

## Option 4: Railway.app ($5/month credit)

**Best for**: Quick testing (not truly free but easiest)

### Setup:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Deploy
railway init
railway up
```

1. Go to: https://railway.app
2. Connect GitHub repo
3. Deploy entire docker-compose (automatically detected!)
4. Get $5 free credit monthly (~140 hours runtime)

---

## Comparison Table:

| Platform | RAM | Storage | Database | Redis | Docker Compose | Forever Free |
|----------|-----|---------|----------|-------|----------------|--------------|
| **Oracle Cloud** | 24GB | 200GB | ✅ | ✅ | ✅ | ✅ |
| Fly.io | 256MB | 3GB | ❌ | ❌ | ❌ | ✅ |
| Render.com | 512MB | Limited | ✅ 90d | ❌ | ❌ | ⚠️ |
| Railway | Varies | Varies | ✅ | ✅ | ✅ | ❌ ($5/mo) |

---

## My Recommendation:

### For Full Production (Free Forever):
**Use Oracle Cloud Always Free** - It's genuinely free forever and powerful enough to run everything. The 24GB RAM ARM VM is better than most paid $50/month VPS services.

### For Quick Demo (Easiest):
**Use Railway.app** - $5 credit gets you ~140 hours/month. Perfect for demos and testing. Automatically deploys Docker Compose.

### For API Only (No Workers):
**Use Render.com** + external DB/Redis from Supabase/Upstash.

---

## Post-Deployment Checklist:

```bash
# 1. Verify services
docker-compose ps

# 2. Check health
curl http://your-ip:8000/health

# 3. Test authentication
curl -X POST http://your-ip:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=changeme123"

# 4. Setup SSL (optional but recommended)
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com

# 5. Setup monitoring
docker-compose logs -f

# 6. Backup database
docker-compose exec db pg_dump -U smartrecon smartrecon > backup.sql
```

---

## Cost Estimate (if you outgrow free tier):

- **DigitalOcean Droplet**: $6-12/month (1-2GB RAM)
- **Hetzner Cloud**: €4-8/month (2-4GB RAM)
- **AWS Lightsail**: $10-20/month (2-4GB RAM)
- **Linode**: $10-20/month (2-4GB RAM)

---

**Need Help?** Check DEPLOYMENT.md for detailed production deployment guide.
