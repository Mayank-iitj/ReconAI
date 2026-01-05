# API Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints (except `/auth/login`) require JWT authentication.

### Login

**POST** `/auth/login`

Request body (form data):
```
username=admin
password=your_password
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### Usage

Include token in Authorization header:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

---

## Targets

### Create Target

**POST** `/targets`

```json
{
  "name": "example.com",
  "description": "Example bug bounty program",
  "root_domains": ["example.com"],
  "in_scope": ["*.example.com", "example.com"],
  "out_of_scope": ["dev.example.com"],
  "ip_ranges": ["192.0.2.0/24"],
  "authorized": true,
  "authorization_proof": "HackerOne program URL: https://hackerone.com/example",
  "rate_limit": 10,
  "max_concurrency": 5,
  "tags": ["bugbounty", "web"],
  "program_name": "Example Bug Bounty",
  "priority": 5
}
```

Response: `201 Created`
```json
{
  "id": 1,
  "name": "example.com",
  "root_domains": ["example.com"],
  "in_scope": ["*.example.com", "example.com"],
  "out_of_scope": ["dev.example.com"],
  "authorized": true,
  "owner_id": 1,
  "created_at": "2026-01-05T10:30:00Z"
}
```

### List Targets

**GET** `/targets?skip=0&limit=50`

Response: `200 OK`
```json
[
  {
    "id": 1,
    "name": "example.com",
    "root_domains": ["example.com"],
    "created_at": "2026-01-05T10:30:00Z"
  }
]
```

### Get Target

**GET** `/targets/{target_id}`

### Update Target

**PUT** `/targets/{target_id}`

### Delete Target

**DELETE** `/targets/{target_id}`

---

## Scans

### Create Scan

**POST** `/scans`

```json
{
  "target_id": 1,
  "name": "Full recon scan",
  "scan_type": "standard",
  "enable_subdomain_discovery": true,
  "enable_port_scan": false,
  "enable_fuzzing": true,
  "enable_nuclei": true,
  "enable_takeover_check": true,
  "tool_config": {
    "nuclei": {
      "severity": ["critical", "high", "medium"]
    }
  }
}
```

Response: `201 Created`
```json
{
  "id": 1,
  "target_id": 1,
  "name": "Full recon scan",
  "status": "pending",
  "scan_type": "standard",
  "created_by": 1,
  "created_at": "2026-01-05T11:00:00Z"
}
```

### Schedule Recurring Scan

**POST** `/scans/schedule`

```json
{
  "target_id": 1,
  "scan_type": "quick",
  "cron_schedule": "0 0 * * *",
  "enable_subdomain_discovery": true,
  "enable_nuclei": true
}
```

### List Scans

**GET** `/scans?target_id=1&status=completed&skip=0&limit=50`

### Get Scan

**GET** `/scans/{scan_id}`

Response:
```json
{
  "id": 1,
  "target_id": 1,
  "status": "completed",
  "started_at": "2026-01-05T11:00:00Z",
  "completed_at": "2026-01-05T11:45:30Z",
  "duration_seconds": 2730,
  "total_findings": 25,
  "critical_findings": 2,
  "high_findings": 5,
  "medium_findings": 10,
  "low_findings": 8,
  "info_findings": 0
}
```

### Cancel Scan

**POST** `/scans/{scan_id}/cancel`

### Delete Scan

**DELETE** `/scans/{scan_id}`

---

## Findings

### List Findings

**GET** `/findings?scan_id=1&severity=high&status=open&skip=0&limit=50`

Response:
```json
[
  {
    "id": 1,
    "scan_id": 1,
    "title": "SQL Injection in login form",
    "description": "SQL injection vulnerability found...",
    "severity": "high",
    "status": "open",
    "vuln_type": "SQLi",
    "cwe_id": "CWE-89",
    "cvss_score": "8.6",
    "affected_url": "https://example.com/login",
    "poc": "curl -X POST 'https://example.com/login' -d \"username=' OR '1'='1\"",
    "ai_priority_rank": 1,
    "likelihood_score": 85,
    "suggested_steps": [
      "Test with sqlmap for confirmation",
      "Check for blind SQL injection",
      "Verify database type"
    ],
    "discovered_at": "2026-01-05T11:20:00Z"
  }
]
```

### Get Finding

**GET** `/findings/{finding_id}`

### Update Finding

**PUT** `/findings/{finding_id}`

```json
{
  "status": "accepted",
  "severity": "critical",
  "description": "Updated description with more details"
}
```

### Get Findings Summary

**GET** `/findings/stats/summary?scan_id=1`

Response:
```json
{
  "total": 25,
  "by_severity": {
    "critical": 2,
    "high": 5,
    "medium": 10,
    "low": 8,
    "info": 0
  },
  "by_status": {
    "open": 20,
    "in_review": 3,
    "accepted": 2
  }
}
```

---

## Reports

### Generate Report

**POST** `/reports`

```json
{
  "scan_id": 1,
  "title": "Security Assessment Report - Example.com",
  "report_type": "bug_bounty",
  "format": "markdown",
  "include_sections": [
    "executive_summary",
    "scope",
    "methodology",
    "findings",
    "remediation"
  ],
  "filters": {
    "severity": ["critical", "high", "medium"],
    "status": ["open"]
  }
}
```

Response: `201 Created`
```json
{
  "id": 1,
  "scan_id": 1,
  "title": "Security Assessment Report - Example.com",
  "report_type": "bug_bounty",
  "format": "markdown",
  "generated_by_llm": true,
  "created_at": "2026-01-05T12:00:00Z"
}
```

### List Reports

**GET** `/reports?scan_id=1`

### Get Report

**GET** `/reports/{report_id}`

### Download Report

**GET** `/reports/{report_id}/download`

Returns file with appropriate Content-Type:
- Markdown: `text/markdown`
- HTML: `text/html`
- PDF: `application/pdf`
- JSON: `application/json`

### Delete Report

**DELETE** `/reports/{report_id}`

---

## Users

### Create User (Admin only)

**POST** `/users`

```json
{
  "username": "researcher1",
  "email": "researcher@example.com",
  "full_name": "John Researcher",
  "password": "SecurePassword123!"
}
```

### List Users (Admin only)

**GET** `/users`

### Get User

**GET** `/users/{user_id}`

### Update User

**PUT** `/users/{user_id}`

```json
{
  "email": "newemail@example.com",
  "full_name": "John D. Researcher",
  "password": "NewSecurePassword123!"
}
```

### Delete User (Admin only)

**DELETE** `/users/{user_id}`

---

## Error Responses

All errors follow this format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable error message",
  "details": {
    "additional": "context"
  }
}
```

