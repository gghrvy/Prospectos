from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./prospectos_dev.db"
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Optional: free-tier (no credit card) fallback business-search provider
    # used automatically when OpenStreetMap's Overpass API is unavailable.
    # Get a key at https://www.geoapify.com (~3000 free requests/day).
    # Discovery works fine without this — OSM is tried first either way.
    geoapify_api_key: str | None = None

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
