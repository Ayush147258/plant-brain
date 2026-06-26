"""Environment variable and settings definitions for PlantBrain."""

from functools import lru_cache
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    environment: str = "development"
    database_url: str
    chroma_persist_dir: str = "./data/chroma_db"
    graph_persist_path: str = "./data/graph/equipment_graph.pkl"
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 50
    chunk_size: int = 800
    chunk_overlap: int = 100
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    top_k_results: int = 5
    whisper_model: str = "base"
    cors_origins: list[str] = ["*"]
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    rate_limit_requests_per_minute: int = 60
    rate_limit_enabled: bool = True
    admin_api_key: str = "changeme"
    default_language: str = "en"
    supported_languages: list[str] = ["en", "hi"]

    model_config = SettingsConfigDict(env_file=".env")


    @model_validator(mode="after")
    def apply_environment_defaults(self) -> "Settings":
        """Tune defaults for constrained production environments like Render free tier."""

        if self.environment == "production":
            self.chunk_size = 600
            self.top_k_results = 3
            self.whisper_model = "tiny"
        return self

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str] | Any:
        """Parse CORS origins from a list, wildcard, or comma-separated string."""

        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


settings = get_settings()




