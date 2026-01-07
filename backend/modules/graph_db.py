"""
Neo4j Graph Database Integration for Username Networks

Provides graph operations for visualizing and querying identity networks,
with nodes for usernames and edges representing relationships.
"""

import logging
from typing import List, Dict, Optional, Any, Set
from datetime import datetime
from enum import Enum

try:
    from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    logging.warning("neo4j driver not available, graph features disabled")

from .database import ConfidenceLevel, PlatformStatus

logger = logging.getLogger(__name__)


class EdgeType(str, Enum):
    """Types of relationships between nodes"""
    FOUND_ON = "FOUND_ON"
    LINKED_TO = "LINKED_TO"
    VARIATION_OF = "VARIATION_OF"
    SAME_AS = "SAME_AS"
    CONNECTED_TO = "CONNECTED_TO"
    EMAIL_ASSOCIATED = "EMAIL_ASSOCIATED"
    PHONE_ASSOCIATED = "PHONE_ASSOCIATED"


class GraphManager:
    """
    Manager for Neo4j graph database operations.
    
    Handles creation and querying of username identity graphs,
    enabling visualization of connections between identities.
    """

    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize the graph manager.
        
        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            username: Neo4j username
            password: Neo4j password
        """
        self.uri = uri
        self.username = username
        self.password = password
        self.driver: Optional[AsyncDriver] = None

    async def initialize(self):
        """Initialize Neo4j driver"""
        if not NEO4J_AVAILABLE:
            raise ImportError("neo4j driver not installed")
        
        self.driver = AsyncGraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password),
        )
        
        # Test connection
        await self.verify_connection()
        
        logger.info("Neo4j graph manager initialized")

    async def close(self):
        """Close Neo4j driver"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j driver closed")

    async def verify_connection(self):
        """Verify Neo4j connection is working"""
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 as test")
                record = await result.single()
                if record and record["test"] == 1:
                    logger.info("Neo4j connection verified")
                    return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            raise
        return False

    async def create_constraints(self):
        """Create database constraints and indexes"""
        constraints = [
            "CREATE CONSTRAINT username_username_unique IF NOT EXISTS FOR (u:Username) REQUIRE u.username IS UNIQUE",
            "CREATE CONSTRAINT email_email_unique IF NOT EXISTS FOR (e:Email) REQUIRE e.email IS UNIQUE",
            "CREATE CONSTRAINT phone_phone_unique IF NOT EXISTS FOR (p:Phone) REQUIRE p.phone IS UNIQUE",
            "CREATE INDEX platform_name IF NOT EXISTS FOR (pl:Platform) REQUIRE (pl.name)",
            "CREATE INDEX username_created IF NOT EXISTS FOR (u:Username) REQUIRE (u.created_at)",
        ]
        
        async with self.driver.session() as session:
            for constraint in constraints:
                try:
                    await session.run(constraint)
                except Exception as e:
                    logger.debug(f"Constraint creation notice: {e}")

    async def create_username_node(
        self,
        username: str,
        platform: str,
        profile_url: str,
        confidence: str,
        additional_info: Optional[Dict] = None,
    ) -> str:
        """
        Create or update a username node in the graph.
        
        Args:
            username: Username value
            platform: Platform where found
            profile_url: URL to profile
            confidence: Confidence level
            additional_info: Additional metadata
            
        Returns:
            Node ID
        """
        query = """
        MERGE (u:Username {username: $username, platform: $platform})
        SET u.profile_url = $profile_url,
            u.confidence = $confidence,
            u.updated_at = datetime(),
            u.discovered_count = coalesce(u.discovered_count, 0) + 1
        """
        
        params = {
            "username": username.lower(),
            "platform": platform,
            "profile_url": profile_url,
            "confidence": confidence,
        }
        
        async with self.driver.session() as session:
            result = await session.run(query, params)
            await result.consume()
        
        # Create or link platform node
        await self._create_or_link_platform(username, platform, confidence)
        
        logger.debug(f"Created username node: {username} on {platform}")
        return f"{username}:{platform}"

    async def _create_or_link_platform(
        self,
        username: str,
        platform: str,
        confidence: str,
    ):
        """Create or link platform node"""
        query = """
        MERGE (pl:Platform {name: $platform})
        WITH pl
        MATCH (u:Username {username: $username, platform: $platform})
        MERGE (u)-[r:FOUND_ON]->(pl)
        SET r.confidence = $confidence,
            r.last_checked = datetime()
        """
        
        params = {
            "username": username.lower(),
            "platform": platform,
            "confidence": confidence,
        }
        
        async with self.driver.session() as session:
            await session.run(query, params)

    async def create_email_node(
        self,
        email: str,
        username: Optional[str] = None,
        platform: Optional[str] = None,
        confidence: str = ConfidenceLevel.MEDIUM.value,
    ):
        """
        Create or update an email node in the graph.
        
        Args:
            email: Email address
            username: Associated username (optional)
            platform: Source platform (optional)
            confidence: Confidence level
        """
        query = """
        MERGE (e:Email {email: $email})
        SET e.confidence = $confidence,
            e.updated_at = datetime()
        """
        
        async with self.driver.session() as session:
            await session.run(query, {"email": email.lower(), "confidence": confidence})
        
        # Link to username if provided
        if username and platform:
            await self._link_email_to_username(email, username, platform, confidence)

    async def _link_email_to_username(
        self,
        email: str,
        username: str,
        platform: str,
        confidence: str,
    ):
        """Link email to username node"""
        query = """
        MATCH (e:Email {email: $email})
        MATCH (u:Username {username: $username, platform: $platform})
        MERGE (u)-[r:EMAIL_ASSOCIATED]->(e)
        SET r.confidence = $confidence,
            r.created_at = datetime()
        """
        
        params = {
            "email": email.lower(),
            "username": username.lower(),
            "platform": platform,
            "confidence": confidence,
        }
        
        async with self.driver.session() as session:
            await session.run(query, params)

    async def create_phone_node(
        self,
        phone: str,
        username: Optional[str] = None,
        platform: Optional[str] = None,
        confidence: str = ConfidenceLevel.MEDIUM.value,
    ):
        """
        Create or update a phone node in the graph.
        
        Args:
            phone: Phone number
            username: Associated username (optional)
            platform: Source platform (optional)
            confidence: Confidence level
        """
        query = """
        MERGE (p:Phone {phone: $phone})
        SET p.confidence = $confidence,
            p.updated_at = datetime()
        """
        
        async with self.driver.session() as session:
            await session.run(query, {"phone": phone, "confidence": confidence})
        
        # Link to username if provided
        if username and platform:
            await self._link_phone_to_username(phone, username, platform, confidence)

    async def _link_phone_to_username(
        self,
        phone: str,
        username: str,
        platform: str,
        confidence: str,
    ):
        """Link phone to username node"""
        query = """
        MATCH (p:Phone {phone: $phone})
        MATCH (u:Username {username: $username, platform: $platform})
        MERGE (u)-[r:PHONE_ASSOCIATED]->(p)
        SET r.confidence = $confidence,
            r.created_at = datetime()
        """
        
        params = {
            "phone": phone,
            "username": username.lower(),
            "platform": platform,
            "confidence": confidence,
        }
        
        async with self.driver.session() as session:
            await session.run(query, params)

    async def create_variation_edge(
        self,
        username1: str,
        username2: str,
        similarity_score: float,
        platform1: Optional[str] = None,
        platform2: Optional[str] = None,
    ):
        """
        Create an edge indicating two usernames are variations of each other.
        
        Args:
            username1: First username
            username2: Second username
            similarity_score: Similarity score (0-1)
            platform1: Platform for first username (optional)
            platform2: Platform for second username (optional)
        """
        query = """
        MATCH (u1:Username {username: $username1})
        OPTIONAL MATCH (u1_with_platform:Username {username: $username1, platform: $platform1})
        WITH u1, coalesce(u1_with_platform, u1) as u1_node
        
        MATCH (u2:Username {username: $username2})
        OPTIONAL MATCH (u2_with_platform:Username {username: $username2, platform: $platform2})
        WITH u1_node, u2, coalesce(u2_with_platform, u2) as u2_node
        
        MERGE (u1_node)-[r:VARIATION_OF]->(u2_node)
        SET r.similarity_score = $similarity_score,
            r.created_at = datetime()
        """
        
        params = {
            "username1": username1.lower(),
            "username2": username2.lower(),
            "similarity_score": similarity_score,
            "platform1": platform1,
            "platform2": platform2,
        }
        
        async with self.driver.session() as session:
            await session.run(query, params)
        
        logger.debug(f"Created variation edge: {username1} <-> {username2} ({similarity_score})")

    async def get_identity_network(
        self,
        username: str,
        max_depth: int = 2,
        include_attributes: bool = True,
    ) -> Dict:
        """
        Get the complete identity network for a username.
        
        Args:
            username: Starting username
            max_depth: Maximum traversal depth
            include_attributes: Include email/phone nodes
            
        Returns:
            Dictionary with nodes and edges
        """
        node_query = """
        MATCH (start:Username {username: $username})
        CALL {
            WITH start
            MATCH path = (start)-[*1..{max_depth}]-(related)
            RETURN nodes(path) as path_nodes, relationships(path) as path_rels
        }
        UNWIND path_nodes as node
        WITH DISTINCT node
        RETURN collect(DISTINCT {
            id: elementId(node),
            labels: labels(node),
            properties: properties(node)
        }) as nodes
        """
        
        edge_query = """
        MATCH (start:Username {username: $username})
        CALL {
            WITH start
            MATCH path = (start)-[*1..{max_depth}]-(related)
            RETURN relationships(path) as path_rels
        }
        UNWIND path_rels as rel
        WITH DISTINCT rel
        RETURN collect(DISTINCT {
            id: elementId(rel),
            type: type(rel),
            properties: properties(rel),
            source: elementId(startNode(rel)),
            target: elementId(endNode(rel))
        }) as edges
        """
        
        async with self.driver.session() as session:
            # Get nodes
            node_result = await session.run(node_query, {"username": username.lower(), "max_depth": max_depth})
            nodes = (await node_result.single()).get("nodes", [])
            
            # Get edges
            edge_result = await session.run(edge_query, {"username": username.lower(), "max_depth": max_depth})
            edges = (await edge_result.single()).get("edges", [])
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
        }

    async def find_connected_identities(
        self,
        username: str,
        min_confidence: float = 0.5,
    ) -> List[Dict]:
        """
        Find identities connected to a given username.
        
        Args:
            username: Starting username
            min_confidence: Minimum confidence score to include
            
        Returns:
            List of connected identities with details
        """
        query = """
        MATCH (u:Username {username: $username})
        OPTIONAL MATCH (u)-[r1:EMAIL_ASSOCIATED]->(e:Email)
        OPTIONAL MATCH (u)-[r2:PHONE_ASSOCIATED]->(p:Phone)
        OPTIONAL MATCH (u)-[r3:VARIATION_OF]-(v:Username)
        OPTIONAL MATCH (u)-[r4:FOUND_ON]->(pl:Platform)
        
        WITH u, collect(DISTINCT e) as emails,
                  collect(DISTINCT p) as phones,
                  collect(DISTINCT v) as variations,
                  collect(DISTINCT pl) as platforms
        
        OPTIONAL MATCH (other:Username)-[email_rel:EMAIL_ASSOCIATED]->(e:Email)
        WHERE e IN emails AND other.username <> u.username
        
        RETURN {
            username: u.username,
            platforms: [pl IN platforms | pl.name],
            emails: [e IN emails | e.email],
            phones: [p IN phones | p.phone],
            variations: [v IN variations | v.username],
            connected_usernames: collect(DISTINCT other.username),
            confidence: u.confidence
        } as identity
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"username": username.lower()})
            record = await result.single()
            
            if record:
                return record["identity"]
            return None

    async def get_platform_distribution(self, username: str) -> Dict[str, int]:
        """
        Get distribution of platforms for a username and its connections.
        
        Args:
            username: Starting username
            
        Returns:
            Dictionary mapping platform to count
        """
        query = """
        MATCH (u:Username {username: $username})-[*1..2]->(pl:Platform)
        RETURN pl.name as platform, count(*) as count
        ORDER BY count DESC
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"username": username.lower()})
            distribution = {}
            
            async for record in result:
                distribution[record["platform"]] = record["count"]
            
            return distribution

    async def find_potential_aliases(
        self,
        username: str,
        min_similarity: float = 0.7,
    ) -> List[Dict]:
        """
        Find potential aliases for a username based on graph connections.
        
        Args:
            username: Starting username
            min_similarity: Minimum similarity threshold
            
        Returns:
            List of potential aliases with evidence
        """
        query = """
        MATCH (u:Username {username: $username})
        
        // Find usernames connected through same email
        MATCH (u)-[:EMAIL_ASSOCIATED]->(e:Email)<-[:EMAIL_ASSOCIATED]-(alias:Username)
        WHERE alias.username <> u.username
        
        // Find usernames connected through same platform with variation edge
        MATCH (u)-[:VARIATION_OF]-(alias:Username)
        WHERE alias.username <> u.username
        
        WITH DISTINCT alias, u
        MATCH (alias)-[r:VARIATION_OF]-(u)
        
        RETURN {
            username: alias.username,
            platform: alias.platform,
            profile_url: alias.profile_url,
            confidence: alias.confidence,
            similarity: r.similarity_score,
            evidence: "variation_edge"
        } as potential_alias
        
        UNION
        
        MATCH (u:Username {username: $username})-[:EMAIL_ASSOCIATED]->(e:Email)<-[:EMAIL_ASSOCIATED]-(alias:Username)
        WHERE alias.username <> u.username
        
        RETURN {
            username: alias.username,
            platform: alias.platform,
            profile_url: alias.profile_url,
            confidence: alias.confidence,
            similarity: 1.0,
            evidence: "shared_email"
        } as potential_alias
        """
        
        async with self.driver.session() as session:
            result = await session.run(query, {"username": username.lower()})
            aliases = []
            
            async for record in result:
                alias = record["potential_alias"]
                if alias.get("similarity", 0) >= min_similarity:
                    aliases.append(alias)
            
            return aliases

    async def batch_create_username_nodes(
        self,
        usernames: List[Dict],
    ):
        """
        Batch create multiple username nodes for performance.
        
        Args:
            usernames: List of username data dictionaries
        """
        query = """
        UNWIND $usernames as data
        MERGE (u:Username {username: data.username, platform: data.platform})
        SET u.profile_url = data.profile_url,
            u.confidence = data.confidence,
            u.updated_at = datetime()
        """
        
        async with self.driver.session() as session:
            await session.run(query, {"usernames": usernames})
        
        logger.debug(f"Batch created {len(usernames)} username nodes")

    async def delete_identity_network(self, username: str):
        """
        Delete the identity network for a username.
        
        Args:
            username: Username to delete
        """
        query = """
        MATCH (u:Username {username: $username})
        DETACH DELETE u
        """
        
        async with self.driver.session() as session:
            await session.run(query, {"username": username.lower()})
        
        logger.info(f"Deleted identity network for {username}")

    async def get_graph_statistics(self) -> Dict:
        """
        Get overall graph statistics.
        
        Returns:
            Dictionary with graph metrics
        """
        queries = {
            "username_count": "MATCH (u:Username) RETURN count(u) as count",
            "email_count": "MATCH (e:Email) RETURN count(e) as count",
            "phone_count": "MATCH (p:Phone) RETURN count(p) as count",
            "platform_count": "MATCH (pl:Platform) RETURN count(pl) as count",
            "total_relationships": "MATCH ()-[r]->() RETURN count(r) as count",
            "high_confidence_count": "MATCH (u:Username {confidence: 'high'}) RETURN count(u) as count",
        }
        
        stats = {}
        
        async with self.driver.session() as session:
            for key, query in queries.items():
                result = await session.run(query)
                record = await result.single()
                stats[key] = record["count"] if record else 0
        
        return stats


