import enum
import uuid

from sqlalchemy import UUID, Column, String, Boolean, Enum as SQLAEnum, ForeignKey
from sqlalchemy.orm import relationship

from app.db.index import Base
from app.db.models.base import TimestampMixin


# Define the environment Enum
class EnvironmentType(str, enum.Enum):
    sandbox = "sandbox"
    production = "production"


class MPESAIntegration(Base, TimestampMixin):
    __tablename__ = "mpesa_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False, index=True)
    tenant = relationship("Tenant", back_populates="mpesa_integrations")
    name = Column(String, nullable=True)  # use lowercase "name" for consistency
    shortcode = Column(String, nullable=False)
    consumer_key = Column(String, nullable=False)
    consumer_secret = Column(String, nullable=False)
    passkey = Column(String, nullable=False)
    callback_url = Column(String, nullable=False)
    account_reference = Column(String, nullable=False, default="NGO")
    environment = Column(SQLAEnum(EnvironmentType), nullable=False, default=EnvironmentType.sandbox)
    is_active = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, default=False)
