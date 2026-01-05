# SmartRecon-AI Usage Guide

## Quick Start

### 1. Start the Platform

```powershell
# Start all services
docker-compose up -d

# Wait for services to be healthy (30-60 seconds)
docker-compose ps
```

### 2. Access the Platform

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs (Swagger UI)
- **Frontend**: http://localhost:3000 (Next.js UI)

**Default Credentials:**
- Username: `admin`
- Password: `changeme123`

> ⚠️ **Security:** Change these credentials immediately in production!

### 3. Using the Swagger UI (Easiest Method)

1. Open http://localhost:8000/docs
2. Click the **"Authorize"** button (🔒 icon, top right)
3. Enter credentials:
   - Username: `admin`
   - Password: `changeme123`
4. Click **"Authorize"** then **"Close"**
5. You can now test all API endpoints directly in the browser!

### 4. Basic Workflow

#### Step 1: Create a Target

```powershell
# Get authentication token
$body = "username=admin&password=changeme123"
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
    -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"

$headers = @{"Authorization" = "Bearer $($login.access_token)"}

# Create target
$target = @{
    name = "HackerOne Bug Bounty"
    description = "Official HackerOne program"
    root_domains = @("hackerone.com", "hackerone.net")
    in_scope = @("*.hackerone.com", "*.hackerone.net")
    out_of_scope = @("admin.hackerone.com")
    authorized = $true
    authorization_proof = "https://hackerone.com/security"
    program_url = "https://hackerone.com/security"
    tags = @("bug-bounty", "high-priority")
    priority = 5
    rate_limit = 10
    max_concurrency = 5
} | ConvertTo-Json

$targetResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/targets" `
    -Method POST -Body $target -Headers $headers -ContentType "application/json"

Write-Host "Target created with ID: $($targetResult.id)"
```

#### Step 2: Create a Scan

```powershell
# Create a comprehensive scan
$scan = @{
    target_id = $targetResult.id
    name = "Initial Discovery Scan"
    scan_type = "comprehensive"
    enable_subdomain_discovery = $true
    enable_port_scan = $false
    enable_fuzzing = $true
    enable_nuclei = $true
    llm_config = @{
        provider = "openai"
        model = "gpt-4"
        temperature = 0.7
        enabled = $true
    }
    scheduled = $false
} | ConvertTo-Json -Depth 10

$scanResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
    -Method POST -Body $scan -Headers $headers -ContentType "application/json"

Write-Host "Scan created with ID: $($scanResult.id)"
Write-Host "Status: $($scanResult.status)"
```

#### Step 3: Monitor Scan Progress

```powershell
# Check scan status
$scanStatus = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$($scanResult.id)" `
    -Headers $headers

Write-Host "Scan Status: $($scanStatus.status)"
Write-Host "Progress: $($scanStatus.progress)%"
Write-Host "Subdomains found: $($scanStatus.stats.subdomains_found)"
Write-Host "HTTP services: $($scanStatus.stats.http_services_found)"

# Monitor in real-time with a loop
while ($scanStatus.status -eq "running") {
    Start-Sleep -Seconds 10
    $scanStatus = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$($scanResult.id)" `
        -Headers $headers
    Write-Host "[$([datetime]::Now.ToString('HH:mm:ss'))] Progress: $($scanStatus.progress)% - Status: $($scanStatus.status)"
}
```

#### Step 4: View Findings

```powershell
# Get all findings for the scan
$findings = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/findings?scan_id=$($scanResult.id)" `
    -Headers $headers

Write-Host "Total findings: $($findings.Count)"

# Show high-severity findings
$highSeverity = $findings | Where-Object { $_.severity -eq "high" -or $_.severity -eq "critical" }
$highSeverity | ForEach-Object {
    Write-Host "`n[$($_.severity.ToUpper())] $($_.title)"
    Write-Host "  Asset: $($_.asset_type) - $($_.asset_value)"
    Write-Host "  Description: $($_.description)"
}
```

#### Step 5: Generate Report

```powershell
# Create a professional PDF report
$report = @{
    scan_id = $scanResult.id
    title = "HackerOne Security Assessment Report"
    report_type = "full"
    format = "pdf"
    include_executive_summary = $true
    include_technical_details = $true
    severity_filter = @("critical", "high", "medium")
} | ConvertTo-Json

$reportResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reports" `
    -Method POST -Body $report -Headers $headers -ContentType "application/json"

