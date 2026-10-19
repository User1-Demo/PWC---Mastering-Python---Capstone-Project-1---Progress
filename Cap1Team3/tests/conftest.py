import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.app.main import app
from src.app.core.security import hash_password
from src.app.db.models import User, UserRole
from src.app.db.session import get_db

TEST_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:5432/claimiq"

engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


@pytest.fixture()
def seeded_users(db):
    users = {}

    admin = db.query(User).filter(User.email == "nisarga@claimiq.com").first()
    if not admin:
        admin = User(
            full_name="Nisarga",
            email="nisarga@claimiq.com",
            hashed_password=hash_password("Admin@123"),
            role=UserRole.ADMIN,
            region=None,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    users["admin"] = {"id": admin.id, "email": admin.email, "password": "Admin@123"}

    manager = db.query(User).filter(User.email == "rohit.manager@claimiq.com").first()
    if not manager:
        manager = User(
            full_name="Rohit Manager",
            email="rohit.manager@claimiq.com",
            hashed_password=hash_password("Manager@123"),
            role=UserRole.CLAIMS_MANAGER,
            region="North",
            is_active=True,
        )
        db.add(manager)
        db.commit()
        db.refresh(manager)
    users["manager"] = {"id": manager.id, "email": manager.email, "password": "Manager@123"}

    adjuster = db.query(User).filter(User.email == "ananya.adjuster@claimiq.com").first()
    if not adjuster:
        adjuster = User(
            full_name="Ananya Adjuster",
            email="ananya.adjuster@claimiq.com",
            hashed_password=hash_password("Adjuster@123"),
            role=UserRole.CLAIMS_ADJUSTER,
            region="North",
            is_active=True,
        )
        db.add(adjuster)
        db.commit()
        db.refresh(adjuster)
    users["adjuster"] = {"id": adjuster.id, "email": adjuster.email, "password": "Adjuster@123"}

    support = db.query(User).filter(User.email == "megha.support@claimiq.com").first()
    if not support:
        support = User(
            full_name="Megha Support",
            email="megha.support@claimiq.com",
            hashed_password=hash_password("Support@123"),
            role=UserRole.SUPPORT_AGENT,
            region="North",
            is_active=True,
        )
        db.add(support)
        db.commit()
        db.refresh(support)
    users["support"] = {"id": support.id, "email": support.email, "password": "Support@123"}

    return users


def login(client, email, password):
    return client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def admin_headers(client, seeded_users):
    response = login(client, seeded_users["admin"]["email"], seeded_users["admin"]["password"])
    token = response.json()["access_token"]
    return bearer(token)


@pytest.fixture()
def manager_headers(client, seeded_users):
    response = login(client, seeded_users["manager"]["email"], seeded_users["manager"]["password"])
    token = response.json()["access_token"]
    return bearer(token)


@pytest.fixture()
def adjuster_headers(client, seeded_users):
    response = login(client, seeded_users["adjuster"]["email"], seeded_users["adjuster"]["password"])
    token = response.json()["access_token"]
    return bearer(token)


@pytest.fixture()
def support_headers(client, seeded_users):
    response = login(client, seeded_users["support"]["email"], seeded_users["support"]["password"])
    token = response.json()["access_token"]
    return bearer(token)