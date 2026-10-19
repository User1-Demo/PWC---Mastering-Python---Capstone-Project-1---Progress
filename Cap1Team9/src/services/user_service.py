from fastapi import HTTPException

from src.models.user import User


def validate_unique_email(email, db):

    existing_user_mail = db.query(User).filter(User.email == email).first()

    if existing_user_mail:
        raise HTTPException(status_code=409, detail="Email already exists")


def validate_unique_username(username, db):

    existing_username = db.query(User).filter(User.username == username).first()

    if existing_username:
        raise HTTPException(status_code=409, detail="Username is taken")


def get_user_by_id(user_id: int, db):

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


def update_user(user_id: int, payload, db):
    user = get_user_by_id(user_id, db)

    if payload.email and payload.email != user.email:

        existing_email = db.query(User).filter(User.email == payload.email).first()

        if existing_email:
            raise HTTPException(status_code=409, detail="Email already exists")

        user.email = payload.email

    if payload.username and payload.username != user.username:

        existing_username = (
            db.query(User).filter(User.username == payload.username).first()
        )

        if existing_username:
            raise HTTPException(status_code=409, detail="Username already exists")

        user.username = payload.username

    if payload.role:
        user.role = payload.role

    db.commit()
    db.refresh(user)

    return user


def delete_user(user_id: int, db):

    user = get_user_by_id(user_id, db)
    user.is_active = False
    db.commit()
    db.refresh(user)
    return {"message": "User deactivated successfully"}
