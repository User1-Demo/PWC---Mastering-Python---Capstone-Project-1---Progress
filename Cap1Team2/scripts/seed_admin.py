from getpass import getpass

from sqlalchemy import select

from claimiq.core.security import hash_password
from claimiq.db.database import SessionLocal
from claimiq.models.user import User, UserRole


def seed_admin() -> None:
    email = input("Admin email: ").strip().lower()
    full_name = input("Admin full name: ").strip()
    password = getpass("Admin password: ")
    confirm_password = getpass("Confirm password: ")

    if not email:
        raise ValueError("Email is required")

    if not full_name:
        raise ValueError("Full name is required")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")

    if password != confirm_password:
        raise ValueError("Passwords do not match")

    with SessionLocal() as db:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user is not None:
            raise ValueError(
                f"A user with email {email} already exists"
            )

        admin = User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"Admin user created successfully: {admin.email}")


if __name__ == "__main__":
    seed_admin()