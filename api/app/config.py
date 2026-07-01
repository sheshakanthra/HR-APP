"""Application configuration.

Loaded once at import time from environment variables (via `.env` in dev).
Fails fast with a clear message if a required secret is missing so the app
never boots half-configured.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_env: str = Field(default="development")
    web_origin: str = Field(default="http://localhost:5173")

    # --- Database ---
    database_url: str = Field(
        default="postgresql+psycopg://peopledesk:change-me-in-real-life@postgres:5432/peopledesk"
    )

    # --- Auth ---
    jwt_secret_key: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=30)
    refresh_token_expire_days: int = Field(default=7)

    # --- Groq (generation only) ---
    groq_api_key: str = Field(default="")
    groq_model: str = Field(default="llama-3.3-70b-versatile")
    groq_model_small: str = Field(default="llama-3.1-8b-instant")

    # --- Embeddings (local, via fastembed) ---
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5")
    embedding_dim: int = Field(default=384)

    # --- Seed ---
    seed_admin_email: str = Field(default="admin@peopledesk.io")
    seed_admin_password: str = Field(default="Admin123!")

    def validate_secrets(self) -> None:
        """Raise a clear error if a required secret is unset or a placeholder.

        Called explicitly at API startup (not at import) so tooling like
        Alembic/seed can import settings without a live Groq key.
        """
        missing: list[str] = []
        if not self.jwt_secret_key or self.jwt_secret_key.startswith("replace"):
            missing.append("JWT_SECRET_KEY")
        if not self.groq_api_key or self.groq_api_key in ("", "gsk_replace_me"):
            missing.append("GROQ_API_KEY")
        if missing:
            raise RuntimeError(
                "Missing/placeholder required environment variables: "
                + ", ".join(missing)
                + ". Copy .env.example to .env and fill in real values."
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
