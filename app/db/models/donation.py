import uuid
from enum import Enum





from sqlalchemy import Column, UUID, Numeric, String, ForeignKey, DateTime, func, Enum as SQLAEnum, JSON, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.db.index import Base
from app.db.models.base import TimestampMixin


class PaymentMethod(str, Enum):
    MPESA = "MPESA"
    CARD = "CARD"
    PAYPAL = "PAYPAL"
    BANK = "BANK"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"



class Donation(Base):
    __tablename__ = "donations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", backref="donations")

    # user - optional for anonymous
    donor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    donor = relationship("User", backref="donations")

    amount = Column(Numeric(12, 2), nullable=False)

    # optional
    donor_name = Column(String, nullable=True)
    donor_email = Column(String, nullable=True)
    donor_phone = Column(String, nullable=True)
    message = Column(String, nullable=True)

    campaign_id = Column(UUID(as_uuid=True),ForeignKey("campaigns.id"), nullable=False)
    campaign = relationship("Campaign", backref="donations")

    # Payment tracking
    method = Column(SQLAEnum(PaymentMethod), nullable=True)
    status = Column(SQLAEnum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String(100), unique=True, nullable=True)
    callback_data = Column(JSON, nullable=True)

    is_anonymous = Column(Boolean, default=False)

    donated_at = Column(DateTime(timezone=True), server_default=func.now())