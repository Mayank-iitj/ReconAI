# SmartRecon-AI Quick Start Guide

## 🚀 Getting Started

### 1. Access the Application

- **API Documentation**: http://localhost:8000/docs (Interactive Swagger UI)
- **Frontend**: http://localhost:3000
- **API Base URL**: http://localhost:8000

### 2. Authentication

First, you need to authenticate to get an access token.

**Default Credentials:**
- Email: `admin@smartrecon.local`
- Password: `changeme123`

#### Using the Swagger UI (Easiest):
1. Go to http://localhost:8000/docs
2. Click the **"Authorize"** button (🔒 icon at top right)
3. Enter credentials:
   - Username: `admin@smartrecon.local`
   - Password: `changeme123`
4. Click "Authorize"
5. Now you can test all API endpoints directly in the browser!

#### Using cURL:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@smartrecon.local&password=changeme123"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

Save the `access_token` for subsequent requests.

#### Using PowerShell:
```powershell
$body = "username=admin@smartrecon.local&password=changeme123"
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
  -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
$token = $response.access_token
$headers = @{"Authorization" = "Bearer $token"}
```

---

## 📋 Basic Workflow

### Step 1: Create a Target

A target represents the scope of your reconnaissance.

**Via Swagger UI:**
1. Go to http://localhost:8000/docs
2. Find `POST /api/v1/targets`
3. Click "Try it out"
4. Enter JSON:

```json
{
  "name": "Example Target",
  "description": "Bug bounty program for example.com",
  "scope": {
    "root_domains": ["example.com", "*.example.com"],
    "ip_ranges": [],
    "excluded_domains": ["admin.example.com"]
  },
  "authorization_proof": "https://bugcrowd.com/example-program",
  "tags": ["bug-bounty", "web-app"]
}
```

5. Click "Execute"
6. Note the `id` in the response (e.g., `1`)

**Via cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/targets" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Target",
    "description": "Bug bounty program for example.com",
    "scope": {
      "root_domains": ["example.com"],
      "ip_ranges": [],
      "excluded_domains": ["admin.example.com"]
    },
    "authorization_proof": "https://bugcrowd.com/example-program",
    "tags": ["bug-bounty"]
  }'
```

---

### Step 2: Create a Scan

Now create a scan to run reconnaissance on your target.

**Via Swagger UI:**
1. Find `POST /api/v1/scans`
2. Click "Try it out"
3. Enter JSON:

```json
{
  "target_id": 1,
  "scan_type": "full",
  "config": {
    "tools": {
      "subfinder": {"enabled": true},
      "httpx": {"enabled": true},
      "nuclei": {"enabled": true, "severity": ["critical", "high", "medium"]}
    },
    "llm": {
      "enabled": true,
      "provider": "openai",
      "auto_prioritize": true
    }
  }
}
```

4. Click "Execute"
5. Note the scan `id` (e.g., `1`)

**What happens:**
- Celery worker picks up the scan job
- Runs Subfinder to find subdomains
- Probes discovered hosts with HTTPX
- Scans for vulnerabilities with Nuclei
- LLM analyzes findings and prioritizes them
- Results are stored in the database

---

### Step 3: Monitor Scan Progress

**Check scan status:**

Via Swagger UI:
1. Find `GET /api/v1/scans/{scan_id}`
2. Enter scan ID: `1`
3. Click "Execute"

Via cURL:
```bash
curl "http://localhost:8000/api/v1/scans/1" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response shows:
```json
{
  "id": 1,
  "status": "running",  // or "completed", "failed"
  "progress": 45,
  "started_at": "2026-01-05T10:00:00Z",
  "duration": 120,
  "findings_count": 15
}
```

---

### Step 4: View Findings

Once scan completes, view the discovered findings.

**Via Swagger UI:**
1. Find `GET /api/v1/findings`
2. Add query parameters:
   - `scan_id`: `1`
   - `severity`: `critical` (optional filter)
