from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # CORS origins (comma-separated string in .env)
    CORS_ORIGINS: str = ""

    # JWT
    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7

    # App
    ENVIRONMENT: str = "production"
    DEBUG: bool = False

    # Database & Auth
    DATABASE_URL: str = ""  # Required - must be set in environment
    VITE_NEON_AUTH_URL: str = ""
    BETTER_AUTH_SECRET: str = ""

    # OpenAI
    OPENAI_API_KEY: str = ""  # Required for AI chatbot features
    OPENAI_MODEL: str = "gpt-4o-mini"  # Default model (cost-effective)

    # Groq (Free alternative - OpenAI compatible)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "DATABASE_URL environment variable is required. "
                "Please set it in Vercel project settings or .env file."
            )
        return v

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert comma-separated CORS_ORIGINS string to list."""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# Instantiate a global settings object
settings = Settings()
