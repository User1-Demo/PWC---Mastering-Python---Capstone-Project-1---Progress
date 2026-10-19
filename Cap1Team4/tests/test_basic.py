import os
import sys
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("DATABASE_URL", "sqlite:///./claims.db")
os.environ.setdefault("SECRET_KEY", "12345678901234567890123456789012")

from app.core.config import Settings
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.main import app


def test_settings_loads_required_values():
    settings = Settings()

    assert settings.APP_NAME == "ClaimIQ"
    assert settings.ENV == "dev"
    assert settings.DATABASE_URL == "sqlite:///./claims.db"
    assert len(settings.SECRET_KEY) >= 32


def test_password_hashing_round_trip():
    password = "P@ssw0rd!"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong-password", hashed) is False


def test_access_token_round_trip():
    user_id = uuid4()
    token = create_access_token(user_id)

    payload = decode_token(token, "access")

    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"
    assert "exp" in payload
    assert "jti" in payload


def test_app_has_expected_routes_and_docs():
    openapi = app.openapi()
    paths = set(openapi.get("paths", {}).keys())

    assert "/docs" in [route.path for route in app.routes if hasattr(route, "path") and route.path == "/docs"]
    assert "/api/v1/users" in paths
    assert app.title == "ClaimIQ"
