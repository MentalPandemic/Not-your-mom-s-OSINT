from __future__ import annotations

import ipaddress
import re
from typing import Any

from osint.core.models import Entity, EntityType, Relationship, RelationshipType


class NetworkCorrelationAlgorithm:
    """Correlates entities based on network information (IPs, domains, etc.)."""

    def __init__(self) -> None:
        pass

    def correlate(self, entities: list[Entity]) -> list[Relationship]:
        """Find network correlations between entities."""
        relationships: list[Relationship] = []

        # Extract IP and domain entities
        ip_entities = [e for e in entities if e.type == EntityType.IP]
        domain_entities = [e for e in entities if e.type == EntityType.DOMAIN]
        account_entities = [e for e in entities if e.type == EntityType.ACCOUNT]

        # Correlate IP entities with each other
        for i, entity_a in enumerate(ip_entities):
            for entity_b in ip_entities[i + 1 :]:
                result = self._correlate_ips(entity_a, entity_b)
                if result:
                    relationships.append(result)

        # Correlate IP entities with account entities
        for ip_entity in ip_entities:
            for account_entity in account_entities:
                result = self._correlate_ip_account(ip_entity, account_entity)
                if result:
                    relationships.append(result)

        # Correlate domain entities with each other
        for i, entity_a in enumerate(domain_entities):
            for entity_b in domain_entities[i + 1 :]:
                result = self._correlate_domains(entity_a, entity_b)
                if result:
                    relationships.append(result)

        # Correlate domain entities with account entities
        for domain_entity in domain_entities:
            for account_entity in account_entities:
                result = self._correlate_domain_account(domain_entity, account_entity)
                if result:
                    relationships.append(result)

        return relationships

    def _correlate_ips(self, entity_a: Entity, entity_b: Entity) -> Relationship | None:
        """Correlate two IP entities."""
        ip_a = entity_a.name
        ip_b = entity_b.name

        # Exact match
        if ip_a == ip_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.SAME_PERSON,
                confidence=100.0,
                evidence=["Exact IP match"],
                metadata={"match_type": "ip_exact"},
            )

        # Check if IPs are in the same subnet
        try:
            ip_obj_a = ipaddress.ip_address(ip_a)
            ip_obj_b = ipaddress.ip_address(ip_b)

            # For IPv4, check /24 subnet
            if isinstance(ip_obj_a, ipaddress.IPv4Address) and isinstance(
                ip_obj_b, ipaddress.IPv4Address
            ):
                network_a = ipaddress.ip_network(f"{ip_a}/24", strict=False)
                if ip_obj_b in network_a:
                    return Relationship(
                        id=f"rel_{entity_a.id}_{entity_b.id}_subnet",
                        entity_a=entity_a.id,
                        entity_b=entity_b.id,
                        type=RelationshipType.POTENTIAL,
                        confidence=40.0,
                        evidence=[f"IPs in same /24 subnet: {network_a}"],
                        metadata={
                            "match_type": "ip_subnet",
                            "subnet": str(network_a),
                            "ip_a": ip_a,
                            "ip_b": ip_b,
                        },
                    )

            # For IPv6, check /64 subnet
            if isinstance(ip_obj_a, ipaddress.IPv6Address) and isinstance(
                ip_obj_b, ipaddress.IPv6Address
            ):
                network_a = ipaddress.ip_network(f"{ip_a}/64", strict=False)
                if ip_obj_b in network_a:
                    return Relationship(
                        id=f"rel_{entity_a.id}_{entity_b.id}_subnet",
                        entity_a=entity_a.id,
                        entity_b=entity_b.id,
                        type=RelationshipType.POTENTIAL,
                        confidence=35.0,
                        evidence=[f"IPs in same /64 subnet: {network_a}"],
                        metadata={
                            "match_type": "ip_subnet",
                            "subnet": str(network_a),
                            "ip_a": ip_a,
                            "ip_b": ip_b,
                        },
                    )
        except ValueError:
            pass

        return None

    def _correlate_ip_account(
        self, ip_entity: Entity, account_entity: Entity
    ) -> Relationship | None:
        """Correlate an IP entity with an account entity."""
        ip = ip_entity.name
        account_ip = account_entity.attributes.get("ip_address", "")

        if account_ip and account_ip == ip:
            return Relationship(
                id=f"rel_{ip_entity.id}_{account_entity.id}",
                entity_a=ip_entity.id,
                entity_b=account_entity.id,
                type=RelationshipType.POTENTIAL,
                confidence=70.0,
                evidence=["Account has matching IP address"],
                metadata={"match_type": "ip_account", "ip": ip},
            )

        return None

    def _correlate_domains(self, entity_a: Entity, entity_b: Entity) -> Relationship | None:
        """Correlate two domain entities."""
        domain_a = entity_a.name.lower()
        domain_b = entity_b.name.lower()

        # Exact match
        if domain_a == domain_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.SAME_PERSON,
                confidence=100.0,
                evidence=["Exact domain match"],
                metadata={"match_type": "domain_exact"},
            )

        # Check for subdomain relationships
        if domain_a.endswith(f".{domain_b}") or domain_b.endswith(f".{domain_a}"):
            parent = domain_b if domain_a.endswith(f".{domain_b}") else domain_a
            child = domain_a if domain_a.endswith(f".{domain_b}") else domain_b
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_subdomain",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.RELATED,
                confidence=85.0,
                evidence=[f"Subdomain relationship: {child} is a subdomain of {parent}"],
                metadata={
                    "match_type": "subdomain",
                    "parent_domain": parent,
                    "subdomain": child,
                },
            )

        # Check for similar domains (typosquatting)
        similarity = self._calculate_domain_similarity(domain_a, domain_b)
        if similarity >= 0.85:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_similar",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.SUSPICIOUS,
                confidence=50.0,
                evidence=[f"Similar domain: {similarity:.1%} similarity"],
                metadata={
                    "match_type": "domain_similar",
                    "similarity": similarity,
                    "domain_a": domain_a,
                    "domain_b": domain_b,
                },
            )

        return None

    def _correlate_domain_account(
        self, domain_entity: Entity, account_entity: Entity
    ) -> Relationship | None:
        """Correlate a domain entity with an account entity."""
        domain = domain_entity.name.lower()

        # Check email domain
        email = account_entity.attributes.get("email", "")
        if email:
            if "@" in email:
                email_domain = email.split("@")[1].lower()
                if email_domain == domain:
                    return Relationship(
                        id=f"rel_{domain_entity.id}_{account_entity.id}",
                        entity_a=domain_entity.id,
                        entity_b=account_entity.id,
                        type=RelationshipType.POTENTIAL,
                        confidence=90.0,
                        evidence=["Account email domain matches"],
                        metadata={"match_type": "domain_email", "domain": domain},
                    )

        # Check website
        website = account_entity.attributes.get("website", "").lower()
        if website:
            website_domain = self._extract_domain_from_url(website)
            if website_domain and website_domain == domain:
                return Relationship(
                    id=f"rel_{domain_entity.id}_{account_entity.id}",
                    entity_a=domain_entity.id,
                    entity_b=account_entity.id,
                    type=RelationshipType.POTENTIAL,
                    confidence=85.0,
                    evidence=["Account website domain matches"],
                    metadata={"match_type": "domain_website", "domain": domain},
                )

        return None

    def _calculate_domain_similarity(self, domain_a: str, domain_b: str) -> float:
        """Calculate similarity between two domains using Levenshtein distance."""
        try:
            import Levenshtein

            distance = Levenshtein.distance(domain_a, domain_b)
            max_len = max(len(domain_a), len(domain_b))
            return 1.0 - (distance / max_len) if max_len > 0 else 0.0
        except ImportError:
            # Simple fallback
            if domain_a == domain_b:
                return 1.0
            common_prefix = 0
            for a, b in zip(domain_a, domain_b):
                if a == b:
                    common_prefix += 1
                else:
                    break
            return common_prefix / max(len(domain_a), len(domain_b))

    def _extract_domain_from_url(self, url: str) -> str | None:
        """Extract domain from URL."""
        url = url.strip().lower()
        # Remove protocol
        url = re.sub(r"^https?://", "", url)
        # Remove www
        url = re.sub(r"^www\.", "", url)
        # Remove path and query
        url = url.split("/")[0]
        # Remove port
        url = url.split(":")[0]
        return url if url else None
