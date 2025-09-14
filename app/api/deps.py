from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.auth import decode_access_token
from app.db.index import get_db
from app.features.auth.models import User
from app.features.tenant.models import Tenant

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> type[User]:
    payload = decode_access_token(token)
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid auth")
    return user


# CHECK ROLES
def require_tenant_admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> tuple[
    User, type[Tenant]]:
    if user.role != "tenant_admin":
        raise HTTPException(status_code=403, detail="Only tenant_admins can perform this action")

    tenant = db.query(Tenant).filter(Tenant.admin_id == user.id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="No tenant found for this tenant_admin")
    return user, tenant


# REQUIRE PLATFORM ADMIN
def require_platform_admin(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
    if user.role != "platform_admin":
        raise HTTPException(status_code=403, detail="Only platform_admins can perform this action")

    return user
