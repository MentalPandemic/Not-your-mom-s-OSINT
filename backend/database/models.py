"""
Database models for domain intelligence data.

Uses SQLAlchemy async for PostgreSQL database operations.
Supports storing WHOIS, DNS, SSL, and infrastructure data.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    Boolean,
    Float,
    JSON,
    Index,
    ForeignKey,
    BigInteger,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Domain(Base):
    """Domain registration and WHOIS information."""
    
    __tablename__ = "domains"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False, index=True)
    
    # Registrant Information
    registrant_name = Column(String(255), nullable=True)
    registrant_email = Column(String(255), nullable=True, index=True)
    registrant_organization = Column(String(255), nullable=True)
    registrant_address = Column(Text, nullable=True)
    registrant_city = Column(String(100), nullable=True)
    registrant_state = Column(String(100), nullable=True)
    registrant_country = Column(String(10), nullable=True)
    registrant_phone = Column(String(50), nullable=True)
    
    # Administrative Contact
    admin_name = Column(String(255), nullable=True)
    admin_email = Column(String(255), nullable=True, index=True)
    admin_organization = Column(String(255), nullable=True)
    admin_address = Column(Text, nullable=True)
    admin_city = Column(String(100), nullable=True)
    admin_state = Column(String(100), nullable=True)
    admin_country = Column(String(10), nullable=True)
    admin_phone = Column(String(50), nullable=True)
    
    # Technical Contact
    tech_name = Column(String(255), nullable=True)
    tech_email = Column(String(255), nullable=True, index=True)
    tech_organization = Column(String(255), nullable=True)
    tech_address = Column(Text, nullable=True)
    tech_city = Column(String(100), nullable=True)
    tech_state = Column(String(100), nullable=True)
    tech_country = Column(String(10), nullable=True)
    tech_phone = Column(String(50), nullable=True)
    
    # Registrar Information
    registrar = Column(String(255), nullable=True, index=True)
    registrar_url = Column(String(255), nullable=True)
    registrar_iana_id = Column(String(50), nullable=True)
    
    # Registration Dates
    registration_date = Column(DateTime, nullable=True)
    expiration_date = Column(DateTime, nullable=True, index=True)
    last_updated = Column(DateTime, nullable=True)
    
    # Name Servers
    nameservers = Column(JSON, nullable=True)  # List of nameserver domains
    
    # DNSSEC
    dnssec = Column(Boolean, default=False)
    dnssec_key_id = Column(String(255), nullable=True)
    
    # Privacy
    privacy_protected = Column(Boolean, default=False)
    privacy_service = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_suspended = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    source = Column(String(100), nullable=True)  # API source
    
    # Relationships
    dns_records = relationship("DnsRecord", back_populates="domain", lazy="dynamic")
    ssl_certificates = relationship("SslCertificate", back_populates="domain", lazy="dynamic")
    subdomains = relationship("Subdomain", back_populates="domain", lazy="dynamic")
    ip_addresses = relationship("IpAddress", back_populates="domain", lazy="dynamic")
    related_domains = relationship(
        "RelatedDomain",
        back_populates="domain",
        foreign_keys="RelatedDomain.domain_id",
        lazy="dynamic",
    )
    
    __table_args__ = (
        Index("idx_domain_registrant_email", "registrant_email"),
        Index("idx_domain_registrar", "registrar"),
    )


class DnsRecord(Base):
    """DNS records for domains."""
    
    __tablename__ = "dns_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    
    # Record Information
    record_type = Column(String(10), nullable=False)  # A, AAAA, MX, TXT, CNAME, NS, etc.
    record_name = Column(String(255), nullable=True)  # Subdomain name or @
    record_value = Column(Text, nullable=False)
    ttl = Column(Integer, nullable=True)
    priority = Column(Integer, nullable=True)  # For MX records
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    is_historical = Column(Boolean, default=False)
    source = Column(String(100), nullable=True)
    
    # Relationships
    domain = relationship("Domain", back_populates="dns_records")
    
    __table_args__ = (
        Index("idx_dns_domain_type", "domain_id", "record_type"),
        Index("idx_dns_value", "record_value"),
    )


class Subdomain(Base):
    """Discovered subdomains."""
    
    __tablename__ = "subdomains"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    
    # Subdomain Information
    subdomain = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45), nullable=True, index=True)  # IPv4 or IPv6
    
    # Discovery Information
    discovery_method = Column(String(50), nullable=True)  # crt.sh, brute_force, zone_transfer, etc.
    source = Column(String(100), nullable=True)
    first_discovered = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    
    # Services
    services = Column(JSON, nullable=True)  # Detected services on this subdomain
    ports = Column(JSON, nullable=True)  # Open ports
    
    # Status
    is_active = Column(Boolean, default=True)
    is_wildcard = Column(Boolean, default=False)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    domain = relationship("Domain", back_populates="subdomains")
    
    __table_args__ = (
        Index("idx_subdomain_domain", "domain_id"),
        Index("idx_subdomain_name", "subdomain"),
    )


class SslCertificate(Base):
    """SSL/TLS certificates."""
    
    __tablename__ = "ssl_certificates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True)
    
    # Certificate Details
    fingerprint_sha256 = Column(String(64), unique=True, nullable=False, index=True)
    fingerprint_sha1 = Column(String(40), nullable=True, index=True)
    common_name = Column(String(255), nullable=True, index=True)
    
    # Subject Alternative Names
    sans = Column(JSON, nullable=True)  # List of SANs
    
    # Issuer Information
    issuer_common_name = Column(String(255), nullable=True)
    issuer_organization = Column(String(255), nullable=True)
    issuer_country = Column(String(10), nullable=True)
    
    # Validity
    validity_start = Column(DateTime, nullable=True)
    validity_end = Column(DateTime, nullable=True, index=True)
    validity_days_remaining = Column(Integer, nullable=True)
    
    # Technical Details
    signature_algorithm = Column(String(100), nullable=True)
    public_key_algorithm = Column(String(50), nullable=True)
    key_size = Column(Integer, nullable=True)
    serial_number = Column(String(64), nullable=True)
    
    # Certificate Transparency
    ct_log_entry = Column(JSON, nullable=True)
    ct_log_name = Column(String(255), nullable=True)
    
    # Source
    source = Column(String(100), nullable=True)  # censys, crt.sh, shodan
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, nullable=True)
    
    # Relationships
    domain = relationship("Domain", back_populates="ssl_certificates")
    
    __table_args__ = (
        Index("idx_ssl_common_name", "common_name"),
        Index("idx_ssl_issuer", "issuer_organization"),
        Index("idx_ssl_validity_end", "validity_end"),
    )


class IpAddress(Base):
    """IP address information."""
    
    __tablename__ = "ip_addresses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=True)
    
    # IP Information
    ip_address = Column(String(45), nullable=False, unique=True, index=True)
    ip_version = Column(Integer, nullable=True)  # 4 or 6
    reverse_dns = Column(String(255), nullable=True)
    
    # Geolocation
    country_code = Column(String(10), nullable=True, index=True)
    country_name = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(50), nullable=True)
    
    # Network Information
    asn = Column(String(20), nullable=True, index=True)
    asn_decimal = Column(Integer, nullable=True)
    asn_organization = Column(String(255), nullable=True)
    network_prefix = Column(String(50), nullable=True)
    isp = Column(String(255), nullable=True)
    organization = Column(String(255), nullable=True)
    connection_type = Column(String(50), nullable=True)
    
    # Status
    is_cdn = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    is_tor_exit = Column(Boolean, default=False)
    is_datacenter = Column(Boolean, default=False)
    
    # Metadata
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    last_checked = Column(DateTime, nullable=True)
    source = Column(String(100), nullable=True)
    
    # Relationships
    domain = relationship("Domain", back_populates="ip_addresses")
    
    __table_args__ = (
        Index("idx_ip_asn", "asn"),
        Index("idx_ip_country", "country_code"),
    )


class RelatedDomain(Base):
    """Related domain relationships."""
    
    __tablename__ = "related_domains"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    domain_id = Column(Integer, ForeignKey("domains.id"), nullable=False)
    
    # Related Domain
    related_domain = Column(String(255), nullable=False, index=True)
    
    # Relationship
    relationship_type = Column(String(50), nullable=False)  # same_registrant, same_ip, same_ns, etc.
    confidence = Column(Float, default=1.0)  # 0.0 to 1.0
    
    # Evidence
    evidence = Column(JSON, nullable=True)
    shared_attribute = Column(String(255), nullable=True)  # email, ip, nameserver, etc.
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime, nullable=True)
    source = Column(String(100), nullable=True)
    
    # Relationships
    domain = relationship(
        "Domain",
        back_populates="related_domains",
        foreign_keys=[domain_id],
    )
    
    __table_args__ = (
        Index("idx_related_domain", "domain_id", "related_domain"),
        Index("idx_related_type", "relationship_type"),
    )


class WhoisQuery(Base):
    """WHOIS query log."""
    
    __tablename__ = "whois_queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Query Information
    query = Column(String(255), nullable=False, index=True)
    query_type = Column(String(20), nullable=False)  # domain, ip, email
    
    # Response
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Metadata
    queried_at = Column(DateTime, default=datetime.utcnow, index=True)
    duration_ms = Column(Integer, nullable=True)
    source = Column(String(100), nullable=True)
    rate_limited = Column(Boolean, default=False)
    
    __table_args__ = (
        Index("idx_whois_query", "query", "query_type"),
    )


class DnsQuery(Base):
    """DNS query log."""
    
    __tablename__ = "dns_queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Query Information
    domain = Column(String(255), nullable=False, index=True)
    record_type = Column(String(10), nullable=False)
    
    # Response
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    # Metadata
    queried_at = Column(DateTime, default=datetime.utcnow, index=True)
    duration_ms = Column(Integer, nullable=True)
    source = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index("idx_dns_query", "domain", "record_type"),
    )


class SubdomainEnumeration(Base):
    """Subdomain enumeration results."""
    
    __tablename__ = "subdomain_enumerations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Target
    domain = Column(String(255), nullable=False, index=True)
    subdomain = Column(String(255), nullable=False)
    
    # Discovery
    method = Column(String(50), nullable=True)  # crt.sh, brute_force, zone_transfer, etc.
    source = Column(String(100), nullable=True)
    
    # Result
    is_resolving = Column(Boolean, default=True)
    ip_address = Column(String(45), nullable=True)
    services = Column(JSON, nullable=True)
    http_status = Column(Integer, nullable=True)
    
    # Metadata
    discovered_at = Column(DateTime, default=datetime.utcnow)
    last_verified = Column(DateTime, nullable=True)
    
    __table_args__ = (
        Index("idx_enum_domain", "domain"),
        Index("idx_enum_subdomain", "subdomain"),
    )
