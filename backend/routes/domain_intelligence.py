"""
Domain Intelligence API Routes.

Provides REST API endpoints for domain intelligence operations.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from modules.whois_lookup import WhoisLookup, DomainWhoisResult, IpWhoisResult
from modules.dns_enumeration import DnsEnumeration, DnsEnumerateResult, DnsHistoryResult
from modules.subdomain_discovery import SubdomainDiscovery, SubdomainDiscoveryResult
from modules.ssl_analysis import SslAnalysis, SslAnalysisResult
from modules.infrastructure_mapping import InfrastructureMapping, ReverseIpResult
from modules.related_domains import RelatedDomains, DomainPortfolioResult, DomainVariationsResult

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/search", tags=["domain-intelligence"])


# Pydantic Models for API

class WhoisRequest(BaseModel):
    """WHOIS lookup request."""
    domain: str = Field(..., description="Domain name or IP address to look up")
    include_raw: bool = Field(False, description="Include raw WHOIS response")


class WhoisResponse(BaseModel):
    """WHOIS lookup response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DnsRecordsRequest(BaseModel):
    """DNS records request."""
    domain: str = Field(..., description="Domain name to query")
    include_txt: bool = Field(True, description="Include TXT records")


class DnsRecordsResponse(BaseModel):
    """DNS records response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SubdomainsRequest(BaseModel):
    """Subdomain discovery request."""
    domain: str = Field(..., description="Domain to enumerate")
    methods: Optional[List[str]] = Field(None, description="Discovery methods to use")
    brute_force: bool = Field(True, description="Use brute force enumeration")
    include_inactive: bool = Field(False, description="Include non-resolving subdomains")


class SubdomainsResponse(BaseModel):
    """Subdomain discovery response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SslCertificatesRequest(BaseModel):
    """SSL certificate analysis request."""
    domain: str = Field(..., description="Domain or IP address")
    port: int = Field(443, description="SSL port")


class SslCertificatesResponse(BaseModel):
    """SSL certificate analysis response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ReverseIpRequest(BaseModel):
    """Reverse IP lookup request."""
    ip: str = Field(..., description="IP address")


class ReverseIpResponse(BaseModel):
    """Reverse IP lookup response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class RelatedDomainsRequest(BaseModel):
    """Related domains request."""
    domain: Optional[str] = Field(None, description="Domain name")
    email: Optional[str] = Field(None, description="Email address")
    company: Optional[str] = Field(None, description="Company name")
    include_infrastructure: bool = Field(True, description="Include infrastructure links")
    include_certificates: bool = Field(True, description="Include certificate links")


class RelatedDomainsResponse(BaseModel):
    """Related domains response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DomainVariationsRequest(BaseModel):
    """Domain variations request."""
    domain: str = Field(..., description="Original domain name")
    check_existence: bool = Field(True, description="Check if variations exist")


class DomainVariationsResponse(BaseModel):
    """Domain variations response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class InfrastructureRequest(BaseModel):
    """Infrastructure mapping request."""
    domain: str = Field(..., description="Domain to map")
    check_common_ports: bool = Field(True, description="Check common ports")
    find_related_domains: bool = Field(True, description="Find related domains")


class InfrastructureResponse(BaseModel):
    """Infrastructure mapping response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DnsHistoryRequest(BaseModel):
    """DNS history request."""
    domain: str = Field(..., description="Domain name")


class DnsHistoryResponse(BaseModel):
    """DNS history response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class DomainPortfolioRequest(BaseModel):
    """Domain portfolio request."""
    email: Optional[str] = Field(None, description="Email address")
    company: Optional[str] = Field(None, description="Company name")


