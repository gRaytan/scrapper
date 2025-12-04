"""Global configuration settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database
    database_url: str = "postgresql://scraper:password@localhost:5432/scraper_db"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    redis_max_connections: int = 50
    
    # LLM
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_provider: str = "openai"
    llm_model: str = "gpt-4-turbo-preview"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    
    # Scraping
    scraper_user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    scraper_timeout: int = 30
    scraper_max_retries: int = 3
    scraper_retry_delay: int = 5
    scraper_concurrent_workers: int = 5
    scraper_rate_limit: int = 10

    # Job Lifecycle
    job_stale_days: int = 90  # Days without updates before marking inactive
    job_posted_cutoff_days: int = 120  # Days since posted_date before marking inactive
    
    # Proxy
    use_proxy: bool = False
    proxy_url: Optional[str] = None
    proxy_username: Optional[str] = None
    proxy_password: Optional[str] = None
    
    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    log_file: str = "logs/scraper.log"
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_reload: bool = False

    # JWT Authentication
    jwt_secret_key: str = "your-secret-key-change-in-production-use-openssl-rand-hex-32"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30  # 30 minutes
    jwt_refresh_token_expire_days: int = 7     # 7 days

    # Monitoring
    sentry_dsn: Optional[str] = None
    prometheus_port: int = 9090

    # Application
    environment: str = "development"
    debug: bool = True
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"
    
    @property
    def db_pool_size(self) -> int:
        """Alias for database_pool_size."""
        return self.database_pool_size
    
    @property
    def db_max_overflow(self) -> int:
        """Alias for database_max_overflow."""
        return self.database_max_overflow
    
    @property
    def db_echo(self) -> bool:
        """Echo SQL queries (for debugging)."""
        return self.debug
    
    @property
    def base_dir(self):
        """Get base directory of the project."""
        from pathlib import Path
        return Path(__file__).parent.parent


# Global settings instance
settings = Settings()
