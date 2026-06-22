from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List
import logging
import sys

class Settings(BaseSettings):
    """
    Application settings for PlantBrain backend.
    Loaded from environment variables or .env file.
    """
    
    # AI API Keys
    ANTHROPIC_API_KEY: str = Field(
        ..., 
        description="Anthropic API key for Claude Sonnet 4.6 (Primary LLM)"
    )
    GEMINI_API_KEY: str = Field(
        ..., 
        description="Google Gemini API key for Gemini 2.0 Flash (Fallback LLM)"
    )
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(
        ..., 
        description="Supabase Project URL for database and storage"
    )
    SUPABASE_KEY: str = Field(
        ..., 
        description="Supabase Project API Key (anon/service_role)"
    )
    
    # App Config
    ALLOWED_ORIGINS: str = Field(
        default="http://localhost:3000,https://plantbrain.vercel.app",
        description="Comma-separated list of allowed CORS origins"
    )
    MAX_DOCUMENT_SIZE_MB: int = Field(
        default=10,
        description="Maximum allowed document size for upload in megabytes"
    )
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level for the application (INFO, DEBUG, etc.)"
    )

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )
    
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v: str) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

def get_settings() -> Settings:
    """
    Factory function to instantiate and return the settings.
    Raises clear startup error if required vars are missing.
    """
    try:
        settings = Settings()
        return settings
    except Exception as e:
        # Standard logging might not be fully configured yet, so we use stderr
        print(f"\nCRITICAL STARTUP ERROR: Configuration failed to load.", file=sys.stderr)
        print(f"Missing or invalid required environment variables.", file=sys.stderr)
        print(f"Details: {e}\n", file=sys.stderr)
        sys.exit(1)

# Initialize settings
settings = get_settings()
