#!/usr/bin/env python3
"""
Stripe setup script for Cognie.
This script creates the necessary Stripe products, prices, and webhooks.
"""

import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Stripe
stripe.api_key = os.getenv("STRIPE_API_KEY")

if not stripe.api_key:
    print("❌ STRIPE_API_KEY not found in environment variables")
    exit(1)

def create_products():
    """Create Stripe products for Cognie plans."""
    print("🛍️  Creating Stripe products...")
    
    products = {
        "basic": {
            "name": "Cognie Basic",
            "description": "Perfect for individuals getting started with productivity",
            "features": ["Unlimited tasks", "Basic AI features", "Notion integration"]
        },
        "pro": {
            "name": "Cognie Pro", 
            "description": "Advanced features for power users",
            "features": ["Everything in Basic", "Advanced AI", "Priority support", "Analytics"]
        },
        "enterprise": {
            "name": "Cognie Enterprise",
            "description": "Complete solution for teams and organizations",
            "features": ["Everything in Pro", "Team collaboration", "Custom integrations", "Dedicated support"]
        }
    }
    
    created_products = {}
    
    for plan_key, product_data in products.items():
        try:
            # Check if product already exists
            existing_products = stripe.Product.list(limit=100)
            existing_product = None
            
            for product in existing_products.data:
                if product.name == product_data["name"]:
                    existing_product = product
                    break
            
            if existing_product:
                print(f"✅ Product '{product_data['name']}' already exists (ID: {existing_product.id})")
                created_products[plan_key] = existing_product
            else:
                # Create new product
                product = stripe.Product.create(
                    name=product_data["name"],
                    description=product_data["description"],
                    metadata={
                        "plan_type": plan_key,
                        "features": ", ".join(product_data["features"])
                    }
                )
                print(f"✅ Created product '{product.name}' (ID: {product.id})")
                created_products[plan_key] = product
                
        except Exception as e:
            print(f"❌ Failed to create product '{product_data['name']}': {e}")
    
    return created_products

def create_prices(products):
    """Create Stripe prices for the products."""
    print("💰 Creating Stripe prices...")
    
    prices = {
        "basic": 999,  # $9.99 in cents
        "pro": 1999,   # $19.99 in cents
        "enterprise": 4999  # $49.99 in cents
    }
    
    created_prices = {}
    
    for plan_key, price_amount in prices.items():
        if plan_key not in products:
            print(f"⚠️  Skipping price for '{plan_key}' - product not found")
            continue
            
        try:
            # Check if price already exists
            existing_prices = stripe.Price.list(
                product=products[plan_key].id,
                active=True,
                limit=100
            )
            
            if existing_prices.data:
                print(f"✅ Price for '{plan_key}' already exists (ID: {existing_prices.data[0].id})")
                created_prices[plan_key] = existing_prices.data[0]
            else:
                # Create new price
                price = stripe.Price.create(
                    product=products[plan_key].id,
                    unit_amount=price_amount,
                    currency="usd",
                    recurring={"interval": "month"},
                    metadata={"plan_type": plan_key}
                )
                print(f"✅ Created price for '{plan_key}' (ID: {price.id}) - ${price_amount/100}/month")
                created_prices[plan_key] = price
                
        except Exception as e:
            print(f"❌ Failed to create price for '{plan_key}': {e}")
    
    return created_prices

def create_webhook():
    """Create Stripe webhook endpoint."""
    print("🔗 Creating Stripe webhook...")
    
    webhook_url = os.getenv("STRIPE_WEBHOOK_URL", "https://yourdomain.com/api/stripe/webhook")
    
    if webhook_url == "https://yourdomain.com/api/stripe/webhook":
        print("⚠️  Please set STRIPE_WEBHOOK_URL in your .env file")
        print("   Example: STRIPE_WEBHOOK_URL=https://yourdomain.com/api/stripe/webhook")
        return None
    
    try:
        # Check if webhook already exists
        existing_webhooks = stripe.WebhookEndpoint.list(limit=100)
        existing_webhook = None
        
        for webhook in existing_webhooks.data:
            if webhook.url == webhook_url:
                existing_webhook = webhook
                break
        
        if existing_webhook:
            print(f"✅ Webhook already exists (ID: {existing_webhook.id})")
            return existing_webhook
        else:
            # Create new webhook
            webhook = stripe.WebhookEndpoint.create(
                url=webhook_url,
                enabled_events=[
                    "checkout.session.completed",
                    "customer.subscription.created",
                    "customer.subscription.updated", 
                    "customer.subscription.deleted",
                    "invoice.payment_succeeded",
                    "invoice.payment_failed"
                ],
                description="Cognie payment webhook"
            )
            print(f"✅ Created webhook (ID: {webhook.id})")
            print("   ⚠️  Webhook secret generated. Please retrieve it securely from the Stripe dashboard.")
            print("   Add the secret to your .env file as STRIPE_WEBHOOK_SECRET.")
            return webhook
            
    except Exception as e:
        print(f"❌ Failed to create webhook: {e}")
        return None

