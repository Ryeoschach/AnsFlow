"""
Configuration management for AnsFlow FastAPI service
"""
import os
from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings"""
    
    # Database connection
    database_url: str = Field(
        default="mysql+aiomysql://ansflow_user:ansflow_password_123@localhost:3306/ansflow_db",
        description="Database connection URL"
    )
    pool_size: int = Field(default=10, description="Database connection pool size")
    max_overflow: int = Field(default=20, description="Database connection pool overflow")
    
    model_config = SettingsConfigDict(env_prefix="DB_")


class RedisSettings(BaseSettings):
    """Redis configuration settings"""
    
    url: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    max_connections: int = Field(default=10, description="Maximum Redis connections")
    
    model_config = SettingsConfigDict(env_prefix="REDIS_")


class RabbitMQSettings(BaseSettings):
    """RabbitMQ configuration settings"""
    
    url: str = Field(default="amqp://guest:guest@localhost:5672/", description="RabbitMQ connection URL")
    exchange_name: str = Field(default="ansflow", description="RabbitMQ exchange name")
    queue_name: str = Field(default="ansflow_events", description="RabbitMQ queue name")
    
    model_config = SettingsConfigDict(env_prefix="RABBITMQ_")


class JWTSettings(BaseSettings):
    """JWT configuration settings"""
    
    secret_key: str = Field(default="your-secret-key-change-in-production", description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=60, description="Access token expiration in minutes")
    
    model_config = SettingsConfigDict(env_prefix="JWT_")


class APISettings(BaseSettings):
    """API configuration settings"""
    
    title: str = Field(default="AnsFlow FastAPI Service", description="API title")
    description: str = Field(default="High-performance API service for AnsFlow CI/CD platform", description="API description")
    version: str = Field(default="1.0.0", description="API version")
    
    # CORS settings
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"],
        description="CORS allowed origins"
    )
    
    # Rate limiting
    rate_limit_per_minute: int = Field(default=100, description="Rate limit per minute")
    
    model_config = SettingsConfigDict(env_prefix="API_")


class Settings(BaseSettings):
    """Main application settings"""
    
    # Environment
    environment: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=True, description="Debug mode")
    
    # Service settings
    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(default=8001, description="Service port")
    workers: int = Field(default=1, description="Number of workers")
    
    # Django service integration
    django_service_url: str = Field(
        default="http://localhost:8000",
        description="Django service URL for integration"
    )
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Logging format")
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    rabbitmq: RabbitMQSettings = Field(default_factory=RabbitMQSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    api: APISettings = Field(default_factory=APISettings)
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment.lower() == "production"


# Global settings instance
settings = Settings()
