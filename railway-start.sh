#!/bin/bash
# Railway deployment initialization script

set -e

echo "🚂 Railway Deployment - Initializing Database..."

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
until PGPASSWORD=$PGPASSWORD psql -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" -c '\q' 2>/dev/null; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 2
done

echo "✅ PostgreSQL is ready!"

# Run database migrations and create tables
python -c "
from app.core.database import SessionLocal, Base, engine
from app.models import User, Role
from app.core.security import get_password_hash
import os

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
            email='admin@smartrecon.local',
            username='admin',
            hashed_password=get_password_hash(admin_password),
            role_id=admin_role.id,
            is_active=True
        )
        db.add(admin_user)
        db.commit()
        print('✅ Admin user created!')
    else:
        print('✅ Admin user already exists')
finally:
    db.close()

print('🚀 Database initialization complete!')
"

# Start the application
echo "🚀 Starting SmartRecon-AI API..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
