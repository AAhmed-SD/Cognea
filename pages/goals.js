import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Avatar,
  Paper,
  Alert,
  Tabs,
  Tab,
  Fab,
  Tooltip,
  Switch,
  FormControlLabel,
  Slider,
  Badge,
  Rating,
  DialogContentText,
  Snackbar,
  CircularProgress,
  CardActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Timeline,
  TimelineItem,
  TimelineSeparator,
  TimelineConnector,
  TimelineContent,
  TimelineDot,
  TimelineOppositeContent,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Checkbox,
  FormGroup,
  Autocomplete,
  ListItemIcon,
  ListItemButton
} from '@mui/material';
import {
  Add,
  Edit,
  Delete,
  CheckCircle,
  Psychology,
  Timer,
  TrendingUp,
  CalendarToday,
  EmojiEvents,
  Star,
  Schedule,
  Assignment,
  LocalFireDepartment,
  Notifications,
  MoreVert,
  PlayArrow,
  Pause,
  Stop,
  ExpandMore,
  SentimentSatisfied,
  SentimentNeutral,
  SentimentDissatisfied,
  TrendingDown,
  CalendarMonth,
  BarChart,
  Refresh,
  FilterList,
  Sort,
  ViewList,
  ViewModule,
  PriorityHigh,
  Flag,
  AccessTime,
  Person,
  Label,
  ExpandLess,
  ExpandMore as ExpandMoreIcon,
  AddCircle,
  RemoveCircle,
  Update,
  Visibility,
  VisibilityOff
} from '@mui/icons-material';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';
import apiService from '../services/api';

