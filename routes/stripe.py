"""Stripe payment and subscription management routes."""

from fastapi import APIRouter, HTTPException, Depends, Request
from services.stripe_service import stripe_service
from services.supabase import get_supabase_client
from services.auth import get_current_user
import logging

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")
        
        if not sig_header:
            raise HTTPException(status_code=400, detail="Missing signature")
            
        # Verify webhook signature
        event = stripe_service.verify_webhook(payload, sig_header)
        
        # Process the event
        await stripe_service.process_webhook_event(event)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail="Webhook error")


@router.post("/create-checkout-session")
async def create_checkout_session(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Create a Stripe checkout session for subscription."""
    try:
        session = await stripe_service.create_checkout_session(current_user["id"])
        return {"session_id": session.id, "url": session.url}
    except Exception as e:
        logger.error(f"Checkout session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@router.post("/create-portal-session")
async def create_portal_session(
    request: Request, current_user: dict = Depends(get_current_user)
):
    """Create a Stripe customer portal session."""
    try:
        session = await stripe_service.create_portal_session(current_user["id"])
        return {"url": session.url}
    except Exception as e:
        logger.error(f"Portal session error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create portal session")


@router.get("/subscription-status")
async def get_subscription_status(
    current_user: dict = Depends(get_current_user)
):
    """Get current user's subscription status."""
    try:
        status = await stripe_service.get_subscription_status(current_user["id"])
        return status
    except Exception as e:
        logger.error(f"Subscription status error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")
