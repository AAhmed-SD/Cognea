-- Migration: Add cost tracking tables for OpenAI usage monitoring
-- This migration adds tables to track token usage and costs per user

-- Create openai_usage table for detailed usage tracking
CREATE TABLE public.openai_usage (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) NOT NULL,
    model TEXT NOT NULL,
    input_tokens INTEGER NOT NULL,
    output_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    input_cost_usd DECIMAL(10,6) NOT NULL,
    output_cost_usd DECIMAL(10,6) NOT NULL,
    total_cost_usd DECIMAL(10,6) NOT NULL,
    endpoint TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Create usage_totals table for daily/monthly aggregates
CREATE TABLE public.usage_totals (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    key TEXT UNIQUE NOT NULL, -- Format: usage_daily:{user_id}:{date} or usage_monthly:{user_id}:{date}
    user_id UUID REFERENCES public.users(id) NOT NULL,
    period_type TEXT NOT NULL, -- 'daily' or 'monthly'
    period_date DATE NOT NULL,
    total_cost_usd DECIMAL(10,6) DEFAULT 0,
    total_requests INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()) NOT NULL
);

-- Add cost tracking columns to users table
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'inactive',
ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT,
ADD COLUMN IF NOT EXISTS subscription_id TEXT,
ADD COLUMN IF NOT EXISTS last_payment_date TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS daily_cost_limit_usd DECIMAL(10,2) DEFAULT 10.00,
ADD COLUMN IF NOT EXISTS monthly_cost_limit_usd DECIMAL(10,2) DEFAULT 100.00;

-- Create indexes for performance
CREATE INDEX idx_openai_usage_user_id ON public.openai_usage(user_id);
CREATE INDEX idx_openai_usage_timestamp ON public.openai_usage(timestamp);
CREATE INDEX idx_openai_usage_model ON public.openai_usage(model);
CREATE INDEX idx_usage_totals_user_id ON public.usage_totals(user_id);
CREATE INDEX idx_usage_totals_key ON public.usage_totals(key);
CREATE INDEX idx_usage_totals_period ON public.usage_totals(period_type, period_date);

-- Add triggers for updated_at
CREATE TRIGGER update_openai_usage_updated_at
    BEFORE UPDATE ON public.openai_usage
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_usage_totals_updated_at
    BEFORE UPDATE ON public.usage_totals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add RLS policies for security
ALTER TABLE public.openai_usage ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_totals ENABLE ROW LEVEL SECURITY;

-- Users can only see their own usage data
CREATE POLICY "Users can view own openai usage" ON public.openai_usage
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own openai usage" ON public.openai_usage
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can view own usage totals" ON public.usage_totals
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own usage totals" ON public.usage_totals
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own usage totals" ON public.usage_totals
    FOR UPDATE USING (auth.uid() = user_id);

-- Create view for easy usage reporting
CREATE VIEW public.user_usage_summary AS
SELECT 
    u.id as user_id,
    u.email,
    u.subscription_status,
    u.daily_cost_limit_usd,
    u.monthly_cost_limit_usd,
    COALESCE(daily.total_cost_usd, 0) as daily_cost_usd,
    COALESCE(daily.total_requests, 0) as daily_requests,
    COALESCE(monthly.total_cost_usd, 0) as monthly_cost_usd,
    COALESCE(monthly.total_requests, 0) as monthly_requests,
    CASE 
        WHEN COALESCE(daily.total_cost_usd, 0) > u.daily_cost_limit_usd THEN true 
        ELSE false 
    END as daily_limit_exceeded,
    CASE 
        WHEN COALESCE(monthly.total_cost_usd, 0) > u.monthly_cost_limit_usd THEN true 
        ELSE false 
    END as monthly_limit_exceeded
FROM public.users u
LEFT JOIN public.usage_totals daily ON 
    daily.user_id = u.id 
    AND daily.period_type = 'daily' 
    AND daily.period_date = CURRENT_DATE
LEFT JOIN public.usage_totals monthly ON 
    monthly.user_id = u.id 
    AND monthly.period_type = 'monthly' 
    AND monthly.period_date = DATE_TRUNC('month', CURRENT_DATE)::date;

-- Add RLS to the view
ALTER VIEW public.user_usage_summary SET (security_invoker = true);

-- Grant necessary permissions
GRANT SELECT ON public.user_usage_summary TO authenticated;
GRANT ALL ON public.openai_usage TO authenticated;
GRANT ALL ON public.usage_totals TO authenticated; 