from app.database.config import get_settings


def test_settings_reads_database_url_from_env(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://u:p@host:5432/db")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.database_url == "postgresql+psycopg2://u:p@host:5432/db"
    assert settings.cors_origins_list == [
        "http://localhost:3000",
        "http://localhost:3001",
    ]
