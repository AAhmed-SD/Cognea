from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from models.subscription import (
    BillingHistory,
    Payment,
    PaymentEvent,
    PaymentStatus,
    PlanType,
    PricingPlan,
    Subscription,
    SubscriptionCreate,
    SubscriptionStatus,
    SubscriptionUpdate,
)


def test_subscription_status_enum():
    assert SubscriptionStatus.ACTIVE.value == "active"
    assert SubscriptionStatus.CANCELED.value == "canceled"
    assert SubscriptionStatus.TRIALING.value == "trialing"


def test_payment_status_enum():
    assert PaymentStatus.SUCCEEDED.value == "succeeded"
    assert PaymentStatus.FAILED.value == "failed"
    assert PaymentStatus.PENDING.value == "pending"


def test_plan_type_enum():
    assert PlanType.BASIC.value == "basic"
    assert PlanType.PRO.value == "pro"
    assert PlanType.ENTERPRISE.value == "enterprise"


def test_subscription_model():
    now = datetime.now(UTC)
    sub = Subscription(
        id="sub_1",
        user_id="user_1",
        stripe_subscription_id="stripe_sub_1",
        stripe_customer_id="stripe_cust_1",
        status=SubscriptionStatus.ACTIVE,
        plan_type=PlanType.PRO,
        current_period_start=now,
        current_period_end=now,
        cancel_at_period_end=False,
    )
    assert sub.id == "sub_1"
    assert sub.status == SubscriptionStatus.ACTIVE
    assert sub.plan_type == PlanType.PRO
    assert sub.cancel_at_period_end is False


def test_subscription_model_defaults():
    now = datetime.now(UTC)
    sub = Subscription(
        id="sub_1",
        user_id="user_1",
        stripe_subscription_id="stripe_sub_1",
        stripe_customer_id="stripe_cust_1",
        status=SubscriptionStatus.ACTIVE,
        plan_type=PlanType.BASIC,
        current_period_start=now,
        current_period_end=now,
    )
    assert sub.cancel_at_period_end is False
    assert sub.created_at is not None
    assert sub.updated_at is not None


def test_payment_model():
    now = datetime.now(UTC)
    payment = Payment(
        id="pay_1",
        user_id="user_1",
        stripe_invoice_id="stripe_inv_1",
        stripe_payment_intent_id="stripe_pi_1",
        amount=29.99,
        currency="usd",
        status=PaymentStatus.SUCCEEDED,
        description="Monthly subscription",
    )
    assert payment.id == "pay_1"
    assert payment.amount == 29.99
    assert payment.currency == "usd"
    assert payment.status == PaymentStatus.SUCCEEDED


def test_payment_model_defaults():
    now = datetime.now(UTC)
    payment = Payment(
        id="pay_1",
        user_id="user_1",
        stripe_invoice_id="stripe_inv_1",
        amount=29.99,
        status=PaymentStatus.PENDING,
    )
    assert payment.currency == "usd"
    assert payment.description is None
    assert payment.created_at is not None


def test_payment_event_model():
    now = datetime.now(UTC)
    event = PaymentEvent(
        id="evt_1",
        user_id="user_1",
        event_type="payment.succeeded",
        event_data={"amount": 29.99, "currency": "usd"},
    )
    assert event.id == "evt_1"
    assert event.event_type == "payment.succeeded"
    assert event.event_data["amount"] == 29.99


def test_billing_history_model():
    history = BillingHistory(
        invoices=[{"id": "inv_1", "amount": 29.99}], total_count=1, has_more=False
    )
    assert len(history.invoices) == 1
    assert history.total_count == 1
    assert history.has_more is False


def test_subscription_create_model():
    create = SubscriptionCreate(
        price_id="price_1",
        success_url="https://success.com",
        cancel_url="https://cancel.com",
    )
    assert create.price_id == "price_1"
    assert create.success_url == "https://success.com"


def test_subscription_update_model():
    update = SubscriptionUpdate(
        cancel_at_period_end=True, plan_type=PlanType.ENTERPRISE
    )
    assert update.cancel_at_period_end is True
    assert update.plan_type == PlanType.ENTERPRISE


def test_subscription_update_model_partial():
    update = SubscriptionUpdate(cancel_at_period_end=True)
    assert update.cancel_at_period_end is True
    assert update.plan_type is None


def test_pricing_plan_model():
    plan = PricingPlan(
        id="plan_1",
        name="Pro Plan",
        price_id="price_pro",
        price=29.99,
        currency="usd",
        billing_cycle="monthly",
        features=["feature1", "feature2"],
        is_popular=True,
        is_enterprise=False,
    )
    assert plan.id == "plan_1"
    assert plan.name == "Pro Plan"
    assert plan.price == 29.99
    assert plan.is_popular is True


def test_pricing_plan_model_defaults():
    plan = PricingPlan(
        id="plan_1",
        name="Basic Plan",
        price_id="price_basic",
        price=9.99,
        features=["feature1"],
    )
    assert plan.currency == "usd"
    assert plan.billing_cycle == "monthly"
    assert plan.is_popular is False
    assert plan.is_enterprise is False


def test_model_config_from_attributes():
    # Test that models can be created from ORM objects
    class MockORM:
        def __init__(self):
            self.id = "test_id"
            self.user_id = "user_1"
            self.stripe_subscription_id = "stripe_sub_1"
            self.stripe_customer_id = "stripe_cust_1"
            self.status = SubscriptionStatus.ACTIVE
            self.plan_type = PlanType.BASIC
            self.current_period_start = datetime.now(UTC)
            self.current_period_end = datetime.now(UTC)
            self.cancel_at_period_end = False
            self.created_at = datetime.now(UTC)
            self.updated_at = datetime.now(UTC)

    mock_orm = MockORM()
    sub = Subscription.model_validate(mock_orm)
    assert sub.id == "test_id"
    assert sub.status == SubscriptionStatus.ACTIVE


def test_enum_validation():
    # Test that invalid enum values raise validation errors
    with pytest.raises(ValidationError):
        Subscription(
            id="sub_1",
            user_id="user_1",
            stripe_subscription_id="stripe_sub_1",
            stripe_customer_id="stripe_cust_1",
            status="invalid_status",  # Invalid enum value
            plan_type=PlanType.BASIC,
            current_period_start=datetime.now(UTC),
            current_period_end=datetime.now(UTC),
        )


def test_required_fields():
    # Test that required fields are enforced
    with pytest.raises(ValidationError):
        Subscription(
            # Missing required fields
            id="sub_1",
            user_id="user_1",
        )


def test_field_types():
    # Test field type validation
    with pytest.raises(ValidationError):
        Payment(
            id="pay_1",
            user_id="user_1",
            stripe_invoice_id="stripe_inv_1",
            amount="not_a_number",  # Should be float
            status=PaymentStatus.SUCCEEDED,
        )
