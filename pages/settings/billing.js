import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Grid,
  useTheme
} from '@mui/material';
import {
  CreditCard,
  Receipt,
  CheckCircle,
  Cancel,
  Star,
  TrendingUp,
  Security
} from '@mui/icons-material';
import Layout from '../../components/Layout/Layout';
import apiService from '../../services/api';

export default function BillingSettings() {
  const [billingData, setBillingData] = useState(null);
  const theme = useTheme();

  useEffect(() => {
    fetchBillingData();
  }, []);

  const fetchBillingData = async () => {
    try {
      const response = await apiService.get('/api/billing/status');
      setBillingData(response);
    } catch (error) {
      console.error('Failed to fetch billing data:', error);
      // Use sample data
      setBillingData({
        current_plan: 'Pro',
        status: 'active',
        next_billing_date: '2025-02-01',
        amount: 19.99,
        currency: 'USD',
        payment_method: {
          type: 'card',
          last4: '4242',
          brand: 'Visa',
          expiry: '12/25'
        },
        usage: {
          tasks_used: 1250,
          tasks_limit: 2000,
          focus_sessions_used: 45,
          focus_sessions_limit: 100,
          storage_used: '2.3GB',
          storage_limit: '10GB'
        },
        billing_history: [
          {
            date: '2025-01-01',
            amount: 19.99,
            status: 'paid',
            description: 'Pro Plan - Monthly'
          },
          {
            date: '2024-12-01',
            amount: 19.99,
            status: 'paid',
            description: 'Pro Plan - Monthly'
          }
        ]
      });
    }
  };

  if (!billingData) {
    return (
      <Layout>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}>
          <Typography>Loading billing information...</Typography>
        </Box>
      </Layout>
    );
  }

  const getUsagePercentage = (used, limit) => {
    if (typeof used === 'string') {
      // Handle storage (e.g., "2.3GB" vs "10GB")
      const usedNum = parseFloat(used);
      const limitNum = parseFloat(limit);
      return (usedNum / limitNum) * 100;
    }
    return (used / limit) * 100;
  };

  return (
    <Layout>
      <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="h4"
            sx={{
              fontWeight: 700,
              fontSize: '28px',
              letterSpacing: '-0.025em',
              color: '#111827',
              mb: 1
            }}
          >
            Billing & Subscription
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: '#6b7280',
              fontSize: '16px'
            }}
          >
            Manage your subscription and billing information
          </Typography>
        </Box>

        {/* Current Plan */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Box>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 1 }}>
                  Current Plan
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="h4" sx={{ fontWeight: 700, color: '#3b82f6' }}>
                    {billingData.current_plan}
                  </Typography>
                  <Chip
                    label={billingData.status}
                    color={billingData.status === 'active' ? 'success' : 'warning'}
                    size="small"
                  />
                </Box>
              </Box>
              <Box sx={{ textAlign: 'right' }}>
                <Typography variant="h5" sx={{ fontWeight: 700 }}>
                  ${billingData.amount}
                </Typography>
                <Typography variant="body2" sx={{ color: '#6b7280' }}>
                  per month
                </Typography>
              </Box>
            </Box>
            <Typography variant="body2" sx={{ color: '#6b7280', mb: 3 }}>
              Next billing date: {new Date(billingData.next_billing_date).toLocaleDateString()}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" color="primary">
                Change Plan
              </Button>
              <Button variant="outlined" color="error">
                Cancel Subscription
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Usage */}
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                  Usage This Month
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <CheckCircle sx={{ color: '#10b981' }} />
                    </ListItemIcon>
                    <ListItemText
                      primary="Tasks"
                      secondary={`${billingData.usage.tasks_used} / ${billingData.usage.tasks_limit}`}
                    />
                    <Typography variant="body2" sx={{ color: '#6b7280' }}>
                      {Math.round(getUsagePercentage(billingData.usage.tasks_used, billingData.usage.tasks_limit))}%
                    </Typography>
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <TrendingUp sx={{ color: '#3b82f6' }} />
                    </ListItemIcon>
                    <ListItemText
                      primary="Focus Sessions"
                      secondary={`${billingData.usage.focus_sessions_used} / ${billingData.usage.focus_sessions_limit}`}
                    />
                    <Typography variant="body2" sx={{ color: '#6b7280' }}>
                      {Math.round(getUsagePercentage(billingData.usage.focus_sessions_used, billingData.usage.focus_sessions_limit))}%
                    </Typography>
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <Security sx={{ color: '#8b5cf6' }} />
                    </ListItemIcon>
                    <ListItemText
                      primary="Storage"
                      secondary={`${billingData.usage.storage_used} / ${billingData.usage.storage_limit}`}
                    />
                    <Typography variant="body2" sx={{ color: '#6b7280' }}>
                      {Math.round(getUsagePercentage(billingData.usage.storage_used, billingData.usage.storage_limit))}%
                    </Typography>
                  </ListItem>
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
                  Payment Method
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <CreditCard sx={{ color: '#3b82f6', mr: 2 }} />
                  <Box>
                    <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                      {billingData.payment_method.brand} •••• {billingData.payment_method.last4}
                    </Typography>
                    <Typography variant="body2" sx={{ color: '#6b7280' }}>
                      Expires {billingData.payment_method.expiry}
                    </Typography>
                  </Box>
                </Box>
                <Button variant="outlined" size="small">
                  Update Payment Method
                </Button>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Billing History */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Billing History
            </Typography>
            <List>
              {billingData.billing_history.map((item, index) => (
                <React.Fragment key={index}>
                  <ListItem>
                    <ListItemIcon>
                      <Receipt sx={{ color: '#6b7280' }} />
                    </ListItemIcon>
                    <ListItemText
                      primary={item.description}
                      secondary={new Date(item.date).toLocaleDateString()}
                    />
                    <Box sx={{ textAlign: 'right' }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        ${item.amount}
                      </Typography>
                      <Chip
                        label={item.status}
                        color={item.status === 'paid' ? 'success' : 'warning'}
                        size="small"
                      />
                    </Box>
                  </ListItem>
                  {index < billingData.billing_history.length - 1 && <Divider />}
                </React.Fragment>
              ))}
            </List>
            <Box sx={{ mt: 2 }}>
              <Button variant="outlined" fullWidth>
                Download All Invoices
              </Button>
            </Box>
          </CardContent>
        </Card>
      </Box>
    </Layout>
  );
} 