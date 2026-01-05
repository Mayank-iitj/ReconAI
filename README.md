# SmartRecon-AI

> **Production-grade, AI-assisted bug bounty reconnaissance agent**

SmartRecon-AI automates web reconnaissance by orchestrating proven recon tools (Amass, Subfinder, HTTPX, FFUF, Nuclei, etc.), leveraging AI for intelligent triage and prioritization, and generating high-quality bug bounty reports with PoCs.

## 🎯 Key Features

- **Automated Recon Pipeline**: Asset discovery, subdomain enumeration, alive checks, tech fingerprinting, and vulnerability scanning
- **AI-Powered Analysis**: LLM-driven triage, risk scoring, correlation, and PoC generation
- **Professional Reporting**: Export to Markdown/HTML/PDF with detailed findings and remediation
- **Web UI + REST API**: Manage scans, define scopes, view findings, and schedule recurring recon
- **Production-Ready**: Role-based access, audit logs, rate limiting, horizontal scaling
- **Compliance First**: Always respect target scope, rate limits, and authorization requirements

## 🏗️ Architecture

```
┌─────────────────┐
│   Frontend      │  React/Next.js UI
│  (Next.js/TS)   │
└────────┬────────┘
         │
┌────────▼────────┐
│   API Server    │  FastAPI + JWT Auth
│   (FastAPI)     │
└────────┬────────┘
         │
    ┌────┴────────────┬──────────────┐
    │                 │              │
┌───▼────┐     ┌─────▼──────┐  ┌───▼────────┐
│ Redis  │     │ PostgreSQL │  │  Workers   │
│ Queue  │     │  Database  │  │  (Celery)  │
└────────┘     └────────────┘  └──────┬─────┘
                                      │
                           ┌──────────▼──────────┐
                           │   Recon Tools       │
                           │ (Docker Containers) │
                           │                     │
                           │ Amass | Subfinder   │
                           │ HTTPX | FFUF        │
                           │ Nuclei | Katana     │
                           └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smartrecon-ai.git
   cd smartrecon-ai
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Run database migrations**
   ```bash
   docker-compose exec api alembic upgrade head
   ```

5. **Access the application**
   - Web UI: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## � Deployment

### Quick Deploy to Railway (Free)

Deploy in 5 minutes with $5 free monthly credit:

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

See [RAILWAY-DEPLOY.md](RAILWAY-DEPLOY.md) for complete Railway deployment guide.

### Other Free Options

- **Oracle Cloud Always Free**: 24GB RAM, truly free forever - [FREE-DEPLOYMENT.md](FREE-DEPLOYMENT.md)
- **Render.com**: Free tier with limitations
- **Fly.io**: 256MB RAM free tier

### Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production guidelines.

## �📖 Usage

### Creating a Scan

1. **Define Target**
   ```bash
   curl -X POST http://localhost:8000/api/v1/targets \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "example.com",
       "root_domains": ["example.com"],
       "in_scope": ["*.example.com"],
       "out_of_scope": ["dev.example.com"],
       "authorized": true
     }'
   ```

2. **Start Recon Scan**
   ```bash
   curl -X POST http://localhost:8000/api/v1/scans \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "target_id": 1,
       "scan_type": "full",
       "intensity": "standard",
       "enable_fuzzing": true,
       "enable_nuclei": true
     }'
   ```

3. **View Results**
   - Navigate to the web UI dashboard
   - Filter findings by severity
   - Export reports in your preferred format

### Continuous Recon

Schedule recurring scans for delta detection:

```bash
curl -X POST http://localhost:8000/api/v1/scans/schedule \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_id": 1,
    "cron_schedule": "0 0 * * *",
    "scan_type": "quick"
  }'
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:password@db:5432/smartrecon

# Redis
REDIS_URL=redis://redis:6379/0

# LLM Provider
LLM_PROVIDER=openai  # openai, gemini, groq, local
OPENAI_API_KEY=your_key_here

# Security
JWT_SECRET=your_secret_key
JWT_ALGORITHM=HS256

# Rate Limiting
MAX_CONCURRENT_SCANS=5
DEFAULT_RATE_LIMIT=10  # requests/second
```

### Tool Configuration

Configure recon tools in `backend/config/tools.yaml`:

```yaml
subdomain_discovery:
  tools: [amass, subfinder]
  timeout: 3600
  max_results: 10000

vulnerability_scanning:
  nuclei:
    templates:
      - cves
      - exposures
      - misconfigurations
    severity: [critical, high, medium]
    rate_limit: 150  # requests/second