class GraphQueryBuilder:
    """Helper class for building complex graph queries"""

    @staticmethod
    def build_identity_query(
        username: str,
        include_emails: bool = True,
        include_phones: bool = True,
        include_variations: bool = True,
        depth: int = 2,
    ) -> str:
        """Build a custom identity query based on parameters"""
        return f"""
        MATCH (u:Username {{username: $username}})
        {'OPTIONAL MATCH (u)-[:EMAIL_ASSOCIATED]->(e:Email)' if include_emails else ''}
        {'OPTIONAL MATCH (u)-[:PHONE_ASSOCIATED]->(p:Phone)' if include_phones else ''}
        {'OPTIONAL MATCH (u)-[*1..{depth}]-(related)' if depth > 0 else ''}
        RETURN u, e, p, related
        """


def get_graph_manager(
    uri: str,
    username: str,
    password: str,
) -> GraphManager:
    """
    Factory function to get a configured GraphManager instance.
    
    Args:
        uri: Neo4j connection URI
        username: Neo4j username
        password: Neo4j password
        
    Returns:
        GraphManager instance
    """
    return GraphManager(uri, username, password)


if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Example usage
        manager = get_graph_manager(
            uri="bolt://localhost:7687",
            username="neo4j",
            password="password",
        )
        
        try:
            await manager.initialize()
            await manager.create_constraints()
            
            # Create a username node
            await manager.create_username_node(
                username="john_doe",
                platform="twitter",
                profile_url="https://twitter.com/john_doe",
                confidence="high",
            )
            
            # Get network
            network = await manager.get_identity_network("john_doe")
            print(f"Network: {network['node_count']} nodes, {network['edge_count']} edges")
            
        finally:
            await manager.close()
    
    asyncio.run(main())
