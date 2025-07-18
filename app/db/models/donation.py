import uuid


from sqlalchemy import Column, UUID, Numeric, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship

from app.db.index import Base
from app.db.models.base import TimestampMixin


class Donation(Base):
    __tablename__ = "donations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    amount = Column(Numeric(12, 2), nullable=False)
    donor_name = Column(String, nullable=True)
    donor_email = Column(String, nullable=True)
    message = Column(String, nullable=True)

    campaign_id = Column(UUID(as_uuid=True),ForeignKey("campaigns.id"), nullable=False)
    campaign = relationship("Campaign", backref="donations")

    donated_at = Column(DateTime(timezone=True), server_default=func.now())