import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./claims.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-at-least-32-characters-long")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.core.security import hash_password
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import UserRole
from app.models.user import Region, User


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(connection, _record):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
        class_=Session,
    )

    def override_get_db():
        with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with session_factory() as session:
            yield session
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def actors(db_session):
    region = Region(code="TEST", name="Test Region")
    db_session.add(region)
    db_session.flush()
    users = {}
    for role in UserRole:
        user = User(
            email=f"{role.value}@example.com",
            full_name=f"Test {role.value}",
            hashed_password=hash_password("SecurePass123"),
            role=role,
            region_id=region.id,
        )
        db_session.add(user)
        users[role] = user
    db_session.commit()
    return {"region": region, **users}


@pytest.fixture
def client(db_session):
    with TestClient(app) as test_client:
        yield test_client


def login(client: TestClient, user: User) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "SecurePass123"},
    )
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def auth_headers(client, actors):
    return {role: login(client, user) for role, user in actors.items() if isinstance(role, UserRole)}