Write-Host "Report generated: $($reportResult.filename)"
Write-Host "Download URL: http://localhost:8000$($reportResult.download_url)"
```

## Common Use Cases

### 1. Scheduled Reconnaissance

Run daily/weekly scans automatically:

```powershell
$scan = @{
    target_id = 1
    name = "Daily Discovery Scan"
    scan_type = "quick"
    enable_subdomain_discovery = $true
    scheduled = $true
    cron_schedule = "0 2 * * *"  # Every day at 2 AM
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
    -Method POST -Body $scan -Headers $headers -ContentType "application/json"
```

### 2. Multi-Target Scan

Scan multiple targets simultaneously:

```powershell
$targets = @("example1.com", "example2.com", "example3.com")

foreach ($domain in $targets) {
    $target = @{
        name = "Target - $domain"
        root_domains = @($domain)
        authorized = $true
        authorization_proof = "Program authorization"
    } | ConvertTo-Json
    
    $t = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/targets" `
        -Method POST -Body $target -Headers $headers -ContentType "application/json"
    
    # Create scan for this target
    $scan = @{
        target_id = $t.id
        name = "Scan - $domain"
        scan_type = "standard"
    } | ConvertTo-Json
    
    Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
        -Method POST -Body $scan -Headers $headers -ContentType "application/json"
}
```

### 3. LLM-Assisted Analysis

Use AI to analyze findings and generate insights:

```powershell
# Create scan with LLM analysis enabled
$scan = @{
    target_id = 1
    name = "AI-Powered Deep Scan"
    scan_type = "comprehensive"
    enable_subdomain_discovery = $true
    enable_nuclei = $true
    llm_config = @{
        provider = "openai"  # or "gemini", "anthropic", "groq"
        model = "gpt-4"
        temperature = 0.7
        enabled = $true
        analysis_prompts = @(
            "Identify potential attack vectors",
            "Suggest prioritized testing approach",
            "Highlight unusual findings"
        )
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
    -Method POST -Body $scan -Headers $headers -ContentType "application/json"
```

### 4. Filter and Export Findings

```powershell
# Get critical findings only
$criticalFindings = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/findings?severity=critical&status=confirmed" `
    -Headers $headers

# Export to JSON
$criticalFindings | ConvertTo-Json -Depth 10 | Out-File "critical_findings.json"

# Export to CSV
$criticalFindings | Select-Object id, title, severity, asset_type, asset_value, created_at | 
    Export-Csv "critical_findings.csv" -NoTypeInformation
```

## Monitoring & Maintenance

### Check Service Health

```powershell
# Overall health
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Database status
docker-compose exec db psql -U smartrecon smartrecon -c "SELECT COUNT(*) FROM targets;"

# Worker status
docker-compose exec worker celery -A app.worker.tasks inspect active

# View logs
docker-compose logs api
docker-compose logs worker
docker-compose logs -f  # Follow all logs
```

### Database Management

```powershell
# Backup database
docker-compose exec db pg_dump -U smartrecon smartrecon > backup.sql

# Restore database
cat backup.sql | docker-compose exec -T db psql -U smartrecon smartrecon

# View database tables
docker-compose exec db psql -U smartrecon smartrecon -c "\dt"
```

### Performance Tuning

Edit `.env` file:

```bash
# Increase worker concurrency
CELERY_WORKER_CONCURRENCY=10

# Adjust rate limits
DEFAULT_RATE_LIMIT=20
DEFAULT_MAX_CONCURRENCY=10

# Redis performance
REDIS_MAX_CONNECTIONS=50
```

## Troubleshooting

### Authentication Issues

```powershell
# Verify user exists
docker-compose exec api python -c "
from app.core.database import SessionLocal
from app.models import User
db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f'Username: {u.username}, Email: {u.email}, Active: {u.is_active}')
"

# Reset admin password
docker-compose exec api python -c "
from app.core.database import SessionLocal
from app.models import User
from app.core.security import get_password_hash
db = SessionLocal()
user = db.query(User).filter(User.username == 'admin').first()
user.hashed_password = get_password_hash('newpassword123')
db.commit()
print('Password updated!')
"
```

### Worker Not Processing Tasks

```powershell
# Check worker logs
docker-compose logs worker

# Restart worker
docker-compose restart worker

# Check Redis connection
docker-compose exec redis redis-cli ping

# View task queue
docker-compose exec redis redis-cli LLEN celery
```

### Scan Stuck in "Running" State

```powershell
# Manually update scan status
docker-compose exec api python -c "
from app.core.database import SessionLocal
from app.models import Scan
db = SessionLocal()
scan = db.query(Scan).filter(Scan.id == 1).first()
scan.status = 'completed'
db.commit()
print('Scan status updated')
"
```

## Best Practices

### 1. Authorization & Ethics
- **Always obtain explicit written authorization** before scanning any target
- Store authorization proof in the `authorization_proof` field
- Use `authorized=true` only when you have legitimate permission
- Respect rate limits and be mindful of target infrastructure
- Follow responsible disclosure practices

### 2. Rate Limiting
- Start with conservative rate limits (5-10 req/s)
- Monitor target response times
- Increase gradually if target can handle it
- Use `rate_limit` and `max_concurrency` in target configuration

### 3. Scope Management
- Clearly define `in_scope` and `out_of_scope` domains
- Use `out_of_scope` to explicitly exclude sensitive areas
- Review and update scope regularly
- Document scope changes in target description

### 4. LLM Usage
- Enable LLM analysis for complex targets
- Use higher quality models (GPT-4, Claude) for production
- Set appropriate temperature (0.7 for balanced output)
- Review LLM suggestions critically

### 5. Data Management
- Regularly backup the database
- Archive old scans and findings
- Clean up test data periodically
- Monitor disk usage for reports

### 6. Security
- Change default credentials immediately
- Use strong JWT secrets
- Enable HTTPS in production
- Restrict API access with firewall rules
- Regularly update dependencies

## Additional Resources

- **Full Documentation**: [QUICKSTART.md](QUICKSTART.md)
- **API Reference**: [API.md](API.md)
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Swagger UI**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc

## Getting Help

1. Check the logs: `docker-compose logs`
2. Review API documentation at http://localhost:8000/docs
3. Run test script: `.\test-api.ps1`
4. Check service health: `docker-compose ps`
5. Verify configuration in `.env` file

---

**Happy Hunting! 🎯**

Remember: With great power comes great responsibility. Always hack ethically and legally!
