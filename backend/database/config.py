"""
Database Configuration and Connection Management

This module handles database connections for PostgreSQL and Neo4j,
including connection pooling, session management, and initialization.
"""

import os
import asyncio
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from neo4j import AsyncDriver, AsyncGraphDatabase
import logging

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Database configuration settings."""
    
    # PostgreSQL Configuration
    POSTGRES_URL: str = os.getenv('POSTGRES_URL', 'postgresql+asyncpg://user:password@localhost:5432/domain_intel')
    POSTGRES_ECHO: bool = os.getenv('POSTGRES_ECHO', 'false').lower() == 'true'
    POSTGRES_POOL_SIZE: int = int(os.getenv('POSTGRES_POOL_SIZE', '10'))
    POSTGRES_MAX_OVERFLOW: int = int(os.getenv('POSTGRES_MAX_OVERFLOW', '20'))
    
    # Neo4j Configuration
    NEO4J_URI: str = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER: str = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASSWORD: str = os.getenv('NEO4J_PASSWORD', 'password')
    NEO4J_DATABASE: str = os.getenv('NEO4J_DATABASE', 'neo4j')


class DatabaseManager:
    """Database connection and session manager."""
    
    def __init__(self):
        self.postgres_engine: Optional[AsyncEngine] = None
        self.postgres_session_maker: Optional[async_sessionmaker] = None
        self.neo4j_driver: Optional[AsyncDriver] = None
        
    async def initialize(self):
        """Initialize database connections."""
        await self._init_postgres()
        await self._init_neo4j()
        
    async def _init_postgres(self):
        """Initialize PostgreSQL connection."""
        try:
            self.postgres_engine = create_async_engine(
                DatabaseConfig.POSTGRES_URL,
                echo=DatabaseConfig.POSTGRES_ECHO,
                poolclass=NullPool,  # Use connection pooling appropriate for async
                pool_size=DatabaseConfig.POSTGRES_POOL_SIZE,
                max_overflow=DatabaseConfig.POSTGRES_MAX_OVERFLOW,
                pool_pre_ping=True,
                pool_recycle=300,  # Recycle connections every 5 minutes
            )
            
            self.postgres_session_maker = async_sessionmaker(
                bind=self.postgres_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("PostgreSQL connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize PostgreSQL: {str(e)}")
            raise
    
    async def _init_neo4j(self):
        """Initialize Neo4j connection."""
        try:
            self.neo4j_driver = AsyncGraphDatabase.driver(
                DatabaseConfig.NEO4J_URI,
                auth=(DatabaseConfig.NEO4J_USER, DatabaseConfig.NEO4J_PASSWORD),
                max_connection_lifetime=300,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60
            )
            
            # Test the connection
            async with self.neo4j_driver.session() as session:
                await session.run("RETURN 1")
            
            logger.info("Neo4j connection initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Neo4j: {str(e)}")
            raise
    
    async def get_postgres_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get PostgreSQL session."""
        if not self.postgres_session_maker:
            raise RuntimeError("PostgreSQL not initialized")
            
        async with self.postgres_session_maker() as session:
            try:
                yield session
            except Exception as e:
                await session.rollback()
                logger.error(f"Database session error: {str(e)}")
                raise
            finally:
                await session.close()
    
    async def get_neo4j_session(self):
        """Get Neo4j session."""
        if not self.neo4j_driver:
            raise RuntimeError("Neo4j not initialized")
            
        return self.neo4j_driver.session()
    
    async def close(self):
        """Close all database connections."""
        if self.postgres_engine:
            await self.postgres_engine.dispose()
            logger.info("PostgreSQL connection closed")
            
        if self.neo4j_driver:
            await self.neo4j_driver.close()
            logger.info("Neo4j connection closed")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency injection for FastAPI
