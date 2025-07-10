import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TextField,
  Button,
  Divider,
  Grid,
  useTheme
} from '@mui/material';
import {
  Notifications,
  DarkMode,
  Language,
  AccessTime,
  VolumeUp,
  Security
} from '@mui/icons-material';
import Layout from '../../components/Layout/Layout';

export default function PreferencesSettings() {
  const [preferences, setPreferences] = useState({
    notifications: {
      email: true,
      push: true,
      desktop: false,
      weekly_reports: true
    },
    appearance: {
      theme: 'light',
      compact_mode: false,
      show_animations: true
    },
    productivity: {
      focus_sessions: 25,
      break_duration: 5,
      long_break_duration: 15,
      auto_start_breaks: true,
      auto_start_sessions: false
    },
    privacy: {
      data_collection: true,
      analytics: true,
      personalized_insights: true
    }
  });
  const theme = useTheme();

  const handleNotificationChange = (key) => (event) => {
    setPreferences({
      ...preferences,
      notifications: {
        ...preferences.notifications,
        [key]: event.target.checked
      }
    });
  };

  const handleAppearanceChange = (key) => (event) => {
    setPreferences({
      ...preferences,
      appearance: {
        ...preferences.appearance,
        [key]: event.target.checked !== undefined ? event.target.checked : event.target.value
      }
    });
  };

  const handleProductivityChange = (key) => (event) => {
    setPreferences({
      ...preferences,
      productivity: {
        ...preferences.productivity,
        [key]: event.target.value
      }
    });
  };

  const handlePrivacyChange = (key) => (event) => {
    setPreferences({
      ...preferences,
      privacy: {
        ...preferences.privacy,
        [key]: event.target.checked
      }
    });
  };

  const handleSave = () => {
    // Here you would typically save to backend
    console.log('Saving preferences:', preferences);
  };

  return (
    <Layout>
      <Box sx={{ maxWidth: 800, mx: 'auto' }}>
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
            Preferences
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: '#6b7280',
              fontSize: '16px'
            }}
          >
            Customize your Cognie experience
          </Typography>
        </Box>

        {/* Notifications */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Notifications sx={{ color: '#3b82f6', mr: 2 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Notifications
              </Typography>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications.email}
                      onChange={handleNotificationChange('email')}
                    />
                  }
                  label="Email Notifications"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications.push}
                      onChange={handleNotificationChange('push')}
                    />
                  }
                  label="Push Notifications"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications.desktop}
                      onChange={handleNotificationChange('desktop')}
                    />
                  }
                  label="Desktop Notifications"
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.notifications.weekly_reports}
                      onChange={handleNotificationChange('weekly_reports')}
                    />
                  }
                  label="Weekly Reports"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Appearance */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <DarkMode sx={{ color: '#8b5cf6', mr: 2 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Appearance
              </Typography>
            </Box>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={preferences.appearance.theme}
                    label="Theme"
                    onChange={handleAppearanceChange('theme')}
                  >
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="auto">Auto</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.appearance.compact_mode}
                      onChange={handleAppearanceChange('compact_mode')}
                    />
                  }
                  label="Compact Mode"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.appearance.show_animations}
                      onChange={handleAppearanceChange('show_animations')}
                    />
                  }
                  label="Show Animations"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Productivity Settings */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <AccessTime sx={{ color: '#10b981', mr: 2 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Productivity Settings
              </Typography>
            </Box>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Focus Session Duration (minutes)"
                  type="number"
                  value={preferences.productivity.focus_sessions}
                  onChange={handleProductivityChange('focus_sessions')}
                  inputProps={{ min: 5, max: 120 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Break Duration (minutes)"
                  type="number"
                  value={preferences.productivity.break_duration}
                  onChange={handleProductivityChange('break_duration')}
                  inputProps={{ min: 1, max: 30 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Long Break Duration (minutes)"
                  type="number"
                  value={preferences.productivity.long_break_duration}
                  onChange={handleProductivityChange('long_break_duration')}
                  inputProps={{ min: 5, max: 60 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.productivity.auto_start_breaks}
                      onChange={handleProductivityChange('auto_start_breaks')}
                    />
                  }
                  label="Auto-start Breaks"
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.productivity.auto_start_sessions}
                      onChange={handleProductivityChange('auto_start_sessions')}
                    />
                  }
                  label="Auto-start Focus Sessions"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Privacy Settings */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
              <Security sx={{ color: '#ef4444', mr: 2 }} />
              <Typography variant="h6" sx={{ fontWeight: 600 }}>
                Privacy & Data
              </Typography>
            </Box>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.privacy.data_collection}
                      onChange={handlePrivacyChange('data_collection')}
                    />
                  }
                  label="Allow Data Collection"
                />
                <Typography variant="caption" sx={{ color: '#6b7280', display: 'block', ml: 4 }}>
                  Help us improve Cognie by collecting anonymous usage data
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.privacy.analytics}
                      onChange={handlePrivacyChange('analytics')}
                    />
                  }
                  label="Analytics & Insights"
                />
                <Typography variant="caption" sx={{ color: '#6b7280', display: 'block', ml: 4 }}>
                  Receive personalized productivity insights and recommendations
                </Typography>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={preferences.privacy.personalized_insights}
                      onChange={handlePrivacyChange('personalized_insights')}
                    />
                  }
                  label="Personalized Insights"
                />
                <Typography variant="caption" sx={{ color: '#6b7280', display: 'block', ml: 4 }}>
                  Get AI-powered recommendations based on your productivity patterns
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Save Button */}
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            onClick={handleSave}
            sx={{
              borderRadius: '8px',
              textTransform: 'none',
              fontWeight: 500
            }}
          >
            Save Preferences
          </Button>
        </Box>
      </Box>
    </Layout>
  );
} 