import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Tabs,
  Tab,
  Chip,
  IconButton,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Alert,
  Tooltip,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  Analytics,
  TrendingUp,
  TrendingDown,
  Timer,
  CheckCircle,
  EmojiEvents,
  Star,
  CalendarToday,
  BarChart,
  PieChart,
  ShowChart,
  Refresh,
  Download,
  FilterList,
  Settings,
  Psychology,
  School,
  Work,
  FitnessCenter,
  Favorite,
  LocalFireDepartment,
  Schedule,
  Assignment,
  Notifications,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';

// Mock data for analytics
const mockAnalyticsData = {
  productivity: {
    daily: [85, 92, 78, 95, 88, 91, 87],
    weekly: [89, 91, 85, 93, 88, 90, 92],
    monthly: [87, 89, 91, 88, 90, 92, 89, 91, 88, 90, 92, 89]
  },
  focusTime: {
    daily: [120, 180, 90, 240, 150, 200, 160],
    weekly: [140, 160, 180, 150, 200, 170, 190],
    monthly: [150, 170, 160, 180, 190, 170, 180, 160, 190, 170, 180, 190]
  },
  completedTasks: {
    daily: [8, 12, 6, 15, 10, 13, 9],
    weekly: [10, 12, 8, 14, 11, 13, 12],
    monthly: [11, 12, 10, 13, 12, 14, 11, 13, 12, 14, 11, 13]
  },
  habits: {
    daily: [5, 7, 4, 8, 6, 7, 5],
    weekly: [6, 7, 5, 8, 6, 7, 8],
    monthly: [6, 7, 6, 8, 7, 8, 6, 7, 8, 7, 6, 8]
  }
};

const insights = [
  {
    id: 1,
    type: 'positive',
    title: 'Productivity Peak',
    description: 'Your productivity is highest between 9-11 AM. Consider scheduling important tasks during this time.',
    icon: <TrendingUp />,
    impact: 'high'
  },
  {
    id: 2,
    type: 'warning',
    title: 'Focus Interruptions',
    description: 'You experience more interruptions on Wednesdays. Consider blocking time for deep work.',
    icon: <Notifications />,
    impact: 'medium'
  },
  {
    id: 3,
    type: 'positive',
    title: 'Habit Consistency',
    description: 'Your morning routine has a 95% completion rate. Great job maintaining consistency!',
    icon: <CheckCircle />,
    impact: 'high'
  },
  {
    id: 4,
    type: 'info',
    title: 'Learning Progress',
    description: 'You\'ve completed 12 learning sessions this month, up 20% from last month.',
    icon: <School />,
    impact: 'medium'
  }
];

const categoryBreakdown = [
  { category: 'Work', percentage: 45, color: '#2196f3', icon: <Work /> },
  { category: 'Learning', percentage: 25, color: '#4caf50', icon: <School /> },
  { category: 'Fitness', percentage: 15, color: '#ff9800', icon: <FitnessCenter /> },
  { category: 'Personal', percentage: 10, color: '#9c27b0', icon: <Favorite /> },
  { category: 'Other', percentage: 5, color: '#607d8b', icon: <Psychology /> }
];

const timeDistribution = [
  { time: '6-9 AM', tasks: 15, focus: 180, productivity: 92 },
  { time: '9-12 PM', tasks: 25, focus: 240, productivity: 95 },
  { time: '12-3 PM', tasks: 20, focus: 160, productivity: 78 },
  { time: '3-6 PM', tasks: 18, focus: 140, productivity: 85 },
  { time: '6-9 PM', tasks: 12, focus: 120, productivity: 88 },
  { time: '9-12 AM', tasks: 8, focus: 60, productivity: 75 }
];

