"""
Database Models for Domain Intelligence

This module contains SQLAlchemy models for PostgreSQL and Neo4j graph models
for storing domain intelligence data including WHOIS, DNS, SSL certificates,
subdomains, and infrastructure information.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, Index, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY, INET
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Optional, List, Dict, Any

Base = declarative_base()


class Domain(Base):
    """Domain information table."""
    __tablename__ = 'domains'
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    
    # WHOIS Information
    registrant_name = Column(String(255), nullable=True)
    registrant_email = Column(String(255), nullable=True, index=True)
    registrant_phone = Column(String(50), nullable=True)
    registrant_address = Column(Text, nullable=True)
    admin_email = Column(String(255), nullable=True, index=True)
    tech_email = Column(String(255), nullable=True, index=True)
    
    registrar = Column(String(255), nullable=True)
    registration_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True)
    updated_date = Column(DateTime, nullable=True)
    
    # Status and Security
    status = Column(String(100), nullable=True)
    dnssec_status = Column(String(50), nullable=True)
    uses_privacy = Column(Boolean, default=False)
    privacy_providers = Column(ARRAY(String), nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    dns_records = relationship("DNSRecord", back_populates="domain", cascade="all, delete-orphan")
    subdomains = relationship("Subdomain", back_populates="parent_domain", cascade="all, delete-orphan")
    ssl_certificates = relationship("SSLCertificate", back_populates="domain", cascade="all, delete-orphan")
    ip_addresses = relationship("IPAddress", back_populates="domain", cascade="all, delete-orphan")


class DNSRecord(Base):
    """DNS records table."""
    __tablename__ = 'dns_records'
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, nullable=False, index=True)
    
    # Record Information
    record_type = Column(String(10), nullable=False, index=True)  # A, AAAA, MX, TXT, CNAME, NS, SRV
    record_name = Column(String(255), nullable=False)
    record_value = Column(Text, nullable=False)
    ttl = Column(Integer, nullable=True)
    
    # Additional data for specific record types
    priority = Column(Integer, nullable=True)  # For MX records
    is_spf = Column(Boolean, default=False)
    is_dkim = Column(Boolean, default=False)
    is_dmarc = Column(Boolean, default=False)
    has_verification = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    
    # Relationships
    domain = relationship("Domain", back_populates="dns_records")
    
    # Indexes
    __table_args__ = (
        Index('idx_dns_record_type_value', 'record_type', 'record_value'),
        Index('idx_dns_record_domain_type', 'domain_id', 'record_type'),
    )


class Subdomain(Base):
    """Subdomain information table."""
    __tablename__ = 'subdomains'
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, nullable=False, index=True)
    
    # Subdomain Information
    subdomain_name = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False, unique=True)
    
    # Infrastructure
    ip_address = Column(INET, nullable=True, index=True)
    status = Column(String(50), default='unknown')  # active, inactive, unknown, wildcard
    response_time = Column(Float, nullable=True)
    
    # Web Analysis
    title = Column(Text, nullable=True)
    server_header = Column(String(255), nullable=True)
    technologies = Column(ARRAY(String), nullable=True)
    services = Column(JSON, nullable=True)
    ports = Column(ARRAY(Integer), nullable=True)
    
    # Discovery Method
    discovery_method = Column(String(50), nullable=True)  # brute_force, certificate_transparency, zone_transfer
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    parent_domain = relationship("Domain", back_populates="subdomains")
    ip_address_obj = relationship("IPAddress", back_populates="subdomains")
    
    # Indexes
    __table_args__ = (
        Index('idx_subdomain_parent_domain', 'domain_id'),
        Index('idx_subdomain_ip', 'ip_address'),
        Index('idx_subdomain_status', 'status'),
    )


class IPAddress(Base):
    """IP address information table."""
    __tablename__ = 'ip_addresses'
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, nullable=True, index=True)
    
    # IP Information
    ip_address = Column(INET, unique=True, nullable=False, index=True)
    
    # Network Information
    asn = Column(String(20), nullable=True, index=True)
    asn_description = Column(Text, nullable=True)
    netrange = Column(String(50), nullable=True)
    netmask = Column(String(50), nullable=True)
    
    # ISP/Organization
    isp = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    hosting_provider = Column(String(255), nullable=True)
    
    # Geolocation
    country = Column(String(2), nullable=True, index=True)
    country_name = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Reverse DNS
    reverse_dns = Column(String(255), nullable=True)
    
    # Security Indicators
    is_public = Column(Boolean, nullable=True)
    is_private = Column(Boolean, nullable=True)
    is_reserved = Column(Boolean, nullable=True)
    is_data_center = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    domain = relationship("Domain", back_populates="ip_addresses")
    subdomains = relationship("Subdomain", back_populates="ip_address_obj")
    
    # Indexes
    __table_args__ = (
        Index('idx_ip_asn', 'asn'),
        Index('idx_ip_country', 'country'),
        Index('idx_ip_isp', 'isp'),
    )


class SSLCertificate(Base):
    """SSL certificate information table."""
    __tablename__ = 'ssl_certificates'
    
    id = Column(Integer, primary_key=True, index=True)
    domain_id = Column(Integer, nullable=True, index=True)
    
    # Certificate Information
    common_name = Column(String(255), nullable=True, index=True)
    subject = Column(Text, nullable=True)
    issuer = Column(Text, nullable=True)
    issuer_organization = Column(String(255), nullable=True)
    serial_number = Column(String(100), nullable=True, index=True)
    
    # Fingerprints
    fingerprint_sha1 = Column(String(64), nullable=True, index=True)
    fingerprint_sha256 = Column(String(64), nullable=True, index=True)
    
    # Validity
    valid_from = Column(DateTime, nullable=True)
    valid_to = Column(DateTime, nullable=True)
    is_valid = Column(Boolean, default=False)
    days_until_expiry = Column(Integer, nullable=True)
    
    # Certificate Properties
    version = Column(Integer, nullable=True)
    signature_algorithm = Column(String(100), nullable=True)
    key_size = Column(Integer, nullable=True)
    is_ca = Column(Boolean, default=False)
    is_self_signed = Column(Boolean, default=False)
    
    # Subject Alternative Names
    subject_alt_names = Column(ARRAY(String), nullable=True)
    
    # Certificate Chain
    certificate_chain = Column(ARRAY(String), nullable=True)
    
    # Certificate Transparency
    ct_log_entries = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    domain = relationship("Domain", back_populates="ssl_certificates")
    
    # Indexes
    __table_args__ = (
        Index('idx_ssl_cert_domain', 'domain_id'),
        Index('idx_ssl_cert_issuer', 'issuer_organization'),
        Index('idx_ssl_cert_valid_to', 'valid_to'),
    )


class RelatedDomain(Base):
    """Related domains table."""
    __tablename__ = 'related_domains'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Domain Relationships
    domain = Column(String(255), nullable=False, index=True)
    related_domain = Column(String(255), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False, index=True)  # same_registrant, same_ns, same_ip, same_asn, typosquatting
    
    # Relationship Details
    confidence = Column(Float, default=0.0)  # 0.0 to 1.0
    evidence = Column(ARRAY(String), nullable=True)
    
    # Analysis
    variation_type = Column(String(50), nullable=True)  # For typosquatting variations
    risk_level = Column(String(20), nullable=True)  # low, medium, high
    
    # Status
    status = Column(String(50), default='unknown')  # active, inactive, available, parked
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_related_domain_type', 'domain', 'relationship_type'),
        Index('idx_related_confidence', 'confidence'),
    )


class DomainAnalysis(Base):
    """Domain analysis results table."""
    __tablename__ = 'domain_analyses'
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, unique=True, index=True)
    
    # Analysis Results
    security_score = Column(Integer, nullable=True)
    reputation_score = Column(Integer, nullable=True)
    risk_level = Column(String(20), nullable=True)
    
    # Security Analysis
    has_spf = Column(Boolean, default=False)
    has_dkim = Column(Boolean, default=False)
    has_dmarc = Column(Boolean, default=False)
    has_dnssec = Column(Boolean, default=False)
    
    # Infrastructure Analysis
    total_subdomains = Column(Integer, default=0)
    active_subdomains = Column(Integer, default=0)
    unique_ips = Column(Integer, default=0)
    unique_asns = Column(Integer, default=0)
    uses_cdn = Column(Boolean, default=False)
    
    # Threat Intelligence
    threat_indicators = Column(ARRAY(String), nullable=True)
    malware_associated = Column(Boolean, default=False)
    phishing_associated = Column(Boolean, default=False)
    
    # Analysis Metadata
    analysis_type = Column(String(50), default='comprehensive')  # comprehensive, quick, security
    analysis_version = Column(String(10), default='1.0')
    analysis_data = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_analyzed = Column(DateTime, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_analysis_security_score', 'security_score'),
        Index('idx_analysis_reputation_score', 'reputation_score'),
        Index('idx_analysis_risk_level', 'risk_level'),
    )


class WHOISQuery(Base):
    """WHOIS query log table."""
    __tablename__ = 'whois_queries'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Query Information
    query_target = Column(String(255), nullable=False, index=True)
    query_type = Column(String(20), nullable=False)  # domain, ip
    
    # Query Results
    query_successful = Column(Boolean, default=False)
    response_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # API Information
    api_source = Column(String(50), nullable=True)  # whois, securitytrails, etc.
    response_time = Column(Float, nullable=True)
    
    # Timestamps
    queried_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_whois_query_target', 'query_target'),
        Index('idx_whois_queried_at', 'queried_at'),
    )


class DNSQuery(Base):
    """DNS query log table."""
    __tablename__ = 'dns_queries'
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Query Information
    domain = Column(String(255), nullable=False, index=True)
    record_type = Column(String(10), nullable=False)
    nameserver = Column(String(255), nullable=True)
    
    # Query Results
    query_successful = Column(Boolean, default=False)
    response_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # DNS Server Information
    dns_server = Column(String(255), nullable=True)
    response_time = Column(Float, nullable=True)
    
    # Timestamps
    queried_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_dns_query_domain_type', 'domain', 'record_type'),
        Index('idx_dns_queried_at', 'queried_at'),
    )


# Neo4j Graph Models
# These would be used with Neo4j driver for relationship modeling

class GraphDomain:
    """Neo4j Domain node."""
    def __init__(self, domain: str, **properties):
        self.domain = domain
        self.labels = ['Domain']
        self.properties = {
            'domain': domain,
            'created_at': datetime.utcnow().isoformat(),
            **properties
        }


class GraphIP:
    """Neo4j IP Address node."""
    def __init__(self, ip_address: str, **properties):
        self.ip_address = ip_address
        self.labels = ['IPAddress']
        self.properties = {
            'ip_address': ip_address,
            'created_at': datetime.utcnow().isoformat(),
            **properties
        }


class GraphPerson:
    """Neo4j Person node for registrants."""
    def __init__(self, email: str, name: str = None, **properties):
        self.email = email
        self.labels = ['Person']
        self.properties = {
            'email': email,
            'name': name,
            'created_at': datetime.utcnow().isoformat(),
            **properties
        }


class GraphOrganization:
    """Neo4j Organization node."""
    def __init__(self, name: str, **properties):
        self.name = name
        self.labels = ['Organization']
        self.properties = {
            'name': name,
            'created_at': datetime.utcnow().isoformat(),
            **properties
        }


class GraphNameserver:
    """Neo4j Nameserver node."""
    def __init__(self, nameserver: str, **properties):
        self.nameserver = nameserver
        self.labels = ['Nameserver']
        self.properties = {
            'nameserver': nameserver,
            'created_at': datetime.utcnow().isoformat(),
            **properties
        }


# Relationship Types for Neo4j
class GraphRelationships:
    """Neo4j relationship types."""
    RESOLVES_TO = "RESOLVES_TO"
    REGISTERED_BY = "REGISTERED_BY"
    OWNED_BY = "OWNED_BY"
    USES_NAMESERVER = "USES_NAMESERVER"
    HOSTED_ON = "HOSTED_ON"
    SAME_ASN = "SAME_ASN"
    RELATED_TO = "RELATED_TO"
    CONNECTED_TO = "CONNECTED_TO"
    SECURED_BY = "SECURED_BY"


# Utility functions
def create_domain_node(domain_data: Dict) -> GraphDomain:
    """Create a GraphDomain node from domain data."""
    return GraphDomain(
        domain=domain_data['domain'],
        registrant_name=domain_data.get('registrant_name'),
        registrant_email=domain_data.get('registrant_email'),
        registrar=domain_data.get('registrar'),
        registration_date=domain_data.get('registration_date'),
        expiration_date=domain_data.get('expiration_date'),
        status=domain_data.get('status'),
        uses_privacy=domain_data.get('uses_privacy', False)
    )


def create_ip_node(ip_data: Dict) -> GraphIP:
    """Create a GraphIP node from IP data."""
    return GraphIP(
        ip_address=ip_data['ip_address'],
        asn=ip_data.get('asn'),
        country=ip_data.get('country'),
        isp=ip_data.get('isp'),
        organization=ip_data.get('organization'),
        is_data_center=ip_data.get('is_data_center', False)
    )


def create_person_node(person_data: Dict) -> GraphPerson:
    """Create a GraphPerson node from person data."""
    return GraphPerson(
        email=person_data['email'],
        name=person_data.get('name'),
        phone=person_data.get('phone'),
        address=person_data.get('address')
    )


def create_organization_node(org_data: Dict) -> GraphOrganization:
    """Create a GraphOrganization node from organization data."""
    return GraphOrganization(
        name=org_data['name'],
        organization_type=org_data.get('type'),
        country=org_data.get('country')
    )


def create_nameserver_node(ns_data: Dict) -> GraphNameserver:
    """Create a GraphNameserver node from nameserver data."""
    return GraphNameserver(
        nameserver=ns_data['nameserver'],
        provider=ns_data.get('provider'),
        country=ns_data.get('country')
    )