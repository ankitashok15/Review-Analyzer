from config.settings import Settings, get_settings


def test_settings_defaults():
    settings = Settings()
    assert settings.gemini_enrichment_model == "gemini-2.0-flash"
    assert settings.vector_dimension == 768
    assert "5434" in settings.database_url


def test_get_settings_cached():
    assert get_settings() is get_settings()
