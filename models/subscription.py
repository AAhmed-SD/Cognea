"""
Subscription and payment models for Stripe integration.
"""

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SubscriptionStatus(str, Enum):
    """Subscription status enum."""

    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAUSED = "paused"


class PaymentStatus(str, Enum):
    """Payment status enum."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PENDING = "pending"
    CANCELED = "canceled"


class PlanType(str, Enum):
    """Plan type enum."""

    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class Subscription(BaseModel):
    """Subscription model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    stripe_subscription_id: str
    stripe_customer_id: str
    status: SubscriptionStatus
    plan_type: PlanType
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class Payment(BaseModel):
    """Payment model."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    stripe_invoice_id: str
    stripe_payment_intent_id: str | None = None
    amount: float
    currency: str = "usd"
    status: PaymentStatus
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class PaymentEvent(BaseModel):
    """Payment event model for logging."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    event_type: str
    event_data: dict[str, Any]
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BillingHistory(BaseModel):
    """Billing history response model."""

    invoices: list[dict[str, Any]]
    total_count: int
    has_more: bool


class SubscriptionCreate(BaseModel):
    """Create subscription request model."""

    price_id: str
    success_url: str
    cancel_url: str


class SubscriptionUpdate(BaseModel):
    """Update subscription request model."""

    cancel_at_period_end: bool | None = None
    plan_type: PlanType | None = None


class PricingPlan(BaseModel):
    """Pricing plan model."""

    id: str
    name: str
    price_id: str
    price: float
    currency: str = "usd"
    billing_cycle: str = "monthly"
    features: list[str]
    is_popular: bool = False
    is_enterprise: bool = False
