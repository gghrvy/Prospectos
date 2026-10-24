from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./prospectos_dev.db"
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"
    # This is enforced by the API, not merely reflected by the frontend.  A
    # demo deployment never reads from or writes to the live prospect store,
    # crawls a visitor-supplied URL, or reaches an external integration.
    # Production defaults to safe demo mode; DEMO_MODE=false is an explicit
    # opt-in for a deliberately provisioned live deployment.
    demo_mode: bool | None = None
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"

    # Optional: free-tier (no credit card) fallback business-search provider
    # used automatically when OpenStreetMap's Overpass API is unavailable.
    # Get a key at https://www.geoapify.com (~3000 free requests/day).
    # Discovery works fine without this — OSM is tried first either way.
    geoapify_api_key: str | None = None
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_oauth_redirect_uri: str = "http://localhost:8000/api/gmail/callback"
    gmail_token_encryption_key: str | None = None
    outreach_daily_send_limit: int = 25
    outreach_hourly_send_limit: int = 5

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_demo_mode(self) -> bool:
        if self.demo_mode is not None:
            return self.demo_mode
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
