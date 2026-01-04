"""
Neo4j graph database schema and operations for domain intelligence.

Creates and manages graph nodes and relationships for tracking
domain ownership, infrastructure, and connections.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import Neo4jError

logger = logging.getLogger(__name__)


@dataclass
class DomainNode:
    """Domain node in the graph."""
    name: str
    registrant_email: Optional[str] = None
    registrant_name: Optional[str] = None
    registrar: Optional[str] = None
    registration_date: Optional[datetime] = None
    expiration_date: Optional[datetime] = None
    is_active: bool = True
    dnssec: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j."""
        data = {
            "name": self.name,
            "is_active": self.is_active,
            "dnssec": self.dnssec,
        }
        
        if self.registrant_email:
            data["registrant_email"] = self.registrant_email
        if self.registrant_name:
            data["registrant_name"] = self.registrant_name
        if self.registrar:
            data["registrar"] = self.registrar
        if self.registration_date:
            data["registration_date"] = self.registration_date.isoformat()
        if self.expiration_date:
            data["expiration_date"] = self.expiration_date.isoformat()
        if self.created_at:
            data["created_at"] = self.created_at.isoformat()
        if self.updated_at:
            data["updated_at"] = self.updated_at.isoformat()
            
        return data


@dataclass
class IpNode:
    """IP address node in the graph."""
    address: str
    version: int = 4
    asn: Optional[str] = None
    asn_org: Optional[str] = None
    country_code: Optional[str] = None
    country_name: Optional[str] = None
    city: Optional[str] = None
    isp: Optional[str] = None
    is_cdn: bool = False
    is_proxy: bool = False
    is_datacenter: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j."""
        data = {
            "address": self.address,
            "version": self.version,
            "is_cdn": self.is_cdn,
            "is_proxy": self.is_proxy,
            "is_datacenter": self.is_datacenter,
        }
        
        if self.asn:
            data["asn"] = self.asn
        if self.asn_org:
            data["asn_org"] = self.asn_org
        if self.country_code:
            data["country_code"] = self.country_code
        if self.country_name:
            data["country_name"] = self.country_name
        if self.city:
            data["city"] = self.city
        if self.isp:
            data["isp"] = self.isp
            
        return data


@dataclass
class PersonNode:
    """Person node linked to registrant email."""
    email: str
    name: Optional[str] = None
    organization: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j."""
        data = {"email": self.email}
        
        if self.name:
            data["name"] = self.name
        if self.organization:
            data["organization"] = self.organization
        if self.phone:
            data["phone"] = self.phone
        if self.country:
            data["country"] = self.country
            
        return data


@dataclass
class NameserverNode:
    """Nameserver node in the graph."""
    server: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j."""
        return {"server": self.server}


@dataclass
class CertificateNode:
    """SSL certificate node in the graph."""
    fingerprint: str
    common_name: Optional[str] = None
    issuer: Optional[str] = None
    validity_start: Optional[datetime] = None
    validity_end: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j."""
        data = {"fingerprint": self.fingerprint}
        
        if self.common_name:
            data["common_name"] = self.common_name
        if self.issuer:
            data["issuer"] = self.issuer
        if self.validity_start:
            data["validity_start"] = self.validity_start.isoformat()
        if self.validity_end:
            data["validity_end"] = self.validity_end.isoformat()
            
        return data


