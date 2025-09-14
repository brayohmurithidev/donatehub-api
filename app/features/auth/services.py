from uuid import UUID

from sqlalchemy.orm import Session

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
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

# Signup

# Reset password