def create_customer_portal():
    """Configure Stripe customer portal."""
    print("🏪 Configuring customer portal...")
    
    try:
        # Configure customer portal
        portal_config = stripe.billing_portal.Configuration.create(
            business_profile={
                "headline": "Cognie - AI-Powered Productivity",
                "privacy_policy_url": "https://cognie.app/privacy",
                "terms_of_service_url": "https://cognie.app/terms"
            },
            features={
                "customer_update": {
                    "allowed_updates": ["email", "address", "phone"],
                    "enabled": True
                },
                "invoice_history": {"enabled": True},
                "payment_method_update": {"enabled": True},
                "subscription_cancel": {
                    "enabled": True,
                    "mode": "at_period_end",
                    "proration_behavior": "none"
                },
                "subscription_pause": {"enabled": True},
                "subscription_update": {
                    "default_allowed_updates": ["price"],
                    "enabled": True,
                    "proration_behavior": "create_prorations"
                }
            }
        )
        print(f"✅ Customer portal configured (ID: {portal_config.id})")
        return portal_config
        
    except Exception as e:
        print(f"❌ Failed to configure customer portal: {e}")
        return None

def update_env_template():
    """Update the environment template with Stripe configuration."""
    print("📝 Updating environment template...")
    
    try:
        with open("env.production.template", "r") as f:
            content = f.read()
        
        # Check if Stripe section already exists
        if "STRIPE_PUBLISHING_KEY" not in content:
            stripe_section = """
# =============================================================================
# PAYMENT CONFIGURATION (Stripe)
# =============================================================================
STRIPE_PUBLISHING_KEY=pk_test_your_stripe_publishing_key
STRIPE_API_KEY=sk_test_your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=whsec_your_stripe_webhook_secret
STRIPE_WEBHOOK_URL=https://yourdomain.com/api/stripe/webhook

"""
            # Insert before deployment configuration
            if "# =============================================================================\n# DEPLOYMENT CONFIGURATION" in content:
                content = content.replace(
                    "# =============================================================================\n# DEPLOYMENT CONFIGURATION",
                    stripe_section + "# =============================================================================\n# DEPLOYMENT CONFIGURATION"
                )
            else:
                content += stripe_section
        
        with open("env.production.template", "w") as f:
            f.write(content)
        
        print("✅ Environment template updated")
        
    except Exception as e:
        print(f"❌ Failed to update environment template: {e}")

def main():
    """Main setup function."""
    print("🚀 Setting up Stripe for Cognie...")
    print("=" * 50)
    
    # Create products
    products = create_products()
    print()
    
    # Create prices
    prices = create_prices(products)
    print()
    
    # Create webhook
    webhook = create_webhook()
    print()
    
    # Configure customer portal
    portal = create_customer_portal()
    print()
    
    # Update environment template
    update_env_template()
    print()
    
    print("=" * 50)
    print("🎉 Stripe setup complete!")
    print()
    print("📋 Next steps:")
    print("1. Add your Stripe keys to your .env file:")
    print("   - STRIPE_PUBLISHING_KEY (from Stripe Dashboard)")
    print("   - STRIPE_API_KEY (from Stripe Dashboard)")
    print("   - STRIPE_WEBHOOK_SECRET (from webhook creation above)")
    print()
    print("2. Update your pricing plans in routes/stripe.py with the actual price IDs:")
    for plan_key, price in prices.items():
        if price:
            print(f"   - {plan_key}: {price.id}")
    print()
    print("3. Deploy your application and test the payment flow")
    print()
    print("🔗 Useful links:")
    print("- Stripe Dashboard: https://dashboard.stripe.com")
    print("- Stripe Documentation: https://stripe.com/docs")
    print("- Webhook Testing: https://dashboard.stripe.com/webhooks")

if __name__ == "__main__":
    main() 