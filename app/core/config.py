from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: str = "ollama"
    llm_model: str = "llama3.2"
    embed_model: str = "nomic-embed-text"
    chroma_path: str = "./data/chroma_db"
    max_file_size_mb: int = 10
    chunk_size: int = 500
    chunk_overlap: int = 50


@lru_cache
def get_settings() -> Settings:
    return Settings()
