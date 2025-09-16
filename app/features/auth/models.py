import enum
import uuid

from sqlalchemy import Column, String, Enum, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID

from app.db.index import Base
from app.db.model_base import TimestampMixin


# from app.db.models.base import TimestampMixin


class UserRole(str, enum.Enum):
    donor = "donor"
    tenant_admin = "tenant_admin"
    platform_admin = "platform_admin"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True, index=True)
    password = Column(String, nullable=False)
    role = Column(Enum(UserRole), default=UserRole.donor)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
