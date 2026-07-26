"""Application configuration loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""
    database_url: str = ""

    # Ollama / LLM
    ollama_base_url: str = "http://localhost:11434"
    # Primary: Ollama Cloud (hosted, high quality). Fallback: local Ollama model.
    ollama_cloud_base_url: str = "https://ollama.com/v1"
    ollama_cloud_api_key: str = ""
    ollama_cloud_model: str = "gpt-oss:120b"
    llm_fallback_model: str = "qwen2.5:7b"
    embed_model: str = "bge-m3"
    embed_dim: int = 1024

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "please-change-me"

    # Behaviour
    llm_request_timeout: int = 150
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
