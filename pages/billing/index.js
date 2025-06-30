import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../contexts/AuthContext';
import PricingCard from '../../components/Payment/PricingCard';
import SubscriptionStatus from '../../components/Payment/SubscriptionStatus';
import BillingHistory from '../../components/Payment/BillingHistory';

const BillingPage = () => {
  const { user, isAuthenticated } = useAuth();
  const router = useRouter();
  const [pricingPlans, setPricingPlans] = useState({});
  const [subscriptionStatus, setSubscriptionStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    fetchPricingPlans();
    fetchSubscriptionStatus();
  }, [isAuthenticated]);

  const fetchPricingPlans = async () => {
    try {
      const response = await fetch('/api/stripe/pricing');
      const data = await response.json();
      setPricingPlans(data.plans);
    } catch (err) {
      setError('Failed to load pricing plans');
      console.error('Error fetching pricing plans:', err);
    }
  };

  const fetchSubscriptionStatus = async () => {
    try {
      const response = await fetch('/api/stripe/subscription-status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setSubscriptionStatus(data);
    } catch (err) {
      console.error('Error fetching subscription status:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async (priceId) => {
    try {
      const response = await fetch('/api/stripe/create-checkout-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          price_id: priceId,
          success_url: `${window.location.origin}/billing/success`,
          cancel_url: `${window.location.origin}/billing/cancel`
        })
      });

      const data = await response.json();
      
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (err) {
      setError('Failed to create checkout session');
      console.error('Error creating checkout session:', err);
    }
  };

  const handleManageSubscription = async () => {
    try {
      const response = await fetch('/api/stripe/create-portal-session', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          return_url: `${window.location.origin}/billing`
        })
      });

      const data = await response.json();
      
      if (data.portal_url) {
        window.location.href = data.portal_url;
      }
    } catch (err) {
      setError('Failed to open customer portal');
      console.error('Error creating portal session:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Billing & Subscription
          </h1>
          <p className="text-xl text-gray-600">
            Choose the perfect plan for your productivity needs
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-8 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  {error}
                </h3>
              </div>
            </div>
          </div>
        )}

        {/* Current Subscription Status */}
        {subscriptionStatus && (
          <div className="mb-12">
            <SubscriptionStatus 
              status={subscriptionStatus} 
              onManageSubscription={handleManageSubscription}
            />
          </div>
        )}

        {/* Pricing Plans */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Choose Your Plan
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            {Object.entries(pricingPlans).map(([key, plan]) => (
              <PricingCard
                key={key}
                plan={plan}
                planKey={key}
                onSubscribe={handleSubscribe}
                currentPlan={subscriptionStatus?.plan_name?.toLowerCase()}
              />
            ))}
          </div>
        </div>

        {/* Billing History */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-8 text-center">
            Billing History
          </h2>
          <BillingHistory />
        </div>
      </div>
    </div>
  );
};

export default BillingPage; 