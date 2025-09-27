import enum
import uuid

from sqlalchemy import Column, String, Text, Boolean, ForeignKey, UniqueConstraint, Enum
from sqlalchemy.dialects.postgresql.base import UUID
from sqlalchemy.orm import relationship

from app.db.index import Base
from app.db.model_base import TimestampMixin


class DocumentVerificationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    logo_url = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    email = Column(String, nullable=True)
    location = Column(String, nullable=True)
    is_email_verified = Column(Boolean, default=False)
    document_verification_status = Column(
        Enum(DocumentVerificationStatus),
        default=DocumentVerificationStatus.PENDING,
        nullable=False,
    )
    document_verification_notes = Column(Text, nullable=True)
    website = Column(String, nullable=True, unique=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    # Link to the admin auth
    admin_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    admin = relationship("User", backref="tenants")

    # Link to MPESA integrations
    mpesa_integrations = relationship("MPESAIntegration", back_populates="tenant", cascade="all, delete-orphan")

    # Link to tenant_support_documents
    support_documents = relationship("TenantSupportDocuments", back_populates="tenant", cascade="all, delete-orphan")


class TenantSupportDocuments(Base, TimestampMixin):
    __tablename__ = "tenant_support_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    document_name = Column(String, nullable=False)
    document_base_id = Column(String, nullable=False)
    document_url = Column(String, nullable=False, unique=True)
    document_type = Column(String, nullable=False)
    is_verified = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Relationship with tenant
    tenant = relationship("Tenant", back_populates="support_documents")

    __table_args__ = (
        UniqueConstraint("tenant_id", "document_base_id", name="uix_tenant_doc_base"),
    )
