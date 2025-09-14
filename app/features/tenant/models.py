import uuid

from sqlalchemy import Column, String, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.index import Base
from app.db.models.base import TimestampMixin


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    location = Column(String, nullable=True)
    is_Verified = Column(Boolean, default=False)
    website = Column(String, nullable=True, unique=True)

    # Link to the admin auth
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    admin = relationship("User", backref="tenants")

    # Link to MPESA integrations
    mpesa_integrations = relationship("MPESAIntegration", back_populates="tenant", cascade="all, delete-orphan")
