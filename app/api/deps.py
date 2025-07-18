from typing import Any

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.auth import decode_access_token
from app.db.models.user import User

from app.db.index import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> type[User]:
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid user")

    return user


# CHECK ROLES
def require_tenant_admin(user:User = Depends(get_current_user)) -> User:
    if user.role != "tenant_admin":
        raise HTTPException(status_code=403, detail="Only tenant_admins can perform this action")
    return user