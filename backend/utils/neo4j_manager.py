from neo4j import AsyncGraphDatabase, AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import uuid

logger = logging.getLogger(__name__)


class Neo4jManager:
    """Neo4j graph database manager for identity relationships"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.uri = config.get('uri', 'bolt://localhost:7687')
        self.user = config.get('user', 'neo4j')
        self.password = config.get('password', 'password')
        
        self.driver: Optional[AsyncGraphDatabase.driver] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize Neo4j driver"""
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
            
            # Test connection
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            
            self._initialized = True
            logger.info("Neo4j manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Neo4j initialization failed: {e}")
            raise
    
    async def create_identity_chain(self, username: str, search_results: List[Dict[str, Any]]):
        """Create identity relationship chain in Neo4j"""
        if not self._initialized or not search_results:
            return
        
        async with self.driver.session() as session:
            try:
                # Create main username node
                await session.run("""
                    MERGE (u:Username {value: $username})
                    SET u.discovered_at = datetime(),
                        u.last_seen = datetime()
                """, username=username)
                
                # Process each search result
                for result in search_results:
                    await self._create_result_relationships(session, username, result)
                
            except Exception as e:
                logger.error(f"Failed to create identity chain: {e}")
                raise
    
    async def _create_result_relationships(
        self, 
        session: AsyncSession, 
        username: str, 
        result: Dict[str, Any]
    ):
        """Create relationships for a search result"""
        platform = result.get('platform', 'unknown')
        profile_url = result.get('profile_url', '')
        confidence = result.get('confidence', 0.5)
        metadata = result.get('metadata', {}) or {}
        
        try:
            # Create platform node
            await session.run("""
                MERGE (p:Platform {name: $platform})
            """, platform=platform)
            
            # Create profile node linked to platform
            await session.run("""
                MERGE (prof:Profile {url: $url})
                SET prof.platform = $platform,
                    prof.discovered_at = datetime(),
                    prof.confidence = $confidence
                MERGE (p:Platform {name: $platform})
                MERGE (prof)-[:ON_PLATFORM]->(p)
            """, url=profile_url, platform=platform, confidence=confidence)
            
            # Link username to profile
            await session.run("""
                MATCH (u:Username {value: $username})
                MATCH (prof:Profile {url: $url})
                MERGE (u)-[r:FOUND_ON {
                    confidence: $confidence,
                    discovered_at: datetime()
                }]->(prof)
            """, username=username, url=profile_url, confidence=confidence)
            
            # Create email node if present in metadata
            email = metadata.get('email')
            if email:
                await self._create_email_node(session, username, email, platform, confidence)
            
            # Create phone node if present in metadata
            phone = metadata.get('phone')
            if phone:
                await self._create_phone_node(session, username, phone, platform, confidence)
        
        except Exception as e:
            logger.error(f"Failed to create result relationships: {e}")
            raise
    
    async def _create_email_node(
        self, 
        session: AsyncSession, 
        username: str, 
        email: str, 
        platform: str, 
        confidence: float
    ):
        """Create email node and relationships"""
        try:
            # Create email node
            await session.run("""
                MERGE (e:Email {address: $email})
                SET e.discovered_at = datetime(),
                    e.platform = $platform
            """, email=email, platform=platform)
            
            # Link email to username
            await session.run("""
                MATCH (u:Username {value: $username})
                MATCH (e:Email {address: $email})
                MERGE (u)-[r:USES_EMAIL {
                    confidence: $confidence,
                    discovered_at: datetime(),
                    platform: $platform
                }]->(e)
            """, username=username, email=email, confidence=confidence, platform=platform)
        
        except Exception as e:
            logger.error(f"Failed to create email node: {e}")
            raise
    
    async def _create_phone_node(
        self, 
        session: AsyncSession, 
        username: str, 
        phone: str, 
        platform: str, 
        confidence: float
    ):
        """Create phone node and relationships"""
        try:
            # Create phone node
            await session.run("""
                MERGE (p:Phone {number: $phone})
                SET p.discovered_at = datetime(),
                    p.platform = $platform
            """, phone=phone, platform=platform)
            
            # Link phone to username
            await session.run("""
                MATCH (u:Username {value: $username})
                MATCH (p:Phone {number: $phone})
                MERGE (u)-[r:USES_PHONE {
                    confidence: $confidence,
                    discovered_at: datetime(),
                    platform: $platform
                }]->(p)
            """, username=username, phone=phone, confidence=confidence, platform=platform)
        
        except Exception as e:
            logger.error(f"Failed to create phone node: {e}")
            raise
    
    async def get_identity_chain(self, username: str) -> Dict[str, Any]:
        """Get identity chain for a username"""
        if not self._initialized:
            return {'nodes': [], 'relationships': [], 'chain_length': 0}
        
        async with self.driver.session() as session:
            try:
                # Query for all nodes connected to the username
                result = await session.run("""
                    MATCH (u:Username {value: $username})
                    OPTIONAL MATCH (u)-[r]->(connected)
                    OPTIONAL MATCH (connected)-[r2]->(secondary)
                    RETURN u, r, connected, r2, secondary
                """, username=username)
                
                nodes = {}
                relationships = []
                
                async for record in result:
                    # Process username node
                    username_node = record['u']
                    if username_node:
                        node_id = str(uuid.uuid4())
                        nodes[node_id] = {
                            'id': node_id,
                            'type': 'username',
                            'value': username_node['value'],
                            'platform': None,
                            'confidence': 1.0
                        }
                    
                    # Process connected node
                    connected_node = record['connected']
                    if connected_node:
                        node_type = list(connected_node.labels)[0] if connected_node.labels else 'Unknown'
                        node_id = str(uuid.uuid4())
                        
                        nodes[node_id] = {
                            'id': node_id,
                            'type': node_type.lower(),
                            'value': connected_node.get('value', '') or connected_node.get('address', '') or connected_node.get('number', '') or connected_node.get('url', ''),
                            'platform': connected_node.get('platform', None),
                            'confidence': connected_node.get('confidence', 0.5)
                        }
                        
                        # Process relationship
                        relationship = record['r']
                        if relationship:
                            relationships.append({
                                'source_id': str(uuid.uuid4()),
                                'target_id': node_id,
                                'relationship_type': relationship.type if hasattr(relationship, 'type') else 'connected',
                                'confidence': relationship.get('confidence', 0.5),
                                'discovered_at': relationship.get('discovered_at', datetime.utcnow())
                            })
                
                return {
                    'nodes': list(nodes.values()),
                    'relationships': relationships,
                    'chain_length': len(relationships)
                }
                
            except Exception as e:
                logger.error(f"Failed to get identity chain: {e}")
                return {'nodes': [], 'relationships': [], 'chain_length': 0}
    
    async def find_similar_usernames(self, username: str, threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Find similar usernames based on connections"""
        if not self._initialized:
            return []
        
        async with self.driver.session() as session:
            try:
                # Find usernames that share connections
                result = await session.run("""
                    MATCH (u1:Username {value: $username})-[r1]->(connected)<-[r2]-(u2:Username)
                    WHERE u1 <> u2
                    WITH u2, COLLECT(DISTINCT connected) as shared_connections, COUNT(DISTINCT connected) as shared_count
                    WHERE shared_count >= 2
                    RETURN u2.value as username, shared_count, shared_connections
                    ORDER BY shared_count DESC
                    LIMIT 10
                """, username=username)
                
                similar_usernames = []
                async for record in result:
                    similar_usernames.append({
                        'username': record['username'],
                        'shared_connection_count': record['shared_count'],
                        'confidence': min(1.0, record['shared_count'] * 0.3)
                    })
                
                return similar_usernames
                
            except Exception as e:
                logger.error(f"Failed to find similar usernames: {e}")
                return []
    
    async def get_platform_stats(self) -> Dict[str, Any]:
        """Get statistics about platform data"""
        if not self._initialized:
            return {}
        
        async with self.driver.session() as session:
            try:
                # Count nodes by type
                node_counts = await session.run("""
                    MATCH (n)
                    RETURN labels(n)[0] as node_type, COUNT(n) as count
                    ORDER BY count DESC
                """)
                
                # Count relationships by type
                rel_counts = await session.run("""
                    MATCH ()-[r]->()
                    RETURN type(r) as rel_type, COUNT(r) as count
                    ORDER BY count DESC
                """)
                
                stats = {
                    'node_counts': {},
                    'relationship_counts': {}
                }
                
                async for record in node_counts:
                    stats['node_counts'][record['node_type']] = record['count']
                
                async for record in rel_counts:
                    stats['relationship_counts'][record['rel_type']] = record['count']
                
                return stats
                
            except Exception as e:
                logger.error(f"Failed to get platform stats: {e}")
                return {}
    
    async def delete_identity_chain(self, username: str) -> bool:
        """Delete identity chain for a username"""
        if not self._initialized:
            return False
        
        async with self.driver.session() as session:
            try:
                await session.run("""
                    MATCH (u:Username {value: $username})
                    OPTIONAL MATCH (u)-[r]-(connected)
                    DELETE r, u, connected
                """, username=username)
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to delete identity chain: {e}")
                return False
    
    async def close(self):
        """Close Neo4j driver"""
        if self.driver:
            await self.driver.close()
            logger.info("Neo4j manager closed")