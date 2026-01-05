# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, report them via:

1. **Email**: security@smartrecon.ai
2. **PGP Key**: Available at https://smartrecon.ai/pgp-key.asc
3. **Private vulnerability disclosure**: GitHub Security Advisories

### What to Include

- Type of vulnerability
- Full paths of affected source files
- Location of affected code (tag/branch/commit or URL)
- Step-by-step instructions to reproduce
- Proof-of-concept or exploit code (if possible)
- Impact assessment
- Potential fix (if known)

### Response Timeline

- **24 hours**: Initial response acknowledging receipt
- **7 days**: Assessment and triage
- **30 days**: Fix development and testing
- **Disclosure**: Coordinated disclosure after fix is released

## Security Best Practices

### For Users

1. **Never scan without authorization**
   - Always obtain written permission
   - Respect target scope and rate limits
   - Follow bug bounty program rules

2. **Protect your credentials**
   - Use strong passwords
   - Rotate API keys regularly
   - Use environment variables, never hardcode secrets

3. **Keep software updated**
   - Apply security patches promptly
   - Monitor security advisories
   - Subscribe to security announcements

4. **Secure your deployment**
   - Use HTTPS/TLS in production
   - Enable firewall rules
   - Restrict network access
   - Use secrets management (Vault, etc.)

5. **Monitor and audit**
   - Enable audit logging
   - Review logs regularly
   - Set up alerts for suspicious activity

### For Developers

1. **Code security**
   - Validate all inputs
   - Use parameterized queries (prevent SQL injection)
   - Sanitize outputs (prevent XSS)
   - Avoid command injection

2. **Authentication & Authorization**
   - Use strong JWT secrets
   - Implement proper RBAC
   - Enforce least privilege
   - Use secure session management

3. **Dependency management**
   - Keep dependencies updated
   - Run `pip audit` or `npm audit` regularly
   - Review dependency licenses
   - Pin versions in production

4. **Secrets management**
   - Never commit secrets to Git
   - Use environment variables
   - Rotate credentials regularly
   - Use secret scanning tools

5. **Docker security**
   - Use minimal base images
   - Run as non-root user
   - Scan images with Trivy
   - Keep images updated

## Known Security Considerations

### Scope Validation

- Always validates targets against scope rules
- Blocks restricted TLDs (.gov, .mil, .edu by default)
- Prevents scanning RFC1918 private IP ranges

### Rate Limiting

- Implements per-target rate limits
- Prevents accidental DoS attacks
- Configurable concurrency limits

### LLM Safety

- LLMs instructed to never generate destructive payloads
- All PoCs are reviewed and sanitized
- Output validation prevents code injection

### Data Protection

- Sensitive findings encrypted at rest
- Access logs maintained for compliance
- GDPR-compliant data handling

## Compliance

SmartRecon-AI is designed to support:

- **GDPR**: Data protection by design
- **SOC 2**: Audit logging and access controls
- **Bug Bounty Programs**: Responsible disclosure practices

## Security Features

- ✅ JWT-based authentication
- ✅ Role-based access control (RBAC)
- ✅ Scope validation before every scan
- ✅ Rate limiting per target
- ✅ Audit logging
- ✅ Encrypted secrets storage
- ✅ SQL injection prevention (parameterized queries)
- ✅ XSS prevention (output sanitization)
- ✅ CSRF protection
- ✅ Secure headers (HSTS, CSP, X-Frame-Options)

## Security Roadmap

Planned security enhancements:

- [ ] Two-factor authentication (2FA)
- [ ] API key rotation
- [ ] Webhook signature validation
- [ ] Advanced intrusion detection
- [ ] Automated security scanning (SAST/DAST)
- [ ] Bug bounty program for SmartRecon-AI itself

## Security Contacts

- **Email**: security@smartrecon.ai
- **PGP Key**: https://smartrecon.ai/pgp-key.asc
- **Security Advisories**: https://github.com/yourusername/smartrecon-ai/security/advisories

---

**Remember**: Security is a shared responsibility. Use SmartRecon-AI ethically and legally.
