from typing import Optional

from pydantic import BaseModel


class CheckoutRequest(BaseModel):
    campaign_id: str
    amount: float
    donor_name: Optional[str] = "Anonymous"
    donor_email: Optional[str] = None
    message:Optional[str] = ""