export default function AnalyticsPage() {
  const { persona } = usePersona();
  const [activeTab, setActiveTab] = useState(0);
  const [timeRange, setTimeRange] = useState('weekly');
  const [showInsights, setShowInsights] = useState(true);
  const [dataVisibility, setDataVisibility] = useState({
    productivity: true,
    focusTime: true,
    completedTasks: true,
    habits: true
  });

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getInsightColor = (type) => {
    switch (type) {
      case 'positive': return 'success';
      case 'warning': return 'warning';
      case 'info': return 'info';
      default: return 'default';
    }
  };

  const getImpactColor = (impact) => {
    switch (impact) {
      case 'high': return '#4caf50';
      case 'medium': return '#ff9800';
      case 'low': return '#f44336';
      default: return '#757575';
    }
  };

  const calculateTrend = (data) => {
    if (data.length < 2) return 0;
    const recent = data.slice(-3).reduce((a, b) => a + b, 0) / 3;
    const previous = data.slice(-6, -3).reduce((a, b) => a + b, 0) / 3;
    return ((recent - previous) / previous) * 100;
  };

  const getCurrentData = () => {
    return {
      productivity: mockAnalyticsData.productivity[timeRange],
      focusTime: mockAnalyticsData.focusTime[timeRange],
      completedTasks: mockAnalyticsData.completedTasks[timeRange],
      habits: mockAnalyticsData.habits[timeRange]
    };
  };

  const currentData = getCurrentData();

  return (
    <Layout>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <Analytics sx={{ fontSize: 32, color: 'primary.main', mr: 2 }} />
            <Typography variant="h4" component="h1">
              Analytics & Insights
            </Typography>
          </Box>
          <Typography variant="body1" color="text.secondary">
            Track your productivity metrics, analyze patterns, and gain insights into your performance.
            {persona && ` Tailored for ${persona.title} persona.`}
          </Typography>
        </Box>

        {/* Controls */}
        <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="daily">Daily</MenuItem>
              <MenuItem value="weekly">Weekly</MenuItem>
              <MenuItem value="monthly">Monthly</MenuItem>
            </Select>
          </FormControl>
          
          <FormControlLabel
            control={
              <Switch
                checked={showInsights}
                onChange={(e) => setShowInsights(e.target.checked)}
              />
            }
            label="Show Insights"
          />
          
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            size="small"
          >
            Refresh Data
          </Button>
          
          <Button
            variant="outlined"
            startIcon={<Download />}
            size="small"
          >
            Export Report
          </Button>
        </Box>

        {/* Main Content */}
        <Grid container spacing={3}>
          {/* Key Metrics */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Key Metrics
                </Typography>
                <Grid container spacing={3}>
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary" gutterBottom>
                        {Math.round(currentData.productivity.reduce((a, b) => a + b, 0) / currentData.productivity.length)}%
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Average Productivity
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 1 }}>
                        {calculateTrend(currentData.productivity) > 0 ? (
                          <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                        ) : (
                          <TrendingDown sx={{ color: 'error.main', fontSize: 16, mr: 0.5 }} />
                        )}
                        <Typography variant="caption" color={calculateTrend(currentData.productivity) > 0 ? 'success.main' : 'error.main'}>
                          {Math.abs(calculateTrend(currentData.productivity)).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary" gutterBottom>
                        {Math.round(currentData.focusTime.reduce((a, b) => a + b, 0) / currentData.focusTime.length)}m
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Average Focus Time
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 1 }}>
                        {calculateTrend(currentData.focusTime) > 0 ? (
                          <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                        ) : (
                          <TrendingDown sx={{ color: 'error.main', fontSize: 16, mr: 0.5 }} />
                        )}
                        <Typography variant="caption" color={calculateTrend(currentData.focusTime) > 0 ? 'success.main' : 'error.main'}>
                          {Math.abs(calculateTrend(currentData.focusTime)).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary" gutterBottom>
                        {Math.round(currentData.completedTasks.reduce((a, b) => a + b, 0) / currentData.completedTasks.length)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Tasks Completed
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 1 }}>
                        {calculateTrend(currentData.completedTasks) > 0 ? (
                          <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                        ) : (
                          <TrendingDown sx={{ color: 'error.main', fontSize: 16, mr: 0.5 }} />
                        )}
                        <Typography variant="caption" color={calculateTrend(currentData.completedTasks) > 0 ? 'success.main' : 'error.main'}>
                          {Math.abs(calculateTrend(currentData.completedTasks)).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                  
                  <Grid item xs={12} sm={6} md={3}>
                    <Box sx={{ textAlign: 'center' }}>
                      <Typography variant="h4" color="primary" gutterBottom>
                        {Math.round(currentData.habits.reduce((a, b) => a + b, 0) / currentData.habits.length)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Avg Habits Completed
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', mt: 1 }}>
                        {calculateTrend(currentData.habits) > 0 ? (
                          <TrendingUp sx={{ color: 'success.main', fontSize: 16, mr: 0.5 }} />
                        ) : (
                          <TrendingDown sx={{ color: 'error.main', fontSize: 16, mr: 0.5 }} />
                        )}
                        <Typography variant="caption" color={calculateTrend(currentData.habits) > 0 ? 'success.main' : 'error.main'}>
                          {Math.abs(calculateTrend(currentData.habits)).toFixed(1)}%
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          {/* Tabs */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
                  <Tab label="Overview" />
                  <Tab label="Time Analysis" />
                  <Tab label="Category Breakdown" />
                  <Tab label="Insights" />
                </Tabs>

                {/* Overview Tab */}
                {activeTab === 0 && (
                  <Grid container spacing={3}>
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2, height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Box sx={{ textAlign: 'center' }}>
                          <BarChart sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                          <Typography variant="h6" gutterBottom>
                            Productivity Trends
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Chart showing productivity over time
                          </Typography>
                        </Box>
                      </Paper>
                    </Grid>
                    
                    <Grid item xs={12} md={6}>
                      <Paper sx={{ p: 2, height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        <Box sx={{ textAlign: 'center' }}>
                          <PieChart sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
                          <Typography variant="h6" gutterBottom>
                            Activity Distribution
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            Pie chart showing activity breakdown
                          </Typography>
                        </Box>
                      </Paper>
                    </Grid>
                  </Grid>
                )}

                {/* Time Analysis Tab */}
                {activeTab === 1 && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Time Distribution Analysis
                    </Typography>
                    <Grid container spacing={2}>
                      {timeDistribution.map((item, index) => (
                        <Grid item xs={12} sm={6} md={4} key={index}>
                          <Card variant="outlined">
                            <CardContent>
                              <Typography variant="subtitle2" gutterBottom>
                                {item.time}
                              </Typography>
                              <Box sx={{ mb: 1 }}>
                                <Typography variant="body2" color="text.secondary">
                                  Tasks: {item.tasks}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  Focus: {item.focus}m
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  Productivity: {item.productivity}%
                                </Typography>
                              </Box>
                              <LinearProgress 
                                variant="determinate" 
                                value={item.productivity} 
                                sx={{ height: 8, borderRadius: 4 }}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}

                {/* Category Breakdown Tab */}
                {activeTab === 2 && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Category Breakdown
                    </Typography>
                    <Grid container spacing={2}>
                      {categoryBreakdown.map((item, index) => (
                        <Grid item xs={12} sm={6} md={4} key={index}>
                          <Card variant="outlined">
                            <CardContent>
                              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                                <Box sx={{ color: item.color, mr: 1 }}>
                                  {item.icon}
                                </Box>
                                <Typography variant="subtitle1">
                                  {item.category}
                                </Typography>
                              </Box>
                              <Typography variant="h4" color="primary" gutterBottom>
                                {item.percentage}%
                              </Typography>
                              <LinearProgress 
                                variant="determinate" 
                                value={item.percentage} 
                                sx={{ 
                                  height: 8, 
                                  borderRadius: 4,
                                  backgroundColor: 'rgba(0,0,0,0.1)',
                                  '& .MuiLinearProgress-bar': {
                                    backgroundColor: item.color
                                  }
                                }}
                              />
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}

                {/* Insights Tab */}
                {activeTab === 3 && showInsights && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      AI-Powered Insights
                    </Typography>
                    <Grid container spacing={2}>
                      {insights.map((insight) => (
                        <Grid item xs={12} md={6} key={insight.id}>
                          <Alert 
                            severity={getInsightColor(insight.type)}
                            icon={insight.icon}
                            sx={{ 
                              '& .MuiAlert-message': { width: '100%' },
                              border: `2px solid ${getImpactColor(insight.impact)}`,
                              borderLeft: `4px solid ${getImpactColor(insight.impact)}`
                            }}
                          >
                            <Typography variant="subtitle1" gutterBottom>
                              {insight.title}
                            </Typography>
                            <Typography variant="body2">
                              {insight.description}
                            </Typography>
                            <Chip 
                              label={`${insight.impact} impact`}
                              size="small"
                              sx={{ 
                                mt: 1,
                                backgroundColor: getImpactColor(insight.impact),
                                color: 'white'
                              }}
                            />
                          </Alert>
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Layout>
  );
} 