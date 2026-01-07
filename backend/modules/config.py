"""
Configuration Settings for Username Enumeration Service
"""

from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings"""
    
    # Database settings
    database_url: str = Field(
        default="postgresql+asyncpg://username_enum:password@localhost/username_enum",
        description="PostgreSQL database connection URL",
    )
    
    # Neo4j settings
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        description="Neo4j connection URI",
    )
    neo4j_username: str = Field(
        default="neo4j",
        description="Neo4j username",
    )
    neo4j_password: str = Field(
        default="password",
        description="Neo4j password",
    )
    
    # Username enumeration settings
    enum_config_path: Optional[str] = Field(
        default=None,
        description="Path to username enumeration platform configuration file",
    )
    max_concurrent_requests: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum concurrent platform requests",
    )
    default_timeout: float = Field(
        default=10.0,
        ge=1.0,
        le=30.0,
        description="Default timeout for platform requests (seconds)",
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retry attempts for failed requests",
    )
    
    # Cache settings
    enable_cache: bool = Field(
        default=True,
        description="Enable search result caching",
    )
    cache_ttl_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Cache time-to-live in hours",
    )
    
    # Rate limiting settings
    enable_rate_limiting: bool = Field(
        default=True,
        description="Enable API rate limiting",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        ge=10,
        le=1000,
        description="Maximum requests per minute per IP",
    )
    
    # Fuzzy matching settings
    fuzzy_threshold: int = Field(
        default=70,
        ge=0,
        le=100,
        description="Minimum similarity score for fuzzy matches (0-100)",
    )
    max_username_variations: int = Field(
        default=50,
        ge=10,
        le=200,
        description="Maximum username variations to generate",
    )
    
    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)",
    )
    
    # Development settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode (enables docs, detailed errors)",
    )
    
    # Performance settings
    connection_pool_size: int = Field(
        default=20,
        ge=5,
        le=100,
        description="Database connection pool size",
    )
    max_overflow_connections: int = Field(
        default=40,
        ge=10,
        le=200,
        description="Maximum overflow database connections",
    )
    
    # Monitoring settings
    enable_metrics: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
    )
    metrics_port: int = Field(
        default=9090,
        ge=1024,
        le=65535,
        description="Port for metrics endpoint",
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
