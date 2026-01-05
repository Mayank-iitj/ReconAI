"""
Scope validation service
Ensures all recon activities stay within authorized scope
"""

import re
import ipaddress
from typing import Dict, Any, List
from urllib.parse import urlparse
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class ScopeValidator:
    """Validates targets against scope rules and blocklists"""
    
    def __init__(self):
        self.blocked_tlds = [tld.strip() for tld in settings.BLOCKED_TLD if tld]
        self.blocked_ip_ranges = [
            ipaddress.ip_network(ip.strip())
            for ip in settings.BLOCKED_IP_RANGES
            if ip.strip()
        ]
    
    def validate_target(self, target_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate target configuration
        
        Args:
            target_data: Target data dict
        
        Returns:
            Dict with 'valid' bool and 'errors' list
        """
        errors = []
        
        # Check root domains
        for domain in target_data.get("root_domains", []):
            if self.is_blocked_tld(domain):
                errors.append(f"Blocked TLD in root domain: {domain}")
        
        # Check in-scope patterns
        for pattern in target_data.get("in_scope", []):
            if self.is_blocked_tld(pattern):
                errors.append(f"Blocked TLD in scope pattern: {pattern}")
        
        # Check IP ranges
        for ip_range in target_data.get("ip_ranges", []):
            try:
                network = ipaddress.ip_network(ip_range, strict=False)
                if self.is_blocked_ip_range(network):
                    errors.append(f"Blocked IP range: {ip_range}")
            except ValueError:
                errors.append(f"Invalid IP range format: {ip_range}")
        
        # Check authorization
        if settings.REQUIRE_EXPLICIT_AUTHORIZATION and not target_data.get("authorized"):
            errors.append("Explicit authorization required but not provided")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    def is_in_scope(self, target: str, scope_rules: Dict[str, Any]) -> bool:
        """
        Check if a target is in scope
        
        Args:
            target: Domain, IP, or URL to check
            scope_rules: Scope rules from Target model
        
        Returns:
            True if in scope, False otherwise
        """
        # Parse target
        if target.startswith(("http://", "https://")):
            parsed = urlparse(target)
            host = parsed.netloc
        else:
            host = target
        
        # Check if it's an IP
        try:
            ip = ipaddress.ip_address(host)
            return self._is_ip_in_scope(ip, scope_rules)
        except ValueError:
            # It's a domain
            return self._is_domain_in_scope(host, scope_rules)
    
    def _is_domain_in_scope(self, domain: str, scope_rules: Dict[str, Any]) -> bool:
        """Check if domain is in scope"""
        # Check blocked TLDs first
        if self.is_blocked_tld(domain):
            logger.warning(f"Domain {domain} has blocked TLD")
            return False
        
        # Check out-of-scope patterns
        out_of_scope = scope_rules.get("out_of_scope", [])
        for pattern in out_of_scope:
            if self._matches_pattern(domain, pattern):
                logger.info(f"Domain {domain} matches out-of-scope pattern {pattern}")
                return False
        
        # Check in-scope patterns
        in_scope = scope_rules.get("in_scope", [])
        for pattern in in_scope:
            if self._matches_pattern(domain, pattern):
                return True
        
        # Check root domains
        root_domains = scope_rules.get("root_domains", [])
        for root in root_domains:
            if domain == root or domain.endswith(f".{root}"):
                return True
        
        return False
    
    def _is_ip_in_scope(self, ip: ipaddress.IPv4Address, scope_rules: Dict[str, Any]) -> bool:
        """Check if IP is in scope"""
        # Check blocked IP ranges
        if self.is_blocked_ip_range(ip):
            logger.warning(f"IP {ip} is in blocked range")
            return False
        
        # Check against allowed IP ranges
        ip_ranges = scope_rules.get("ip_ranges", [])
        for ip_range_str in ip_ranges:
            try:
                network = ipaddress.ip_network(ip_range_str, strict=False)
                if ip in network:
                    return True
            except ValueError:
                continue
        
        return False
    
    def _matches_pattern(self, domain: str, pattern: str) -> bool:
        """
        Check if domain matches wildcard pattern
        
        Examples:
            *.example.com matches sub.example.com
            example.com matches example.com only
        """
        if pattern.startswith("*."):
            # Wildcard subdomain
            root = pattern[2:]
            return domain.endswith(f".{root}") or domain == root
        else:
            # Exact match
            return domain == pattern
    
    def is_blocked_tld(self, domain: str) -> bool:
        """Check if domain has a blocked TLD"""
        for tld in self.blocked_tlds:
            if domain.endswith(tld):
                return True
        return False
    
    def is_blocked_ip_range(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address | ipaddress.IPv4Network) -> bool:
        """Check if IP is in a blocked range"""
        if isinstance(ip, (ipaddress.IPv4Network, ipaddress.IPv6Network)):
            # Check if network overlaps with any blocked range
            for blocked_range in self.blocked_ip_ranges:
                if ip.overlaps(blocked_range):
                    return True
        else:
            # Check if IP is in any blocked range
            for blocked_range in self.blocked_ip_ranges:
                if ip in blocked_range:
                    return True
        return False