export default function Goals() {
  const { persona } = usePersona();
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [openMilestoneDialog, setOpenMilestoneDialog] = useState(false);
  const [editingGoal, setEditingGoal] = useState(null);
  const [selectedGoal, setSelectedGoal] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' });
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    category: ''
  });
  const [sortBy, setSortBy] = useState('target_date');
  const [sortOrder, setSortOrder] = useState('asc');
  const [expandedGoals, setExpandedGoals] = useState(new Set());

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'personal',
    priority: 'medium',
    target_date: '',
    progress: 0,
    status: 'in-progress',
    milestones: []
  });

  const [milestoneData, setMilestoneData] = useState({
    title: '',
    description: '',
    target_date: '',
    completed: false
  });

  // Load goals on component mount
  useEffect(() => {
    loadGoals();
  }, [filters, sortBy, sortOrder]);

  const loadGoals = async () => {
    try {
      setLoading(true);
      const params = {
        ...filters,
        sort_by: sortBy,
        sort_order: sortOrder
      };
      const data = await apiService.getGoals(params);
      setGoals(data);
    } catch (error) {
      console.error('Failed to load goals:', error);
      // Fallback to mock data
      setGoals(apiService.getMockData('goals'));
    } finally {
      setLoading(false);
    }
  };

  const handleAddGoal = () => {
    setEditingGoal(null);
    setFormData({
      title: '',
      description: '',
      category: 'personal',
      priority: 'medium',
      target_date: '',
      progress: 0,
      status: 'in-progress',
      milestones: []
    });
    setOpenDialog(true);
  };

  const handleEditGoal = (goal) => {
    setEditingGoal(goal);
    setFormData({
      title: goal.title,
      description: goal.description || '',
      category: goal.category,
      priority: goal.priority,
      target_date: goal.target_date || '',
      progress: goal.progress || 0,
      status: goal.status,
      milestones: goal.milestones || []
    });
    setOpenDialog(true);
  };

  const handleSaveGoal = async () => {
    try {
      if (editingGoal) {
        await apiService.updateGoal(editingGoal.id, formData);
        setGoals(goals.map(g => g.id === editingGoal.id ? { ...g, ...formData } : g));
        showSnackbar('Goal updated successfully!', 'success');
      } else {
        const newGoal = await apiService.createGoal(formData);
        setGoals([...goals, newGoal]);
        showSnackbar('Goal created successfully!', 'success');
      }
      setOpenDialog(false);
    } catch (error) {
      console.error('Failed to save goal:', error);
      showSnackbar('Failed to save goal. Please try again.', 'error');
    }
  };

  const handleDeleteGoal = async (goalId) => {
    if (window.confirm('Are you sure you want to delete this goal?')) {
      try {
        await apiService.deleteGoal(goalId);
        setGoals(goals.filter(g => g.id !== goalId));
        showSnackbar('Goal deleted successfully!', 'success');
      } catch (error) {
        console.error('Failed to delete goal:', error);
        showSnackbar('Failed to delete goal. Please try again.', 'error');
      }
    }
  };

  const handleUpdateProgress = async (goalId, progress) => {
    try {
      await apiService.updateGoalProgress(goalId, progress);
      setGoals(goals.map(g => g.id === goalId ? { ...g, progress } : g));
      showSnackbar('Progress updated successfully!', 'success');
    } catch (error) {
      console.error('Failed to update progress:', error);
      showSnackbar('Failed to update progress. Please try again.', 'error');
    }
  };

  const handleToggleGoalExpansion = (goalId) => {
    const newExpanded = new Set(expandedGoals);
    if (newExpanded.has(goalId)) {
      newExpanded.delete(goalId);
    } else {
      newExpanded.add(goalId);
    }
    setExpandedGoals(newExpanded);
  };

  const handleAddMilestone = (goal) => {
    setSelectedGoal(goal);
    setMilestoneData({
      title: '',
      description: '',
      target_date: '',
      completed: false
    });
    setOpenMilestoneDialog(true);
  };

  const handleSaveMilestone = () => {
    if (!milestoneData.title.trim()) {
      showSnackbar('Milestone title is required.', 'error');
      return;
    }

    const newMilestone = {
      id: Date.now(),
      ...milestoneData
    };

    const updatedGoal = {
      ...selectedGoal,
      milestones: [...(selectedGoal.milestones || []), newMilestone]
    };

    setGoals(goals.map(g => g.id === selectedGoal.id ? updatedGoal : g));
    setOpenMilestoneDialog(false);
    showSnackbar('Milestone added successfully!', 'success');
  };

  const handleToggleMilestone = (goalId, milestoneId) => {
    const goal = goals.find(g => g.id === goalId);
    const updatedMilestones = goal.milestones.map(m => 
      m.id === milestoneId ? { ...m, completed: !m.completed } : m
    );

    const completedCount = updatedMilestones.filter(m => m.completed).length;
    const totalCount = updatedMilestones.length;
    const newProgress = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

    const updatedGoal = {
      ...goal,
      milestones: updatedMilestones,
      progress: newProgress
    };

    setGoals(goals.map(g => g.id === goalId ? updatedGoal : g));
    handleUpdateProgress(goalId, newProgress);
  };

  const handleDeleteMilestone = (goalId, milestoneId) => {
    const goal = goals.find(g => g.id === goalId);
    const updatedMilestones = goal.milestones.filter(m => m.id !== milestoneId);

    const completedCount = updatedMilestones.filter(m => m.completed).length;
    const totalCount = updatedMilestones.length;
    const newProgress = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

    const updatedGoal = {
      ...goal,
      milestones: updatedMilestones,
      progress: newProgress
    };

    setGoals(goals.map(g => g.id === goalId ? updatedGoal : g));
    handleUpdateProgress(goalId, newProgress);
    showSnackbar('Milestone deleted successfully!', 'success');
  };

  const showSnackbar = (message, severity = 'success') => {
    setSnackbar({ open: true, message, severity });
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return '#f44336';
      case 'medium': return '#ff9800';
      case 'low': return '#4caf50';
      default: return '#757575';
    }
  };

  const getPriorityIcon = (priority) => {
    switch (priority) {
      case 'high': return <PriorityHigh />;
      case 'medium': return <Star />;
      case 'low': return <Flag />;
      default: return <Star />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#4caf50';
      case 'in-progress': return '#2196f3';
      case 'pending': return '#ff9800';
      case 'overdue': return '#f44336';
      default: return '#757575';
    }
  };

  const getCategoryColor = (category) => {
    const categoryConfig = goalCategories.find(c => c.value === category);
    return categoryConfig ? categoryConfig.color : '#757575';
  };

  const getCategoryLabel = (category) => {
    const categoryConfig = goalCategories.find(c => c.value === category);
    return categoryConfig ? categoryConfig.label : category;
  };

  const getDaysUntilTarget = (targetDate) => {
    if (!targetDate) return null;
    const today = new Date();
    const target = new Date(targetDate);
    const diffTime = target - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getTargetDateColor = (targetDate) => {
    const daysUntil = getDaysUntilTarget(targetDate);
    if (daysUntil === null) return '#757575';
    if (daysUntil < 0) return '#f44336';
    if (daysUntil <= 30) return '#ff9800';
    if (daysUntil <= 90) return '#ffc107';
    return '#4caf50';
  };

  const goalCategories = [
    { value: 'personal', label: 'Personal', color: '#4caf50' },
    { value: 'career', label: 'Career', color: '#2196f3' },
    { value: 'health', label: 'Health', color: '#ff9800' },
    { value: 'learning', label: 'Learning', color: '#9c27b0' },
    { value: 'finance', label: 'Finance', color: '#607d8b' },
    { value: 'relationships', label: 'Relationships', color: '#e91e63' }
  ];

  const priorityLevels = [
    { value: 'low', label: 'Low', color: '#4caf50' },
    { value: 'medium', label: 'Medium', color: '#ff9800' },
    { value: 'high', label: 'High', color: '#f44336' }
  ];

  const statusOptions = [
    { value: 'pending', label: 'Pending', color: '#ff9800' },
    { value: 'in-progress', label: 'In Progress', color: '#2196f3' },
    { value: 'completed', label: 'Completed', color: '#4caf50' },
    { value: 'overdue', label: 'Overdue', color: '#f44336' }
  ];

  const filteredGoals = goals.filter(goal => {
    if (activeTab === 1 && goal.status !== 'pending') return false;
    if (activeTab === 2 && goal.status !== 'in-progress') return false;
    if (activeTab === 3 && goal.status !== 'completed') return false;
    if (activeTab === 4 && getDaysUntilTarget(goal.target_date) >= 0) return false;
    return true;
  });

  if (loading) {
    return (
      <Layout>
        <Container maxWidth="xl" sx={{ py: 3 }}>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress />
          </Box>
        </Container>
      </Layout>
    );
  }

  return (
    <Layout>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h4" component="h1">
              Goals & Aspirations
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<Refresh />}
                onClick={loadGoals}
              >
                Refresh
              </Button>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleAddGoal}
              >
                Add Goal
              </Button>
            </Box>
          </Box>

          {/* Stats Overview */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Total Goals
                  </Typography>
                  <Typography variant="h4">
                    {goals.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    In Progress
                  </Typography>
                  <Typography variant="h4" color="info.main">
                    {goals.filter(g => g.status === 'in-progress').length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Completed
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {goals.filter(g => g.status === 'completed').length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Typography color="textSecondary" gutterBottom>
                    Avg Progress
                  </Typography>
                  <Typography variant="h4">
                    {goals.length > 0 ? Math.round(goals.reduce((sum, g) => sum + (g.progress || 0), 0) / goals.length) : 0}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>

        {/* Filters */}
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Status</InputLabel>
                  <Select
                    value={filters.status}
                    onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                    label="Status"
                  >
                    <MenuItem value="">All</MenuItem>
                    {statusOptions.map((status) => (
                      <MenuItem key={status.value} value={status.value}>
                        {status.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={filters.priority}
                    onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
                    label="Priority"
                  >
                    <MenuItem value="">All</MenuItem>
                    {priorityLevels.map((priority) => (
                      <MenuItem key={priority.value} value={priority.value}>
                        {priority.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={4}>
                <FormControl fullWidth size="small">
                  <InputLabel>Category</InputLabel>
                  <Select
                    value={filters.category}
                    onChange={(e) => setFilters({ ...filters, category: e.target.value })}
                    label="Category"
                  >
                    <MenuItem value="">All</MenuItem>
                    {goalCategories.map((category) => (
                      <MenuItem key={category.value} value={category.value}>
                        {category.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>

        {/* Main Content */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)}>
            <Tab label="All Goals" />
            <Tab label="Pending" />
            <Tab label="In Progress" />
            <Tab label="Completed" />
            <Tab label="Overdue" />
          </Tabs>
        </Box>

        {/* Goals Display */}
        <Grid container spacing={3}>
          {filteredGoals.map((goal) => (
            <Grid item xs={12} key={goal.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Box sx={{ flexGrow: 1 }}>
                      <Typography variant="h6" gutterBottom>
                        {goal.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                        {goal.description}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <IconButton size="small" onClick={() => handleEditGoal(goal)}>
                        <Edit />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDeleteGoal(goal.id)}>
                        <Delete />
                      </IconButton>
                      <IconButton 
                        size="small" 
                        onClick={() => handleToggleGoalExpansion(goal.id)}
                      >
                        {expandedGoals.has(goal.id) ? <ExpandLess /> : <ExpandMoreIcon />}
                      </IconButton>
                    </Box>
                  </Box>

                  <Box sx={{ display: 'flex', gap: 1, mb: 2, flexWrap: 'wrap' }}>
                    <Chip
                      icon={getPriorityIcon(goal.priority)}
                      label={goal.priority}
                      size="small"
                      sx={{ color: getPriorityColor(goal.priority) }}
                      variant="outlined"
                    />
                    <Chip
                      label={getCategoryLabel(goal.category)}
                      size="small"
                      sx={{ backgroundColor: getCategoryColor(goal.category), color: 'white' }}
                    />
                    <Chip
                      label={goal.status}
                      size="small"
                      sx={{ backgroundColor: getStatusColor(goal.status), color: 'white' }}
                    />
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                      <Typography variant="body2" color="text.secondary">
                        Progress: {goal.progress || 0}%
                      </Typography>
                      <Typography 
                        variant="body2" 
                        sx={{ color: getTargetDateColor(goal.target_date) }}
                      >
                        {goal.target_date ? new Date(goal.target_date).toLocaleDateString() : 'No target date'}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={goal.progress || 0}
                      sx={{ height: 8, borderRadius: 4 }}
                      color={goal.progress >= 100 ? 'success' : 'primary'}
                    />
                  </Box>

                  {/* Progress Slider */}
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Update Progress
                    </Typography>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Slider
                        value={goal.progress || 0}
                        onChange={(e, value) => handleUpdateProgress(goal.id, value)}
                        min={0}
                        max={100}
                        marks
                        valueLabelDisplay="auto"
                        sx={{ flexGrow: 1 }}
                      />
                      <Typography variant="body2" sx={{ minWidth: 40 }}>
                        {goal.progress || 0}%
                      </Typography>
                    </Box>
                  </Box>

                  {/* Expanded Content */}
                  {expandedGoals.has(goal.id) && (
                    <Box sx={{ mt: 3 }}>
                      <Divider sx={{ mb: 2 }} />
                      
                      {/* Milestones */}
                      <Box sx={{ mb: 3 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6">
                            Milestones
                          </Typography>
                          <Button
                            size="small"
                            startIcon={<AddCircle />}
                            onClick={() => handleAddMilestone(goal)}
                          >
                            Add Milestone
                          </Button>
                        </Box>
                        
                        {goal.milestones && goal.milestones.length > 0 ? (
                          <List dense>
                            {goal.milestones.map((milestone) => (
                              <ListItem key={milestone.id} disablePadding>
                                <ListItemButton>
                                  <ListItemIcon>
                                    <Checkbox
                                      checked={milestone.completed}
                                      onChange={() => handleToggleMilestone(goal.id, milestone.id)}
                                    />
                                  </ListItemIcon>
                                  <ListItemText
                                    primary={
                                      <Typography
                                        variant="body2"
                                        sx={{
                                          textDecoration: milestone.completed ? 'line-through' : 'none',
                                          color: milestone.completed ? 'text.secondary' : 'text.primary'
                                        }}
                                      >
                                        {milestone.title}
                                      </Typography>
                                    }
                                    secondary={
                                      <Box>
                                        <Typography variant="caption" color="text.secondary">
                                          {milestone.description}
                                        </Typography>
                                        {milestone.target_date && (
                                          <Typography variant="caption" color="text.secondary" display="block">
                                            Due: {new Date(milestone.target_date).toLocaleDateString()}
                                          </Typography>
                                        )}
                                      </Box>
                                    }
                                  />
                                  <ListItemSecondaryAction>
                                    <IconButton
                                      size="small"
                                      onClick={() => handleDeleteMilestone(goal.id, milestone.id)}
                                    >
                                      <Delete />
                                    </IconButton>
                                  </ListItemSecondaryAction>
                                </ListItemButton>
                              </ListItem>
                            ))}
                          </List>
                        ) : (
                          <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                            No milestones added yet. Click "Add Milestone" to get started.
                          </Typography>
                        )}
                      </Box>

                      {/* Timeline View */}
                      <Box>
                        <Typography variant="h6" gutterBottom>
                          Timeline
                        </Typography>
                        <Timeline>
                          {goal.milestones && goal.milestones.map((milestone, index) => (
                            <TimelineItem key={milestone.id}>
                              <TimelineSeparator>
                                <TimelineDot color={milestone.completed ? 'success' : 'primary'} />
                                {index < goal.milestones.length - 1 && <TimelineConnector />}
                              </TimelineSeparator>
                              <TimelineContent>
                                <Typography variant="body2" component="span">
                                  {milestone.title}
                                </Typography>
                                <Typography variant="caption" color="text.secondary" display="block">
                                  {milestone.target_date && new Date(milestone.target_date).toLocaleDateString()}
                                </Typography>
                              </TimelineContent>
                            </TimelineItem>
                          ))}
                        </Timeline>
                      </Box>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Add/Edit Goal Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            {editingGoal ? 'Edit Goal' : 'Add New Goal'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Goal Title"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                fullWidth
                required
              />
              <TextField
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                multiline
                rows={3}
                fullWidth
              />
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Category</InputLabel>
                    <Select
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      label="Category"
                    >
                      {goalCategories.map((category) => (
                        <MenuItem key={category.value} value={category.value}>
                          {category.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Priority</InputLabel>
                    <Select
                      value={formData.priority}
                      onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                      label="Priority"
                    >
                      {priorityLevels.map((priority) => (
                        <MenuItem key={priority.value} value={priority.value}>
                          {priority.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    label="Target Date"
                    type="date"
                    value={formData.target_date}
                    onChange={(e) => setFormData({ ...formData, target_date: e.target.value })}
                    fullWidth
                    InputLabelProps={{ shrink: true }}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <FormControl fullWidth>
                    <InputLabel>Status</InputLabel>
                    <Select
                      value={formData.status}
                      onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                      label="Status"
                    >
                      {statusOptions.map((status) => (
                        <MenuItem key={status.value} value={status.value}>
                          {status.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <Typography gutterBottom>Initial Progress</Typography>
                  <Slider
                    value={formData.progress}
                    onChange={(e, value) => setFormData({ ...formData, progress: value })}
                    min={0}
                    max={100}
                    marks
                    valueLabelDisplay="auto"
                  />
                </Grid>
              </Grid>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveGoal} variant="contained">
              {editingGoal ? 'Update' : 'Create'} Goal
            </Button>
          </DialogActions>
        </Dialog>

        {/* Add Milestone Dialog */}
        <Dialog open={openMilestoneDialog} onClose={() => setOpenMilestoneDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            Add Milestone to: {selectedGoal?.title}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Milestone Title"
                value={milestoneData.title}
                onChange={(e) => setMilestoneData({ ...milestoneData, title: e.target.value })}
                fullWidth
                required
              />
              <TextField
                label="Description"
                value={milestoneData.description}
                onChange={(e) => setMilestoneData({ ...milestoneData, description: e.target.value })}
                multiline
                rows={2}
                fullWidth
              />
              <TextField
                label="Target Date"
                type="date"
                value={milestoneData.target_date}
                onChange={(e) => setMilestoneData({ ...milestoneData, target_date: e.target.value })}
                fullWidth
                InputLabelProps={{ shrink: true }}
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenMilestoneDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveMilestone} variant="contained">
              Add Milestone
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert
            onClose={() => setSnackbar({ ...snackbar, open: false })}
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </Layout>
  );
} 