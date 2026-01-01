"""Tests for database operations"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import asyncio

from backend.utils.database import DatabaseManager, PostgreSQLManager, Neo4jManager


@pytest.fixture
def postgres_config():
    """Test PostgreSQL configuration"""
    return {
        'enabled': True,
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'password',
        'database': 'test_db',
        'min_connections': 2,
        'max_connections': 10
    }


@pytest.fixture
def neo4j_config():
    """Test Neo4j configuration"""
    return {
        'enabled': True,
        'uri': 'bolt://localhost:7687',
        'user': 'neo4j',
        'password': 'password'
    }


@pytest.mark.asyncio
class TestPostgreSQLManager:
    """Tests for PostgreSQL database manager"""
    
    async def test_initialization(self, postgres_config):
        """Test PostgreSQL manager initialization"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            manager = PostgreSQLManager(postgres_config)
            await manager.initialize()
            
            assert manager.pool is not None
            mock_create_pool.assert_called_once()
    
    async def test_close(self, postgres_config):
        """Test closing database connection"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            manager = PostgreSQLManager(postgres_config)
            await manager.initialize()
            await manager.close()
            
            mock_pool.close.assert_called_once()
    
    async def test_log_search_query(self, postgres_config):
        """Test logging a search query"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()
            mock_pool.acquire = AsyncMock(return_value=mock_conn)
            mock_create_pool.return_value = mock_pool
            
            manager = PostgreSQLManager(postgres_config)
            await manager.initialize()
            
            await manager.log_search_query(
                search_type='username_search',
                query_params={'username': 'johndoe'},
                ip_address='127.0.0.1',
                user_agent='test-agent'
            )
            
            mock_conn.execute.assert_called_once()
    
    async def test_get_identity_data(self, postgres_config):
        """Test retrieving identity data"""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_conn = AsyncMock()
            mock_conn.fetch = AsyncMock(return_value=[])
            mock_pool.acquire = AsyncMock(return_value=mock_conn)
            mock_create_pool.return_value = mock_pool
            
            manager = PostgreSQLManager(postgres_config)
            await manager.initialize()
            
            data = await manager.get_identity_data('johndoe')
            
            mock_conn.fetch.assert_called_once()
            assert isinstance(data, list)


@pytest.mark.asyncio
class TestNeo4jManager:
    """Tests for Neo4j graph database manager"""
    
    async def test_initialization(self, neo4j_config):
        """Test Neo4j manager initialization"""
        with patch('neo4j.GraphDatabase.driver') as mock_driver:
            mock_session = Mock()
            mock_driver_instance = Mock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance
            
            manager = Neo4jManager(neo4j_config)
            await manager.initialize()
            
            assert manager.driver is not None
    
    async def test_create_identity_node(self, neo4j_config):
        """Test creating an identity node in Neo4j"""
        with patch('neo4j.GraphDatabase.driver') as mock_driver:
            mock_session = Mock()
            mock_result = Mock()
            mock_result.single.return_value = {"id": "node-123"}
            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_driver_instance = Mock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance
            
            manager = Neo4jManager(neo4j_config)
            await manager.initialize()
            
            node_id = await manager.create_identity_node(
                node_type='username',
                value='johndoe',
                platform='GitHub',
                confidence=0.95
            )
            
            assert node_id == "node-123"
            mock_session.run.assert_called()
    
    async def test_create_relationship(self, neo4j_config):
        """Test creating a relationship in Neo4j"""
        with patch('neo4j.GraphDatabase.driver') as mock_driver:
            mock_session = Mock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_driver_instance = Mock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance
            
            manager = Neo4jManager(neo4j_config)
            await manager.initialize()
            
            await manager.create_relationship(
                source_id='node-1',
                target_id='node-2',
                relationship_type='found_on',
                confidence=0.95
            )
            
            mock_session.run.assert_called()
    
    async def test_get_identity_chain(self, neo4j_config):
        """Test retrieving identity chain from Neo4j"""
        with patch('neo4j.GraphDatabase.driver') as mock_driver:
            mock_session = Mock()
            mock_result = Mock()
            mock_result.data.return_value = []
            mock_result.__aiter__ = Mock(return_value=iter([]))
            mock_session.run.return_value = mock_result
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=None)
            
            mock_driver_instance = Mock()
            mock_driver_instance.session.return_value = mock_session
            mock_driver.return_value = mock_driver_instance
            
            manager = Neo4jManager(neo4j_config)
            await manager.initialize()
            
            chain = await manager.get_identity_chain('johndoe')
            
            assert 'nodes' in chain
            assert 'relationships' in chain
            assert 'chain_length' in chain


@pytest.mark.asyncio
class TestDatabaseManager:
    """Tests for database manager orchestration"""
    
    async def test_initialization(self):
        """Test database manager initialization"""
        config = {
            'postgresql': {
                'enabled': True,
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': 'password',
                'database': 'test_db'
            },
            'neo4j': {
                'enabled': True,
                'uri': 'bolt://localhost:7687',
                'user': 'neo4j',
                'password': 'password'
            }
        }
        
        with patch('asyncpg.create_pool'), patch('neo4j.GraphDatabase.driver'):
            manager = DatabaseManager(config)
            await manager.initialize()
            
            assert manager.postgresql is not None
            assert manager.neo4j is not None
    
    async def test_initialization_postgres_only(self):
        """Test initialization with only PostgreSQL"""
        config = {
            'postgresql': {
                'enabled': True,
                'host': 'localhost',
                'port': 5432,
                'user': 'postgres',
                'password': 'password',
                'database': 'test_db'
            },
            'neo4j': {
                'enabled': False
            }
        }
        
        with patch('asyncpg.create_pool'):
            manager = DatabaseManager(config)
            await manager.initialize()
            
            assert manager.postgresql is not None
            assert manager.neo4j is None
    
    async def test_initialization_neo4j_only(self):
        """Test initialization with only Neo4j"""
        config = {
            'postgresql': {
                'enabled': False
            },
            'neo4j': {
                'enabled': True,
                'uri': 'bolt://localhost:7687',
                'user': 'neo4j',
                'password': 'password'
            }
        }
        
        with patch('neo4j.GraphDatabase.driver'):
            manager = DatabaseManager(config)
            await manager.initialize()
            
            assert manager.postgresql is None
            assert manager.neo4j is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
