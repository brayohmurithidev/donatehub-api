import uuid

from sqlalchemy import UUID, Column, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.models.base import TimestampMixin
from app.db.index import Base


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    goal_amount = Column(Numeric(12, 2), nullable=False)
    current_amount = Column(Numeric(12, 2), default=0)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    image_url = Column(String, nullable=True)

    # Join with tenant
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    tenant = relationship("Tenant", backref="campaigns")
