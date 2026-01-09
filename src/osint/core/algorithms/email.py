from __future__ import annotations

import re
from typing import Any

from osint.core.models import Entity, EntityType, Relationship, RelationshipType


class EmailCorrelationAlgorithm:
    """Correlates entities using email addresses and patterns."""

    def __init__(self) -> None:
        # Common email patterns
        self.patterns = {
            "firstlast": r"^(\w+)\.(\w+)@",  # firstname.lastname@domain
            "first_last": r"^(\w+)_(\w+)@",  # firstname_lastname@domain
            "firstlast": r"^(\w+)(\w+)@",  # firstnamelastname@domain
            "f_last": r"^(\w)\.(\w+)@",  # f.lastname@domain
            "first_last99": r"^(\w+)_(\w+)\d*@",  # firstname_lastname123@domain
        }

    def correlate(self, entities: list[Entity]) -> list[Relationship]:
        """Find email correlations between entities."""
        relationships: list[Relationship] = []

        # Extract email addresses from entities
        email_entities = [e for e in entities if e.type == EntityType.EMAIL]
        account_entities = [e for e in entities if e.type == EntityType.ACCOUNT]

        # Correlate email entities with each other
        for i, entity_a in enumerate(email_entities):
            for entity_b in email_entities[i + 1 :]:
                result = self._correlate_emails(entity_a, entity_b)
                if result:
                    relationships.append(result)

        # Correlate email entities with account entities (if they have email in attributes)
        for email_entity in email_entities:
            for account_entity in account_entities:
                result = self._correlate_email_account(email_entity, account_entity)
                if result:
                    relationships.append(result)

        # Correlate account entities based on email attributes
        for i, entity_a in enumerate(account_entities):
            for entity_b in account_entities[i + 1 :]:
                result = self._correlate_accounts_by_email(entity_a, entity_b)
                if result:
                    relationships.append(result)

        return relationships

    def _correlate_emails(self, entity_a: Entity, entity_b: Entity) -> Relationship | None:
        """Correlate two email entities."""
        email_a = entity_a.name.lower()
        email_b = entity_b.name.lower()

        # Exact match
        if email_a == email_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.SAME_PERSON,
                confidence=100.0,
                evidence=["Exact email match"],
                metadata={"match_type": "exact_email"},
            )

        # Check for same domain
        domain_a = self._extract_domain(email_a)
        domain_b = self._extract_domain(email_b)

        if domain_a and domain_b and domain_a == domain_b:
            # Check username patterns
            pattern_result = self._check_email_patterns(
                entity_a, entity_b, email_a, email_b, domain_a
            )
            if pattern_result:
                return pattern_result

        return None

    def _correlate_email_account(
        self, email_entity: Entity, account_entity: Entity
    ) -> Relationship | None:
        """Correlate an email entity with an account entity."""
        email = email_entity.name.lower()
        account_email = account_entity.attributes.get("email", "").lower()

        if account_email:
            if email == account_email:
                return Relationship(
                    id=f"rel_{email_entity.id}_{account_entity.id}",
                    entity_a=email_entity.id,
                    entity_b=account_entity.id,
                    type=RelationshipType.SAME_PERSON,
                    confidence=100.0,
                    evidence=["Email matches account email attribute"],
                    metadata={"match_type": "email_account"},
                )

        return None

    def _correlate_accounts_by_email(
        self, entity_a: Entity, entity_b: Entity
    ) -> Relationship | None:
        """Correlate two account entities based on email attributes."""
        email_a = entity_a.attributes.get("email", "").lower()
        email_b = entity_b.attributes.get("email", "").lower()

        if email_a and email_b and email_a == email_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.SAME_PERSON,
                confidence=100.0,
                evidence=["Same email in account attributes"],
                metadata={"match_type": "account_email"},
            )

        # Check for domain similarity if emails exist
        if email_a and email_b:
            domain_a = self._extract_domain(email_a)
            domain_b = self._extract_domain(email_b)

            if domain_a and domain_b and domain_a == domain_b:
                pattern_result = self._check_email_patterns(
                    entity_a, entity_b, email_a, email_b, domain_a
                )
                if pattern_result:
                    return pattern_result

        return None

    def _check_email_patterns(
        self,
        entity_a: Entity,
        entity_b: Entity,
        email_a: str,
        email_b: str,
        domain: str,
    ) -> Relationship | None:
        """Check if emails follow similar patterns."""
        local_a = email_a.split("@")[0] if "@" in email_a else email_a
        local_b = email_b.split("@")[0] if "@" in email_b else email_b

        # Check for patterns like first.last vs first_last
        local_a_clean = re.sub(r"[-_.]", "", local_a)
        local_b_clean = re.sub(r"[-_.]", "", local_b)

        if local_a_clean == local_b_clean and local_a != local_b:
            return Relationship(
                id=f"rel_{entity_a.id}_{entity_b.id}_pattern",
                entity_a=entity_a.id,
                entity_b=entity_b.id,
                type=RelationshipType.POTENTIAL,
                confidence=65.0,
                evidence=[
                    f"Similar email pattern: same local part with different separators"
                ],
                metadata={
                    "match_type": "email_pattern",
                    "domain": domain,
                    "local_a": local_a,
                    "local_b": local_b,
                },
            )

        return None

    def _extract_domain(self, email: str) -> str | None:
        """Extract domain from email address."""
        if "@" not in email:
            return None

        parts = email.split("@")
        if len(parts) != 2:
            return None

        return parts[1].lower()
