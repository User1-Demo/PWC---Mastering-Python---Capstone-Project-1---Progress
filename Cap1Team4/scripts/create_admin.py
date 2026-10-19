from getpass import getpass

from sqlalchemy import select

from app.core.exceptions import BusinessRuleError
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.audit_service import log_action


def main() -> None:
    email = input("Administrator email: ").strip().lower()
    full_name = input("Administrator name: ").strip()
    password = getpass("Password (10+ chars, upper/lower/digit): ")
    confirmation = getpass("Confirm password: ")
    if password != confirmation:
        raise ValueError("Passwords do not match")
    payload = UserCreate(
        email=email,
        full_name=full_name,
        password=password,
        role=UserRole.ADMIN,
    )

    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == payload.email.lower())):
            raise BusinessRuleError("An account with this email already exists")
        admin = User(
            email=payload.email.lower(),
            full_name=payload.full_name,
            hashed_password=hash_password(payload.password),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.flush()
        log_action(
            db,
            action="ADMIN_BOOTSTRAPPED",
            entity_type="user",
            entity_id=str(admin.id),
            new={"email": admin.email, "role": UserRole.ADMIN.value},
        )
        db.commit()
    print(f"Administrator account created for {payload.email}.")


if __name__ == "__main__":
    main()
