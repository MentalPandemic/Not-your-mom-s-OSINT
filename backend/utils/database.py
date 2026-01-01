import asyncio
import asyncpg
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import logging
from contextlib import asynccontextmanager
import uuid

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass


class PostgreSQLManager:
    """PostgreSQL database manager for storing search queries and results"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.get('host', 'localhost'),
                port=self.config.get('port', 5432),
                user=self.config.get('user', 'postgres'),
                password=self.config.get('password', ''),
                database=self.config.get('database', 'osint_db'),
                min_size=self.config.get('min_connections', 2),
                max_size=self.config.get('max_connections', 10),
                command_timeout=self.config.get('command_timeout', 60),
                server_settings={
                    'jit': 'off'  # Disable JIT for better performance with small queries
                }
            )
            
            # Test connection and create tables
            async with self.pool.acquire() as conn:
                await self._create_tables(conn)
            
            self._initialized = True
            logger.info("PostgreSQL manager initialized successfully")
            
        except Exception as e:
            logger.error(f"PostgreSQL initialization failed: {e}")
            raise DatabaseError(f"Failed to initialize PostgreSQL: {e}")
    
    async def _create_tables(self, conn: asyncpg.Connection):
        """Create necessary tables if they don't exist"""
        
        # Search queries table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS search_queries (
                id UUID PRIMARY KEY,
                search_type VARCHAR(50) NOT NULL,
                query_params JSONB NOT NULL,
                results_count INTEGER NOT NULL,
                execution_time_ms INTEGER NOT NULL,
                ip_address INET,
                user_agent TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_search_type (search_type),
                INDEX idx_created_at (created_at),
                INDEX idx_ip_address (ip_address)
            )
        """)
        
        # Search results table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS search_results (
                id UUID PRIMARY KEY,
                query_id UUID REFERENCES search_queries(id) ON DELETE CASCADE,
                username VARCHAR(100) NOT NULL,
                platform VARCHAR(100) NOT NULL,
                profile_url TEXT NOT NULL,
                confidence FLOAT NOT NULL,
                match_type VARCHAR(20) NOT NULL,
                metadata JSONB,
                discovered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                INDEX idx_query_id (query_id),
                INDEX idx_username (username),
                INDEX idx_platform (platform),
                INDEX idx_confidence (confidence),
                INDEX idx_discovered_at (discovered_at)
            )
        """)
        
        # Identities table for linking profiles
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS identities (
                id UUID PRIMARY KEY,
                primary_username VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                phone VARCHAR(20),
                confidence FLOAT NOT NULL,
                first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB,
                INDEX idx_primary_username (primary_username),
                INDEX idx_email (email),
                INDEX idx_phone (phone),
                UNIQUE (primary_username)
            )
        """)
        
        # Identity links table for relationships
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS identity_links (
                id UUID PRIMARY KEY,
                identity_id UUID REFERENCES identities(id) ON DELETE CASCADE,
                linked_username VARCHAR(100) NOT NULL,
                platform VARCHAR(100) NOT NULL,
                relationship_type VARCHAR(50) NOT NULL,
                confidence FLOAT NOT NULL,
                first_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                metadata JSONB,
                INDEX idx_identity_id (identity_id),
                INDEX idx_linked_username (linked_username),
                INDEX idx_platform (platform),
                UNIQUE (identity_id, linked_username, platform)
            )
        """)
        
        # Analytics table for usage statistics
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS search_analytics (
                id UUID PRIMARY KEY,
                date DATE NOT NULL,
                search_type VARCHAR(50) NOT NULL,
                request_count INTEGER NOT NULL DEFAULT 0,
                total_execution_time_ms INTEGER NOT NULL DEFAULT 0,
                average_response_time_ms FLOAT,
                success_count INTEGER NOT NULL DEFAULT 0,
                error_count INTEGER NOT NULL DEFAULT 0,
                rate_limited_count INTEGER NOT NULL DEFAULT 0,
                cache_hit_rate FLOAT,
                UNIQUE (date, search_type)
            )
        """)
    
    async def log_search_query(self, query_data: Dict[str, Any]) -> str:
        """Log a search query to the database"""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        query_id = str(uuid.uuid4())
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO search_queries (
                        id, search_type, query_params, results_count,
                        execution_time_ms, ip_address, user_agent
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                    query_id,
                    query_data['search_type'],
                    query_data['query_params'],
                    query_data['results_count'],
                    query_data['execution_time_ms'],
                    query_data.get('ip_address'),
                    query_data.get('user_agent')
                )
                
                return query_id
                
            except Exception as e:
                logger.error(f"Failed to log search query: {e}")
                raise DatabaseError(f"Failed to log search query: {e}")
    
    async def log_search_results(self, query_id: str, results: List[Dict[str, Any]]):
        """Log search results to the database"""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        if not results:
            return
        
        async with self.pool.acquire() as conn:
            try:
                # Bulk insert for better performance
                await conn.executemany("""
                    INSERT INTO search_results (
                        id, query_id, username, platform, profile_url,
                        confidence, match_type, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """, [
                    (
                        str(uuid.uuid4()),
                        query_id,
                        result['username'],
                        result['platform'],
                        result['profile_url'],
                        result['confidence'],
                        result['match_type'],
                        json.dumps(result['metadata']) if result.get('metadata') else None
                    )
                    for result in results
                ])
                
            except Exception as e:
                logger.error(f"Failed to log search results: {e}")
                raise DatabaseError(f"Failed to log search results: {e}")
    
    async def get_search_history(
        self,
        ip_address: Optional[str] = None,
        search_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get search history with optional filters"""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            try:
                query = """
                    SELECT * FROM search_queries
                    WHERE 1=1
                """
                params = []
                
                if ip_address:
                    query += " AND ip_address = $" + str(len(params) + 1)
                    params.append(ip_address)
                
                if search_type:
                    query += " AND search_type = $" + str(len(params) + 1)
                    params.append(search_type)
                
                query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1)
                params.append(limit)
                
                if offset > 0:
                    query += " OFFSET $" + str(len(params) + 1)
                    params.append(offset)
                
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
                
            except Exception as e:
                logger.error(f"Failed to get search history: {e}")
                raise DatabaseError(f"Failed to get search history: {e}")
    
    async def get_identity_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get identity data for a username"""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow("""
                    SELECT * FROM identities
                    WHERE primary_username = $1
                """, username)
                
                return dict(row) if row else None
                
            except Exception as e:
                logger.error(f"Failed to get identity data: {e}")
                raise DatabaseError(f"Failed to get identity data: {e}")
    
    async def create_or_update_identity(
        self,
        primary_username: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        confidence: float = 0.5,
        metadata: Optional[Dict] = None
    ) -> str:
        """Create or update identity record"""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        identity_id = str(uuid.uuid4())
        
        async with self.pool.acquire() as conn:
            try:
                # Use upsert to handle existing records
                row = await conn.fetchrow("""
                    INSERT INTO identities (
                        id, primary_username, email, phone, confidence, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (primary_username)
                    DO UPDATE SET
                        email = COALESCE($3, identities.email),
                        phone = COALESCE($4, identities.phone),
                        confidence = $5,
                        metadata = $6,
                        last_updated = NOW()
                    RETURNING id
                """,
                    identity_id,
                    primary_username,
                    email,
                    phone,
                    confidence,
                    metadata
                )
                
                return row['id']
                
            except Exception as e:
                logger.error(f"Failed to create/update identity: {e}")
                raise DatabaseError(f"Failed to create/update identity: {e}")
    
    async def link_identity(
        self,
        identity_id: str,
        linked_username: str,
        platform: str,
        relationship_type: str,
        confidence: float,
        metadata: Optional[Dict] = None
    ):
        """Create identity link relationship"""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO identity_links (
                        id, identity_id, linked_username, platform,
                        relationship_type, confidence, metadata
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ON CONFLICT (identity_id, linked_username, platform)
                    DO UPDATE SET
                        relationship_type = $5,
                        confidence = $6,
                        metadata = $7,
                        last_seen = NOW()
                """,
                    str(uuid.uuid4()),
                    identity_id,
                    linked_username,
                    platform,
                    relationship_type,
                    confidence,
                    metadata
                )
                
            except Exception as e:
                logger.error(f"Failed to link identity: {e}")
                raise DatabaseError(f"Failed to link identity: {e}")
    
    async def get_platform_statistics(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get platform discovery statistics"""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch("""
                    SELECT 
                        platform,
                        COUNT(*) as total_profiles,
                        AVG(confidence) as avg_confidence,
                        COUNT(DISTINCT username) as unique_usernames
                    FROM search_results
                    WHERE discovered_at >= NOW() - INTERVAL '1 day' * $1
                    GROUP BY platform
                    ORDER BY total_profiles DESC
                """, days)
                
                return [dict(row) for row in rows]
                
            except Exception as e:
                logger.error(f"Failed to get platform statistics: {e}")
                raise DatabaseError(f"Failed to get platform statistics: {e}")
    
    async def update_analytics(
        self,
        date: datetime,
        search_type: str,
        execution_time_ms: int,
        success: bool = True,
        is_rate_limited: bool = False,
        cache_hit: bool = False
    ):
        """Update analytics data"""
        if not self._initialized:
            raise DatabaseError("Database not initialized")
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO search_analytics (
                        date, search_type, request_count, total_execution_time_ms,
                        success_count, error_count, rate_limited_count, cache_hit_rate
                    )
                    VALUES ($1, $2, 1, $3, $4, $5, $6, $7)
                    ON CONFLICT (date, search_type)
                    DO UPDATE SET
                        request_count = search_analytics.request_count + 1,
                        total_execution_time_ms = search_analytics.total_execution_time_ms + $3,
                        success_count = search_analytics.success_count + $4,
                        error_count = search_analytics.error_count + $5,
                        rate_limited_count = search_analytics.rate_limited_count + $6,
                        cache_hit_rate = (search_analytics.cache_hit_rate * (search_analytics.request_count - 1) + $7) / search_analytics.request_count,
                        average_response_time_ms = (search_analytics.total_execution_time_ms + $3) / (search_analytics.request_count + 1)
                """,
                    date.date(),
                    search_type,
                    execution_time_ms,
                    1 if success else 0,
                    0 if success else 1,
                    1 if is_rate_limited else 0,
                    1.0 if cache_hit else 0.0
                )
                
            except Exception as e:
                logger.error(f"Failed to update analytics: {e}")
                # Don't raise error for analytics failure
    
    async def close(self):
        """Close database connections"""
        if self.pool:
            await self.pool.close()
            logger.info("PostgreSQL manager closed")


