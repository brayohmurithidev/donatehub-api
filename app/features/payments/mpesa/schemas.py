from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class EnvironmentType(str, Enum):
    sandbox = "sandbox"
    production = "production"


class MPESAIntegrationCreate(BaseModel):
    name: str | None = None
    shortcode: str
    consumer_key: str
    consumer_secret: str
    passkey: str
    callback_url: HttpUrl
    account_reference: str
    environment: EnvironmentType
    is_active: bool = False


class MpesaIntegrationTestCreate(BaseModel):
    phone: str
    amount: float = 1.00


class IntegrationBase(BaseModel):
    name: str | None = None
    shortcode: str
    consumer_key: str
    consumer_secret: str
    passkey: str
    callback_url: HttpUrl
    account_reference: str = "NGO"
    environment: EnvironmentType
    is_active: bool = False
    is_verified: bool = False


class PaymentSTK(BaseModel):
    phone_number: str
    amount: float
    integration: IntegrationBase


class MpesaIntegrationUpdate(BaseModel):
    name: Optional[str] = None
    shortcode: Optional[str] = None
    consumer_key: Optional[str] = None
    consumer_secret: Optional[str] = None
    passkey: Optional[str] = None
    callback_url: Optional[HttpUrl] = None
    account_reference: Optional[str] = None
    environment: Optional[EnvironmentType] = None
    is_active: Optional[bool] = None


class MPESAIntegrationOut(BaseModel):
    consumer_key: str
    consumer_secret: str
    shortcode: str
    passkey: str
    callback_url: str
    environment: str
    is_active: bool
    name: str | None = None
    account_reference: str = "NGO",
    is_verified: bool = False
    id: UUID
    tenant_id: UUID
    created_at: datetime
    updated_at: datetime

