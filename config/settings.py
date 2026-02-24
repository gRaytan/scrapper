"""Global configuration settings."""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
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


    # Internal API Key (for Node BFF to call Python API)
    internal_api_key: str = "change-this-in-production-use-openssl-rand-hex-32"

    # Monitoring
    sentry_dsn: Optional[str] = None
    prometheus_port: int = 9090

    # Mixpanel Analytics
    mixpanel_token: Optional[str] = None

    # AWS SES Email Configuration
    ses_from_email: str = "noreply@hiddenjobs.me"
    ses_from_name: str = "HiddenJobs"
    aws_region: str = "eu-north-1"

    # OneSignal Email Configuration
    onesignal_enabled: bool = True  # Use OneSignal for emails (SES is fallback)
    onesignal_app_id: Optional[str] = None
    onesignal_api_key: Optional[str] = None
    onesignal_from_email: str = "noreply@hiddenjobs.me"
    onesignal_from_name: str = "HiddenJobs"

    # Email Digest Configuration
    email_digest_hour_utc: int = 6  # 6 AM UTC = 8 AM Israel time
    email_digest_enabled: bool = True

    # Application
    environment: str = "development"
    debug: bool = True

    # LinkedIn Job Search
    # Categories: Engineering, Data/Analytics, Product, Business Analyst, Marketing, Sales, GTM, Customer Success
    linkedin_job_positions: str = (
        # Engineering & Technical
        "Software Engineer,Backend Developer,Frontend Developer,Full Stack Developer,"
        "DevOps Engineer,Data Engineer,Data Scientist,Machine Learning Engineer,"
        "QA Engineer,Security Engineer,Cloud Engineer,Mobile Developer,Site Reliability Engineer,"
        "VP Engineering,VP R&D,VP of Engineering,VP of R&D,Vice President Engineering,Vice President R&D,"
        "Director of Engineering,Director of R&D,Engineering Director,R&D Director,"
        "Head of Engineering,Head of R&D,CTO,Chief Technology Officer,"
        # Product
        "Product Manager,Senior Product Manager,VP Product,Head of Product,Chief Product Officer,"
        # Business Analyst & BI
        "Business Analyst,Senior Business Analyst,BI Analyst,Senior BI Analyst,"
        "Business Data Analyst,Senior Business Data Analyst,Business Intelligence Analyst,"
        # Marketing
        "Marketing Manager,Senior Marketing Manager,VP Marketing,CMO,Chief Marketing Officer,"
        "Product Marketing Manager,Senior Product Marketing Manager,Head of Product Marketing,"
        "Growth Marketing Manager,Demand Generation Manager,Digital Marketing Manager,"
        "Content Marketing Manager,Brand Manager,Marketing Director,Head of Marketing,"
        # Sales
        "Account Executive,Senior Account Executive,Enterprise Account Executive,"
        "Sales Development Representative,SDR,Business Development Representative,BDR,"
        "Account Manager,Senior Account Manager,Sales Manager,Regional Sales Manager,"
        "VP Sales,Head of Sales,Chief Revenue Officer,CRO,Sales Director,"
        # GTM & Partnerships
        "GTM Manager,Go-to-Market Manager,Partner Manager,Partnerships Manager,"
        "Channel Manager,Alliances Manager,Business Development Manager,Strategic Partnerships,"
        "VP Partnerships,Head of Partnerships,VP Business Development,"
        # Customer Success
        "Customer Success Manager,Senior Customer Success Manager,VP Customer Success,"
        "Head of Customer Success,Customer Success Director,Account Success Manager"
    )
    linkedin_search_location: str = "Israel"
    linkedin_max_pages: int = 10

    # Location filtering - comma-separated list of allowed countries
    allowed_countries: str = "Israel"

    # CORS - comma-separated list of allowed origins (use * for all in dev)
    cors_origins: str = "https://hiddenjobs.me,https://www.hiddenjobs.me"

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

    @property
    def linkedin_positions_list(self) -> list[str]:
        """Get LinkedIn job positions as a list."""
        if not self.linkedin_job_positions:
            return []
        return [pos.strip() for pos in self.linkedin_job_positions.split(',') if pos.strip()]

    @property
    def allowed_countries_list(self) -> list[str]:
        """Get allowed countries as a list."""
        if not self.allowed_countries:
            return ["Israel"]  # Default to Israel
        return [country.strip() for country in self.allowed_countries.split(',') if country.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list. Returns ['*'] if set to * or empty."""
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]


# Global settings instance
settings = Settings()
