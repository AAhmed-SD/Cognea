import React, { useState } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
  Paper,
  Avatar,
  Chip,
  IconButton,
  Switch,
  FormControlLabel,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import {
  Person,
  Notifications,
  Security,
  Palette,
  Language,
  Storage,
  Help,
  Feedback,
  Logout,
  Settings as SettingsIcon,
  AccountCircle,
  NotificationsActive,
  Lock,
  Brush,
  Translate,
  Cloud,
  Support,
  RateReview,
  ExitToApp,
  ChevronRight,
  Edit,
  Save,
  Cancel
} from '@mui/icons-material';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';

const settingsSections = [
  {
    id: 'profile',
    title: 'Profile & Account',
    description: 'Manage your personal information and account settings',
    icon: <Person />,
    color: '#3b82f6',
    path: '/settings/profile'
  },
  {
    id: 'preferences',
    title: 'Preferences',
    description: 'Customize your app experience and notifications',
    icon: <Notifications />,
    color: '#8b5cf6',
    path: '/settings/preferences'
  },
  {
    id: 'features',
    title: 'Features & Integrations',
    description: 'Enable or disable features and connect external services',
    icon: <SettingsIcon />,
    color: '#10b981',
    path: '/settings/features'
  },
  {
    id: 'billing',
    title: 'Billing & Subscription',
    description: 'Manage your subscription and payment methods',
    icon: <Storage />,
    color: '#f59e0b',
    path: '/settings/billing'
  }
];

const quickSettings = [
  {
    id: 'notifications',
    title: 'Push Notifications',
    description: 'Receive reminders and updates',
    icon: <NotificationsActive />,
    enabled: true
  },
  {
    id: 'darkMode',
    title: 'Dark Mode',
    description: 'Switch between light and dark themes',
    icon: <Palette />,
    enabled: false
  },
  {
    id: 'autoSync',
    title: 'Auto Sync',
    description: 'Automatically sync data across devices',
    icon: <Cloud />,
    enabled: true
  }
];

export default function Settings() {
  const { persona } = usePersona();
  const [activeTab, setActiveTab] = useState(0);
  const [quickSettingsState, setQuickSettingsState] = useState(
    quickSettings.reduce((acc, setting) => {
      acc[setting.id] = setting.enabled;
      return acc;
    }, {})
  );

  const handleQuickSettingToggle = (settingId) => {
    setQuickSettingsState(prev => ({
      ...prev,
      [settingId]: !prev[settingId]
    }));
  };

  const handleSectionClick = (path) => {
    // In a real app, this would navigate to the specific settings page
    console.log(`Navigate to: ${path}`);
  };

  return (
    <Layout>
      <Container maxWidth="xl">
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h4" component="h1" sx={{ fontWeight: 600 }}>
              Settings
            </Typography>
            <Button
              variant="outlined"
              startIcon={<Help />}
              onClick={() => console.log('Open help')}
            >
              Help & Support
            </Button>
          </Box>
          <Typography variant="body1" color="text.secondary">
            Manage your account settings and customize your experience
          </Typography>
        </Box>

        {/* User Profile Summary */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
              <Avatar
                sx={{ width: 80, height: 80, bgcolor: 'primary.main' }}
              >
                <AccountCircle sx={{ fontSize: 40 }} />
              </Avatar>
              <Box sx={{ flex: 1 }}>
                <Typography variant="h6" sx={{ mb: 1 }}>
                  User Name
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                  user@example.com
                </Typography>
                <Chip 
                  label={persona?.title || 'Student'} 
                  size="small" 
                  color="primary" 
                  variant="outlined"
                />
              </Box>
              <Button
                variant="outlined"
                startIcon={<Edit />}
                onClick={() => handleSectionClick('/settings/profile')}
              >
                Edit Profile
              </Button>
            </Box>
          </CardContent>
        </Card>

        {/* Quick Settings */}
        <Typography variant="h6" sx={{ mb: 2 }}>
          Quick Settings
        </Typography>
        <Grid container spacing={2} sx={{ mb: 4 }}>
          {quickSettings.map((setting) => (
            <Grid item xs={12} md={4} key={setting.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Box sx={{ color: 'primary.main' }}>
                        {setting.icon}
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                          {setting.title}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {setting.description}
                        </Typography>
                      </Box>
                    </Box>
                    <Switch
                      checked={quickSettingsState[setting.id]}
                      onChange={() => handleQuickSettingToggle(setting.id)}
                      color="primary"
                    />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Settings Sections */}
        <Typography variant="h6" sx={{ mb: 2 }}>
          All Settings
        </Typography>
        <Grid container spacing={3}>
          {settingsSections.map((section) => (
            <Grid item xs={12} md={6} key={section.id}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  transition: 'all 0.2s ease-in-out',
                  '&:hover': {
                    transform: 'translateY(-2px)',
                    boxShadow: 3
                  }
                }}
                onClick={() => handleSectionClick(section.path)}
              >
                <CardContent>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 3 }}>
                      <Box 
                        sx={{ 
                          p: 1.5, 
                          borderRadius: 2, 
                          bgcolor: `${section.color}15`,
                          color: section.color
                        }}
                      >
                        {section.icon}
                      </Box>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 600, mb: 0.5 }}>
                          {section.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          {section.description}
                        </Typography>
                      </Box>
                    </Box>
                    <ChevronRight color="action" />
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Additional Actions */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" sx={{ mb: 2 }}>
            Additional Actions
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={4}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<Support />}
                onClick={() => console.log('Open support')}
                sx={{ justifyContent: 'flex-start', p: 2 }}
              >
                Contact Support
              </Button>
            </Grid>
            <Grid item xs={12} md={4}>
              <Button
                fullWidth
                variant="outlined"
                startIcon={<RateReview />}
                onClick={() => console.log('Open feedback')}
                sx={{ justifyContent: 'flex-start', p: 2 }}
              >
                Send Feedback
              </Button>
            </Grid>
            <Grid item xs={12} md={4}>
              <Button
                fullWidth
                variant="outlined"
                color="error"
                startIcon={<Logout />}
                onClick={() => console.log('Logout')}
                sx={{ justifyContent: 'flex-start', p: 2 }}
              >
                Sign Out
              </Button>
            </Grid>
          </Grid>
        </Box>

        {/* System Info */}
        <Card sx={{ mt: 4 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2 }}>
              System Information
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">
                  App Version
                </Typography>
                <Typography variant="body1">
                  1.0.0
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Last Updated
                </Typography>
                <Typography variant="body1">
                  {new Date().toLocaleDateString()}
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Storage Used
                </Typography>
                <Typography variant="body1">
                  2.4 MB
                </Typography>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="text.secondary">
                  Sync Status
                </Typography>
                <Chip label="Up to date" size="small" color="success" />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Container>
    </Layout>
  );
} 