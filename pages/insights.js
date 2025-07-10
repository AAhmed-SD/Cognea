import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  Button, 
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Alert,
  Tabs,
  Tab,
  LinearProgress,
  Avatar,
  IconButton,
  Tooltip
} from '@mui/material';
import { 
  TrendingUp,
  TrendingDown,
  Psychology,
  Lightbulb,
  Analytics,
  Schedule,
  EmojiEvents,
  Star,
  CheckCircle,
  Warning,
  Info,
  Refresh,
  Download,
  Share,
  Timeline,
  BarChart,
  PieChart,
  ShowChart
} from '@mui/icons-material';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';

// Mock data for demonstration
const mockAnalytics = {
  productivity: {
    current: 78,
    previous: 65,
    trend: 'up',
    insights: [
      'Your productivity has improved by 20% this week',
      'You\'re most productive between 9-11 AM',
      'Deep work sessions are your most effective time blocks'
    ]
  },
  focus: {
    current: 85,
    previous: 72,
    trend: 'up',
    insights: [
      'Focus time has increased by 18%',
      'You complete 3x more tasks during focus mode',
      'Morning focus sessions are most successful'
    ]
  },
  habits: {
    current: 92,
    previous: 88,
    trend: 'up',
    insights: [
      'You\'ve maintained 92% habit consistency',
      'Exercise habit is your strongest',
      'Reading habit needs attention'
    ]
  },
  goals: {
    current: 45,
    previous: 40,
    trend: 'up',
    insights: [
      'You\'re 45% through your quarterly goals',
      'Academic goals are progressing well',
      'Business goals need more focus'
    ]
  }
};

const mockRecommendations = [
  {
    id: 1,
    type: 'productivity',
    title: 'Optimize Your Morning Routine',
    description: 'Based on your data, you\'re most productive in the morning. Consider scheduling your most important tasks between 9-11 AM.',
    priority: 'high',
    impact: 'high',
    category: 'routine'
  },
  {
    id: 2,
    type: 'focus',
    title: 'Extend Focus Sessions',
    description: 'Your focus sessions are highly effective. Try extending them from 25 to 45 minutes for even better results.',
    priority: 'medium',
    impact: 'medium',
    category: 'focus'
  },
  {
    id: 3,
    type: 'habits',
    title: 'Improve Reading Habit',
    description: 'Your reading habit has dropped to 60% consistency. Try reading for 15 minutes before bed.',
    priority: 'medium',
    impact: 'medium',
    category: 'habits'
  },
  {
    id: 4,
    type: 'goals',
    title: 'Review Business Goals',
    description: 'Your business goals are behind schedule. Consider breaking them into smaller, more manageable tasks.',
    priority: 'high',
    impact: 'high',
    category: 'goals'
  }
];

const mockTrends = [
  {
    metric: 'Daily Focus Hours',
    current: 4.2,
    previous: 3.8,
    change: '+10.5%',
    trend: 'up'
  },
  {
    metric: 'Tasks Completed',
    current: 12,
    previous: 10,
    change: '+20%',
    trend: 'up'
  },
  {
    metric: 'Habit Streak',
    current: 15,
    previous: 12,
    change: '+25%',
    trend: 'up'
  },
  {
    metric: 'Goal Progress',
    current: 45,
    previous: 40,
    change: '+12.5%',
    trend: 'up'
  }
];

const personaInsights = {
  student: {
    strengths: ['Academic focus', 'Time management', 'Goal setting'],
    areas: ['Work-life balance', 'Stress management', 'Social activities'],
    recommendations: [
      'Schedule study breaks every 45 minutes',
      'Use the Pomodoro technique for long study sessions',
      'Join study groups to improve retention'
    ]
  },
  founder: {
    strengths: ['Strategic thinking', 'Goal orientation', 'Productivity'],
    areas: ['Work-life balance', 'Team delegation', 'Personal health'],
    recommendations: [
      'Delegate more tasks to your team',
      'Schedule regular breaks to prevent burnout',
      'Focus on high-impact activities only'
    ]
  },
  neurodivergent: {
    strengths: ['Creative thinking', 'Deep focus', 'Unique perspectives'],
    areas: ['Routine consistency', 'Social interactions', 'Executive function'],
    recommendations: [
      'Create visual schedules and reminders',
      'Use noise-canceling headphones during focus time',
      'Break tasks into smaller, manageable steps'
    ]
  },
  lifestyle: {
    strengths: ['Spiritual discipline', 'Community focus', 'Balanced approach'],
    areas: ['Time management', 'Goal prioritization', 'Personal development'],
    recommendations: [
      'Integrate spiritual practices into daily routine',
      'Set aside time for community service',
      'Balance religious and worldly responsibilities'
    ]
  }
};

