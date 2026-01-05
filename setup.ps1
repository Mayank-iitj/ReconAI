# PowerShell Setup Script for SmartRecon-AI

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "SmartRecon-AI - Quick Setup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check prerequisites
Write-Host "[1/8] Checking prerequisites..." -ForegroundColor Yellow
$dockerInstalled = Get-Command docker -ErrorAction SilentlyContinue
$dockerComposeInstalled = Get-Command docker-compose -ErrorAction SilentlyContinue

if (-not $dockerInstalled) {
    Write-Host "Error: Docker is required but not installed." -ForegroundColor Red
    exit 1
}

if (-not $dockerComposeInstalled) {
    Write-Host "Error: Docker Compose is required but not installed." -ForegroundColor Red
    exit 1
}

Write-Host "✓ Prerequisites met" -ForegroundColor Green
Write-Host ""

# Create environment file
Write-Host "[2/8] Setting up environment file..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "✓ Created .env file" -ForegroundColor Green
    Write-Host "⚠️  IMPORTANT: Edit .env and set your API keys and passwords!" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to continue after editing .env"
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}
Write-Host ""

# Create required directories
Write-Host "[3/8] Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "storage" | Out-Null
New-Item -ItemType Directory -Force -Path "reports" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
Write-Host "✓ Directories created" -ForegroundColor Green
Write-Host ""

# Build recon tools image
Write-Host "[4/8] Building recon tools container..." -ForegroundColor Yellow
docker build -t smartrecon/tools:latest -f docker/tools/Dockerfile docker/tools/
Write-Host "✓ Recon tools container built" -ForegroundColor Green
Write-Host ""

# Build application containers
Write-Host "[5/8] Building application containers..." -ForegroundColor Yellow
docker-compose build
Write-Host "✓ Application containers built" -ForegroundColor Green
Write-Host ""

# Start services
Write-Host "[6/8] Starting services..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "✓ Services started" -ForegroundColor Green
Write-Host ""

# Wait for database
Write-Host "[7/8] Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10
Write-Host "✓ Database ready" -ForegroundColor Green
Write-Host ""

# Run database migrations
Write-Host "[8/8] Running database migrations..." -ForegroundColor Yellow
docker-compose exec -T api alembic upgrade head
Write-Host "✓ Database migrated" -ForegroundColor Green
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Services are now running:" -ForegroundColor White
Write-Host "  • Frontend:    http://localhost:3000" -ForegroundColor Cyan
Write-Host "  • API:         http://localhost:8000" -ForegroundColor Cyan
Write-Host "  • API Docs:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  • Flower:      http://localhost:5555" -ForegroundColor Cyan
Write-Host ""
Write-Host "Default admin credentials:" -ForegroundColor White
Write-Host "  Username: admin" -ForegroundColor Cyan
Write-Host "  Password: (check your .env file)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor White
Write-Host "  • View logs:        docker-compose logs -f" -ForegroundColor Gray
Write-Host "  • Stop services:    docker-compose down" -ForegroundColor Gray
Write-Host "  • Restart:          docker-compose restart" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  IMPORTANT REMINDERS:" -ForegroundColor Yellow
Write-Host "  1. Change the default admin password" -ForegroundColor White
Write-Host "  2. Set a strong JWT_SECRET in .env" -ForegroundColor White
Write-Host "  3. Configure your LLM API keys" -ForegroundColor White
Write-Host "  4. Always obtain authorization before scanning" -ForegroundColor White
Write-Host ""
Write-Host "Happy hunting! 🎯" -ForegroundColor Green
