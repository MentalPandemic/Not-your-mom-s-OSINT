"""
Database connection and session management for domain intelligence.

Provides async SQLAlchemy connection to PostgreSQL with proper
connection pooling and transaction management.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import AsyncAdaptedQueuePool

from database.models import Base

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager for PostgreSQL."""
    
    def __init__(
        self,
        database_url: str,
        pool_size: int = 10,
        max_overflow: int = 20,
        echo: bool = False,
    ):
        """
        Initialize database connection.
        
        Args:
            database_url: PostgreSQL connection URL (async)
            pool_size: Connection pool size
            max_overflow: Maximum overflow connections
            echo: Whether to log SQL statements
        """
        self.database_url = database_url
        self._engine: Optional[AsyncEngine] = None
        self._session_factory: Optional[async_sessionmaker] = None
        
        # Create async engine
        self._engine = create_async_engine(
            database_url,
            poolclass=AsyncAdaptedQueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=echo,
        )
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    
    async def create_tables(self):
        """Create all database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self):
        """Drop all database tables."""
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a database session.
        
        Yields:
            AsyncSession: Database session
            
        Example:
            async with db.session() as session:
                result = await session.execute(query)
        """
        session = self._session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get a session within a transaction.
        
        Yields:
            AsyncSession: Database session in transaction
            
        Example:
            async with db.transaction() as session:
                session.add(domain)
        """
        async with self.session() as session:
            async with session.begin():
                yield session
    
    async def close(self):
        """Close the database connection."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None


def get_database_url(
    host: str = "localhost",
    port: int = 5432,
    database: str = "domain_intel",
    user: str = "postgres",
    password: str = "postgres",
) -> str:
    """
    Generate PostgreSQL connection URL.
    
    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        
    Returns:
        str: Async PostgreSQL connection URL
    """
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"


async def get_db() -> AsyncGenerator[Database, None]:
    """
    Get database instance for dependency injection.
    
    Yields:
        Database: Database instance
    """
    from app import get_database
    
    db = get_database()
    try:
        yield db
    finally:
        pass  # Don't close here, let the app manage lifecycle


class DomainRepository:
    """Repository for domain-related database operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_domain(self, domain: str):
        """Get domain by name."""
        from database.models import Domain
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Domain).where(Domain.domain == domain)
        )
        return result.scalar_one_or_none()
    
    async def create(self, **kwargs):
        """Create a new domain."""
        from database.models import Domain
        
        domain = Domain(**kwargs)
        self.session.add(domain)
        await self.session.flush()
        return domain
    
    async def update(self, domain: str, **kwargs):
        """Update a domain."""
        from database.models import Domain
        from sqlalchemy import select, update
        
        await self.session.execute(
            update(Domain).where(Domain.domain == domain).values(**kwargs)
        )
        
    async def get_all_by_registrant_email(self, email: str):
        """Get all domains registered with an email."""
        from database.models import Domain
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(Domain).where(
                Domain.registrant_email == email
            ).order_by(Domain.registration_date.desc())
        )
        return result.scalars().all()


class DnsRecordRepository:
    """Repository for DNS record operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_domain_and_type(self, domain: str, record_type: str):
        """Get DNS records for a domain and type."""
        from database.models import Domain, DnsRecord
        from sqlalchemy import select, join
        
        result = await self.session.execute(
            select(DnsRecord)
            .select_from(join(DnsRecord, Domain, DnsRecord.domain_id == Domain.id))
            .where(Domain.domain == domain)
            .where(DnsRecord.record_type == record_type)
        )
        return result.scalars().all()
    
    async def upsert_records(
        self,
        domain_id: int,
        records: list[dict],
    ):
        """Upsert DNS records."""
        from database.models import DnsRecord
        from sqlalchemy import delete
        
        # Delete existing records of same type
        if records:
            record_type = records[0].get("record_type")
            await self.session.execute(
                delete(DnsRecord)
                .where(DnsRecord.domain_id == domain_id)
                .where(DnsRecord.record_type == record_type)
            )
            
            # Add new records
            for record in records:
                dns_record = DnsRecord(domain_id=domain_id, **record)
                self.session.add(dns_record)


class IpAddressRepository:
    """Repository for IP address operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_ip(self, ip_address: str):
        """Get IP address by address."""
        from database.models import IpAddress
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(IpAddress).where(IpAddress.ip_address == ip_address)
        )
        return result.scalar_one_or_none()
    
    async def upsert(self, **kwargs):
        """Upsert IP address."""
        from database.models import IpAddress
        from sqlalchemy import select
        
        result = await self.session.execute(
            select(IpAddress).where(IpAddress.ip_address == kwargs.get("ip_address"))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            for key, value in kwargs.items():
                setattr(existing, key, value)
            return existing
        else:
            ip = IpAddress(**kwargs)
            self.session.add(ip)
            return ip


class RelatedDomainRepository:
    """Repository for related domain operations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_related(
        self,
        domain: str,
        relationship_type: Optional[str] = None,
    ):
        """Get related domains for a domain."""
        from database.models import Domain, RelatedDomain
        from sqlalchemy import select, join
        
        query = (
            select(RelatedDomain)
            .select_from(join(RelatedDomain, Domain, RelatedDomain.domain_id == Domain.id))
            .where(Domain.domain == domain)
        )
        
        if relationship_type:
            query = query.where(RelatedDomain.relationship_type == relationship_type)
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def create_relationship(
        self,
        domain_id: int,
        related_domain: str,
        relationship_type: str,
        confidence: float = 1.0,
        **kwargs,
    ):
        """Create a related domain relationship."""
        from database.models import RelatedDomain
        
        relationship = RelatedDomain(
            domain_id=domain_id,
            related_domain=related_domain,
            relationship_type=relationship_type,
            confidence=confidence,
            **kwargs,
        )
        self.session.add(relationship)
        return relationship
