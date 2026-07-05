from config.settings import Settings, get_settings, normalize_database_url, validate_database_url


def test_settings_defaults():
    settings = Settings(
        _env_file=None,
        database_url="postgresql://postgres:postgres@localhost:5434/review_engine",
    )
    assert settings.gemini_enrichment_model == "gemini-2.0-flash"
    assert settings.vector_dimension == 768
    assert "5434" in settings.database_url


def test_get_settings_cached():
    assert get_settings() is get_settings()


def test_normalize_database_url_strips_quotes():
    url = '"postgresql://user:pass@host.example/db?sslmode=require"'
    assert normalize_database_url(url).startswith("postgresql://user:pass@host.example")


def test_normalize_database_url_converts_postgres_scheme():
    url = "postgres://user:pass@host.example/db"
    assert normalize_database_url(url) == "postgresql://user:pass@host.example/db"


def test_neon_database_url_overrides_database_url():
    settings = Settings(
        database_url="postgresql://wrong:wrong@localhost/wrong",
        neon_database_url="postgresql://neondb_owner:secret@ep-example-pooler.neon.tech/neondb?sslmode=require",
    )
    assert "neon.tech" in settings.database_url


def test_validate_database_url_rejects_unexpanded_reference():
    try:
        validate_database_url("${{Postgres.DATABASE_URL}}")
        raised = False
    except ValueError as exc:
        raised = True
        assert "unexpanded Railway reference" in str(exc)
    assert raised