async def get_postgres_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency injection for PostgreSQL sessions."""
    async for session in db_manager.get_postgres_session():
        yield session


async def get_neo4j_session():
    """Dependency injection for Neo4j sessions."""
    async with db_manager.get_neo4j_session() as session:
        yield session


# Database initialization utilities
async def create_tables():
    """Create all database tables."""
    try:
        from models.domain_intelligence import Base
        
        if not db_manager.postgres_engine:
            raise RuntimeError("PostgreSQL not initialized")
            
        async with db_manager.postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create tables: {str(e)}")
        raise


async def drop_tables():
    """Drop all database tables."""
    try:
        from models.domain_intelligence import Base
        
        if not db_manager.postgres_engine:
            raise RuntimeError("PostgreSQL not initialized")
            
        async with db_manager.postgres_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            
        logger.info("Database tables dropped successfully")
        
    except Exception as e:
        logger.error(f"Failed to drop tables: {str(e)}")
        raise


# Neo4j Graph utilities
async def create_constraints():
    """Create Neo4j constraints and indexes."""
    try:
        async with db_manager.get_neo4j_session() as session:
            # Create constraints for unique properties
            constraints = [
                "CREATE CONSTRAINT domain_unique IF NOT EXISTS FOR (d:Domain) REQUIRE d.domain IS UNIQUE",
                "CREATE CONSTRAINT ip_unique IF NOT EXISTS FOR (i:IPAddress) REQUIRE i.ip_address IS UNIQUE",
                "CREATE CONSTRAINT person_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.email IS UNIQUE",
                "CREATE CONSTRAINT org_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.name IS UNIQUE",
                "CREATE CONSTRAINT ns_unique IF NOT EXISTS FOR (n:Nameserver) REQUIRE n.nameserver IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                    logger.info(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint may already exist: {constraint} - {str(e)}")
            
            # Create indexes for performance
            indexes = [
                "CREATE INDEX domain_registrant_email IF NOT EXISTS FOR (d:Domain) ON (d.registrant_email)",
                "CREATE INDEX domain_registrar IF NOT EXISTS FOR (d:Domain) ON (d.registrar)",
                "CREATE INDEX ip_asn IF NOT EXISTS FOR (i:IPAddress) ON (i.asn)",
                "CREATE INDEX ip_country IF NOT EXISTS FOR (i:IPAddress) ON (i.country)",
            ]
            
            for index in indexes:
                try:
                    await session.run(index)
                    logger.info(f"Created index: {index}")
                except Exception as e:
                    logger.warning(f"Index may already exist: {index} - {str(e)}")
            
        logger.info("Neo4j constraints and indexes created successfully")
        
    except Exception as e:
        logger.error(f"Failed to create constraints: {str(e)}")
        raise


# Database health checks
async def check_postgres_health() -> Dict:
    """Check PostgreSQL database health."""
    try:
        async for session in db_manager.get_postgres_session():
            result = await session.execute("SELECT 1")
            result.fetchone()
            return {"status": "healthy", "database": "postgresql"}
    except Exception as e:
        return {"status": "unhealthy", "database": "postgresql", "error": str(e)}


async def check_neo4j_health() -> Dict:
    """Check Neo4j database health."""
    try:
        async with db_manager.get_neo4j_session() as session:
            result = await session.run("RETURN 1 as test")
            await result.single()
            return {"status": "healthy", "database": "neo4j"}
    except Exception as e:
        return {"status": "unhealthy", "database": "neo4j", "error": str(e)}


async def check_database_health() -> Dict:
    """Check health of all databases."""
    postgres_health = await check_postgres_health()
    neo4j_health = await check_neo4j_health()
    
    return {
        "postgresql": postgres_health,
        "neo4j": neo4j_health,
        "overall": "healthy" if all(db["status"] == "healthy" for db in [postgres_health, neo4j_health]) else "unhealthy"
    }


# Utility functions for database operations
async def execute_postgres_query(query: str, params: Dict = None) -> List[Dict]:
    """Execute a raw PostgreSQL query."""
    async for session in db_manager.get_postgres_session():
        try:
            result = await session.execute(query, params or {})
            if result.returns_rows:
                return [dict(row._mapping) for row in result.fetchall()]
            else:
                return []
        except Exception as e:
            logger.error(f"PostgreSQL query error: {str(e)}")
            raise


async def execute_neo4j_query(query: str, parameters: Dict = None) -> List[Dict]:
    """Execute a Neo4j query."""
    try:
        async with db_manager.get_neo4j_session() as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records
    except Exception as e:
        logger.error(f"Neo4j query error: {str(e)}")
        raise


# Transaction helpers
async def execute_postgres_transaction(operations: List[callable]) -> bool:
    """Execute multiple operations in a PostgreSQL transaction."""
    async for session in db_manager.get_postgres_session():
        try:
            async with session.begin():
                for operation in operations:
                    await operation(session)
                await session.commit()
                return True
        except Exception as e:
            await session.rollback()
            logger.error(f"PostgreSQL transaction error: {str(e)}")
            raise


# Initialization function for startup
async def initialize_databases():
    """Initialize all databases."""
    try:
        await db_manager.initialize()
        
        # Create tables and constraints
        await create_tables()
        await create_constraints()
        
        logger.info("All databases initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise


# Cleanup function for shutdown
async def cleanup_databases():
    """Cleanup database connections."""
    await db_manager.close()
    logger.info("Database connections cleaned up")