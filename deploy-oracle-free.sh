#!/bin/bash
# SmartRecon-AI Deployment Script for Oracle Cloud Always Free Tier
# This script deploys the full stack on a free ARM VM (4 cores, 24GB RAM!)

set -e

echo "=========================================="
echo "  SmartRecon-AI Oracle Cloud Deployment"
echo "=========================================="

# 1. Update system
echo "[1/7] Updating system..."
sudo apt update && sudo apt upgrade -y

# 2. Install Docker
echo "[2/7] Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
rm get-docker.sh

# 3. Install Docker Compose
echo "[3/7] Installing Docker Compose..."
sudo apt install docker-compose -y

# 4. Setup firewall
echo "[4/7] Configuring firewall..."
sudo apt install ufw -y
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8000/tcp  # API (temporary, use nginx later)
sudo ufw allow 3000/tcp  # Frontend (temporary)
echo "y" | sudo ufw enable

# 5. Clone repository
echo "[5/7] Setting up application..."
cd ~
git clone https://github.com/yourusername/smartrecon-ai.git || echo "Please push to GitHub first!"
cd smartrecon-ai

# 6. Configure environment
echo "[6/7] Configuring environment..."
cp .env.example .env

# Generate secure secrets
JWT_SECRET=$(openssl rand -hex 32)
ADMIN_PASSWORD=$(openssl rand -base64 16)

# Update .env with secure values
sed -i "s/your-super-secret-jwt-key-change-this-in-production/$JWT_SECRET/" .env
sed -i "s/changeme123/$ADMIN_PASSWORD/" .env
sed -i "s/localhost/0.0.0.0/g" .env

echo ""
echo "🔑 IMPORTANT - Save these credentials:"
echo "Admin Password: $ADMIN_PASSWORD"
echo ""
read -p "Press Enter to continue..."

# 7. Deploy
echo "[7/7] Starting services..."
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 10

# Initialize database
docker-compose exec -T api python -c "
from app.core.database import SessionLocal, Base, engine
from app.models import User, Role
from app.core.security import get_password_hash

# Create tables
Base.metadata.create_all(bind=engine)

# Create admin user
db = SessionLocal()
admin_role = Role(name='admin', description='Administrator', permissions={'all': True})
db.add(admin_role)
db.commit()

admin = User(
    email='admin@smartrecon.local',
    username='admin',
    hashed_password=get_password_hash('$ADMIN_PASSWORD'),
    role_id=admin_role.id,
    is_active=True
)
db.add(admin)
db.commit()
print('Admin user created!')
db.close()
"

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me)

echo ""
echo "=========================================="
echo "  ✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Access your instance:"
echo "  API: http://$PUBLIC_IP:8000"
echo "  API Docs: http://$PUBLIC_IP:8000/docs"
echo "  Frontend: http://$PUBLIC_IP:3000"
echo ""
echo "Credentials:"
echo "  Username: admin"
echo "  Password: $ADMIN_PASSWORD"
echo ""
echo "Next Steps:"
echo "  1. Test API: curl http://$PUBLIC_IP:8000/health"
echo "  2. Open Swagger UI: http://$PUBLIC_IP:8000/docs"
echo "  3. Configure domain/SSL (optional)"
echo ""
echo "Monitor services:"
echo "  docker-compose ps"
echo "  docker-compose logs -f"
echo ""
echo "=========================================="