3. Click "Execute"

**Via cURL:**
```bash
curl "http://localhost:8000/api/v1/findings?scan_id=1&severity=critical" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "items": [
    {
      "id": 1,
      "title": "SQL Injection in login form",
      "severity": "critical",
      "cvss_score": 9.8,
      "confidence": "high",
      "affected_url": "https://example.com/login",
      "description": "SQL injection vulnerability allows...",
      "ai_priority": 95,
      "ai_analysis": "High priority - exploitable without authentication...",
      "suggested_poc": "sqlmap -u 'https://example.com/login?id=1' --dbs"
    }
  ],
  "total": 15,
  "page": 1
}
```

---

### Step 5: Generate Report

Create a professional bug bounty report.

**Via Swagger UI:**
1. Find `POST /api/v1/reports`
2. Enter JSON:

```json
{
  "scan_id": 1,
  "title": "Security Assessment Report - Example.com",
  "format": "markdown",
  "include_ai_summary": true,
  "filters": {
    "min_severity": "medium"
  }
}
```

3. Click "Execute"
4. Get the report ID

**Download the report:**
1. Find `GET /api/v1/reports/{report_id}/download`
2. Enter report ID
3. Click "Execute" → "Download file"

**Formats available:**
- `markdown` - Clean Markdown for platforms like HackerOne
- `html` - Formatted HTML report
- `pdf` - Professional PDF document
- `json` - Machine-readable JSON

---

## 🔧 Advanced Features

### LLM Configuration

SmartRecon-AI uses LLMs to:
- Prioritize findings based on exploitability
- Suggest proof-of-concepts
- Generate report summaries
- Correlate weak signals into attack chains

**Configure in `.env`:**
```env
# Choose provider
LLM_PROVIDER=openai  # or gemini, groq, local

# OpenAI
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4-turbo

# Gemini
GEMINI_API_KEY=your-key-here

# Groq (fast inference)
GROQ_API_KEY=your-key-here
```

### Custom Tool Configuration

Customize tool behavior per scan:

```json
{
  "scan_type": "full",
  "config": {
    "tools": {
      "subfinder": {
        "enabled": true,
        "timeout": 1800,
        "sources": ["crtsh", "virustotal", "securitytrails"]
      },
      "httpx": {
        "enabled": true,
        "threads": 50,
        "timeout": 10,
        "follow_redirects": true
      },
      "nuclei": {
        "enabled": true,
        "severity": ["critical", "high"],
        "templates": ["cves", "vulnerabilities"],
        "rate_limit": 150
      }
    }
  }
}
```

### Scheduled Scans

Create recurring scans for continuous monitoring:

```json
{
  "target_id": 1,
  "scan_type": "quick",
  "schedule": {
    "enabled": true,
    "cron": "0 2 * * *",  // Daily at 2 AM
    "timezone": "UTC"
  }
}
```

### Filtering and Search

**Find high-priority findings:**
```bash
curl "http://localhost:8000/api/v1/findings?severity=critical&status=open&min_priority=80" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Search by keyword:**
```bash
curl "http://localhost:8000/api/v1/findings?search=sql+injection" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🎯 Best Practices

### 1. Always Get Authorization
```json
{
  "authorization_proof": "https://bugcrowd.com/program/policy",
  "authorization_notes": "Written permission obtained via email on 2026-01-05"
}
```

### 2. Start with Quick Scans
Use `scan_type: "quick"` first to verify scope before running full scans.

### 3. Review Scope Carefully
```json
{
  "scope": {
    "root_domains": ["example.com", "*.example.com"],
    "excluded_domains": ["admin.example.com", "internal.example.com"],
    "ip_ranges": ["192.0.2.0/24"],
    "excluded_ips": ["192.0.2.1"]
  }
}
```

### 4. Use Tags for Organization
```json
{
  "tags": ["bug-bounty", "web-app", "high-priority", "fintech"]
}
```

