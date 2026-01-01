from neo4j import AsyncGraphDatabase
from loguru import logger
from app.core.config import settings


class Neo4jConnection:
    """Neo4j database connection manager"""
    
    def __init__(self):
        self.driver = None
        self.uri = settings.NEO4J_URI
        self.user = settings.NEO4J_USER
        self.password = settings.NEO4J_PASSWORD
    
    async def get_driver(self):
        """Get or create Neo4j driver"""
        if self.driver is None:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password)
            )
        return self.driver
    
    async def close(self):
        """Close Neo4j connection"""
        if self.driver is not None:
            await self.driver.close()
            self.driver = None
    
    async def test_connection(self):
        """Test Neo4j connection"""
        driver = await self.get_driver()
        async with driver.session() as session:
            result = await session.run("RETURN 1 AS test")
            record = await result.single()
            return record["test"] == 1
    
    async def execute_query(self, query: str, parameters: dict = None):
        """Execute a Cypher query"""
        driver = await self.get_driver()
        async with driver.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()
    
    async def create_indexes(self):
        """Create Neo4j indexes for better performance"""
        driver = await self.get_driver()
        async with driver.session() as session:
            # Create indexes for common node types
            indexes = [
                "CREATE INDEX identity_id IF NOT EXISTS FOR (n:Identity) ON (n.id)",
                "CREATE INDEX email_address IF NOT EXISTS FOR (n:Email) ON (n.address)",
                "CREATE INDEX phone_number IF NOT EXISTS FOR (n:Phone) ON (n.number)",
                "CREATE INDEX username_value IF NOT EXISTS FOR (n:Username) ON (n.value)",
                "CREATE INDEX domain_name IF NOT EXISTS FOR (n:Domain) ON (n.name)",
                "CREATE INDEX social_profile IF NOT EXISTS FOR (n:SocialMedia) ON (n.profile_url)",
                "CREATE INDEX adult_profile IF NOT EXISTS FOR (n:AdultProfile) ON (n.profile_url)",
                "CREATE INDEX personals_post IF NOT EXISTS FOR (n:PersonalsPost) ON (n.post_id)",
            ]
            
            for index in indexes:
                try:
                    await session.run(index)
                    logger.info(f"Created index: {index}")
                except Exception as e:
                    logger.warning(f"Index may already exist or error: {e}")
    
    async def create_constraints(self):
        """Create Neo4j constraints"""
        driver = await self.get_driver()
        async with driver.session() as session:
            constraints = [
                "CREATE CONSTRAINT identity_unique IF NOT EXISTS FOR (n:Identity) REQUIRE n.id IS UNIQUE",
                "CREATE CONSTRAINT email_unique IF NOT EXISTS FOR (n:Email) REQUIRE n.address IS UNIQUE",
                "CREATE CONSTRAINT phone_unique IF NOT EXISTS FOR (n:Phone) REQUIRE n.number IS UNIQUE",
            ]
            
            for constraint in constraints:
                try:
                    await session.run(constraint)
                    logger.info(f"Created constraint: {constraint}")
                except Exception as e:
                    logger.warning(f"Constraint may already exist or error: {e}")


# Global instance
neo4j_conn = Neo4jConnection()


async def get_neo4j():
    """Dependency for getting Neo4j connection"""
    return neo4j_conn