@dataclass
class AsnNode:
    """ASN (Autonomous System Number) node."""
    asn: str
    organization: Optional[str] = None
    country_code: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Neo4j."""
        data = {"asn": self.asn}
        
        if self.organization:
            data["organization"] = self.organization
        if self.country_code:
            data["country_code"] = self.country_code
            
        return data


# Relationship types
REL_REGISTERED_TO = "REGISTERED_TO"
REL_POINTS_TO = "POINTS_TO"
REL_HOSTED_ON = "HOSTED_ON"
REL_USES_NAMESERVER = "USES_NAMESERVER"
REL_SAME_IP = "SAME_IP"
REL_SAME_ASN = "SAME_ASN"
REL_SAME_REGISTRANT = "SAME_REGISTRANT"
REL_RELATED_TO = "RELATED_TO"
REL_CERTIFICATE_FOR = "CERTIFICATE_FOR"
REL_SUBdomain_OF = "SUBDOMAIN_OF"


class Neo4jGraph:
    """Neo4j graph database manager for domain intelligence."""
    
    INDEXES = [
        "CREATE INDEX IF NOT EXISTS FOR (d:Domain) ON (d.name)",
        "CREATE INDEX IF NOT EXISTS FOR (i:Ip) ON (i.address)",
        "CREATE INDEX IF NOT EXISTS FOR (p:Person) ON (p.email)",
        "CREATE INDEX IF NOT EXISTS FOR (n:Nameserver) ON (n.server)",
        "CREATE INDEX IF NOT EXISTS FOR (c:Certificate) ON (c.fingerprint)",
        "CREATE INDEX IF NOT EXISTS FOR (a:Asn) ON (a.asn)",
    ]
    
    CONSTRAINTS = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Domain) REQUIRE d.name IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (i:Ip) REQUIRE i.address IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Person) REQUIRE p.email IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (c:Certificate) REQUIRE c.fingerprint IS UNIQUE",
    ]
    
    def __init__(
        self,
        uri: str,
        user: str = "neo4j",
        password: str = "neo4j",
        database: str = "neo4j",
        max_connections: int = 50,
    ):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j connection URI
            user: Database user
            password: Database password
            database: Database name
            max_connections: Maximum connection pool size
        """
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self._driver = None
        
        self._driver = AsyncGraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_lifetime=3600,
            max_connection_poolsize=max_connections,
        )
    
    async def close(self):
        """Close the database driver."""
        if self._driver:
            await self._driver.close()
            self._driver = None
    
    async def verify_connectivity(self):
        """Verify database connectivity."""
        if self._driver:
            await self._driver.verify_connectivity()
    
    async def initialize_schema(self):
        """Create indexes and constraints."""
        async with self._driver.session(database=self.database) as session:
            # Create constraints
            for constraint in self.CONSTRAINTS:
                try:
                    await session.run(constraint)
                except Neo4jError:
                    pass
            
            # Create indexes
            for index in self.INDEXES:
                try:
                    await session.run(index)
                except Neo4jError:
                    pass
    
    @asynccontextmanager
    async def session(self) -> AsyncSession:
        """Get a Neo4j session."""
        async with self._driver.session(database=self.database) as session:
            yield session
    
    async def create_domain_node(self, domain: DomainNode) -> str:
        """Create or update a domain node."""
        async with self.session() as session:
            result = await session.run(
                """
                MERGE (d:Domain {name: $name})
                SET d += $properties
                RETURN d.name
                """,
                name=domain.name,
                properties=domain.to_dict(),
            )
            record = await result.single()
            return record["d.name"] if record else None
    
    async def create_ip_node(self, ip: IpNode) -> str:
        """Create or update an IP node."""
        async with self.session() as session:
            result = await session.run(
                """
                MERGE (i:Ip {address: $address})
                SET i += $properties
                RETURN i.address
                """,
                address=ip.address,
                properties=ip.to_dict(),
            )
            record = await result.single()
            return record["i.address"] if record else None
    
    async def create_person_node(self, person: PersonNode) -> str:
        """Create or update a person node."""
        async with self.session() as session:
            result = await session.run(
                """
                MERGE (p:Person {email: $email})
                SET p += $properties
                RETURN p.email
                """,
                email=person.email,
                properties=person.to_dict(),
            )
            record = await result.single()
            return record["p.email"] if record else None
    
    async def create_nameserver_node(self, nameserver: NameserverNode) -> str:
        """Create or update a nameserver node."""
        async with self.session() as session:
            result = await session.run(
                """
                MERGE (n:Nameserver {server: $server})
                RETURN n.server
                """,
                server=nameserver.server,
            )
            record = await result.single()
            return record["n.server"] if record else None
    
    async def create_certificate_node(self, cert: CertificateNode) -> str:
        """Create or update a certificate node."""
        async with self.session() as session:
            result = await session.run(
                """
                MERGE (c:Certificate {fingerprint: $fingerprint})
                SET c += $properties
                RETURN c.fingerprint
                """,
                fingerprint=cert.fingerprint,
                properties=cert.to_dict(),
            )
            record = await result.single()
            return record["c.fingerprint"] if record else None
    
    async def create_asn_node(self, asn: AsnNode) -> str:
        """Create or update an ASN node."""
        async with self.session() as session:
            result = await session.run(
                """
                MERGE (a:Asn {asn: $asn})
                SET a += $properties
                RETURN a.asn
                """,
                asn=asn.asn,
                properties=asn.to_dict(),
            )
            record = await result.single()
            return record["a.asn"] if record else None
    
    async def create_domain_ip_relationship(
        self,
        domain: str,
        ip: str,
        relationship_type: str = REL_POINTS_TO,
        properties: Optional[Dict] = None,
    ):
        """Create relationship between domain and IP."""
        async with self.session() as session:
            await session.run(
                f"""
                MATCH (d:Domain {{name: $domain}})
                MATCH (i:Ip {{address: $ip}})
                MERGE (d)-[r:{relationship_type}]->(i)
                SET r = $properties
                """,
                domain=domain,
                ip=ip,
                properties=properties or {},
            )
    
    async def create_domain_nameserver_relationship(
        self,
        domain: str,
        nameserver: str,
    ):
        """Create relationship between domain and nameserver."""
        async with self.session() as session:
            await session.run(
                """
                MATCH (d:Domain {name: $domain})
                MATCH (n:Nameserver {server: $nameserver})
                MERGE (d)-[r:USES_NAMESERVER]->(n)
                """,
                domain=domain,
                nameserver=nameserver,
            )
    
    async def create_domain_person_relationship(
        self,
        domain: str,
        email: str,
        relationship_type: str = REL_REGISTERED_TO,
    ):
        """Create relationship between domain and person."""
        async with self.session() as session:
            await session.run(
                """
                MATCH (d:Domain {name: $domain})
                MATCH (p:Person {email: $email})
                MERGE (d)-[r:REGISTERED_TO]->(p)
                """,
                domain=domain,
                email=email,
            )
    
    async def create_related_domain_relationship(
        self,
        domain1: str,
        domain2: str,
        relationship_type: str = REL_RELATED_TO,
        confidence: float = 1.0,
        shared_attribute: Optional[str] = None,
    ):
        """Create relationship between related domains."""
        async with self.session() as session:
            await session.run(
                """
                MATCH (d1:Domain {name: $domain1})
                MATCH (d2:Domain {name: $domain2})
                MERGE (d1)-[r:RELATED_TO]->(d2)
                SET r.type = $relationship_type
                SET r.confidence = $confidence
                SET r.shared_attribute = $shared_attribute
                """,
                domain1=domain1,
                domain2=domain2,
                relationship_type=relationship_type,
                confidence=confidence,
                shared_attribute=shared_attribute,
            )
    
    async def get_domain_graph(
        self,
        domain: str,
        depth: int = 2,
    ) -> Dict[str, Any]:
        """Get the graph neighborhood of a domain."""
        async with self.session() as session:
            result = await session.run(
                f"""
                MATCH path = (d:Domain {{name: $domain}})-[*1..{depth}]-(connected)
                WITH nodes(path) as nodes, relationships(path) as rels
                UNWIND nodes as node
                WITH node, rels
                WITH node, 
                     [r IN rels WHERE startNode(r) = node OR endNode(r) = node] as node_rels
                RETURN collect(DISTINCT node) as nodes,
                       collect(DISTINCT node_rels) as relationships
                """,
                domain=domain,
            )
            record = await result.single()
            return {"nodes": record["nodes"], "relationships": record["relationships"]} if record else {}
    
    async def get_domains_by_person(
        self,
        email: str,
    ) -> List[str]:
        """Get all domains registered to a person."""
        async with self.session() as session:
            result = await session.run(
                """
                MATCH (d:Domain)-[:REGISTER_TO]->(p:Person {email: $email})
                RETURN d.name as domain
                """,
                email=email,
            )
            records = await result.values()
            return [r[0] for r in records]
    
    async def get_domains_by_ip(
        self,
        ip: str,
    ) -> List[str]:
        """Get all domains pointing to an IP."""
        async with self.session() as session:
            result = await session.run(
                """
                MATCH (d:Domain)-[:POINTS_TO]->(i:Ip {address: $ip})
                RETURN d.name as domain
                """,
                ip=ip,
            )
            records = await result.values()
            return [r[0] for r in records]
    
    async def get_domains_by_nameserver(
        self,
        nameserver: str,
    ) -> List[str]:
        """Get all domains using a nameserver."""
        async with self.session() as session:
            result = await session.run(
                """
                MATCH (d:Domain)-[:USES_NAMESERVER]->(n:Nameserver {server: $nameserver})
                RETURN d.name as domain
                """,
                nameserver=nameserver,
            )
            records = await result.values()
            return [r[0] for r in records]
    
    async def get_common_registrant_domains(
        self,
        email: str,
    ) -> List[Dict[str, Any]]:
        """Find domains registered by the same person."""
        async with self.session() as session:
            result = await session.run(
                """
                MATCH (d1:Domain)-[:REGISTERED_TO]->(p:Person {email: $email})
                MATCH (d2:Domain)-[:REGISTERED_TO]->(p)
                WHERE d1.name <> d2.name
                WITH d1.name as source, d2.name as target, p.email as shared_email
                RETURN source, target, shared_email, 'same_registrant' as relationship
                """,
                email=email,
            )
            records = await result.values()
            return [
                {
                    "source": r[0],
                    "target": r[1],
                    "shared_email": r[2],
                    "relationship": r[3],
                }
                for r in records
            ]
    
    async def delete_domain(self, domain: str):
        """Delete a domain and its relationships."""
        async with self.session() as session:
            await session.run(
                """
                MATCH (d:Domain {name: $domain})
                DETACH DELETE d
                """,
                domain=domain,
            )
    
    async def execute_cypher(
        self,
        query: str,
        parameters: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        """Execute a custom Cypher query."""
        async with self.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()
