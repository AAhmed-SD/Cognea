"""
Tests for Stripe payment and subscription integration.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, UTC

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def mock_stripe():
    """Mock Stripe API calls."""
    with patch("routes.stripe.stripe") as mock_stripe:
        yield mock_stripe


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    with patch("routes.stripe.get_supabase_client") as mock_supabase:
        yield mock_supabase


@pytest.fixture
def mock_stripe_queue():
    """Mock Stripe rate-limited queue."""
    with patch("routes.stripe.stripe_queue") as mock_queue:
        mock_queue.safe_call = AsyncMock()
        yield mock_queue


class TestStripePricing:
    """Test pricing plans endpoint."""
    
    def test_get_pricing_plans(self):
        """Test getting available pricing plans."""
        response = client.get("/api/stripe/pricing")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "plans" in data
        assert "currency" in data
        assert "billing_cycle" in data
        
        plans = data["plans"]
        assert "basic" in plans
        assert "pro" in plans
        assert "enterprise" in plans
        
        # Check plan structure
        for plan in plans.values():
            assert "name" in plan
            assert "price_id" in plan
            assert "price" in plan
            assert "features" in plan


class TestStripeCheckout:
    """Test checkout session creation."""
    
    @patch("routes.stripe.get_current_user")
    def test_create_checkout_session_success(self, mock_get_user, mock_stripe_queue, mock_supabase):
        """Test successful checkout session creation."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        # Mock checkout session
        mock_session = Mock()
        mock_session.id = "cs_test_123"
        mock_session.url = "https://checkout.stripe.com/test"
        mock_session.amount_total = 1999
        mock_stripe_queue.safe_call.return_value = mock_session
        
        # Mock Supabase
        mock_supabase_instance = Mock()
        mock_supabase.return_value = mock_supabase_instance
        
        response = client.post(
            "/api/stripe/create-checkout-session",
            json={
                "price_id": "price_pro_monthly",
                "success_url": "https://cognie.app/success",
                "cancel_url": "https://cognie.app/cancel"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert "checkout_url" in data
        assert "status" in data
        assert data["status"] == "created"
    
    @patch("routes.stripe.get_current_user")
    def test_create_checkout_session_invalid_price(self, mock_get_user):
        """Test checkout session with invalid price ID."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        response = client.post(
            "/api/stripe/create-checkout-session",
            json={
                "price_id": "invalid_price_id",
                "success_url": "https://cognie.app/success",
                "cancel_url": "https://cognie.app/cancel"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 400
        assert "Invalid price ID" in response.json()["detail"]


class TestStripePortal:
    """Test customer portal session creation."""
    
    @patch("routes.stripe.get_current_user")
    def test_create_portal_session_success(self, mock_get_user, mock_stripe_queue, mock_supabase):
        """Test successful portal session creation."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_get_user.return_value = mock_user
        
        # Mock Supabase response
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"stripe_customer_id": "cus_test_123"}
        ]
        mock_supabase.return_value = mock_supabase_instance
        
        # Mock portal session
        mock_portal = Mock()
        mock_portal.url = "https://billing.stripe.com/test"
        mock_stripe_queue.safe_call.return_value = mock_portal
        
        response = client.post(
            "/api/stripe/create-portal-session",
            json={"return_url": "https://cognie.app/billing"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "portal_url" in data
        assert "status" in data
        assert data["status"] == "created"
    
    @patch("routes.stripe.get_current_user")
    def test_create_portal_session_no_subscription(self, mock_get_user, mock_supabase):
        """Test portal session when user has no subscription."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_get_user.return_value = mock_user
        
        # Mock Supabase response - no subscription
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.return_value = mock_supabase_instance
        
        response = client.post(
            "/api/stripe/create-portal-session",
            json={"return_url": "https://cognie.app/billing"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 404
        assert "No subscription found" in response.json()["detail"]


class TestStripeSubscriptionStatus:
    """Test subscription status endpoint."""
    
    @patch("routes.stripe.get_current_user")
    def test_get_subscription_status_active(self, mock_get_user, mock_stripe_queue, mock_supabase):
        """Test getting active subscription status."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_get_user.return_value = mock_user
        
        # Mock Supabase response
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "stripe_customer_id": "cus_test_123",
                "stripe_subscription_id": "sub_test_123",
                "subscription_status": "active",
                "subscription_plan": "pro"
            }
        ]
        mock_supabase.return_value = mock_supabase_instance
        
        # Mock Stripe subscription
        mock_subscription = Mock()
        mock_subscription.id = "sub_test_123"
        mock_subscription.status = "active"
        mock_subscription.current_period_end = int(datetime.now(UTC).timestamp()) + 86400
        mock_subscription.cancel_at_period_end = False
        mock_subscription.items.data = [Mock(price=Mock(id="price_pro_monthly"))]
        mock_stripe_queue.safe_call.return_value = mock_subscription
        
        response = client.get(
            "/api/stripe/subscription-status",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "test_user_123"
        assert data["subscription_id"] == "sub_test_123"
        assert data["status"] == "active"
        assert data["cancel_at_period_end"] == False
    
    @patch("routes.stripe.get_current_user")
    def test_get_subscription_status_no_subscription(self, mock_get_user, mock_supabase):
        """Test getting status when user has no subscription."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_get_user.return_value = mock_user
        
        # Mock Supabase response - no subscription
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.return_value = mock_supabase_instance
        
        response = client.get(
            "/api/stripe/subscription-status",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["user_id"] == "test_user_123"
        assert data["status"] == "no_subscription"


class TestStripeWebhook:
    """Test Stripe webhook handling."""
    
    def test_webhook_missing_signature(self):
        """Test webhook without signature header."""
        response = client.post("/api/stripe/webhook", json={})
        
        assert response.status_code == 400
        assert "Missing stripe-signature header" in response.json()["detail"]
    
    @patch("routes.stripe.os.getenv")
    def test_webhook_missing_secret(self, mock_getenv):
        """Test webhook without webhook secret configured."""
        mock_getenv.return_value = None
        
        response = client.post(
            "/api/stripe/webhook",
            json={},
            headers={"stripe-signature": "test_signature"}
        )
        
        assert response.status_code == 500
        assert "Webhook secret not configured" in response.json()["detail"]
    
    @patch("routes.stripe.stripe.Webhook.construct_event")
    @patch("routes.stripe.os.getenv")
    def test_webhook_success(self, mock_getenv, mock_construct_event):
        """Test successful webhook processing."""
        mock_getenv.return_value = "whsec_test_secret"
        
        # Mock webhook event
        mock_event = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test_123",
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                    "metadata": {
                        "user_id": "test_user_123",
                        "plan_type": "pro"
                    }
                }
            }
        }
        mock_construct_event.return_value = mock_event
        
        response = client.post(
            "/api/stripe/webhook",
            json=mock_event,
            headers={"stripe-signature": "test_signature"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "success"


class TestStripeBillingHistory:
    """Test billing history endpoint."""
    
    @patch("routes.stripe.get_current_user")
    def test_get_billing_history_success(self, mock_get_user, mock_stripe_queue, mock_supabase):
        """Test getting billing history."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_get_user.return_value = mock_user
        
        # Mock Supabase response
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {"stripe_customer_id": "cus_test_123"}
        ]
        mock_supabase.return_value = mock_supabase_instance
        
        # Mock Stripe invoices
        mock_invoices = Mock()
        mock_invoice = Mock()
        mock_invoice.id = "in_test_123"
        mock_invoice.amount_paid = 1999
        mock_invoice.currency = "usd"
        mock_invoice.status = "paid"
        mock_invoice.created = int(datetime.now(UTC).timestamp())
        mock_invoice.period_start = int(datetime.now(UTC).timestamp())
        mock_invoice.period_end = int(datetime.now(UTC).timestamp()) + 86400
        mock_invoice.invoice_pdf = "https://invoice.stripe.com/test"
        mock_invoice.hosted_invoice_url = "https://invoice.stripe.com/test"
        mock_invoices.data = [mock_invoice]
        mock_stripe_queue.safe_call.return_value = mock_invoices
        
        response = client.get(
            "/api/stripe/billing-history",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "invoices" in data
        assert len(data["invoices"]) == 1
        
        invoice = data["invoices"][0]
        assert invoice["id"] == "in_test_123"
        assert invoice["amount_paid"] == 19.99
        assert invoice["currency"] == "usd"
        assert invoice["status"] == "paid"
    
    @patch("routes.stripe.get_current_user")
    def test_get_billing_history_no_subscription(self, mock_get_user, mock_supabase):
        """Test getting billing history when user has no subscription."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_get_user.return_value = mock_user
        
        # Mock Supabase response - no subscription
        mock_supabase_instance = Mock()
        mock_supabase_instance.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        mock_supabase.return_value = mock_supabase_instance
        
        response = client.get(
            "/api/stripe/billing-history",
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "invoices" in data
        assert len(data["invoices"]) == 0


class TestStripeErrorHandling:
    """Test Stripe error handling."""
    
    @patch("routes.stripe.get_current_user")
    def test_stripe_api_error(self, mock_get_user, mock_stripe_queue):
        """Test handling of Stripe API errors."""
        # Mock user
        mock_user = Mock()
        mock_user.id = "test_user_123"
        mock_user.email = "test@example.com"
        mock_get_user.return_value = mock_user
        
        # Mock Stripe error
        mock_stripe_queue.safe_call.side_effect = Exception("Stripe API error")
        
        response = client.post(
            "/api/stripe/create-checkout-session",
            json={
                "price_id": "price_pro_monthly",
                "success_url": "https://cognie.app/success",
                "cancel_url": "https://cognie.app/cancel"
            },
            headers={"Authorization": "Bearer test_token"}
        )
        
        assert response.status_code == 500
        assert "Failed to create checkout session" in response.json()["detail"] 