from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "OSINT Intelligence Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # API
    API_PREFIX: str = "/api"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://frontend:3000"
    ]
    
    # PostgreSQL
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "osint_user")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "osint_password")
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", "5432"))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "osint_db")
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Neo4j
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "osint_neo4j_password")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Scraping
    USER_AGENT: str = "OSINT-Platform/1.0"
    REQUEST_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
