"""Stripe service for payment processing and subscription management."""

import logging
import os
from datetime import datetime
from typing import Any

import stripe

from services.redis_client import get_redis_client
from services.supabase import get_supabase_client

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StripeService:
    """Service class for Stripe operations."""

    def __init__(self):
        pass
        self.supabase = get_supabase_client()
        self.redis_client = get_redis_client()

    async def create_checkout_session(self, user_id: str) -> stripe.checkout.Session:
        """Create a Stripe checkout session for subscription."""
        try:
            # Get user data
            user_result = (
                self.supabase.table("users").select("email").eq("id", user_id).execute()
            )
            if not user_result.data:
                raise Exception("User not found")

            user_email = user_result.data[0].get("email")

            # Get default price ID (Pro plan)
            price_id = os.getenv("STRIPE_PRO_PRICE_ID")
            if not price_id:
                raise Exception("STRIPE_PRO_PRICE_ID not configured")

            # Create checkout session
            session = await self.redis_client.safe_call(
                "stripe",
                stripe.checkout.Session.create,
                customer_email=user_email,
                line_items=[{"price": price_id, "quantity": 1}],
                mode="subscription",
                success_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/billing?success=true",
                cancel_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/billing?canceled=true",
                metadata={"user_id": user_id},
                allow_promotion_codes=True,
            )

            logger.info(f"Created checkout session for user {user_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create checkout session: {str(e)}")
            raise

    async def create_portal_session(
        self, user_id: str
    ) -> stripe.billing_portal.Session:
        """Create a Stripe customer portal session."""
        try:
            # Get user's Stripe customer ID
            user_result = (
                self.supabase.table("users")
                .select("stripe_customer_id")
                .eq("id", user_id)
                .execute()
            )
            if not user_result.data or not user_result.data[0].get(
                "stripe_customer_id"
            ):
                raise Exception("User has no Stripe customer ID")

            customer_id = user_result.data[0]["stripe_customer_id"]

            # Create portal session
            session = await self.redis_client.safe_call(
                "stripe",
                stripe.billing_portal.Session.create,
                customer=customer_id,
                return_url=f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/billing",
            )

            logger.info(f"Created portal session for user {user_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to create portal session: {str(e)}")
            raise

    async def get_subscription_status(self, user_id: str) -> dict[str, Any]:
        """Get current user's subscription status."""
        try:
            # Get user's subscription data
            user_result = (
                self.supabase.table("users")
                .select("subscription_status, stripe_customer_id, subscription_id")
                .eq("id", user_id)
                .execute()
            )

            if not user_result.data:
                raise Exception("User not found")

            user_data = user_result.data[0]
            subscription_status = user_data.get("subscription_status", "inactive")
            stripe_customer_id = user_data.get("stripe_customer_id")
            subscription_id = user_data.get("subscription_id")

            # Get subscription details from Stripe if available
            subscription_details = None
            if subscription_id:
                try:
                    subscription = await self.redis_client.safe_call(
                        "stripe", stripe.Subscription.retrieve, subscription_id
                    )
                    subscription_details = {
                        "id": subscription.id,
                        "status": subscription.status,
                        "current_period_end": datetime.fromtimestamp(
                            subscription.current_period_end
                        ).isoformat(),
                        "cancel_at_period_end": subscription.cancel_at_period_end,
                    }
                except Exception as e:
                    logger.warning(
                        f"Failed to retrieve subscription {subscription_id}: {str(e)}"
                    )

            return {
                "status": subscription_status,
                "stripe_customer_id": stripe_customer_id,
                "subscription_id": subscription_id,
                "subscription_details": subscription_details,
            }

        except Exception as e:
            logger.error(f"Failed to get subscription status: {str(e)}")
            raise

    def verify_webhook(self, payload: bytes, sig_header: str) -> stripe.Event:
        """Verify Stripe webhook signature."""
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
            logger.info(f"Verified webhook event: {event.type}")
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            raise
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise

    async def process_webhook_event(self, event: stripe.Event):
        pass
        """Process Stripe webhook events."""
        try:
            event_type = event.type

            if event_type == "checkout.session.completed":
                await self._handle_checkout_completed(event.data.object)
            elif event_type == "customer.subscription.created":
                await self._handle_subscription_created(event.data.object)
            elif event_type == "customer.subscription.updated":
                await self._handle_subscription_updated(event.data.object)
            elif event_type == "customer.subscription.deleted":
                await self._handle_subscription_deleted(event.data.object)
            elif event_type == "invoice.payment_succeeded":
                await self._handle_payment_succeeded(event.data.object)
            elif event_type == "invoice.payment_failed":
                await self._handle_payment_failed(event.data.object)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")

        except Exception as e:
            logger.error(f"Failed to process webhook event {event.type}: {str(e)}")
            raise

    async def _handle_checkout_completed(self, session: stripe.checkout.Session):
        pass
        """Handle checkout session completion."""
        try:
            user_id = session.metadata.get("user_id")
            customer_id = session.customer

            if not user_id or not customer_id:
                logger.error("Missing user_id or customer_id in checkout session")
                return

            # Update user with Stripe customer ID
            self.supabase.table("users").update(
                {
                    "stripe_customer_id": customer_id,
                    "subscription_status": "active",
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", user_id).execute()

            logger.info(f"Updated user {user_id} with customer ID {customer_id}")

        except Exception as e:
            logger.error(f"Failed to handle checkout completed: {str(e)}")
            raise

    async def _handle_subscription_created(self, subscription: stripe.Subscription):
        pass
        """Handle subscription creation."""
        try:
            customer_id = subscription.customer

            # Find user by customer ID
            user_result = (
                self.supabase.table("users")
                .select("id")
                .eq("stripe_customer_id", customer_id)
                .execute()
            )
            if not user_result.data:
                logger.error(f"No user found for customer {customer_id}")
                return

            user_id = user_result.data[0]["id"]

            # Update user subscription
            self.supabase.table("users").update(
                {
                    "subscription_id": subscription.id,
                    "subscription_status": subscription.status,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("id", user_id).execute()

            logger.info(f"Updated subscription for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to handle subscription created: {str(e)}")
            raise

    async def _handle_subscription_updated(self, subscription: stripe.Subscription):
        pass
        """Handle subscription updates."""
        try:
            # Update subscription status
            self.supabase.table("users").update(
                {
                    "subscription_status": subscription.status,
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("subscription_id", subscription.id).execute()

            logger.info(f"Updated subscription {subscription.id}")

        except Exception as e:
            logger.error(f"Failed to handle subscription updated: {str(e)}")
            raise

    async def _handle_subscription_deleted(self, subscription: stripe.Subscription):
        pass
        """Handle subscription deletion."""
        try:
            # Update subscription status
            self.supabase.table("users").update(
                {
                    "subscription_status": "canceled",
                    "updated_at": datetime.utcnow().isoformat(),
                }
            ).eq("subscription_id", subscription.id).execute()

            logger.info(f"Canceled subscription {subscription.id}")

        except Exception as e:
            logger.error(f"Failed to handle subscription deleted: {str(e)}")
            raise

    async def _handle_payment_succeeded(self, invoice: stripe.Invoice):
        pass
        """Handle successful payment."""
        try:
            subscription_id = invoice.subscription
            if subscription_id:
                self.supabase.table("users").update(
                    {
                        "subscription_status": "active",
                        "last_payment_date": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).eq("subscription_id", subscription_id).execute()

                logger.info(f"Payment succeeded for subscription {subscription_id}")

        except Exception as e:
            logger.error(f"Failed to handle payment succeeded: {str(e)}")
            raise

    async def _handle_payment_failed(self, invoice: stripe.Invoice):
        pass
        """Handle failed payment."""
        try:
            subscription_id = invoice.subscription
            if subscription_id:
                self.supabase.table("users").update(
                    {
                        "subscription_status": "past_due",
                        "updated_at": datetime.utcnow().isoformat(),
                    }
                ).eq("subscription_id", subscription_id).execute()

                logger.info(f"Payment failed for subscription {subscription_id}")

        except Exception as e:
            logger.error(f"Failed to handle payment failed: {str(e)}")
            raise


# Create singleton instance
stripe_service = StripeService()
