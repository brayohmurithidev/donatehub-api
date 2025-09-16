from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.auth import hash_password
from app.common.handle_error import handle_error
from app.features.auth.models import User


# Find the user by email ->
def find_user_by_email(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    return user


# Find user by id ->
def find_user_by_id(db: Session, id: UUID):
    user = db.query(User).filter(User.id == id).first()
    return user


# create user
def create_new_user(db: Session, data):
    password = data.pop("password")
    hashed_pass = hash_password(password)
    data["password"] = hashed_pass
    try:
        user = User(**data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError as e:
        db.rollback()

        if "ix_user_email" in str(e.orig):
            handle_error(400, "This user is already linked with another Organization")
        else:
            handle_error(500, "An error occurred while creating the user. Please try again later", e)

    except Exception as e:
        db.rollback()
        handle_error(500, "Unexpected error occurred while creating the user", e)

# Signup

# Reset password
