# Deployment Guide for SmartRecon-AI

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Development Deployment](#development-deployment)
3. [Production Deployment](#production-deployment)
4. [Kubernetes Deployment](#kubernetes-deployment)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software
- Docker 20.10+ and Docker Compose 2.0+
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- PostgreSQL 15+
- Redis 7+

### System Requirements
**Minimum (Development):**
- 4 CPU cores
- 8 GB RAM
- 50 GB disk space

**Recommended (Production):**
- 8+ CPU cores
- 16+ GB RAM
- 200+ GB disk space (for scan outputs and reports)

## Development Deployment

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/smartrecon-ai.git
cd smartrecon-ai
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings:
nano .env
```

**Critical settings to configure:**
- `JWT_SECRET`: Generate a strong secret key
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `OPENAI_API_KEY` (or other LLM provider key)
- `ADMIN_PASSWORD`: Set a strong admin password

### 3. Build and Start Services
```bash
# Build all containers
docker-compose build

# Start services
docker-compose up -d

# Check service status
docker-compose ps
```

### 4. Initialize Database
```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Create admin user (automatically created from .env)
# Verify with:
docker-compose exec api python -c "from app.core.database import init_db; init_db()"
```

### 5. Build Recon Tools Container
```bash
cd docker/tools
docker build -t smartrecon/tools:latest .
cd ../..
```

### 6. Access Services
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Flower (Celery monitor)**: http://localhost:5555
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### 7. Login
Use credentials from `.env`:
- Username: `admin` (or value from `ADMIN_USERNAME`)
- Password: Value from `ADMIN_PASSWORD`

## Production Deployment

### 1. Prepare Environment

**Create production `.env` file:**
```bash
cp .env.example .env.prod
```

**Update critical production settings:**
```env
# Security
JWT_SECRET=<generate-strong-random-secret>
DEBUG=false
API_RELOAD=false

# Database
DATABASE_URL=postgresql://user:secure_password@db:5432/smartrecon

# LLM API Keys (use secure secret management)
OPENAI_API_KEY=<your-key>

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
SENTRY_DSN=<your-sentry-dsn>  # Optional

# Resource limits
MAX_CONCURRENT_SCANS=10
CELERY_WORKER_CONCURRENCY=8
```

### 2. Build Production Images
```bash
# Backend API
docker build -t smartrecon/api:v1.0.0 -f backend/Dockerfile backend/

# Frontend
docker build -t smartrecon/frontend:v1.0.0 -f frontend/Dockerfile frontend/

# Recon tools
docker build -t smartrecon/tools:v1.0.0 -f docker/tools/Dockerfile docker/tools/

# Tag as latest
docker tag smartrecon/api:v1.0.0 smartrecon/api:latest
docker tag smartrecon/frontend:v1.0.0 smartrecon/frontend:latest
docker tag smartrecon/tools:v1.0.0 smartrecon/tools:latest
```

### 3. Deploy with Docker Compose
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=5
```

### 4. SSL/TLS Configuration

**Using Let's Encrypt with Certbot:**
```bash
# Generate certificates
docker run -it --rm -v $(pwd)/nginx/ssl:/etc/letsencrypt \
  certbot/certbot certonly --standalone \
  -d yourdomain.com \
  --email admin@yourdomain.com \
  --agree-tos

# Update nginx.conf to use SSL
```

**nginx.conf for SSL:**
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 5. Database Backups

**Automated backup script:**
```bash
#!/bin/bash
# backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
CONTAINER_NAME="smartrecon-db"

docker exec -t $CONTAINER_NAME pg_dump -U smartrecon smartrecon | gzip > "$BACKUP_DIR/smartrecon_$DATE.sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "smartrecon_*.sql.gz" -mtime +30 -delete
```

**Schedule with cron:**
```bash
0 2 * * * /path/to/backup-db.sh
```

### 6. Monitoring Setup

**Add Prometheus metrics collection:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'smartrecon-api'
    static_configs:
      - targets: ['api:9090']
```

**Grafana dashboard:** Import pre-built dashboard from `monitoring/grafana-dashboard.json`

### 7. Health Checks

```bash
# Check API health
curl https://yourdomain.com/health

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api worker
```

## Kubernetes Deployment

### 1. Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3+ (optional but recommended)

### 2. Create Namespace
```bash
kubectl create namespace smartrecon
kubectl config set-context --current --namespace=smartrecon
```

### 3. Deploy PostgreSQL
```bash
kubectl apply -f k8s/postgres.yaml
```

### 4. Deploy Redis
```bash
kubectl apply -f k8s/redis.yaml
```

### 5. Create ConfigMap and Secrets
```bash
# Create secret for sensitive data
kubectl create secret generic smartrecon-secrets \
  --from-literal=jwt-secret=<your-secret> \
  --from-literal=db-password=<db-password> \
  --from-literal=openai-api-key=<api-key>

# Create ConfigMap for non-sensitive config
kubectl create configmap smartrecon-config \
  --from-file=.env.prod
```

### 6. Deploy API and Workers
```bash
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/worker.yaml
```

### 7. Deploy Frontend
```bash
kubectl apply -f k8s/frontend.yaml
```

### 8. Expose Services
```bash
kubectl apply -f k8s/ingress.yaml
```

### 9. Verify Deployment
```bash
kubectl get pods
kubectl get services
kubectl logs -f deployment/smartrecon-api
```

## Configuration

### Environment Variables Reference

See [.env.example](.env.example) for all available options.

**Critical Security Settings:**
- `JWT_SECRET`: Strong random string (use `openssl rand -base64 32`)
- `ADMIN_PASSWORD`: Strong password for admin account
- `DATABASE_URL`: PostgreSQL connection with strong password
- `REQUIRE_EXPLICIT_AUTHORIZATION=true`: Always require authorization

**Performance Tuning:**
- `MAX_CONCURRENT_SCANS`: Limit concurrent scans per target
- `CELERY_WORKER_CONCURRENCY`: Workers per Celery process
- `HTTPX_THREADS`: HTTP probing concurrency
- `NUCLEI_CONCURRENCY`: Nuclei scanning concurrency

**Rate Limiting:**
- `DEFAULT_RATE_LIMIT`: Requests per second for tools
- `NUCLEI_RATE_LIMIT`: Nuclei-specific rate limit

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL logs
docker-compose logs db

# Test connection
docker-compose exec api python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

### Celery Worker Not Processing Tasks
```bash
# Check worker status
docker-compose logs worker

# Check Redis connection
docker-compose exec worker redis-cli -h redis ping

# Manually start worker for debugging
docker-compose exec worker celery -A app.worker.celery_app worker --loglevel=debug
```

### Recon Tools Not Working
```bash
# Check tools container
docker-compose exec recon-tools subfinder -version
docker-compose exec recon-tools nuclei -version

# Test tool manually
docker-compose exec recon-tools subfinder -d example.com
```

### High Memory Usage
- Reduce `CELERY_WORKER_CONCURRENCY`
- Limit `MAX_CONCURRENT_SCANS`
- Lower `HTTPX_THREADS` and `NUCLEI_CONCURRENCY`
- Add memory limits in docker-compose:
  ```yaml
  deploy:
    resources:
      limits:
        memory: 2G
  ```

### API Response Slow
- Enable caching: `LLM_ENABLE_CACHING=true`
- Add Redis caching layer
- Scale workers: `docker-compose up -d --scale worker=5`
- Use Gunicorn with multiple workers

### Permission Denied Errors
```bash
# Fix file permissions
sudo chown -R 1001:1001 storage/ reports/
sudo chmod -R 755 storage/ reports/
```

## Upgrading

### From Docker Compose
```bash
# Pull latest images
docker-compose pull

# Stop services
docker-compose down

# Run migrations
docker-compose run --rm api alembic upgrade head

# Restart services
docker-compose up -d
```

### Kubernetes Rolling Update
```bash
# Update image versions in k8s manifests
kubectl set image deployment/smartrecon-api api=smartrecon/api:v1.1.0

# Monitor rollout
kubectl rollout status deployment/smartrecon-api
```

## Security Hardening

1. **Use secrets management** (HashiCorp Vault, AWS Secrets Manager)
2. **Enable firewall** and restrict access to internal services
3. **Regular security updates**: `apt-get update && apt-get upgrade`
4. **Enable audit logging**: Set `LOG_FORMAT=json` and ship to SIEM
5. **Rate limiting**: Configure nginx rate limits
6. **Network segmentation**: Use Docker networks / K8s network policies
7. **Scan Docker images**: Use Trivy or similar tools

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/smartrecon-ai/issues
- Documentation: https://docs.smartrecon.ai
- Discord: https://discord.gg/smartrecon

---

**Remember**: Always test deployments in a staging environment first!