class DomainPortfolioResponse(BaseModel):
    """Domain portfolio response."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# Dependency injection for modules
def get_whois_lookup() -> WhoisLookup:
    """Get WHOIS lookup module instance."""
    from app import config
    return WhoisLookup(
        securitytrails_api_key=config.securitytrails_api_key,
    )


def get_dns_enumeration() -> DnsEnumeration:
    """Get DNS enumeration module instance."""
    from app import config
    return DnsEnumeration(
        securitytrails_api_key=config.securitytrails_api_key,
    )


def get_subdomain_discovery() -> SubdomainDiscovery:
    """Get subdomain discovery module instance."""
    from app import config
    return SubdomainDiscovery(
        securitytrails_api_key=config.securitytrails_api_key,
    )


def get_ssl_analysis() -> SslAnalysis:
    """Get SSL analysis module instance."""
    from app import config
    return SslAnalysis(
        censys_api_id=config.censys_api_id,
        censys_api_secret=config.censys_api_secret,
        shodan_api_key=config.shodan_api_key,
    )


def get_infrastructure_mapping() -> InfrastructureMapping:
    """Get infrastructure mapping module instance."""
    from app import config
    return InfrastructureMapping(
        censys_api_id=config.censys_api_id,
        censys_api_secret=config.censys_api_secret,
        shodan_api_key=config.shodan_api_key,
        securitytrails_api_key=config.securitytrails_api_key,
        geoip_db_path=config.geoip_db_path,
    )


def get_related_domains() -> RelatedDomains:
    """Get related domains module instance."""
    from app import config
    return RelatedDomains(
        securitytrails_api_key=config.securitytrails_api_key,
        censys_api_id=config.censys_api_id,
        censys_api_secret=config.censys_api_secret,
        shodan_api_key=config.shodan_api_key,
    )


# API Endpoints

@router.post("/whois", response_model=WhoisResponse)
async def whois_lookup(
    request: WhoisRequest,
    whois: WhoisLookup = Depends(get_whois_lookup),
):
    """
    Perform WHOIS lookup for a domain or IP address.
    
    Returns registrant information, registrar details, dates, and nameservers.
    """
    try:
        # Determine if domain or IP
        import ipaddress
        
        try:
            ipaddress.ip_address(request.domain)
            result = await whois.lookup_ip(request.domain)
        except ValueError:
            result = await whois.lookup_domain(request.domain, include_raw=request.include_raw)
        
        return WhoisResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"WHOIS lookup failed: {e}")
        return WhoisResponse(
            success=False,
            error=str(e),
        )


@router.post("/dns-records", response_model=DnsRecordsResponse)
async def dns_records(
    request: DnsRecordsRequest,
    dns: DnsEnumeration = Depends(get_dns_enumeration),
):
    """
    Enumerate DNS records for a domain.
    
    Returns A, AAAA, MX, TXT, CNAME, NS, and other records.
    """
    try:
        result = await dns.enumerate_all(request.domain, include_txt=request.include_txt)
        
        return DnsRecordsResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"DNS enumeration failed: {e}")
        return DnsRecordsResponse(
            success=False,
            error=str(e),
        )


@router.post("/subdomains", response_model=SubdomainsResponse)
async def subdomains(
    request: SubdomainsRequest,
    subdomain: SubdomainDiscovery = Depends(get_subdomain_discovery),
):
    """
    Discover subdomains for a domain.
    
    Uses Certificate Transparency logs, brute force, and DNS enumeration.
    """
    try:
        result = await subdomain.discover(
            request.domain,
            methods=request.methods,
            brute_force=request.brute_force,
            include_inactive=request.include_inactive,
        )
        
        return SubdomainsResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"Subdomain discovery failed: {e}")
        return SubdomainsResponse(
            success=False,
            error=str(e),
        )


@router.post("/ssl-certificates", response_model=SslCertificatesResponse)
async def ssl_certificates(
    request: SslCertificatesRequest,
    ssl: SslAnalysis = Depends(get_ssl_analysis),
):
    """
    Analyze SSL certificates for a domain.
    
    Returns certificate details, SANs, issuer, and validity information.
    """
    try:
        result = await ssl.analyze(request.domain, port=request.port)
        
        return SslCertificatesResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"SSL analysis failed: {e}")
        return SslCertificatesResponse(
            success=False,
            error=str(e),
        )


@router.post("/reverse-ip", response_model=ReverseIpResponse)
async def reverse_ip(
    request: ReverseIpRequest,
    infra: InfrastructureMapping = Depends(get_infrastructure_mapping),
):
    """
    Find all domains hosted on an IP address.
    
    Returns domains using reverse IP lookup and certificate data.
    """
    try:
        result = await infra.reverse_ip_lookup(request.ip)
        
        return ReverseIpResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"Reverse IP lookup failed: {e}")
        return ReverseIpResponse(
            success=False,
            error=str(e),
        )


@router.post("/related-domains", response_model=RelatedDomainsResponse)
async def related_domains(
    request: RelatedDomainsRequest,
    related: RelatedDomains = Depends(get_related_domains),
):
    """
    Find domains related to the target.
    
    Uses WHOIS, infrastructure, and certificate data to find related domains.
    """
    try:
        if not any([request.domain, request.email, request.company]):
            raise ValueError("Must provide domain, email, or company")
        
        if request.domain:
            result = await related.find_related_domains(
                request.domain,
                include_infrastructure=request.include_infrastructure,
                include_certificates=request.include_certificates,
            )
            
            return RelatedDomainsResponse(
                success=True,
                result={
                    "query": request.domain,
                    "query_type": "domain",
                    "related_domains": [d.to_dict() for d in result],
                    "total_related": len(result),
                },
            )
        elif request.email:
            result = await related.find_domains_by_email(request.email)
            
            return RelatedDomainsResponse(
                success=True,
                result=result.to_dict(),
            )
        elif request.company:
            result = await related.find_domains_by_company(request.company)
            
            return RelatedDomainsResponse(
                success=True,
                result=result.to_dict(),
            )
        
    except Exception as e:
        logger.error(f"Related domains search failed: {e}")
        return RelatedDomainsResponse(
            success=False,
            error=str(e),
        )


@router.post("/domain-variations", response_model=DomainVariationsResponse)
async def domain_variations(
    request: DomainVariationsRequest,
    related: RelatedDomains = Depends(get_related_domains),
):
    """
    Find domain variations and typosquatting candidates.
    
    Generates and checks domain variations for potential impersonation.
    """
    try:
        result = await related.find_domain_variations(
            request.domain,
            check_existence=request.check_existence,
        )
        
        return DomainVariationsResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"Domain variations search failed: {e}")
        return DomainVariationsResponse(
            success=False,
            error=str(e),
        )


@router.post("/dns-history", response_model=DnsHistoryResponse)
async def dns_history(
    request: DnsHistoryRequest,
    dns: DnsEnumeration = Depends(get_dns_enumeration),
):
    """
    Get historical DNS records for a domain.
    
    Returns historical A records, IP changes, and DNS changes.
    """
    try:
        result = await dns.get_historical_dns(request.domain)
        
        return DnsHistoryResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"DNS history lookup failed: {e}")
        return DnsHistoryResponse(
            success=False,
            error=str(e),
        )


@router.post("/domain-portfolio", response_model=DomainPortfolioResponse)
async def domain_portfolio(
    request: DomainPortfolioRequest,
    related: RelatedDomains = Depends(get_related_domains),
):
    """
    Find all domains for a person or company.
    
    Returns complete domain portfolio with registration details.
    """
    try:
        if not any([request.email, request.company]):
            raise ValueError("Must provide email or company")
        
        if request.email:
            result = await related.find_domains_by_email(request.email)
        else:
            result = await related.find_domains_by_company(request.company)
        
        return DomainPortfolioResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"Domain portfolio search failed: {e}")
        return DomainPortfolioResponse(
            success=False,
            error=str(e),
        )


# Infrastructure endpoints

@router.get("/infrastructure/{domain}", response_model=InfrastructureResponse)
async def get_infrastructure(
    domain: str,
    check_common_ports: bool = Query(True),
    find_related_domains: bool = Query(True),
    infra: InfrastructureMapping = Depends(get_infrastructure_mapping),
):
    """
    Get complete infrastructure map for a domain.
    
    Returns IPs, services, ASN info, geolocation, and related domains.
    """
    try:
        result = await infra.map_infrastructure(
            domain,
            check_common_ports=check_common_ports,
            find_related_domains=find_related_domains,
        )
        
        return InfrastructureResponse(
            success=True,
            result=result.to_dict(),
        )
    except Exception as e:
        logger.error(f"Infrastructure mapping failed: {e}")
        return InfrastructureResponse(
            success=False,
            error=str(e),
        )


# Bulk search endpoints

@router.post("/bulk/whois")
async def bulk_whois(
    domains: List[str],
    whois: WhoisLookup = Depends(get_whois_lookup),
):
    """
    Perform WHOIS lookups for multiple domains.
    
    Returns results for all domains.
    """
    results = {}
    
    for domain in domains:
        try:
            result = await whois.lookup_domain(domain)
            results[domain] = result.to_dict()
        except Exception as e:
            results[domain] = {"error": str(e)}
    
    return {"results": results}


@router.post("/bulk/dns")
async def bulk_dns(
    domains: List[str],
    dns: DnsEnumeration = Depends(get_dns_enumeration),
):
    """
    Enumerate DNS records for multiple domains.
    
    Returns results for all domains.
    """
    results = {}
    
    for domain in domains:
        try:
            result = await dns.enumerate_all(domain)
            results[domain] = result.to_dict()
        except Exception as e:
            results[domain] = {"error": str(e)}
    
    return {"results": results}


@router.post("/bulk/subdomains")
async def bulk_subdomains(
    domains: List[str],
    subdomain: SubdomainDiscovery = Depends(get_subdomain_discovery),
):
    """
    Discover subdomains for multiple domains.
    
    Returns results for all domains.
    """
    results = {}
    
    for domain in domains:
        try:
            result = await subdomain.discover(domain)
            results[domain] = result.to_dict()
        except Exception as e:
            results[domain] = {"error": str(e)}
    
    return {"results": results}
