"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4-turbo-preview"

    # Kubernetes Configuration
    kubeconfig_path: Optional[str] = None
    in_cluster: bool = False
    default_namespace: str = "default"

    # Application Settings
    app_name: str = "IntelliK8sBot"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"

    # API Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./data/intellik8s.db"

    # Security Settings
    allow_destructive_operations: bool = False
    require_confirmation: bool = True

    # Feature Flags
    enable_auto_remediation: bool = False
    enable_cost_analysis: bool = True
    enable_resource_recommendations: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
