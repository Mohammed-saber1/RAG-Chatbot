"""Application configuration via environment variables."""

import logging
import os
import secrets

from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


def _resolve_api_key() -> str:
    """Resolve the Mistral API key using a multi-tiered strategy.

    Resolution order:
    1. Environment variable MISTRAL_API_KEY
    2. Local file mistral_api_key.txt
    3. Fail with a clear error (no hardcoded fallback)
    """
    # 1. Environment variable
    env_key = os.getenv("MISTRAL_API_KEY")
    if env_key and env_key != "your_mistral_api_key_here":
        return env_key

    # 2. Local file
    key_file = os.path.join(os.path.dirname(__file__), "..", "mistral_api_key.txt")
    if os.path.exists(key_file):
        with open(key_file, "r") as f:
            file_key = f.read().strip()
        if file_key:
            return file_key

    # 3. No key available — raise clear error
    raise ValueError(
        "MISTRAL_API_KEY is not configured. "
        "Set the MISTRAL_API_KEY environment variable or create a "
        "backend/mistral_api_key.txt file containing your API key."
    )


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    # Mistral AI Configuration
    mistral_api_key: str = ""
    mistral_model: str = "mistral-large-latest"

    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000

    # CORS
    allowed_origins: str = "http://localhost:5173"

    # Storage Paths
    upload_dir: str = "uploads"
    chroma_persist_dir: str = "chroma_db"

    # Upload Limits
    max_file_size_mb: int = 10

    # RAG Configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    similarity_threshold: float = 0.3

    # Embedding Model (local, no API key needed)
    embedding_model: str = "all-MiniLM-L6-v2"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_allowed_origins_list(self) -> list[str]:
        """Parse comma-separated allowed origins into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    def resolve_mistral_key(self) -> str:
        """Get the resolved Mistral API key."""
        if self.mistral_api_key and self.mistral_api_key != "your_mistral_api_key_here":
            return self.mistral_api_key
        return _resolve_api_key()


def get_settings() -> Settings:
    """Create and return settings instance."""
    return Settings()
