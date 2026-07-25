"""Configuration management for Atlas."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration."""
    
    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/atlas",
        description="Async database connection URL",
    )
    echo: bool = Field(
        default=False,
        description="Echo SQL queries",
    )
    pool_size: int = Field(
        default=20,
        description="Connection pool size",
    )
    max_overflow: int = Field(
        default=10,
        description="Max pool overflow",
    )
    pool_timeout: int = Field(
        default=30,
        description="Pool timeout in seconds",
    )
    pool_recycle: int = Field(
        default=3600,
        description="Pool recycle time in seconds",
    )

    model_config = SettingsConfigDict(
        env_prefix="ATLAS_DB_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


class RedisSettings(BaseSettings):
    """Redis configuration."""
    
    url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    db: int = Field(
        default=0,
        description="Redis database number",
    )
    password: str | None = Field(
        default=None,
        description="Redis password",
    )
    max_connections: int = Field(
        default=50,
        description="Max Redis connections",
    )
    socket_timeout: int = Field(
        default=5,
        description="Socket timeout in seconds",
    )
    socket_connect_timeout: int = Field(
        default=5,
        description="Socket connect timeout in seconds",
    )

    model_config = SettingsConfigDict(
        env_prefix="ATLAS_REDIS_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


class LLMSettings(BaseSettings):
    """LLM provider configuration."""
    
    provider: Literal["openai", "anthropic", "ollama"] = Field(
        default="openai",
        description="Default LLM provider",
    )
    api_key: str | None = Field(
        default=None,
        description="API key for LLM provider",
    )
    base_url: str | None = Field(
        default=None,
        description="Base URL for LLM API (for proxies)",
    )
    model: str = Field(
        default="gpt-4",
        description="Default model name",
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default temperature",
    )
    max_tokens: int = Field(
        default=128000,
        description="Max tokens per request",
    )
    request_timeout: int = Field(
        default=60,
        description="Request timeout in seconds",
    )

    model_config = SettingsConfigDict(
        env_prefix="ATLAS_LLM_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


class SecuritySettings(BaseSettings):
    """Security configuration."""
    
    secret_key: str = Field(
        default="change-me-in-production",
        description="Secret key for JWT and encryption",
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration in minutes",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration in days",
    )

    model_config = SettingsConfigDict(
        env_prefix="ATLAS_SECURITY_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


class APISettings(BaseSettings):
    """API configuration."""
    
    host: str = Field(
        default="0.0.0.0",
        description="API host",
    )
    port: int = Field(
        default=8000,
        description="API port",
    )
    workers: int = Field(
        default=4,
        description="Number of workers",
    )
    reload: bool = Field(
        default=False,
        description="Enable auto-reload",
    )
    log_level: Literal["debug", "info", "warning", "error"] = Field(
        default="info",
        description="Log level",
    )
    cors_origins: list[str] = Field(
        default=["*"],
        description="CORS allowed origins",
    )
    rate_limit_per_minute: int = Field(
        default=60,
        description="Rate limit per minute per IP",
    )

    model_config = SettingsConfigDict(
        env_prefix="ATLAS_API_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


class SandboxSettings(BaseSettings):
    """Sandbox execution configuration."""
    
    enabled: bool = Field(
        default=True,
        description="Enable sandbox execution",
    )
    docker_enabled: bool = Field(
        default=True,
        description="Enable Docker sandbox",
    )
    docker_image: str = Field(
        default="atlas-sandbox:latest",
        description="Docker image for sandbox",
    )
    memory_limit: str = Field(
        default="512m",
        description="Memory limit per sandbox",
    )
    cpu_limit: float = Field(
        default=1.0,
        description="CPU limit per sandbox",
    )
    timeout_seconds: int = Field(
        default=300,
        description="Execution timeout in seconds",
    )
    max_concurrent: int = Field(
        default=10,
        description="Max concurrent sandboxes",
    )
    network_enabled: bool = Field(
        default=False,
        description="Enable network in sandbox",
    )

    model_config = SettingsConfigDict(
        env_prefix="ATLAS_SANDBOX_",
        env_file=".env",
        env_file_encoding="utf-8",
    )


class Settings(BaseSettings):
    """Main application settings."""
    
    app_name: str = Field(
        default="Atlas AI OS",
        description="Application name",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version",
    )
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Environment",
    )
    debug: bool = Field(
        default=False,
        description="Debug mode",
    )
    
    # Subsections
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    api: APISettings = Field(default_factory=APISettings)
    sandbox: SandboxSettings = Field(default_factory=SandboxSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
