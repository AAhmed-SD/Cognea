import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Avatar,
  Grid,
  Divider,
  useTheme
} from '@mui/material';
import {
  Person,
  Email,
  Phone,
  LocationOn
} from '@mui/icons-material';
import Layout from '../../components/Layout/Layout';

export default function ProfileSettings() {
  const [profile, setProfile] = useState({
    name: 'John Doe',
    email: 'john.doe@example.com',
    phone: '+1 (555) 123-4567',
    location: 'San Francisco, CA',
    bio: 'Productivity enthusiast and software developer. Always looking for ways to optimize my workflow and help others do the same.'
  });
  const [isEditing, setIsEditing] = useState(false);
  const theme = useTheme();

  const handleSave = () => {
    // Here you would typically save to backend
    setIsEditing(false);
  };

  const handleCancel = () => {
    setIsEditing(false);
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
            Profile Settings
          </Typography>
          <Typography
            variant="body1"
            sx={{
              color: '#6b7280',
              fontSize: '16px'
            }}
          >
            Manage your personal information and preferences
          </Typography>
        </Box>

        {/* Profile Card */}
        <Card sx={{ mb: 4 }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 4 }}>
              <Avatar
                sx={{
                  width: 80,
                  height: 80,
                  fontSize: '32px',
                  fontWeight: 600,
                  backgroundColor: theme.palette.primary.main,
                  mr: 3
                }}
              >
                {profile.name.split(' ').map(n => n[0]).join('')}
              </Avatar>
              <Box sx={{ flexGrow: 1 }}>
                <Typography variant="h5" sx={{ fontWeight: 600, mb: 1 }}>
                  {profile.name}
                </Typography>
                <Typography variant="body2" sx={{ color: '#6b7280' }}>
                  Member since January 2025
                </Typography>
              </Box>
              <Button
                variant={isEditing ? "outlined" : "contained"}
                onClick={() => setIsEditing(!isEditing)}
                sx={{
                  borderRadius: '8px',
                  textTransform: 'none',
                  fontWeight: 500
                }}
              >
                {isEditing ? 'Cancel' : 'Edit Profile'}
              </Button>
            </Box>

            <Divider sx={{ mb: 4 }} />

            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Person sx={{ color: '#6b7280', mr: 2 }} />
                  <Typography variant="body2" sx={{ color: '#6b7280', fontWeight: 500 }}>
                    Full Name
                  </Typography>
                </Box>
                <TextField
                  fullWidth
                  value={profile.name}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                  disabled={!isEditing}
                  variant="outlined"
                  sx={{ mb: 3 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Email sx={{ color: '#6b7280', mr: 2 }} />
                  <Typography variant="body2" sx={{ color: '#6b7280', fontWeight: 500 }}>
                    Email Address
                  </Typography>
                </Box>
                <TextField
                  fullWidth
                  value={profile.email}
                  onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                  disabled={!isEditing}
                  variant="outlined"
                  sx={{ mb: 3 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Phone sx={{ color: '#6b7280', mr: 2 }} />
                  <Typography variant="body2" sx={{ color: '#6b7280', fontWeight: 500 }}>
                    Phone Number
                  </Typography>
                </Box>
                <TextField
                  fullWidth
                  value={profile.phone}
                  onChange={(e) => setProfile({ ...profile, phone: e.target.value })}
                  disabled={!isEditing}
                  variant="outlined"
                  sx={{ mb: 3 }}
                />
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <LocationOn sx={{ color: '#6b7280', mr: 2 }} />
                  <Typography variant="body2" sx={{ color: '#6b7280', fontWeight: 500 }}>
                    Location
                  </Typography>
                </Box>
                <TextField
                  fullWidth
                  value={profile.location}
                  onChange={(e) => setProfile({ ...profile, location: e.target.value })}
                  disabled={!isEditing}
                  variant="outlined"
                  sx={{ mb: 3 }}
                />
              </Grid>

              <Grid item xs={12}>
                <Typography variant="body2" sx={{ color: '#6b7280', fontWeight: 500, mb: 2 }}>
                  Bio
                </Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={4}
                  value={profile.bio}
                  onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                  disabled={!isEditing}
                  variant="outlined"
                  sx={{ mb: 3 }}
                />
              </Grid>
            </Grid>

            {isEditing && (
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  onClick={handleCancel}
                  sx={{
                    borderRadius: '8px',
                    textTransform: 'none',
                    fontWeight: 500
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  onClick={handleSave}
                  sx={{
                    borderRadius: '8px',
                    textTransform: 'none',
                    fontWeight: 500
                  }}
                >
                  Save Changes
                </Button>
              </Box>
            )}
          </CardContent>
        </Card>

        {/* Account Security */}
        <Card>
          <CardContent>
            <Typography variant="h6" sx={{ fontWeight: 600, mb: 3 }}>
              Account Security
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" sx={{ color: '#6b7280', fontWeight: 500, mb: 1 }}>
                  Password
                </Typography>
                <Button
                  variant="outlined"
                  sx={{
                    borderRadius: '8px',
                    textTransform: 'none',
                    fontWeight: 500
                  }}
                >
                  Change Password
                </Button>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" sx={{ color: '#6b7280', fontWeight: 500, mb: 1 }}>
                  Two-Factor Authentication
                </Typography>
                <Button
                  variant="outlined"
                  sx={{
                    borderRadius: '8px',
                    textTransform: 'none',
                    fontWeight: 500
                  }}
                >
                  Enable 2FA
                </Button>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Box>
    </Layout>
  );
} 