### 5. Review AI Suggestions
Always manually verify:
- AI priority scores
- Suggested proof-of-concepts  
- Report summaries

The LLM assists but doesn't replace human expertise!

### 6. Rate Limiting
Configure appropriate rate limits to avoid overwhelming targets:
```json
{
  "config": {
    "rate_limit": 10,  // requests per second
    "max_concurrent": 5
  }
}
```

---

## 📊 Monitoring

### Celery Flower Dashboard
Monitor background workers:
```bash
# Start Flower (if not running)
docker-compose up -d flower

# Access dashboard
http://localhost:5555
```

### Metrics & Logs
```bash
# View API logs
docker-compose logs -f api

# View worker logs
docker-compose logs -f worker

# Check service status
docker-compose ps

# View metrics
http://localhost:8000/metrics
```

---

## 🐛 Troubleshooting

### Scan stuck in "pending"
```bash
# Check worker is running
docker-compose ps worker

# Restart worker
docker-compose restart worker

# Check logs
docker-compose logs worker
```

### LLM not working
```bash
# Verify API key in .env
grep OPENAI_API_KEY .env

# Check API logs for errors
docker-compose logs api | grep -i llm
```

### Database connection failed
```bash
# Check database is healthy
docker-compose ps db

# Restart database
docker-compose restart db api
```

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Full API Reference**: See [API.md](API.md)
- **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)

---

## ⚠️ Legal & Ethical Use

**CRITICAL REMINDERS:**

✅ **DO:**
- Obtain explicit written authorization
- Respect target scope and exclusions
- Follow bug bounty program rules
- Use responsible disclosure practices
- Keep rate limits reasonable

❌ **DON'T:**
- Scan without permission
- Test production systems destructively
- Exceed authorized scope
- Ignore rate limits
- Share credentials or findings publicly

**You are solely responsible for how you use this tool. Always act ethically and legally.**

---

## 🎓 Example: Complete Workflow

```powershell
# 1. Login
$body = "username=admin@smartrecon.local&password=changeme123"
$login = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/login" `
  -Method POST -Body $body -ContentType "application/x-www-form-urlencoded"
$headers = @{"Authorization" = "Bearer $($login.access_token)"}

# 2. Create target
$target = @{
  name = "Example Bug Bounty"
  description = "Authorized testing for example.com"
  scope = @{
    root_domains = @("example.com")
  }
  authorization_proof = "https://bugcrowd.com/example"
} | ConvertTo-Json

$targetResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/targets" `
  -Method POST -Body $target -Headers $headers -ContentType "application/json"
$targetId = $targetResult.id

# 3. Create scan
$scan = @{
  target_id = $targetId
  scan_type = "full"
  config = @{
    tools = @{
      subfinder = @{ enabled = $true }
      httpx = @{ enabled = $true }
      nuclei = @{ enabled = $true }
    }
  }
} | ConvertTo-Json -Depth 10

$scanResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans" `
  -Method POST -Body $scan -Headers $headers -ContentType "application/json"
$scanId = $scanResult.id

# 4. Monitor progress
Start-Sleep -Seconds 30
$status = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/scans/$scanId" `
  -Headers $headers
Write-Host "Scan Status: $($status.status) - Progress: $($status.progress)%"

# 5. View findings (once completed)
$findings = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/findings?scan_id=$scanId" `
  -Headers $headers
$findings.items | Format-Table title, severity, affected_url

# 6. Generate report
$report = @{
  scan_id = $scanId
  title = "Security Assessment"
  format = "markdown"
} | ConvertTo-Json

$reportResult = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/reports" `
  -Method POST -Body $report -Headers $headers -ContentType "application/json"
Write-Host "Report generated: ID $($reportResult.id)"
```

---

**Ready to start? Visit http://localhost:8000/docs and begin your first scan!** 🚀
