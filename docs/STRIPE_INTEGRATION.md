# Stripe Integration for Cognie

## Overview

This document outlines the complete Stripe payment integration for Cognie, including subscription management, billing, and payment processing.

## 🏗️ Architecture

### Backend Components

1. **Stripe Routes** (`routes/stripe.py`)
   - Checkout session creation
   - Customer portal management
   - Subscription status tracking
   - Webhook handling
   - Billing history

2. **Database Models** (`models/subscription.py`)
   - Subscription tracking
   - Payment records
   - Payment event logging

3. **Database Migration** (`migrations/add_stripe_tables.sql`)
   - User subscription fields
   - Subscriptions table
   - Payments table
   - Payment events table

### Frontend Components

1. **Billing Page** (`pages/billing/index.js`)
   - Pricing plans display
   - Subscription management
   - Billing history

2. **Payment Components** (`components/Payment/`)
   - PricingCard.js
   - SubscriptionStatus.js
   - BillingHistory.js

## 🚀 Setup Instructions

### 1. Environment Configuration

Add these variables to your `.env` file:

```bash
# Stripe Configuration
STRIPE_PUBLISHING_KEY=pk_test_your_stripe_publishing_key
STRIPE_API_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret
STRIPE_WEBHOOK_URL=https://yourdomain.com/api/stripe/webhook
```

### 2. Database Setup

Run the Stripe migration:

```bash
# Apply the migration to your database
psql -d your_database -f migrations/add_stripe_tables.sql
```

### 3. Stripe Dashboard Setup

1. **Create Products & Prices**
   ```bash
   python setup_stripe.py
   ```

2. **Configure Webhooks**
   - Go to Stripe Dashboard > Webhooks
   - Add endpoint: `https://yourdomain.com/api/stripe/webhook`
   - Select events:
     - `checkout.session.completed`
     - `customer.subscription.created`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

3. **Configure Customer Portal**
   - Go to Stripe Dashboard > Settings > Customer Portal
   - Enable features:
     - Subscription management
     - Payment method updates
     - Invoice history
     - Subscription cancellation

## 📋 API Endpoints

### Pricing Plans
- `GET /api/stripe/pricing` - Get available pricing plans

### Checkout
- `POST /api/stripe/create-checkout-session` - Create checkout session
- `POST /api/stripe/create-portal-session` - Create customer portal session

### Subscription Management
- `GET /api/stripe/subscription-status` - Get user's subscription status
- `GET /api/stripe/billing-history` - Get billing history

### Webhooks
- `POST /api/stripe/webhook` - Handle Stripe webhook events

## 💳 Pricing Plans

### Basic Plan - $9.99/month
- Unlimited tasks
- Basic AI features
- Notion integration

### Pro Plan - $19.99/month
- Everything in Basic
- Advanced AI features
- Priority support
- Analytics dashboard

### Enterprise Plan - $49.99/month
- Everything in Pro
- Team collaboration
- Custom integrations
- Dedicated support

## 🔄 Webhook Events

The system handles these Stripe webhook events:

1. **checkout.session.completed**
   - Updates user subscription status
   - Links Stripe customer to user account

2. **customer.subscription.created**
   - Records new subscription
   - Updates user plan type

3. **customer.subscription.updated**
   - Updates subscription status
   - Handles plan changes

4. **customer.subscription.deleted**
   - Marks subscription as canceled
   - Removes subscription ID

5. **invoice.payment_succeeded**
   - Records successful payment
   - Logs payment event

6. **invoice.payment_failed**
   - Records failed payment
   - Logs payment event

## 🧪 Testing

Run the Stripe integration tests:

```bash
# Run all Stripe tests
python -m pytest tests/test_stripe_integration.py -v

# Run specific test categories
python -m pytest tests/test_stripe_integration.py::TestStripePricing -v
python -m pytest tests/test_stripe_integration.py::TestStripeCheckout -v
python -m pytest tests/test_stripe_integration.py::TestStripeWebhook -v
```

## 🔒 Security Features

1. **Webhook Signature Verification**
   - All webhooks are verified using Stripe signatures
   - Prevents unauthorized webhook calls

2. **Rate Limiting**
   - Stripe API calls are rate-limited
   - Uses the existing rate-limited queue system

3. **Authentication**
   - All endpoints require user authentication
   - User data is isolated using RLS policies

4. **Data Encryption**
   - Sensitive data is encrypted in transit
   - Payment data is not stored locally

## 📊 Monitoring

### Payment Events
All payment events are logged to the `payment_events` table for:
- Audit trails
- Analytics
- Debugging

### Error Handling
- Comprehensive error handling for all Stripe operations
- Detailed logging for troubleshooting
- Graceful fallbacks for failed operations

## 🚀 Deployment Checklist

- [ ] Set up Stripe account and get API keys
- [ ] Configure environment variables
- [ ] Run database migrations
- [ ] Set up webhook endpoints
- [ ] Configure customer portal
- [ ] Test payment flow end-to-end
- [ ] Set up monitoring and alerts
- [ ] Configure backup and recovery

## 🔧 Troubleshooting

### Common Issues

1. **Webhook Verification Fails**
   - Check webhook secret configuration
   - Verify webhook URL is accessible
   - Check Stripe dashboard for webhook status

2. **Checkout Session Creation Fails**
   - Verify Stripe API key is correct
   - Check price IDs exist in Stripe
   - Ensure user authentication is working

3. **Subscription Status Not Updating**
   - Check webhook events are being received
   - Verify database connection
   - Check user permissions

### Debug Commands

```bash
# Check Stripe configuration
python -c "import stripe; print(stripe.api_key[:10] + '...')"

# Test webhook endpoint
curl -X POST https://yourdomain.com/api/stripe/webhook \
  -H "Content-Type: application/json" \
  -H "Stripe-Signature: test" \
  -d '{"test": "data"}'

# Check database tables
psql -d your_database -c "SELECT * FROM subscriptions LIMIT 5;"
```

## 📈 Analytics

Track subscription metrics:

```sql
-- Active subscriptions by plan
SELECT subscription_plan, COUNT(*) 
FROM users 
WHERE subscription_status = 'active' 
GROUP BY subscription_plan;

-- Monthly recurring revenue
SELECT 
  DATE_TRUNC('month', created_at) as month,
  SUM(CASE WHEN subscription_plan = 'basic' THEN 9.99
           WHEN subscription_plan = 'pro' THEN 19.99
           WHEN subscription_plan = 'enterprise' THEN 49.99
           ELSE 0 END) as mrr
FROM users 
WHERE subscription_status = 'active'
GROUP BY month
ORDER BY month;
```

## 🔄 Future Enhancements

1. **Usage-Based Billing**
   - Track API usage
   - Implement usage-based pricing tiers

2. **Team Billing**
   - Multi-user subscriptions
   - Team management features

3. **Advanced Analytics**
   - Revenue tracking
   - Churn analysis
   - Customer lifetime value

4. **Payment Methods**
   - Support for additional payment methods
   - International payment support

5. **Subscription Management**
   - Pause/resume subscriptions
   - Upgrade/downgrade flows
   - Promotional codes 