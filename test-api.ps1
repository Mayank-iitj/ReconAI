# SmartRecon-AI Test Script
# This script demonstrates the basic workflow

Write-Host "`n=== SmartRecon-AI Test ===" -ForegroundColor Cyan
Write-Host "Testing API endpoints...`n" -ForegroundColor White

# 1. Test health endpoint
Write-Host "[1/5] Testing health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health"
    Write-Host "✅ API is healthy: $($health.status)" -ForegroundColor Green
    Write-Host "   Version: $($health.version)`n" -ForegroundColor Gray
} catch {
    Write-Host "❌ API health check failed" -ForegroundColor Red
    exit 1
}

# 2. Login
Write-Host "[2/5] Authenticating..." -ForegroundColor Yellow
try {
    $body = "username=admin&password=changeme123"
    $login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
        -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
    $headers = @{"Authorization" = "Bearer $($login.access_token)"}
    Write-Host "✅ Authenticated successfully`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nNote: You may need to initialize the database first." -ForegroundColor Yellow
    Write-Host "Run: docker-compose exec api python -c 'from app.core.database import Base, engine; Base.metadata.create_all(bind=engine)'" -ForegroundColor Gray
    exit 1
}

# 3. Create a test target
Write-Host "[3/5] Creating test target..." -ForegroundColor Yellow
try {
    $target = @{
        name = "Test Target - Example.com"
        description = "Test target for demonstration"
        root_domains = @("example.com")
        in_scope = @("*.example.com")
        out_of_scope = @("admin.example.com")
        ip_ranges = @()
        authorized = $true
        authorization_proof = "Test authorization - educational demo"
        tags = @("test", "demo")
        priority = 3
    } | ConvertTo-Json

    $targetResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/targets" `
        -Method POST -Body $target -Headers $headers -ContentType "application/json"
    
    $targetId = $targetResult.id
    Write-Host "✅ Target created: ID $targetId" -ForegroundColor Green
    Write-Host "   Name: $($targetResult.name)`n" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to create target: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 4. List targets
Write-Host "[4/5] Listing all targets..." -ForegroundColor Yellow
try {
    $targets = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/targets" -Headers $headers
    Write-Host "✅ Found $($targets.total) target(s)" -ForegroundColor Green
    
    if ($targets.items.Count -gt 0) {
        Write-Host "`n   Targets:" -ForegroundColor Gray
        foreach ($t in $targets.items) {
            Write-Host "   - ID: $($t.id) | Name: $($t.name) | Created: $($t.created_at)" -ForegroundColor Gray
        }
    }
    Write-Host ""
} catch {
    Write-Host "❌ Failed to list targets: $($_.Exception.Message)" -ForegroundColor Red
}

# 5. Get target details
Write-Host "[5/5] Getting target details..." -ForegroundColor Yellow
try {
    $targetDetail = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/targets/$targetId" -Headers $headers
    Write-Host "✅ Target details retrieved" -ForegroundColor Green
    Write-Host "`n   Target Information:" -ForegroundColor Gray
    Write-Host "   ID:          $($targetDetail.id)" -ForegroundColor Gray
    Write-Host "   Name:        $($targetDetail.name)" -ForegroundColor Gray
    Write-Host "   Status:      $($targetDetail.status)" -ForegroundColor Gray
    Write-Host "   Domains:     $($targetDetail.scope.root_domains -join ', ')" -ForegroundColor Gray
    Write-Host "   Created:     $($targetDetail.created_at)" -ForegroundColor Gray
    Write-Host "   Tags:        $($targetDetail.tags -join ', ')`n" -ForegroundColor Gray
} catch {
    Write-Host "❌ Failed to get target details: $($_.Exception.Message)" -ForegroundColor Red
}

# Summary
Write-Host "`n=== Test Complete ===" -ForegroundColor Cyan
Write-Host "`nNext Steps:" -ForegroundColor White
Write-Host "1. Open http://localhost:8000/docs to explore all API endpoints" -ForegroundColor Gray
Write-Host "2. Create a scan for target ID $targetId" -ForegroundColor Gray
Write-Host "3. Monitor scan progress and view findings" -ForegroundColor Gray
Write-Host "4. Generate professional reports`n" -ForegroundColor Gray

Write-Host "Full documentation: QUICKSTART.md" -ForegroundColor Yellow
Write-Host "Frontend UI: http://localhost:3000`n" -ForegroundColor Yellow