### Common Error Codes

| Code | Status | Description |
|------|--------|-------------|
| `AUTHORIZATION_ERROR` | 403 | Target not authorized for testing |
| `SCOPE_VALIDATION_ERROR` | 400 | Scope validation failed |
| `TOOL_EXECUTION_ERROR` | 500 | Recon tool failed |
| `LLM_ERROR` | 503 | LLM API unavailable |
| `SCAN_NOT_FOUND` | 404 | Scan not found |
| `TARGET_NOT_FOUND` | 404 | Target not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `CONCURRENT_SCAN_LIMIT` | 429 | Too many concurrent scans |

---

## Rate Limiting

API implements rate limiting per IP address:
- Default: 60 requests per minute
- Burst: 10 additional requests

When rate limit is exceeded:
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Try again in 30 seconds."
}
```

---

## Pagination

List endpoints support pagination:

```
GET /api/v1/targets?skip=0&limit=50
```

- `skip`: Number of items to skip (default: 0)
- `limit`: Max items to return (default: 50, max: 100)

---

## Filtering

### Scans
- `target_id`: Filter by target
- `status`: Filter by status (pending, running, completed, failed, cancelled)

### Findings
- `scan_id`: Filter by scan
- `severity`: Filter by severity (critical, high, medium, low, info)
- `status`: Filter by status (open, in_review, accepted, false_positive, etc.)

---

## WebSocket Support (Coming Soon)

Real-time scan progress updates via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/scans/1');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Scan update:', update);
};
```

---

## Examples

### Complete Workflow

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin&password=your_password" \
  | jq -r '.access_token')

# 2. Create target
TARGET_ID=$(curl -X POST http://localhost:8000/api/v1/targets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example.com",
    "root_domains": ["example.com"],
    "in_scope": ["*.example.com"],
    "authorized": true
  }' | jq -r '.id')

# 3. Start scan
SCAN_ID=$(curl -X POST http://localhost:8000/api/v1/scans \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"target_id\": $TARGET_ID,
    \"scan_type\": \"standard\",
    \"enable_nuclei\": true
  }" | jq -r '.id')

# 4. Check scan status
curl http://localhost:8000/api/v1/scans/$SCAN_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.status'

# 5. Get findings
curl "http://localhost:8000/api/v1/findings?scan_id=$SCAN_ID&severity=high" \
  -H "Authorization: Bearer $TOKEN" | jq '.[:5]'

# 6. Generate report
REPORT_ID=$(curl -X POST http://localhost:8000/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"scan_id\": $SCAN_ID,
    \"title\": \"Security Report\",
    \"format\": \"markdown\"
  }" | jq -r '.id')

# 7. Download report
curl "http://localhost:8000/api/v1/reports/$REPORT_ID/download" \
  -H "Authorization: Bearer $TOKEN" \
  -o report.md
```

---

For interactive API exploration, visit: **http://localhost:8000/docs**