```

## 🧪 Recon Pipeline

SmartRecon-AI executes a comprehensive pipeline:

1. **Subdomain Discovery**: Amass + Subfinder in parallel
2. **Alive Check**: HTTPX for live hosts, tech fingerprinting
3. **URL Collection**: Katana/GAU for historical and current endpoints
4. **Fuzzing**: FFUF for directories, Arjun for parameters
5. **Vulnerability Scanning**: Nuclei with curated templates
6. **Subdomain Takeover**: Automated CNAME + HTTP checks
7. **AI Analysis**: LLM-powered prioritization and PoC generation
8. **Report Generation**: Professional reports with remediation steps

## 🤖 LLM Integration

### Supported Providers

- **OpenAI**: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
- **Google Gemini**: Gemini Pro, Gemini Ultra
- **Groq**: Fast inference for Llama, Mixtral
- **Local Models**: Ollama, LM Studio

### LLM Capabilities

The AI agent assists with:

- **Finding Prioritization**: Risk scoring using CVSS-like rubric
- **Deduplication**: Merge similar findings from multiple tools
- **PoC Generation**: Safe, non-destructive proof-of-concept payloads
- **Report Writing**: Professional, concise bug bounty reports
- **Attack Path Analysis**: Correlate weak signals into actionable leads

### Example LLM Output

```json
{
  "priority_rank": 1,
  "severity": "HIGH",
  "likelihood_of_valid_bug": 0.85,
  "finding": {
    "title": "Open Redirect via OAuth Callback",
    "cwe": "CWE-601",
    "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:U/C:L/I:L/A:N"
  },
  "suggested_manual_steps": [
    "Test with phishing domain to confirm full redirect",
    "Check if state parameter validation can be bypassed",
    "Verify if other OAuth endpoints are affected"
  ],
  "poc": {
    "request": "GET /oauth/callback?redirect_uri=https://evil.com HTTP/1.1\nHost: example.com",
    "impact": "Attackers can phish users via trusted domain redirect"
  }
}
```

## 📊 Reporting

### Export Formats

- **Markdown**: Direct submission to bug bounty platforms
- **HTML**: Interactive web reports with embedded evidence
- **PDF**: Professional reports for client delivery
- **JSON**: Machine-readable for integrations

### Report Sections

1. **Executive Summary**: Scope, methodology, key findings
2. **Asset Overview**: Discovered domains, tech stack, attack surface
3. **Findings**: Detailed vulnerabilities with severity, PoC, impact
4. **Remediation**: Actionable fix recommendations per finding
5. **Appendix**: Tool outputs, configurations, logs

## 🔒 Security & Compliance

### Authorization Guardrails

- ✅ Explicit authorization confirmation required per target
- ✅ Hard-coded blocklists for restricted TLDs and IP ranges
- ✅ Scope validation before any tool execution
- ✅ Rate limiting and concurrency caps per target
- ✅ Audit logs for all scan activities

### RBAC (Role-Based Access Control)

- **Admin**: Full system access, user management
- **Researcher**: Create scans, view findings, export reports
- **Read-Only**: View-only access to reports and findings

### Best Practices

- Store secrets in environment variables or secret managers
- Use JWT with short expiry for authentication
- Enable audit logging for compliance tracking
- Run recon tools in sandboxed Docker containers
- Never scan without explicit, documented authorization

## 🐳 Docker Deployment

### Development

```bash
docker-compose -f docker-compose.dev.yml up
```

### Production

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Run with health checks and auto-restart
docker-compose -f docker-compose.prod.yml up -d

# Scale workers
docker-compose -f docker-compose.prod.yml up -d --scale worker=5
```

### Kubernetes

See `k8s/` directory for Kubernetes manifests:

```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/redis.yaml
kubectl apply -f k8s/api.yaml
kubectl apply -f k8s/worker.yaml
kubectl apply -f k8s/frontend.yaml
```

## 🧰 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/login` | Authenticate user |
| GET | `/api/v1/targets` | List all targets |
| POST | `/api/v1/targets` | Create new target |
| GET | `/api/v1/targets/{id}` | Get target details |
| POST | `/api/v1/scans` | Start new scan |
| GET | `/api/v1/scans/{id}` | Get scan status |
| GET | `/api/v1/scans/{id}/findings` | List scan findings |
| POST | `/api/v1/reports/generate` | Generate report |
| GET | `/api/v1/reports/{id}/export` | Export report (PDF/MD/HTML) |

Full API documentation: http://localhost:8000/docs

## 📈 Monitoring & Observability

### Metrics

- Scans per day, per target
- Findings per severity level
- Average scan duration per tool
- Worker queue depth and processing rate

### Logging

Structured JSON logs with:
- Timestamp, level, service name
- User context (for audit)
- Request/response details
- Tool execution logs

### Alerting

Configure alerts for:
- Failed scans (> 3 retries)
- High-severity findings detected
- Worker queue backlog
- Database connection issues

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Install pre-commit hooks: `pre-commit install`
4. Make your changes with tests
5. Run tests: `pytest`
6. Submit a pull request

### Code Quality

- **Linting**: Ruff, Black, isort
- **Type Checking**: mypy
- **Security**: Bandit, Trivy
- **Tests**: pytest (aim for >80% coverage)

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**FOR AUTHORIZED TESTING ONLY**

This tool is intended for authorized security testing and bug bounty programs only. Users are solely responsible for obtaining proper authorization before scanning any targets. Unauthorized testing may be illegal and unethical. The developers assume no liability for misuse.

## 🙏 Acknowledgments

Built on top of amazing open-source recon tools:

- [Amass](https://github.com/OWASP/Amass) - Subdomain discovery
- [Subfinder](https://github.com/projectdiscovery/subfinder) - Fast subdomain enumeration
- [HTTPX](https://github.com/projectdiscovery/httpx) - HTTP probing
- [FFUF](https://github.com/ffuf/ffuf) - Fuzzing
- [Nuclei](https://github.com/projectdiscovery/nuclei) - Vulnerability scanning
- [Katana](https://github.com/projectdiscovery/katana) - Crawling & URL collection

## 📞 Support

- **Documentation**: [docs.smartrecon.ai](https://docs.smartrecon.ai)
- **Issues**: [GitHub Issues](https://github.com/yourusername/smartrecon-ai/issues)
- **Discord**: [Join our community](https://discord.gg/smartrecon)
- **Email**: support@smartrecon.ai

---

**Happy Hunting! 🎯🔍**
