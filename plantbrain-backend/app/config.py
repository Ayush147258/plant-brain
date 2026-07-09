"""Environment variable and settings definitions for PlantBrain."""

import os
from functools import lru_cache
from typing import Annotated, Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


def _first_env(*names: str) -> str:
    """Return the first non-empty environment variable from a list of aliases."""

    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return ""


def _is_production_env() -> bool:
    """Return True when the process is running as the deployed backend."""

    return os.getenv("ENVIRONMENT", os.getenv("environment", "development")).lower() == "production"


def _default_data_path(relative_path: str) -> str:
    """Use Hugging Face persistent storage in production, local data otherwise."""

    if _is_production_env():
        return f"/data/{relative_path}"
    return f"./data/{relative_path}"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    gemini_api_key: str = _first_env("GEMINI_API_KEY", "gemini_api_key", "gemini_api")
    gemini_model: str = "gemini-3.5-flash"
    gemini_extraction_model: str = "gemini-3.5-flash"
    multimodal_extraction_enabled: bool = True
    graph_backend: str = "neo4j"
    require_neo4j_in_production: bool = True
    worker_queue_url: str = ""
    environment: str = "development"
    database_url: str = (
        _first_env("DATABASE_URL", "database_url", "supabase_database_url", "supabasedatabase_url")
        or ("sqlite+aiosqlite:////data/plantbrain.db" if _is_production_env() else "sqlite+aiosqlite:///./data/plantbrain.db")
    )
    neo4j_uri: str = ""
    neo4j_user: str = ""
    neo4j_password: str = _first_env("NEO4J_PASSWORD", "neo4j_password")
    chroma_persist_dir: str = _default_data_path("chroma_db")
    graph_persist_path: str = _default_data_path("graph/equipment_graph.pkl")
    upload_dir: str = _default_data_path("uploads")
    document_parser: str = "docling"
    ocr_confidence_threshold: float = 55.0
    max_upload_size_mb: int = 50
    chunk_size: int = 800
    chunk_overlap: int = 100
    embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    lightweight_embeddings: bool = False
    top_k_results: int = 5
    whisper_model: str = "base"
    cors_origins: Annotated[list[str], NoDecode] = ["*"]
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_whatsapp_from: str = "whatsapp:+14155238886"
    rate_limit_requests_per_minute: int = 60
    rate_limit_enabled: bool = True
    admin_api_key: str = _first_env("ADMIN_API_KEY", "admin_api_key", "admin_apikey") or "changeme"
    default_language: str = "en"
    supported_languages: Annotated[list[str], NoDecode] = ["en", "hi"]

    model_config = SettingsConfigDict(env_file=".env")


    @model_validator(mode="after")
    def apply_environment_defaults(self) -> "Settings":
        """Tune defaults for constrained demo containers."""

        if self.environment == "production":
            self.chunk_size = 600
            self.top_k_results = 3
            self.whisper_model = "tiny"
            if self.database_url == "sqlite+aiosqlite:///./data/plantbrain.db":
                self.database_url = "sqlite+aiosqlite:////data/plantbrain.db"
            self.chroma_persist_dir = self._production_data_path(self.chroma_persist_dir, "chroma_db")
            self.graph_persist_path = self._production_data_path(self.graph_persist_path, "graph/equipment_graph.pkl")
            self.upload_dir = self._production_data_path(self.upload_dir, "uploads")
        return self

    @staticmethod
    def _production_data_path(value: str, fallback: str) -> str:
        """Normalize local data paths to Hugging Face persistent storage."""

        if not value:
            return f"/data/{fallback}"
        normalized = value.replace("\\", "/")
        if normalized.startswith("./data/"):
            return f"/data/{normalized.removeprefix('./data/')}"
        if normalized == "./data":
            return "/data"
        return value

    @field_validator("cors_origins", "supported_languages", mode="before")
    @classmethod
    def parse_list_settings(cls, value: Any) -> list[str] | Any:
        """Parse CORS origins from a list, wildcard, or comma-separated string."""

        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings."""

    return Settings()


settings = get_settings()
