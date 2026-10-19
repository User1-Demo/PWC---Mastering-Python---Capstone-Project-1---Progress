from claimiq.core.settings import get_settings


def test_default_settings() -> None:
    settings = get_settings()

    assert settings.app_name == "ClaimIQ API"
    assert settings.app_version == "0.1.0"
    assert settings.access_token_expire_minutes == 30