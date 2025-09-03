from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, verify_refresh_token, create_refresh_token
from app.core.security import hash_password, verify_password
from app.db.index import get_db
from app.db.models.user import User
from app.schemas.auth import TokenRefreshRequest
from app.schemas.user import UserOut, UserCreate

router = APIRouter()


@router.post('/register', response_model=UserOut)
def register(user: UserCreate, db: Session = Depends(get_db)):
    # check of user exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    try:
        # hash pwd
        hashed_pwd = hash_password(user.password)

        print("hashed pwd: ", hashed_pwd)

        # Create a user instance
        new_user = User(
            full_name=user.full_name,
            email=user.email,
            password=hashed_pwd,
            role=user.role
        )

        # Save to DB
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail='Invalid credentials')

    token_data = {
        "sub": str(user.id),
        "email": user.email,
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


@router.post('/refresh')
def refresh_token(request: TokenRefreshRequest, db: Session = Depends(get_db)):
    payload = verify_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail='Invalid refresh token')
    # user = db.query(User).filter(User.id == payload['sub']).first()
    new_access_token = create_access_token({"sub": payload["sub"]})
    return {"access_token": new_access_token, "token_type": "bearer"}
