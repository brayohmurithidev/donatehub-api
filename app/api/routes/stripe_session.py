import stripe
from fastapi import APIRouter, Query, HTTPException

router = APIRouter()


@router.get("/session")
def get_checkout_session(session_id: str = Query(..., alias="session_id")):
    try:
        session = stripe.checkout.Session.retrieve(session_id)

        return {
            "amount_total": session["amount_total"],
            "currency": session["currency"],
            "customer_email": session.get("customer_email"),
            "metadata": session.get("metadata", {}),
        }
    except stripe.error.InvalidRequestError as e:
        raise HTTPException(status_code=400, detail="Invalid session ID")
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error fetching session details")