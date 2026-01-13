"""
Domain Intelligence API Routes

This module contains FastAPI routes for domain intelligence operations including
WHOIS lookup, DNS enumeration, subdomain discovery, SSL analysis, and infrastructure mapping.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl
from typing import Dict, List, Optional, Any
import asyncio
import logging
from datetime import datetime

# Import domain intelligence modules
from modules.whois_lookup import WHOISLookup, DomainWHOIS, IPWHOIS
from modules.dns_enumeration import DNSEnumeration
from modules.subdomain_discovery import SubdomainDiscovery
from modules.ssl_analysis import SSLAnalyzer
from modules.infrastructure_mapping import InfrastructureMapping
from modules.related_domains import RelatedDomainDiscovery

# Import database utilities
from database.config import get_postgres_session, get_neo4j_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/search", tags=["domain-intelligence"])

# Pydantic models for API requests/responses
class WHOISRequest(BaseModel):
    target: str = Field(..., description="Domain or IP address to lookup")
    include_analysis: bool = Field(True, description="Include additional analysis")
    timeout: int = Field(30, description="Request timeout in seconds")

class WHOISResponse(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    execution_time: float

class DNSRequest(BaseModel):
    domain: str = Field(..., description="Domain to enumerate")
    record_types: List[str] = Field(["A", "AAAA", "MX", "TXT", "CNAME", "NS"], description="DNS record types to query")
    include_history: bool = Field(False, description="Include DNS history")
    include_propagation: bool = Field(False, description="Check DNS propagation")
    timeout: int = Field(30, description="Request timeout in seconds")

class SubdomainRequest(BaseModel):
    domain: str = Field(..., description="Target domain")
    use_extended_wordlist: bool = Field(False, description="Use extended subdomain wordlist")
    include_cert_transparency: bool = Field(True, description="Include certificate transparency search")
    analyze_subdomains: bool = Field(True, description="Analyze discovered subdomains")
    timeout: int = Field(300, description="Request timeout in seconds")

class SSLRequest(BaseModel):
    target: str = Field(..., description="Domain or IP address")
    include_chain: bool = Field(True, description="Include certificate chain")
    include_history: bool = Field(True, description="Include certificate history")
    analyze_security: bool = Field(True, description="Perform security analysis")
    timeout: int = Field(30, description="Request timeout in seconds")

class ReverseIPRequest(BaseModel):
    ip_address: str = Field(..., description="IP address for reverse lookup")
    include_services: bool = Field(True, description="Include service information")
    timeout: int = Field(60, description="Request timeout in seconds")

class RelatedDomainsRequest(BaseModel):
    target: str = Field(..., description="Domain, email, or company name")
    search_types: List[str] = Field(["variations", "registrant_links", "infrastructure_links"], 
                                   description="Types of relationships to search")
    max_results: int = Field(100, description="Maximum number of results")
    timeout: int = Field(120, description="Request timeout in seconds")

class InfrastructureRequest(BaseModel):
    domain: str = Field(..., description="Target domain")
    include_port_scan: bool = Field(True, description="Include port scanning")
    include_services: bool = Field(True, description="Include service detection")
    include_cdn_detection: bool = Field(True, description="Include CDN detection")
    timeout: int = Field(120, description="Request timeout in seconds")

class DomainPortfolioRequest(BaseModel):
    identifier: str = Field(..., description="Email address or company name")
    identifier_type: str = Field("email", description="Type of identifier: email or company")
    include_analysis: bool = Field(True, description="Include domain analysis")
    timeout: int = Field(60, description="Request timeout in seconds")


# Dependency injection for domain intelligence services
async def get_whois_service() -> WHOISLookup:
    return WHOISLookup()

async def get_dns_service() -> DNSEnumeration:
    return DNSEnumeration()

async def get_subdomain_service() -> SubdomainDiscovery:
    return SubdomainDiscovery()

async def get_ssl_service() -> SSLAnalyzer:
    return SSLAnalyzer()

async def get_infrastructure_service() -> InfrastructureMapping:
    return InfrastructureMapping()

async def get_related_domains_service() -> RelatedDomainDiscovery:
    return RelatedDomainDiscovery()


# WHOIS Endpoints
@router.post("/whois", response_model=WHOISResponse)
async def perform_whois_lookup(
    request: WHOISRequest,
    background_tasks: BackgroundTasks,
    whois_service: WHOISLookup = Depends(get_whois_service),
    postgres_session: AsyncSession = Depends(get_postgres_session)
):
    """Perform WHOIS lookup for domain or IP address."""
    start_time = datetime.utcnow()
    
    try:
        # Determine if target is domain or IP
        target = request.target.strip().lower()
        is_ip = target.replace('.', '').replace(':', '').isdigit()
        
        if is_ip:
            # IP WHOIS lookup
            ip_info = await whois_service.lookup_ip(target)
            result = ip_info.to_dict()
        else:
            # Domain WHOIS lookup
            domain_info = await whois_service.lookup_domain(target)
            
            # Perform additional analysis if requested
            if request.include_analysis:
                analysis = await whois_service.analyze_registrant(domain_info)
                result = {
                    **domain_info.to_dict(),
                    'analysis': analysis
                }
            else:
                result = domain_info.to_dict()
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log the query (background task)
        background_tasks.add_task(log_whois_query, target, is_ip, execution_time, True, None)
        
        return WHOISResponse(
            success=True,
            data=result,
            execution_time=execution_time
        )
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_message = str(e)
        
        # Log the failed query (background task)
        background_tasks.add_task(log_whois_query, target, is_ip, execution_time, False, error_message)
        
        logger.error(f"WHOIS lookup failed for {target}: {error_message}")
        
        raise HTTPException(status_code=500, detail=f"WHOIS lookup failed: {error_message}")


# DNS Enumeration Endpoints
@router.post("/dns-records")
async def enumerate_dns_records(
    request: DNSRequest,
    background_tasks: BackgroundTasks,
    dns_service: DNSEnumeration = Depends(get_dns_service),
    postgres_session: AsyncSession = Depends(get_postgres_session)
):
    """Enumerate DNS records for a domain."""
    start_time = datetime.utcnow()
    
    try:
        domain = request.domain.strip().lower()
        
        # Get all requested record types
        all_records = {}
        
        # Query each record type
        for record_type in request.record_types:
            if record_type.upper() == 'A':
                records = await dns_service.get_a_records(domain)
            elif record_type.upper() == 'AAAA':
                records = await dns_service.get_aaaa_records(domain)
            elif record_type.upper() == 'MX':
                records = await dns_service.get_mx_records(domain)
                all_records['mx_analysis'] = dns_service.analyze_mx_records(records)
            elif record_type.upper() == 'TXT':
                records = await dns_service.get_txt_records(domain)
                all_records['txt_analysis'] = dns_service.analyze_txt_records(records)
            elif record_type.upper() == 'CNAME':
                records = await dns_service.get_cname_records(domain)
            elif record_type.upper() == 'NS':
                records = await dns_service.get_ns_records(domain)
            elif record_type.upper() == 'SRV':
                records = await dns_service.get_srv_records(domain)
            else:
                continue
            
            all_records[f"{record_type.lower()}_records"] = [record.to_dict() for record in records]
        
        # Add propagation check if requested
        if request.include_propagation:
            all_records['propagation_check'] = await dns_service.check_dns_propagation(domain)
        
        # Add DNS security analysis
        all_records['security_analysis'] = await dns_service.analyze_dns_security(domain)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Log the DNS query (background task)
        background_tasks.add_task(log_dns_query, domain, request.record_types, execution_time, True, None)
        
        return {
            "success": True,
            "domain": domain,
            "records": all_records,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat()
        }
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_message = str(e)
        
        # Log the failed query (background task)
        background_tasks.add_task(log_dns_query, domain, request.record_types, execution_time, False, error_message)
        
        logger.error(f"DNS enumeration failed for {domain}: {error_message}")
        
        raise HTTPException(status_code=500, detail=f"DNS enumeration failed: {error_message}")


# Subdomain Discovery Endpoints
@router.post("/subdomains")
async def discover_subdomains(
    request: SubdomainRequest,
    background_tasks: BackgroundTasks,
    subdomain_service: SubdomainDiscovery = Depends(get_subdomain_service),
    postgres_session: AsyncSession = Depends(get_postgres_session)
):
    """Discover subdomains for a domain."""
    start_time = datetime.utcnow()
    
    try:
        domain = request.domain.strip().lower()
        
        # Perform subdomain discovery
        results = await subdomain_service.discover_subdomains(
            domain=domain,
            use_extended=request.use_extended_wordlist,
            include_cert_transparency=request.include_cert_transparency,
            analyze_subdomains=request.analyze_subdomains
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Add results to database (background task)
        background_tasks.add_task(save_subdomain_results, domain, results)
        
        return {
            "success": True,
            "domain": domain,
            "results": results,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat()
        }
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_message = str(e)
        
        logger.error(f"Subdomain discovery failed for {domain}: {error_message}")
        
        raise HTTPException(status_code=500, detail=f"Subdomain discovery failed: {error_message}")


# SSL Certificate Analysis Endpoints
@router.post("/ssl-certificates")
async def analyze_ssl_certificates(
    request: SSLRequest,
    background_tasks: BackgroundTasks,
    ssl_service: SSLAnalyzer = Depends(get_ssl_service)
):
    """Analyze SSL certificates for a domain or IP."""
    start_time = datetime.utcnow()
    
    try:
        target = request.target.strip().lower()
        
        results = {}
        
        # Determine if target is domain or IP
        is_ip = target.replace('.', '').replace(':', '').isdigit()
        
        if is_ip:
            # Get certificate for IP
            cert_info = await ssl_service.get_certificate_for_ip(target)
        else:
            # Get certificate for domain
            cert_info = await ssl_service.get_certificate(target)
        
        if cert_info:
            results['current_certificate'] = cert_info.to_dict()
            
            # Perform security analysis if requested
            if request.analyze_security:
                results['security_analysis'] = await ssl_service.analyze_certificate_security(cert_info)
            
            # Get certificate chain if requested
            if request.include_chain:
                results['certificate_chain'] = [
                    cert.to_dict() for cert in await ssl_service.get_certificate_chain(target)
                ]
            
            # Find domains on same certificate
            results['related_domains'] = await ssl_service.find_domains_on_same_certificate(cert_info)
        
        # Get certificate history if requested
        if request.include_history and not is_ip:
            results['certificate_history'] = await ssl_service.analyze_certificate_history(target)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "success": True,
            "target": target,
            "results": results,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat()
        }
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_message = str(e)
        
        logger.error(f"SSL analysis failed for {target}: {error_message}")
        
        raise HTTPException(status_code=500, detail=f"SSL analysis failed: {error_message}")


# Reverse IP Lookup Endpoints
@router.post("/reverse-ip")
async def perform_reverse_ip_lookup(
    request: ReverseIPRequest,
    background_tasks: BackgroundTasks,
    infrastructure_service: InfrastructureMapping = Depends(get_infrastructure_service)
):
    """Perform reverse IP lookup to find domains on same IP."""
    start_time = datetime.utcnow()
    
    try:
        ip_address = request.ip_address.strip()
        
        # Validate IP address
        import ipaddress
        ipaddress.ip_address(ip_address)
        
        results = {}
        
        # Get domains on same IP
        results['domains'] = await infrastructure_service.reverse_ip_lookup(ip_address)
        
        # Get IP information
        results['ip_info'] = (await infrastructure_service.get_ip_info(ip_address)).to_dict()
        
        # Get ASN information
        results['asn_info'] = (await infrastructure_service.get_asn_info(ip_address)).to_dict()
        
        # Perform port scanning if requested
        if request.include_services:
            results['services'] = [
                service.to_dict() for service in await infrastructure_service.port_scan(ip_address)
            ]
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "success": True,
            "ip_address": ip_address,
            "results": results,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat()
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address format")
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_message = str(e)
        
        logger.error(f"Reverse IP lookup failed for {ip_address}: {error_message}")
        
        raise HTTPException(status_code=500, detail=f"Reverse IP lookup failed: {error_message}")


# Related Domains Endpoints
@router.post("/related-domains")
async def discover_related_domains(
    request: RelatedDomainsRequest,
    background_tasks: BackgroundTasks,
    related_domains_service: RelatedDomainDiscovery = Depends(get_related_domains_service)
):
    """Discover domains related to target domain/email/company."""
    start_time = datetime.utcnow()
    
    try:
        target = request.target.strip()
        
        # Perform related domain discovery
        results = await related_domains_service.discover_related_domains(
            target_domain=target,
            search_types=request.search_types
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "success": True,
            "target": target,
            "results": results,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat()
        }
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_message = str(e)
        
        logger.error(f"Related domains discovery failed for {target}: {error_message}")
        
        raise HTTPException(status_code=500, detail=f"Related domains discovery failed: {error_message}")


# Infrastructure Mapping Endpoints
@router.get("/infrastructure/{domain}")
async def map_domain_infrastructure(
    domain: str,
    include_port_scan: bool = Query(True, description="Include port scanning"),
    include_services: bool = Query(True, description="Include service detection"),
    include_cdn_detection: bool = Query(True, description="Include CDN detection"),
    background_tasks: BackgroundTasks = None,
    infrastructure_service: InfrastructureMapping = Depends(get_infrastructure_service)
):
    """Map complete infrastructure for a domain."""
    start_time = datetime.utcnow()
    
    try:
        domain = domain.strip().lower()
        
        # Perform infrastructure mapping
        results = await infrastructure_service.map_domain_infrastructure(domain)
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "success": True,
            "domain": domain,
            "results": results,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat()
        }
        
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_message = str(e)
        
        logger.error(f"Infrastructure mapping failed for {domain}: {error_message}")
        
        raise HTTPException(status_code=500, detail=f"Infrastructure mapping failed: {error_message}")


# Domain Portfolio Endpoints
@router.post("/domain-portfolio")
async def get_domain_portfolio(
    request: DomainPortfolioRequest,
    background_tasks: BackgroundTasks,
    whois_service: WHOISLookup = Depends(get_whois_service),
    related_domains_service: RelatedDomainDiscovery = Depends(get_related_domains_service)
):
    """Find all domains for a person or company."""
    start_time = datetime.utcnow()
    
    try:
        identifier = request.identifier.strip()
        
        results = {}
        
        if request.identifier_type == "email":
            # Search by registrant email
            results['registrant_domains'] = await whois_service.find_domains_by_email(identifier)
            results['search_type'] = 'registrant_email'
            
        elif request.identifier_type == "company":
            # Search by company name
            results['company_domains'] = await related_domains_service.search_domains_by_registrant(name=identifier)
            results['search_type'] = 'registrant_organization'
            
        else:
            raise HTTPException(status_code=400, detail="Invalid identifier type. Use 'email' or 'company'")
        
        # Perform additional analysis if requested
        if request.include_analysis:
            # Analyze found domains
            domain_list = results.get('registrant_domains', []) + results.get('company_domains', [])
            analysis_results = []
            
            for domain in domain_list[:10]:  # Limit analysis to first 10 domains
                try:
                    domain_analysis = {
                        'domain': domain,
                        'whois_info': (await whois_service.lookup_domain(domain)).to_dict()
                    }
                    analysis_results.append(domain_analysis)
                except Exception as e:
                    logger.warning(f"Failed to analyze domain {domain}: {str(e)}")
            
            results['analysis'] = analysis_results
        
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        return {
            "success": True,
            "identifier": identifier,
            "identifier_type": request.identifier_type,
            "results": results,
            "execution_time": execution_time,
            "timestamp": start_time.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        error_message = str(e)
        
        logger.error(f"Domain portfolio search failed for {identifier}: {error_message}")
        
        raise HTTPException(status_code=500, detail=f"Domain portfolio search failed: {error_message}")


# Background task functions for logging and data persistence
async def log_whois_query(target: str, is_ip: bool, execution_time: float, success: bool, error: str = None):
    """Log WHOIS query to database."""
    try:
        # This would implement database logging logic
        logger.info(f"WHOIS query logged: {target}, success: {success}, time: {execution_time}s")
    except Exception as e:
        logger.error(f"Failed to log WHOIS query: {str(e)}")

async def log_dns_query(domain: str, record_types: List[str], execution_time: float, success: bool, error: str = None):
    """Log DNS query to database."""
    try:
        # This would implement database logging logic
        logger.info(f"DNS query logged: {domain}, success: {success}, time: {execution_time}s")
    except Exception as e:
        logger.error(f"Failed to log DNS query: {str(e)}")

async def save_subdomain_results(domain: str, results: Dict):
    """Save subdomain discovery results to database."""
    try:
        # This would implement database persistence logic
        logger.info(f"Subdomain results saved for {domain}")
    except Exception as e:
        logger.error(f"Failed to save subdomain results: {str(e)}")


# Utility endpoints
@router.get("/health")
async def check_api_health():
    """Check API health status."""
    return {
        "status": "healthy",
        "service": "domain-intelligence",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/stats")
async def get_api_stats():
    """Get API usage statistics."""
    return {
        "endpoints": {
            "whois": "POST /api/search/whois",
            "dns-records": "POST /api/search/dns-records",
            "subdomains": "POST /api/search/subdomains",
            "ssl-certificates": "POST /api/search/ssl-certificates",
            "reverse-ip": "POST /api/search/reverse-ip",
            "related-domains": "POST /api/search/related-domains",
            "infrastructure": "GET /api/search/infrastructure/{domain}",
            "domain-portfolio": "POST /api/search/domain-portfolio"
        },
        "supported_features": [
            "WHOIS lookup for domains and IPs",
            "DNS enumeration and security analysis",
            "Subdomain discovery via multiple methods",
            "SSL/TLS certificate analysis",
            "Infrastructure mapping and port scanning",
            "Related domain discovery",
            "Domain portfolio analysis"
        ],
        "rate_limits": {
            "requests_per_minute": 60,
            "concurrent_requests": 10
        }
    }