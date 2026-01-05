"""
Core configuration settings for SmartRecon-AI
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Project metadata
    PROJECT_NAME: str = "SmartRecon-AI"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # Server Configuration
    PORT: int = 8000
    
    # Security
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    API_KEY_HEADER: str = "X-API-Key"
    
    # Admin user
    ADMIN_EMAIL: str = "admin@smartrecon.local"
    ADMIN_PASSWORD: str
    ADMIN_USERNAME: str = "admin"
    
    # LLM Configuration
    LLM_PROVIDER: str = "openai"
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo"
    OPENAI_MAX_TOKENS: int = 4096
    OPENAI_TEMPERATURE: float = 0.3
    
    # Gemini
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-pro"
    
    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    
    # Local models
    LOCAL_MODEL_URL: Optional[str] = None
    LOCAL_MODEL_NAME: str = "llama2"
    
    # LLM behavior
    LLM_MAX_RETRIES: int = 3
    LLM_TIMEOUT: int = 60
    LLM_ENABLE_CACHING: bool = True
    
    # Recon tool configuration
    MAX_CONCURRENT_SCANS: int = 5
    DEFAULT_TIMEOUT: int = 3600
    DEFAULT_RATE_LIMIT: int = 10
    MAX_SUBDOMAIN_RESULTS: int = 10000
    
    # Tool-specific timeouts
    AMASS_TIMEOUT: int = 3600
    SUBFINDER_TIMEOUT: int = 1800
    HTTPX_THREADS: int = 50
    HTTPX_TIMEOUT: int = 10
    FFUF_THREADS: int = 40
    FFUF_TIMEOUT: int = 900
    NUCLEI_CONCURRENCY: int = 25
    NUCLEI_RATE_LIMIT: int = 150
    KATANA_CONCURRENCY: int = 10
    KATANA_DEPTH: int = 3
    
    # Scope & compliance
    BLOCKED_TLD: List[str] = [".gov", ".mil", ".edu"]
    BLOCKED_IP_RANGES: List[str] = ["10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "169.254.0.0/16"]
    REQUIRE_EXPLICIT_AUTHORIZATION: bool = True
    ENABLE_SCOPE_VALIDATION: bool = True
    
    # API server
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = False
    API_LOG_LEVEL: str = "info"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 10
    
    # Celery workers
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 4
    CELERY_TASK_SOFT_TIME_LIMIT: int = 3600
    CELERY_TASK_HARD_TIME_LIMIT: int = 7200
    CELERY_TASK_MAX_RETRIES: int = 3
    
    # Reporting
    REPORTS_DIR: str = "/app/reports"
    REPORT_RETENTION_DAYS: int = 90
    ENABLE_PDF_EXPORT: bool = True
    ENABLE_HTML_EXPORT: bool = True
    ENABLE_MARKDOWN_EXPORT: bool = True
    
    # Storage
    STORAGE_BACKEND: str = "local"
    STORAGE_PATH: str = "/app/storage"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_FILE: Optional[str] = None
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PORT: int = 9090
    
    # Sentry
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = "production"
    
    # Notifications
    ENABLE_NOTIFICATIONS: bool = False
    SLACK_WEBHOOK_URL: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @field_validator("BLOCKED_TLD", mode="before")
    @classmethod
    def parse_blocked_tld(cls, v):
        """Parse blocked TLDs from string"""
        if isinstance(v, str):
            return [tld.strip() for tld in v.split(",")]
        return v
    
    @field_validator("BLOCKED_IP_RANGES", mode="before")
    @classmethod
    def parse_blocked_ip_ranges(cls, v):
        """Parse blocked IP ranges from string"""
        if isinstance(v, str):
            return [ip.strip() for ip in v.split(",")]
        return v
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_parse_none_str="null"
    )


# Create settings instance
settings = Settings()
