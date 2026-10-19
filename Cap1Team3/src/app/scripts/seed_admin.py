from sqlalchemy import select

from src.app.core.security import hash_password
from src.app.db.models import User, UserRole
from src.app.db.session import SessionLocal


def seed_admin():
    db = SessionLocal()

    existing = db.scalar(
        select(User).where(User.email == "admin@claimiq.com")
    )

    if existing:
        print("Admin already exists")
        db.close()
        return

    raw_password = "Admin@123"

    admin = User(
        full_name="System Admin",
        email="admin@claimiq.com",
        hashed_password=hash_password(raw_password),
        role=UserRole.ADMIN,
        region=None,
        is_active=True,
    )

    db.add(admin)
    db.commit()
    db.close()

    print("Admin user created")


if __name__ == "__main__":
    seed_admin()