class DatabaseManager:
    """Unified database manager for PostgreSQL and Neo4j"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.postgresql: Optional[PostgreSQLManager] = None
        self.neo4j: Optional[Any] = None  # Neo4j driver
        self._initialized = False
    
    async def initialize(self):
        """Initialize all database connections"""
        try:
            # Initialize PostgreSQL
            postgres_config = self.config.get('postgresql', {})
            if postgres_config.get('enabled', True):
                self.postgresql = PostgreSQLManager(postgres_config)
                await self.postgresql.initialize()
            
            # Initialize Neo4j
            neo4j_config = self.config.get('neo4j', {})
            if neo4j_config.get('enabled', True):
                # Import here to avoid dependency if not using Neo4j
                from .neo4j_manager import Neo4jManager
                self.neo4j = Neo4jManager(neo4j_config)
                await self.neo4j.initialize()
            
            self._initialized = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Database manager initialization failed: {e}")
            raise
    
    async def log_complete_search(
        self,
        search_type: str,
        query_params: Dict[str, Any],
        results: List[Dict[str, Any]],
        execution_time_ms: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        cache_hit: bool = False
    ):
        """Log complete search to all databases"""
        if not self._initialized:
            return
        
        try:
            # Log to PostgreSQL
            if self.postgresql:
                query_id = await self.postgresql.log_search_query({
                    'search_type': search_type,
                    'query_params': query_params,
                    'results_count': len(results),
                    'execution_time_ms': execution_time_ms,
                    'ip_address': ip_address,
                    'user_agent': user_agent
                })
                
                if results:
                    await self.postgresql.log_search_results(query_id, results)
            
            # Log to Neo4j
            if self.neo4j:
                await self.neo4j.create_identity_chain(query_params.get('username'), results)
            
            # Update analytics
            if self.postgresql:
                await self.postgresql.update_analytics(
                    date=datetime.utcnow(),
                    search_type=search_type,
                    execution_time_ms=execution_time_ms,
                    success=True,
                    cache_hit=cache_hit
                )
                
        except Exception as e:
            logger.error(f"Failed to log complete search: {e}")
    
    async def close(self):
        """Close all database connections"""
        if self.postgresql:
            await self.postgresql.close()
        
        if self.neo4j:
            await self.neo4j.close()
        
        logger.info("Database manager closed")