export default function Insights() {
  const { persona } = usePersona();
  const [activeTab, setActiveTab] = useState(0);
  const [analytics, setAnalytics] = useState(mockAnalytics);
  const [recommendations, setRecommendations] = useState(mockRecommendations);
  const [trends, setTrends] = useState(mockTrends);

  const getTrendIcon = (trend) => {
    return trend === 'up' ? <TrendingUp color="success" /> : <TrendingDown color="error" />;
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#f44336';
      case 'medium': return '#ff9800';
      case 'low': return '#4caf50';
      default: return '#757575';
    }
  };

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'high': return '#2196f3';
      case 'medium': return '#ff9800';
      case 'low': return '#4caf50';
      default: return '#757575';
    }
  };

  const personaData = persona ? personaInsights[persona.id] : null;

  return (
    <Layout>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h4" component="h1">
              Insights & Analytics
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
              >
                Refresh Data
              </Button>
              <Button
                variant="outlined"
                startIcon={<Download />}
              >
                Export Report
              </Button>
            </Box>
          </Box>

          {/* Key Metrics */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            {Object.entries(analytics).map(([key, data]) => (
              <Grid item xs={12} sm={6} md={3} key={key}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="h6" sx={{ textTransform: 'capitalize' }}>
                        {key}
                      </Typography>
                      {getTrendIcon(data.trend)}
                    </Box>
                    <Typography variant="h4" color="primary">
                      {data.current}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      vs {data.previous}% last week
                    </Typography>
                    <LinearProgress 
                      variant="determinate" 
                      value={data.current} 
                      sx={{ mt: 1, height: 6, borderRadius: 3 }}
                    />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Tabs */}
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
            <Tab label="Overview" />
            <Tab label="Recommendations" />
            <Tab label="Trends" />
            <Tab label="Persona Insights" />
          </Tabs>
        </Box>

        {/* Content */}
        {activeTab === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Weekly Performance Overview
                  </Typography>
                  <Grid container spacing={2}>
                    {trends.map((trend) => (
                      <Grid item xs={12} sm={6} key={trend.metric}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, border: '1px solid #e0e0e0', borderRadius: 1 }}>
                          <Box>
                            <Typography variant="body2" color="text.secondary">
                              {trend.metric}
                            </Typography>
                            <Typography variant="h6">
                              {trend.current}
                            </Typography>
                          </Box>
                          <Box sx={{ textAlign: 'right' }}>
                            {getTrendIcon(trend.trend)}
                            <Typography variant="body2" color={trend.trend === 'up' ? 'success.main' : 'error.main'}>
                              {trend.change}
                            </Typography>
                          </Box>
                        </Box>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Key Insights
                  </Typography>
                  <List>
                    {Object.entries(analytics).map(([key, data]) => (
                      <React.Fragment key={key}>
                        <ListItem>
                          <ListItemIcon>
                            <Psychology color="primary" />
                          </ListItemIcon>
                          <ListItemText 
                            primary={data.insights[0]}
                            secondary={`${key.charAt(0).toUpperCase() + key.slice(1)} performance`}
                          />
                        </ListItem>
                        {data.insights.slice(1).map((insight, index) => (
                          <ListItem key={`${key}-${index}`} sx={{ pl: 4 }}>
                            <ListItemText primary={insight} />
                          </ListItem>
                        ))}
                        <Divider />
                      </React.Fragment>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={4}>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Quick Actions
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Button variant="outlined" fullWidth startIcon={<Schedule />}>
                      Schedule Review
                    </Button>
                    <Button variant="outlined" fullWidth startIcon={<Analytics />}>
                      Detailed Report
                    </Button>
                    <Button variant="outlined" fullWidth startIcon={<Share />}>
                      Share Insights
                    </Button>
                  </Box>
                </CardContent>
              </Card>

              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Score
                  </Typography>
                  <Box sx={{ textAlign: 'center', mb: 2 }}>
                    <Typography variant="h3" color="primary">
                      85
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Overall Score
                    </Typography>
                  </Box>
                  <LinearProgress 
                    variant="determinate" 
                    value={85} 
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                  <Typography variant="body2" sx={{ mt: 1, textAlign: 'center' }}>
                    Excellent performance this week!
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {activeTab === 1 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Typography variant="h6" gutterBottom>
                AI-Powered Recommendations
              </Typography>
              {recommendations.map((rec) => (
                <Card key={rec.id} sx={{ mb: 2 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" gutterBottom>
                          {rec.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                          {rec.description}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1 }}>
                          <Chip 
                            label={`Priority: ${rec.priority}`} 
                            size="small"
                            sx={{ backgroundColor: getPriorityColor(rec.priority), color: 'white' }}
                          />
                          <Chip 
                            label={`Impact: ${rec.impact}`} 
                            size="small"
                            sx={{ backgroundColor: getImpactColor(rec.impact), color: 'white' }}
                          />
                          <Chip label={rec.category} size="small" />
                        </Box>
                      </Box>
                      <IconButton>
                        <Lightbulb color="primary" />
                      </IconButton>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Button size="small" variant="outlined">
                        Apply
                      </Button>
                      <Button size="small" variant="outlined">
                        Dismiss
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Grid>

            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Recommendation Summary
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="High Priority"
                        secondary={`${recommendations.filter(r => r.priority === 'high').length} recommendations`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="High Impact"
                        secondary={`${recommendations.filter(r => r.impact === 'high').length} recommendations`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Applied"
                        secondary="3 recommendations"
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {activeTab === 2 && (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Trends
                  </Typography>
                  <Grid container spacing={2}>
                    {trends.map((trend) => (
                      <Grid item xs={12} sm={6} md={3} key={trend.metric}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="primary">
                            {trend.current}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {trend.metric}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                            {getTrendIcon(trend.trend)}
                            <Typography variant="body2" color={trend.trend === 'up' ? 'success.main' : 'error.main'}>
                              {trend.change}
                            </Typography>
                          </Box>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {activeTab === 3 && personaData && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Your Strengths
                  </Typography>
                  <List>
                    {personaData.strengths.map((strength, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckCircle color="success" />
                        </ListItemIcon>
                        <ListItemText primary={strength} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Areas for Improvement
                  </Typography>
                  <List>
                    {personaData.areas.map((area, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Warning color="warning" />
                        </ListItemIcon>
                        <ListItemText primary={area} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Personalized Recommendations
                  </Typography>
                  <List>
                    {personaData.recommendations.map((rec, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Lightbulb color="primary" />
                        </ListItemIcon>
                        <ListItemText primary={rec} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}
      </Container>
    </Layout>
  );
} 