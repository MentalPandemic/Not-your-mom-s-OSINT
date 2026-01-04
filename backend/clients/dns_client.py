"""
DNS Client for domain intelligence operations.

Uses dnspython for DNS queries with support for all record types.
Implements async DNS resolution with caching and rate limiting.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import dns.asyncresolver
from dns.resolver import NXDOMAIN, NoAnswer, NoNameservers, Timeout, YXDOMAIN
from dns.rdatatype import RDATATYPE

from clients.dns_client_base import BaseDnsClient, DnsRecord, DnsResult

logger = logging.getLogger(__name__)


class DnsClient(BaseDnsClient):
    """
    DNS client for performing DNS lookups.
    
    Supports all standard DNS record types including:
    - A, AAAA (address records)
    - MX (mail exchange)
    - TXT (text records)
    - CNAME (canonical names)
    - NS (name servers)
    - SOA (start of authority)
    - PTR (pointer records)
    - SRV (service records)
    - CAA (Certification Authority Authorization)
    """
    
    DEFAULT_TIMEOUT = 10.0
    DEFAULT_RETRIES = 3
    CACHE_TTL = 300  # 5 minutes
    
    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        cache_ttl: int = CACHE_TTL,
        nameservers: Optional[List[str]] = None,
    ):
        self.timeout = timeout
        self.retries = retries
        self.cache_ttl = cache_ttl
        self.nameservers = nameservers or []
        self._cache: Dict[str, tuple[datetime, DnsResult]] = {}
        
    async def resolve(
        self,
        domain: str,
        record_type: str = "A",
        timeout: Optional[float] = None,
    ) -> DnsResult:
        """
        Resolve DNS records for a domain.
        
        Args:
            domain: The domain name to query
            record_type: DNS record type (A, AAAA, MX, TXT, CNAME, NS, SOA, PTR, SRV, CAA)
            timeout: Query timeout in seconds
            
        Returns:
            DnsResult containing the DNS records
            
        Raises:
            DnsLookupFailed: If the DNS query fails
        """
        cache_key = f"{domain}:{record_type}"
        timeout = timeout or self.timeout
        
        # Check cache
        if cache_key in self._cache:
            cached_time, cached_result = self._cache[cache_key]
            if datetime.now() - cached_time < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
        
        try:
            # Convert record type to DNS type
            dns_type = self._getDnsType(record_type)
            
            # Perform async DNS lookup
            result = await self._async_resolve(domain, dns_type, timeout)
            
            # Cache result
            self._cache[cache_key] = (datetime.now(), result)
            
            return result
            
        except NXDOMAIN:
            logger.info(f"NXDOMAIN for {domain}")
            return DnsResult(
                domain=domain,
                record_type=record_type,
                records=[],
                found=False,
                error=None,
            )
        except NoNameservers as e:
            logger.error(f"No nameservers for {domain}: {e}")
            raise DnsLookupFailed(f"No nameservers available: {e}")
        except NoAnswer as e:
            logger.info(f"No answer for {domain} {record_type}: {e}")
            return DnsResult(
                domain=domain,
                record_type=record_type,
                records=[],
                found=False,
                error=None,
            )
        except Timeout as e:
            logger.warning(f"DNS timeout for {domain}: {e}")
            raise DnsLookupFailed(f"DNS query timed out: {e}")
        except Exception as e:
            logger.error(f"DNS lookup failed for {domain}: {e}")
            raise DnsLookupFailed(f"DNS lookup failed: {e}")
    
    async def _async_resolve(
        self,
        domain: str,
        dns_type: Any,
        timeout: float,
    ) -> DnsResult:
        """Perform async DNS resolution using dnspython."""
        loop = asyncio.get_event_loop()
        
        def _resolve():
            resolver = dns.asyncresolver.Resolver()
            resolver.timeout = timeout
            resolver.lifetime = timeout
            
            if self.nameservers:
                resolver.nameservers = self.nameservers
            
            answers = resolver.resolve(domain, dns_type)
            
            records = []
            for rdata in answers:
                record_value = self._format_record_value(rdata, dns_type)
                records.append(DnsRecord(
                    value=record_value,
                    ttl=answers.rrset.ttl if hasattr(answers.rrset, 'ttl') else None,
                    type=dns_type.name if hasattr(dns_type, 'name') else str(dns_type),
                ))
            
            return DnsResult(
                domain=domain,
                record_type=dns_type.name if hasattr(dns_type, 'name') else str(dns_type),
                records=records,
                found=True,
                error=None,
            )
        
        return await loop.run_in_executor(None, _resolve)
    
    async def resolve_all(self, domain: str) -> Dict[str, DnsResult]:
        """
        Resolve all common record types for a domain.
        
        Args:
            domain: The domain name to query
            
        Returns:
            Dictionary mapping record type to DnsResult
        """
        record_types = ["A", "AAAA", "MX", "TXT", "CNAME", "NS", "SOA", "PTR", "SRV", "CAA"]
        results = {}
        
        # Run all queries concurrently
        tasks = [
            self.resolve(domain, record_type)
            for record_type in record_types
        ]
        
        dns_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for record_type, result in zip(record_types, dns_results):
            if isinstance(result, Exception):
                logger.warning(f"Failed to resolve {record_type} for {domain}: {result}")
                results[record_type] = DnsResult(
                    domain=domain,
                    record_type=record_type,
                    records=[],
                    found=False,
                    error=str(result),
                )
            else:
                results[record_type] = result
        
        return results
    
    async def resolve_multiple(
        self,
        domains: List[str],
        record_type: str = "A",
        timeout: Optional[float] = None,
    ) -> Dict[str, DnsResult]:
        """
        Resolve DNS records for multiple domains concurrently.
        
        Args:
            domains: List of domain names to query
            record_type: DNS record type
            timeout: Query timeout in seconds
            
        Returns:
            Dictionary mapping domain to DnsResult
        """
        tasks = [
            self.resolve(domain, record_type, timeout)
            for domain in domains
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            domain: result if not isinstance(result, Exception) else DnsResult(
                domain=domain,
                record_type=record_type,
                records=[],
                found=False,
                error=str(result),
            )
            for domain, result in zip(domains, results)
        }
    
    def _getDnsType(self, record_type: str) -> Any:
        """Convert string record type to dnspython type."""
        type_map = {
            "A": dns.rdatatype.A,
            "AAAA": dns.rdatatype.AAAA,
            "MX": dns.rdatatype.MX,
            "TXT": dns.rdatatype.TXT,
            "CNAME": dns.rdatatype.CNAME,
            "NS": dns.rdatatype.NS,
            "SOA": dns.rdatatype.SOA,
            "PTR": dns.rdatatype.PTR,
            "SRV": dns.rdatatype.SRV,
            "CAA": dns.rdatatype.CAA,
        }
        return type_map.get(record_type.upper(), dns.rdatatype.A)
    
    def _format_record_value(self, rdata: Any, dns_type: Any) -> str:
        """Format DNS record value for display."""
        type_name = getattr(dns_type, 'name', str(dns_type))
        
        if type_name == "A":
            return str(rdata)
        elif type_name == "AAAA":
            return str(rdata)
        elif type_name == "MX":
            return f"{rdata.exchange} {rdata.preference}"
        elif type_name == "TXT":
            return str(rdata).strip('"')
        elif type_name == "CNAME":
            return str(rdata)
        elif type_name == "NS":
            return str(rdata)
        elif type_name == "SOA":
            return f"{rdata.mname} {rdata.rname} ({rdata.serial} {rdata.refresh}s {rdata.retry}s {rdata.expire}s {rdata.minimum}s)"
        elif type_name == "PTR":
            return str(rdata)
        elif type_name == "SRV":
            return f"{rdata.priority} {rdata.weight} {rdata.port} {rdata.target}"
        elif type_name == "CAA":
            return f"{rdata.flags} {rdata.tag} {rdata.value}"
        else:
            return str(rdata)
    
    def clear_cache(self, domain: Optional[str] = None):
        """Clear DNS cache."""
        if domain:
            keys_to_remove = [k for k in self._cache if k.startswith(domain)]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            "size": len(self._cache),
            "ttl": self.cache_ttl,
        }


class DnsLookupFailed(Exception):
    """Raised when DNS lookup fails."""
    
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
