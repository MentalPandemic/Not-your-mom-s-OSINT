"""
DNS Enumeration Module for domain intelligence.

Provides comprehensive DNS record enumeration including A, AAAA, MX, TXT,
CNAME, NS, SOA, and other record types with historical data support.
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from clients.dns_client import DnsClient, DnsRecord, DnsResult
from clients.securitytrails_client import SecurityTrailsClient, SecurityTrailsHistory

logger = logging.getLogger(__name__)


@dataclass
class DnsEnumerateResult:
    """Result of DNS enumeration for a domain."""
    domain: str
    a_records: List[Dict[str, Any]] = field(default_factory=list)
    aaaa_records: List[Dict[str, Any]] = field(default_factory=list)
    mx_records: List[Dict[str, Any]] = field(default_factory=list)
    txt_records: List[Dict[str, Any]] = field(default_factory=list)
    cname_records: List[Dict[str, Any]] = field(default_factory=list)
    ns_records: List[Dict[str, Any]] = field(default_factory=list)
    soa_records: List[Dict[str, Any]] = field(default_factory=list)
    srv_records: List[Dict[str, Any]] = field(default_factory=list)
    caa_records: List[Dict[str, Any]] = field(default_factory=list)
    
    # Email services
    email_providers: List[str] = field(default_factory=list)
    
    # Nameservers
    nameserver_ips: Dict[str, List[str]] = field(default_factory=dict)
    
    # Validation
    is_valid: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "a_records": self.a_records,
            "aaaa_records": self.aaaa_records,
            "mx_records": self.mx_records,
            "txt_records": self.txt_records,
            "cname_records": self.cname_records,
            "ns_records": self.ns_records,
            "soa_records": self.soa_records,
            "srv_records": self.srv_records,
            "caa_records": self.caa_records,
            "email_providers": self.email_providers,
            "nameserver_ips": self.nameserver_ips,
            "is_valid": self.is_valid,
            "error": self.error,
        }
    
    def get_all_ips(self) -> List[str]:
        """Get all IP addresses from A and AAAA records."""
        ips = []
        for record in self.a_records:
            if "value" in record:
                ips.append(record["value"])
        for record in self.aaaa_records:
            if "value" in record:
                ips.append(record["value"])
        return ips
    
    def get_all_nameservers(self) -> List[str]:
        """Get all nameserver domains."""
        return [record.get("value", "") for record in self.ns_records if record.get("value")]
    
    def get_mail_servers(self) -> List[str]:
        """Get mail server domains."""
        return [record.get("target", "") for record in self.mx_records if record.get("target")]


@dataclass
class DnsHistoryResult:
    """Historical DNS records for a domain."""
    domain: str
    history: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    ip_changes: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "history": self.history,
            "ip_changes": self.ip_changes,
            "error": self.error,
        }


@dataclass
class DnsPropagationResult:
    """DNS propagation check result."""
    domain: str
    nameservers: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    is_propagated: bool = True
    inconsistencies: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "nameservers": self.nameservers,
            "is_propagated": self.is_propagated,
            "inconsistencies": self.inconsistencies,
        }


class DnsEnumeration:
    """
    DNS enumeration module for comprehensive DNS record discovery.
    
    Provides:
    - All DNS record type enumeration
    - Email service identification
    - Nameserver IP resolution
    - Historical DNS data
    - Propagation checking
    - DNS takeover detection
    """
    
    RECORD_TYPES = ["A", "AAAA", "MX", "TXT", "CNAME", "NS", "SOA", "SRV", "CAA"]
    EMAIL_PROVIDERS = {
        "google.com": ["google", "gmail", "google workspace"],
        "googlemail.com": ["google", "gmail"],
        "outlook.com": ["microsoft", "outlook", "office 365"],
        "office365.com": ["microsoft", "outlook", "office 365"],
        "exchange-online.com": ["microsoft", "exchange online"],
        "zoho.com": ["zoho", "mail"],
        "yahoo.com": ["yahoo", "ymail"],
        "protonmail.com": ["proton", "protonmail"],
        "tutanota.com": ["tutanota", "tuta"],
        "fastmail.com": ["fastmail"],
        "runbox.com": ["runbox"],
        "mailgun.org": ["mailgun"],
        "sendgrid.net": ["sendgrid"],
        "mailchimp.com": ["mailchimp"],
        "amazonses.com": ["aws", "amazon ses"],
        "postmarkapp.com": ["postmark"],
        "mandrillapp.com": ["mandrill"],
    }
    
    def __init__(
        self,
        securitytrails_api_key: Optional[str] = None,
        timeout: float = 10.0,
    ):
        """
        Initialize DNS enumeration module.
        
        Args:
            securitytrails_api_key: SecurityTrails API key for historical data
            timeout: DNS query timeout in seconds
        """
        self.dns_client = DnsClient(timeout=timeout)
        self._securitytrails: Optional[SecurityTrailsClient] = None
        
        if securitytrails_api_key:
            self._securitytrails = SecurityTrailsClient(securitytrails_api_key)
    
    async def enumerate_all(
        self,
        domain: str,
        include_txt: bool = True,
    ) -> DnsEnumerateResult:
        """
        Enumerate all DNS records for a domain.
        
        Args:
            domain: Domain name to enumerate
            include_txt: Whether to include TXT records
            
        Returns:
            DnsEnumerateResult with all DNS records
        """
        logger.info(f"Enumerating DNS records for {domain}")
        
        result = DnsEnumerateResult(domain=domain)
        
        try:
            # Resolve all record types concurrently
            record_types = self.RECORD_TYPES.copy()
            if not include_txt:
                record_types.remove("TXT")
            
            tasks = [
                self.dns_client.resolve(domain, record_type)
                for record_type in record_types
            ]
            
            dns_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Parse results
            for record_type, dns_result in zip(record_types, dns_results):
                if isinstance(dns_result, Exception):
                    logger.warning(f"Failed to resolve {record_type} for {domain}: {dns_result}")
                    continue
                
                records = self._parse_dns_result(dns_result)
                
                if record_type == "A":
                    result.a_records = records
                elif record_type == "AAAA":
                    result.aaaa_records = records
                elif record_type == "MX":
                    result.mx_records = records
                elif record_type == "TXT":
                    result.txt_records = records
                elif record_type == "CNAME":
                    result.cname_records = records
                elif record_type == "NS":
                    result.ns_records = records
                elif record_type == "SOA":
                    result.soa_records = records
                elif record_type == "SRV":
                    result.srv_records = records
                elif record_type == "CAA":
                    result.caa_records = records
            
            # Identify email providers
            result.email_providers = self._identify_email_providers(result.mx_records)
            
            # Resolve nameserver IPs
            result.nameserver_ips = await self._resolve_nameserver_ips(result.get_all_nameservers())
            
        except Exception as e:
            logger.error(f"DNS enumeration failed for {domain}: {e}")
            result.error = str(e)
            result.is_valid = False
        
        return result
    
    async def get_a_records(
        self,
        domain: str,
        resolve_cname: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get A records for a domain.
        
        Args:
            domain: Domain name
            resolve_cname: Whether to resolve CNAME chains
            
        Returns:
            List of A record dictionaries
        """
        result = await self.dns_client.resolve(domain, "A")
        
        if result.found:
            records = self._parse_dns_result(result)
            
            # Resolve CNAME chains if needed
            if resolve_cname:
                for record in records:
                    if "cname_chain" not in record and "cname" in record:
                        cname = record["cname"]
                        cname_a = await self.get_a_records(cname, resolve_cname=False)
                        if cname_a:
                            record["cname_chain"] = cname_a
            
            return records
        
        return []
    
    async def get_mx_records(
        self,
        domain: str,
    ) -> List[Dict[str, Any]]:
        """
        Get MX records for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            List of MX record dictionaries
        """
        result = await self.dns_client.resolve(domain, "MX")
        
        if result.found:
            records = []
            for record in result.records:
                parts = record.value.split()
                records.append({
                    "priority": int(parts[0]) if len(parts) > 1 else 0,
                    "target": parts[-1] if parts else record.value,
                    "ttl": record.ttl,
                    "ip_addresses": await self._resolve_hostname(parts[-1]) if parts else [],
                })
            
            return records
        
        return []
    
    async def get_txt_records(
        self,
        domain: str,
        parse_spf_dkim_dmarc: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Get TXT records for a domain.
        
        Args:
            domain: Domain name
            parse_spf_dkim_dmarc: Whether to parse SPF, DKIM, DMARC records
            
        Returns:
            List of TXT record dictionaries
        """
        result = await self.dns_client.resolve(domain, "TXT")
        
        if result.found:
            records = []
            for record in result.records:
                txt_value = record.value
                record_dict = {
                    "value": txt_value,
                    "ttl": record.ttl,
                    "type": "txt",
                }
                
                if parse_spf_dkim_dmarc:
                    if txt_value.startswith("v=spf1"):
                        record_dict["type"] = "spf"
                        record_dict["parsed"] = self._parse_spf_record(txt_value)
                    elif txt_value.startswith("v=DKIM1") or "dkim" in txt_value.lower():
                        record_dict["type"] = "dkim"
                        record_dict["selector"] = self._extract_dkim_selector(txt_value)
                    elif txt_value.startswith("v=DMARC1"):
                        record_dict["type"] = "dmarc"
                        record_dict["parsed"] = self._parse_dmarc_record(txt_value)
                
                records.append(record_dict)
            
            return records
        
        return []
    
    async def get_nameserver_records(
        self,
        domain: str,
    ) -> List[Dict[str, Any]]:
        """
        Get NS records for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            List of NS record dictionaries
        """
        result = await self.dns_client.resolve(domain, "NS")
        
        if result.found:
            records = []
            for record in result.records:
                ns_domain = record.value
                record_dict = {
                    "nameserver": ns_domain,
                    "ttl": record.ttl,
                    "ip_addresses": await self._resolve_hostname(ns_domain),
                }
                records.append(record_dict)
            
            return records
        
        return []
    
    async def get_historical_dns(
        self,
        domain: str,
    ) -> DnsHistoryResult:
        """
        Get historical DNS records for a domain.
        
        Args:
            domain: Domain name
            
        Returns:
            DnsHistoryResult with historical records
        """
        logger.info(f"Getting historical DNS for {domain}")
        
        result = DnsHistoryResult(domain=domain)
        
        if not self._securitytrails:
            result.error = "SecurityTrails API not configured"
            return result
        
        try:
            # Get historical A records
            history = await self._securitytrails.get_dns_history(domain, "A")
            
            if history:
                result.history["a"] = [
                    {
                        "values": record.values,
                        "first_seen": record.first_seen.isoformat() if record.first_seen else None,
                        "last_seen": record.last_seen.isoformat() if record.last_seen else None,
                    }
                    for record in history.a_records
                ]
            
            # Get IP history
            ip_history = await self._securitytrails.get_ip_history(domain)
            
            if ip_history:
                result.ip_changes = [
                    {
                        "ip": change.get("ip"),
                        "first_seen": change.get("first_seen"),
                        "last_seen": change.get("last_seen"),
                    }
                    for change in ip_history
                ]
            
        except Exception as e:
            logger.error(f"Failed to get historical DNS for {domain}: {e}")
            result.error = str(e)
        
        return result
    
    async def check_propagation(
        self,
        domain: str,
        nameservers: Optional[List[str]] = None,
    ) -> DnsPropagationResult:
        """
        Check DNS propagation across nameservers.
        
        Args:
            domain: Domain name
            nameservers: Specific nameservers to check
            
        Returns:
            DnsPropagationResult with propagation status
        """
        logger.info(f"Checking DNS propagation for {domain}")
        
        result = DnsPropagationResult(domain=domain)
        
        try:
            # Get authoritative nameservers
            if not nameservers:
                ns_records = await self.get_nameserver_records(domain)
                nameservers = [ns["nameserver"] for ns in ns_records]
            
            if not nameservers:
                result.inconsistencies.append("No nameservers found")
                result.is_propagated = False
                return result
            
            # Query each nameserver for A records
            a_record_values = set()
            
            for ns in nameservers:
                try:
                    # Create resolver pointing to specific nameserver
                    resolver = self.dns_client
                    resolver.nameservers = await self._resolve_hostname(ns)
                    
                    dns_result = await resolver.resolve(domain, "A")
                    ns_values = set(r.value for r in dns_result.records)
                    
                    result.nameservers[ns] = {
                        "ip": resolver.nameservers,
                        "a_records": list(ns_values),
                        "reachable": True,
                    }
                    
                    if not a_record_values:
                        a_record_values = ns_values
                    elif ns_values != a_record_values:
                        result.inconsistencies.append(
                            f"NS {ns} has different A records: {ns_values}"
                        )
                        
                except Exception as e:
                    result.nameservers[ns] = {
                        "nameserver": ns,
                        "reachable": False,
                        "error": str(e),
                    }
                    result.inconsistencies.append(f"NS {ns} unreachable: {e}")
            
            result.is_propagated = len(result.inconsistencies) == 0
            
        except Exception as e:
            logger.error(f"Propagation check failed for {domain}: {e}")
            result.inconsistencies.append(str(e))
            result.is_propagated = False
        
        return result
    
    async def detect_dns_takeover(
        self,
        domain: str,
    ) -> List[Dict[str, Any]]:
        """
        Check for potential DNS takeover vulnerabilities.
        
        Args:
            domain: Domain name
            
        Returns:
            List of potential takeover vulnerabilities
        """
        logger.info(f"Checking DNS takeover vulnerabilities for {domain}")
        
        vulnerabilities = []
        
        try:
            # Check CNAME records for dangling references
            cname_result = await self.dns_client.resolve(domain, "CNAME")
            
            for record in cname_result.records:
                target = record.value
                
                # Check if target resolves
                try:
                    a_result = await self.dns_client.resolve(target, "A")
                    if not a_result.found or not a_result.records:
                        vulnerabilities.append({
                            "type": "dangling_cname",
                            "record": record.value,
                            "description": f"CNAME {record.value} does not resolve",
                            "severity": "high",
                        })
                except Exception:
                    vulnerabilities.append({
                        "type": "dangling_cname",
                        "record": record.value,
                        "description": f"CNAME {record.value} lookup failed",
                        "severity": "medium",
                    })
            
            # Check NS records for dangling references
            ns_result = await self.dns_client.resolve(domain, "NS")
            
            for record in ns_result.records:
                ns_domain = record.value
                
                # Check if nameserver resolves
                try:
                    a_result = await self.dns_client.resolve(ns_domain, "A")
                    if not a_result.found or not a_result.records:
                        vulnerabilities.append({
                            "type": "dangling_ns",
                            "record": record.value,
                            "description": f"Nameserver {record.value} does not resolve",
                            "severity": "high",
                        })
                except Exception:
                    pass  # NS records might not resolve, which is normal
            
        except Exception as e:
            logger.error(f"DNS takeover check failed for {domain}: {e}")
        
        return vulnerabilities
    
    def _parse_dns_result(self, dns_result: DnsResult) -> List[Dict[str, Any]]:
        """Parse DNS result into list of dictionaries."""
        records = []
        
        for record in dns_result.records:
            record_dict = {
                "value": record.value,
                "ttl": record.ttl,
            }
            records.append(record_dict)
        
        return records
    
    def _identify_email_providers(self, mx_records: List[Dict[str, Any]]) -> List[str]:
        """Identify email providers from MX records."""
        providers = set()
        
        for mx in mx_records:
            target = mx.get("target", "").lower()
            
            for provider, patterns in self.EMAIL_PROVIDERS.items():
                for pattern in patterns:
                    if pattern in target:
                        providers.add(provider)
                        break
        
        return list(providers)
    
    async def _resolve_nameserver_ips(
        self,
        nameservers: List[str],
    ) -> Dict[str, List[str]]:
        """Resolve nameserver domains to IP addresses."""
        ns_ips = {}
        
        for ns in nameservers:
            ips = await self._resolve_hostname(ns)
            ns_ips[ns] = ips
        
        return ns_ips
    
    async def _resolve_hostname(self, hostname: str) -> List[str]:
        """Resolve a hostname to IP addresses."""
        try:
            a_result = await self.dns_client.resolve(hostname, "A")
            aaaa_result = await self.dns_client.resolve(hostname, "AAAA")
            
            ips = [r.value for r in a_result.records]
            ips.extend(r.value for r in aaaa_result.records)
            
            return ips
            
        except Exception:
            return []
    
    def _parse_spf_record(self, spf: str) -> Dict[str, Any]:
        """Parse SPF record into components."""
        result = {
            "mechanisms": [],
            "modifiers": {},
            "all": "softfail",
        }
        
        parts = spf.split()
        for part in parts:
            if part.startswith("v=spf1"):
                continue
            elif part.startswith("all"):
                result["all"] = part
            elif part.startswith("include:"):
                result["mechanisms"].append({
                    "type": "include",
                    "domain": part[8:],
                })
            elif part.startswith("a:"):
                result["mechanisms"].append({
                    "type": "a",
                    "domain": part[2:] or None,
                })
            elif part.startswith("mx:"):
                result["mechanisms"].append({
                    "type": "mx",
                    "domain": part[3:] or None,
                })
            elif part.startswith("ptr:"):
                result["mechanisms"].append({
                    "type": "ptr",
                    "domain": part[4:] or None,
                })
            elif part.startswith("ip4:"):
                result["mechanisms"].append({
                    "type": "ip4",
                    "cidr": part[4:],
                })
            elif part.startswith("ip6:"):
                result["mechanisms"].append({
                    "type": "ip6",
                    "cidr": part[4:],
                })
            elif part.startswith("exists:"):
                result["mechanisms"].append({
                    "type": "exists",
                    "domain": part[7:],
                })
            elif part.startswith("redirect="):
                result["modifiers"]["redirect"] = part[9:]
            elif part.startswith("exp="):
                result["modifiers"]["exp"] = part[4:]
            elif part.startswith("~") or part.startswith("+"):
                result["mechanisms"].append({
                    "type": part[1:] if part.startswith("+") else part,
                    "qualifier": part[0] if part[0] in "~-+?" else None,
                })
            else:
                result["mechanisms"].append({
                    "type": part,
                })
        
        return result
    
    def _parse_dmarc_record(self, dmarc: str) -> Dict[str, Any]:
        """Parse DMARC record into components."""
        result = {}
        
        parts = dmarc.split()
        for part in parts:
            if part.startswith("v=DMARC1"):
                continue
            elif part.startswith("p="):
                result["policy"] = part[2:]
            elif part.startswith("sp="):
                result["subdomain_policy"] = part[3:]
            elif part.startswith("adkim="):
                result["alignment_mode_dkim"] = part[6:]
            elif part.startswith("aspf="):
                result["alignment_mode_spf"] = part[5:]
            elif part.startswith("pct="):
                result["percentage"] = int(part[4:])
            elif part.startswith("rua="):
                result["aggregate_report_uri"] = part[4:]
            elif part.startswith("ruf="):
                result["forensic_report_uri"] = part[4:]
            elif part.startswith("fo="):
                result["failure_options"] = part[3:]
        
        return result
    
    def _extract_dkim_selector(self, dkim: str) -> Optional[str]:
        """Extract DKIM selector from record."""
        match = re.search(r"k=rsa;\s*s=(\w+)", dkim)
        return match.group(1) if match else None
    
    async def close(self):
        """Close client connections."""
        if self._securitytrails:
            await self._securitytrails.close()
            self._securitytrails = None
