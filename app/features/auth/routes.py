from email_validator import validate_email, EmailNotValidError
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.common.auth import check_password_match, create_access_token, create_refresh_token, verify_refresh_token
from app.common.handle_error import handle_error
from app.db.index import get_db
from app.features.auth.models import User
from app.features.auth.schemas import TokenRefreshRequest, UserCreate, UserOut
from app.features.auth.services import find_user_by_email, create_new_user

router = APIRouter()


# Register
@router.post('/register', response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    new_user = create_new_user(db, user.model_dump())
    return new_user


# Login
@router.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        emailInfo = validate_email(form_data.username, check_deliverability=False)
        email = emailInfo.normalized
        user = find_user_by_email(db, email=email)
        if not user:
            handle_error(401, "Invalid credentials. Please check your email and password.")
        if not check_password_match(form_data.password, user.password):
            handle_error(401, "Invalid credentials. Please check your email and password.")

        token_data = {
            "sub": str(user.id),
            "role": user.role
        }
        access_token = create_access_token(token_data)
        refreshToken = create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refreshToken,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "full_name": user.full_name
            }
        }
    except EmailNotValidError as e:
        handle_error(400, "Invalid email address. Please try again.")


# Refresh Token
@router.post('/refresh')
def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        handle_error(401, "Invalid refresh token. Please login again.")

    user = find_user_by_email(db, payload["sub"])
    if not user:
        handle_error(401, "Invalid refresh token. Please login again.")
    new_access_token = create_access_token({"sub": payload["sub"]})
    return {
        "access_token": new_access_token,
        "token_type": "bearer",
    }


# SEND RESET EMAIL
@router.post("/reset-request-otp")
def reset_request_otp(email: EmailStr, db: Session = Depends(get_db)):
    user = find_user_by_email(db, email)
