#!/bin/bash
# Railway deployment initialization script

set -e

echo "🚂 Railway Deployment - Starting..."

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  WARNING: DATABASE_URL not set!"
    echo "   Please add PostgreSQL database in Railway dashboard"
    echo "   Skipping database initialization..."
    echo ""
else
    echo "📦 Database URL detected"
    echo "⏳ Waiting for database to be ready (max 60s)..."
    
    # Wait for database with timeout
    TIMEOUT=60
    ELAPSED=0
    
    # Extract connection details from DATABASE_URL
    # Format: postgresql://user:pass@host:port/db
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\(.*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    while [ $ELAPSED -lt $TIMEOUT ]; do
        if python -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.getenv('DATABASE_URL'))
    conn.close()
    print('✅ Database connected!')
    exit(0)
except:
    exit(1)
" 2>/dev/null; then
            break
        fi
        echo "   Waiting for database at $DB_HOST:$DB_PORT..."
        sleep 3
        ELAPSED=$((ELAPSED + 3))
    done
    
    if [ $ELAPSED -ge $TIMEOUT ]; then
        echo "⚠️  Database connection timeout. Starting without initialization..."
    else
        echo "✅ Database is ready!"
    fi
fi

# Run database migrations and create tables
if [ ! -z "$DATABASE_URL" ]; then
    echo "🔧 Initializing database..."
    python -c "
from app.core.database import SessionLocal, Base, engine
from app.models import User, Role
from app.core.security import get_password_hash
import os

try:
    print('Creating database tables...')
    Base.metadata.create_all(bind=engine)
    print('✅ Tables created!')

    # Create admin user if not exists
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            print('Creating admin user...')
            admin_role = db.query(Role).filter(Role.name == 'admin').first()
            if not admin_role:
                admin_role = Role(
                    name='admin',
                    description='Administrator role',
                    permissions={'all': True}
                )
                db.add(admin_role)
                db.commit()
                db.refresh(admin_role)
            
            admin_password = os.getenv('ADMIN_PASSWORD', 'changeme123')
            admin_user = User(
                email=os.getenv('ADMIN_EMAIL', 'admin@smartrecon.local'),
                username=os.getenv('ADMIN_USERNAME', 'admin'),
                hashed_password=get_password_hash(admin_password),
                role_id=admin_role.id,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
            print('✅ Admin user created!')
            print(f'   Username: {admin_user.username}')
            print(f'   Email: {admin_user.email}')
        else:
            print('✅ Admin user already exists')
    finally:
        db.close()
    
    print('🚀 Database initialization complete!')
except Exception as e:
    print(f'⚠️  Database initialization error: {e}')
    print('   API will start but may have limited functionality')
"
else
    echo "⚠️  Skipping database initialization (no DATABASE_URL)"
fi

# Start the application
echo "🚀 Starting SmartRecon-AI API..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
