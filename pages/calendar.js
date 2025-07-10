import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Typography,
  Card,
  CardContent,
  Grid,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Alert,
  IconButton,
  Tooltip,
  Paper,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress,
  Badge,
  Tabs,
  Tab
} from '@mui/material';
import {
  CalendarToday,
  Add,
  Edit,
  Delete,
  School,
  Schedule,
  TrendingUp,
  CheckCircle,
  Warning,
  Info,
  ExpandMore,
  Today,
  Event,
  Assignment,
  Timer,
  Psychology,
  AutoAwesome,
  SmartToy,
  Analytics,
  Notifications,
  Settings,
  ViewWeek,
  ViewDay,
  ViewMonth,
  FilterList,
  Search,
  Refresh,
  PlayArrow,
  Pause,
  Stop,
  Book,
  Quiz,
  FlashOn,
  Target,
  Timeline,
  BarChart,
  PieChart,
  Assessment,
  Lightbulb,
  Star,
  PriorityHigh,
  PriorityMedium,
  PriorityLow,
  Science,
  Nature
} from '@mui/icons-material';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider, DatePicker, TimePicker } from '@mui/x-date-pickers';
import { format, addDays, startOfWeek, endOfWeek, eachDayOfInterval, isSameDay, parseISO } from 'date-fns';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';

const Calendar = () => {
  const { persona } = usePersona();
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [viewMode, setViewMode] = useState('week'); // week, day, month
  const [events, setEvents] = useState([]);
  const [studyPlans, setStudyPlans] = useState([]);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Study Plan Generation
  const [planDialog, setPlanDialog] = useState(false);
  const [planForm, setPlanForm] = useState({
    name: '',
    subjects: [],
    examDate: null,
    topics: [],
    availableHours: 4,
    learningStyle: 'visual',
    difficulty: 'medium',
    goals: []
  });

  // Event Management
  const [eventDialog, setEventDialog] = useState(false);
  const [eventForm, setEventForm] = useState({
    title: '',
    description: '',
    startTime: new Date(),
    endTime: new Date(),
    type: 'study',
    subject: '',
    topic: '',
    priority: 'medium',
    reminders: []
  });

  // Analytics
  const [analytics, setAnalytics] = useState({
    totalStudyTime: 0,
    completedSessions: 0,
    adherenceRate: 0,
    subjectsCovered: [],
    upcomingExams: [],
    recommendations: []
  });

  const subjects = [
    { name: 'Mathematics', icon: <TrendingUp />, color: '#3f51b5' },
    { name: 'Physics', icon: <FlashOn />, color: '#f50057' },
    { name: 'Chemistry', icon: <School />, color: '#4caf50' },
    { name: 'Biology', icon: <School />, color: '#8bc34a' },
    { name: 'History', icon: <Book />, color: '#ff9800' },
    { name: 'Literature', icon: <Book />, color: '#9c27b0' },
    { name: 'Computer Science', icon: <Book />, color: '#2196f3' },
    { name: 'Economics', icon: <TrendingUp />, color: '#00bcd4' }
  ];

  const eventTypes = [
    { value: 'study', label: 'Study Session', icon: <School />, color: '#3f51b5' },
    { value: 'exam', label: 'Exam', icon: <Quiz />, color: '#f44336' },
    { value: 'review', label: 'Review', icon: <Refresh />, color: '#ff9800' },
    { value: 'practice', label: 'Practice', icon: <Assignment />, color: '#4caf50' },
    { value: 'break', label: 'Break', icon: <Pause />, color: '#9e9e9e' }
  ];

  const priorityLevels = [
    { value: 'high', label: 'High', icon: <PriorityHigh />, color: '#f44336' },
    { value: 'medium', label: 'Medium', icon: <PriorityMedium />, color: '#ff9800' },
    { value: 'low', label: 'Low', icon: <PriorityLow />, color: '#4caf50' }
  ];

  useEffect(() => {
    loadCalendarData();
  }, [selectedDate, viewMode]);

  const loadCalendarData = async () => {
    setLoading(true);
    try {
      // Load events, study plans, and analytics
      // This would integrate with your backend
      setLoading(false);
    } catch (err) {
      setError('Failed to load calendar data');
      setLoading(false);
    }
  };

  const generateStudyPlan = async () => {
    setLoading(true);
    try {
      // AI-powered study plan generation
      const plan = {
        id: Date.now(),
        name: planForm.name,
        subjects: planForm.subjects,
        examDate: planForm.examDate,
        topics: planForm.topics,
        schedule: generateOptimalSchedule(),
        progress: 0,
        createdAt: new Date()
      };
      
      setStudyPlans([...studyPlans, plan]);
      setPlanDialog(false);
      setPlanForm({
        name: '',
        subjects: [],
        examDate: null,
        topics: [],
        availableHours: 4,
        learningStyle: 'visual',
        difficulty: 'medium',
        goals: []
      });
    } catch (err) {
      setError('Failed to generate study plan');
    }
    setLoading(false);
  };

  const generateOptimalSchedule = () => {
    // AI algorithm to generate optimal study schedule
    // Based on spaced repetition, learning styles, and exam dates
    const schedule = [];
    const daysUntilExam = planForm.examDate ? 
      Math.ceil((new Date(planForm.examDate) - new Date()) / (1000 * 60 * 60 * 24)) : 30;
    
    // Generate daily study blocks
    for (let day = 0; day < daysUntilExam; day++) {
      const studyDate = addDays(new Date(), day);
      const daySchedule = {
        date: studyDate,
        sessions: planForm.subjects.map((subject, index) => ({
          subject,
          topic: planForm.topics[index % planForm.topics.length],
          duration: Math.floor(planForm.availableHours / planForm.subjects.length * 60),
          startTime: new Date(studyDate.setHours(9 + index * 2)),
          type: 'study',
          priority: 'medium'
        }))
      };
      schedule.push(daySchedule);
    }
    
    return schedule;
  };

  const getWeekDays = () => {
    const start = startOfWeek(selectedDate, { weekStartsOn: 1 });
    const end = endOfWeek(selectedDate, { weekStartsOn: 1 });
    return eachDayOfInterval({ start, end });
  };

  const getEventsForDate = (date) => {
    return events.filter(event => isSameDay(parseISO(event.startTime), date));
  };

  const getSubjectColor = (subjectName) => {
    const subject = subjects.find(s => s.name === subjectName);
    return subject ? subject.color : '#9e9e9e';
  };

  const getEventTypeIcon = (type) => {
    const eventType = eventTypes.find(t => t.value === type);
    return eventType ? eventType.icon : <Event />;
  };

  return (
    <Layout>
      <LocalizationProvider dateAdapter={AdapterDateFns}>
        <Container maxWidth="xl">
          {/* Header */}
          <Box sx={{ mb: 4 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h4" component="h1">
                <CalendarToday sx={{ mr: 2, verticalAlign: 'middle' }} />
                Smart Study Calendar
              </Typography>
              <Box>
                <Button
                  variant="contained"
                  startIcon={<AutoAwesome />}
                  onClick={() => setPlanDialog(true)}
                  sx={{ mr: 2 }}
                >
                  Generate Study Plan
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<Add />}
                  onClick={() => setEventDialog(true)}
                >
                  Add Event
                </Button>
              </Box>
            </Box>
            
            <Typography variant="body1" color="text.secondary">
              AI-powered calendar that auto-generates study plans and helps you stick to them
            </Typography>
          </Box>

          {/* Tabs */}
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
            <Tab label="Calendar View" icon={<CalendarToday />} />
            <Tab label="Study Plans" icon={<School />} />
            <Tab label="Analytics" icon={<Analytics />} />
            <Tab label="AI Insights" icon={<SmartToy />} />
          </Tabs>

          {/* Calendar View Tab */}
          {activeTab === 0 && (
            <Grid container spacing={3}>
              {/* Calendar Controls */}
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Box display="flex" alignItems="center" gap={2}>
                        <Button
                          variant="outlined"
                          onClick={() => setSelectedDate(addDays(selectedDate, -7))}
                        >
                          Previous Week
                        </Button>
                        <Typography variant="h6">
                          {format(startOfWeek(selectedDate, { weekStartsOn: 1 }), 'MMM d')} - {format(endOfWeek(selectedDate, { weekStartsOn: 1 }), 'MMM d, yyyy')}
                        </Typography>
                        <Button
                          variant="outlined"
                          onClick={() => setSelectedDate(addDays(selectedDate, 7))}
                        >
                          Next Week
                        </Button>
                      </Box>
                      
                      <Box display="flex" gap={1}>
                        <Button
                          variant={viewMode === 'day' ? 'contained' : 'outlined'}
                          onClick={() => setViewMode('day')}
                          startIcon={<ViewDay />}
                        >
                          Day
                        </Button>
                        <Button
                          variant={viewMode === 'week' ? 'contained' : 'outlined'}
                          onClick={() => setViewMode('week')}
                          startIcon={<ViewWeek />}
                        >
                          Week
                        </Button>
                        <Button
                          variant={viewMode === 'month' ? 'contained' : 'outlined'}
                          onClick={() => setViewMode('month')}
                          startIcon={<ViewMonth />}
                        >
                          Month
                        </Button>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>

              {/* Week View */}
              {viewMode === 'week' && (
                <Grid item xs={12}>
                  <Card>
                    <CardContent>
                      <Grid container>
                        {/* Time column */}
                        <Grid item xs={1}>
                          <Box sx={{ height: 60 }} />
                          {Array.from({ length: 12 }, (_, i) => (
                            <Box key={i} sx={{ height: 60, borderBottom: '1px solid #e0e0e0', display: 'flex', alignItems: 'center', px: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                {i + 8}:00
                              </Typography>
                            </Box>
                          ))}
                        </Grid>

                        {/* Days */}
                        {getWeekDays().map((day, index) => (
                          <Grid item xs key={index}>
                            <Box sx={{ borderLeft: '1px solid #e0e0e0', minHeight: 720 }}>
                              {/* Day header */}
                              <Box sx={{ 
                                height: 60, 
                                borderBottom: '1px solid #e0e0e0',
                                display: 'flex',
                                flexDirection: 'column',
                                justifyContent: 'center',
                                alignItems: 'center',
                                bgcolor: isSameDay(day, new Date()) ? 'primary.light' : 'transparent',
                                color: isSameDay(day, new Date()) ? 'white' : 'inherit'
                              }}>
                                <Typography variant="body2" fontWeight="bold">
                                  {format(day, 'EEE')}
                                </Typography>
                                <Typography variant="h6">
                                  {format(day, 'd')}
                                </Typography>
                              </Box>

                              {/* Events for this day */}
                              <Box sx={{ position: 'relative', height: 660 }}>
                                {getEventsForDate(day).map((event, eventIndex) => (
                                  <Box
                                    key={eventIndex}
                                    sx={{
                                      position: 'absolute',
                                      left: 4,
                                      right: 4,
                                      top: `${(parseInt(format(parseISO(event.startTime), 'H')) - 8) * 60}px`,
                                      height: `${(parseInt(format(parseISO(event.endTime), 'H')) - parseInt(format(parseISO(event.startTime), 'H'))) * 60}px`,
                                      bgcolor: getSubjectColor(event.subject),
                                      color: 'white',
                                      borderRadius: 1,
                                      p: 1,
                                      fontSize: '0.75rem',
                                      overflow: 'hidden',
                                      cursor: 'pointer',
                                      '&:hover': {
                                        bgcolor: 'rgba(0,0,0,0.1)'
                                      }
                                    }}
                                  >
                                    <Box display="flex" alignItems="center" gap={0.5}>
                                      {getEventTypeIcon(event.type)}
                                      <Typography variant="caption" fontWeight="bold">
                                        {event.title}
                                      </Typography>
                                    </Box>
                                    <Typography variant="caption">
                                      {event.subject} • {event.topic}
                                    </Typography>
                                  </Box>
                                ))}
                              </Box>
                            </Box>
                          </Grid>
                        ))}
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              )}
            </Grid>
          )}

          {/* Study Plans Tab */}
          {activeTab === 1 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="h5" gutterBottom>
                  Your Study Plans
                </Typography>
              </Grid>
              
              {studyPlans.map((plan) => (
                <Grid item xs={12} md={6} key={plan.id}>
                  <Card>
                    <CardContent>
                      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                        <Typography variant="h6">{plan.name}</Typography>
                        <Box>
                          <IconButton size="small">
                            <Edit />
                          </IconButton>
                          <IconButton size="small" color="error">
                            <Delete />
                          </IconButton>
                        </Box>
                      </Box>
                      
                      <Box mb={2}>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          Progress
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={plan.progress} 
                          sx={{ height: 8, borderRadius: 4 }}
                        />
                        <Typography variant="caption" color="text.secondary">
                          {plan.progress}% complete
                        </Typography>
                      </Box>
                      
                      <Box display="flex" flexWrap="wrap" gap={1} mb={2}>
                        {plan.subjects.map((subject) => (
                          <Chip 
                            key={subject} 
                            label={subject} 
                            size="small" 
                            icon={<School />}
                            sx={{ bgcolor: getSubjectColor(subject), color: 'white' }}
                          />
                        ))}
                      </Box>
                      
                      {plan.examDate && (
                        <Alert severity="warning" sx={{ mb: 2 }}>
                          <Typography variant="body2">
                            Exam on {format(new Date(plan.examDate), 'MMM d, yyyy')}
                          </Typography>
                        </Alert>
                      )}
                      
                      <Button variant="outlined" fullWidth>
                        View Schedule
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}

          {/* Analytics Tab */}
          {activeTab === 2 && (
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <Card sx={{ bgcolor: 'primary.light', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h4">{analytics.totalStudyTime}h</Typography>
                    <Typography variant="body2">Total Study Time</Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Card sx={{ bgcolor: 'success.light', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h4">{analytics.completedSessions}</Typography>
                    <Typography variant="body2">Completed Sessions</Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Card sx={{ bgcolor: 'warning.light', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h4">{analytics.adherenceRate}%</Typography>
                    <Typography variant="body2">Plan Adherence</Typography>
                  </CardContent>
                </Card>
              </Grid>
              
              <Grid item xs={12} md={3}>
                <Card sx={{ bgcolor: 'info.light', color: 'white' }}>
                  <CardContent>
                    <Typography variant="h4">{analytics.subjectsCovered.length}</Typography>
                    <Typography variant="body2">Subjects Covered</Typography>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* AI Insights Tab */}
          {activeTab === 3 && (
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      <SmartToy sx={{ mr: 1, verticalAlign: 'middle' }} />
                      AI Study Recommendations
                    </Typography>
                    
                    <List>
                      <ListItem>
                        <ListItemIcon>
                          <Lightbulb color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary="Increase study time for Mathematics"
                          secondary="Your performance in calculus needs more practice sessions"
                        />
                      </ListItem>
                      
                      <ListItem>
                        <ListItemIcon>
                          <Schedule color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary="Optimize your study schedule"
                          secondary="Move difficult topics to your peak energy hours (9-11 AM)"
                        />
                      </ListItem>
                      
                      <ListItem>
                        <ListItemIcon>
                          <Psychology color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary="Try spaced repetition for Physics"
                          secondary="Review concepts every 3 days for better retention"
                        />
                      </ListItem>
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}

          {/* Study Plan Generation Dialog */}
          <Dialog open={planDialog} onClose={() => setPlanDialog(false)} maxWidth="md" fullWidth>
            <DialogTitle>
              <AutoAwesome sx={{ mr: 1, verticalAlign: 'middle' }} />
              Generate AI Study Plan
            </DialogTitle>
            <DialogContent>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Plan Name"
                    value={planForm.name}
                    onChange={(e) => setPlanForm({...planForm, name: e.target.value})}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <FormControl fullWidth>
                    <InputLabel>Subjects</InputLabel>
                    <Select
                      multiple
                      value={planForm.subjects}
                      onChange={(e) => setPlanForm({...planForm, subjects: e.target.value})}
                      label="Subjects"
                      renderValue={(selected) => (
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {selected.map((value) => (
                            <Chip key={value} label={value} size="small" />
                          ))}
                        </Box>
                      )}
                    >
                      {subjects.map((subject) => (
                        <MenuItem key={subject.name} value={subject.name}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {subject.icon}
                            <Typography sx={{ ml: 1 }}>{subject.name}</Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <DatePicker
                    label="Exam Date (Optional)"
                    value={planForm.examDate}
                    onChange={(date) => setPlanForm({...planForm, examDate: date})}
                    renderInput={(params) => <TextField {...params} fullWidth />}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    type="number"
                    label="Available Hours per Day"
                    value={planForm.availableHours}
                    onChange={(e) => setPlanForm({...planForm, availableHours: parseInt(e.target.value)})}
                  />
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    multiline
                    rows={3}
                    label="Topics to Study"
                    value={planForm.topics.join(', ')}
                    onChange={(e) => setPlanForm({...planForm, topics: e.target.value.split(',').map(s => s.trim())})}
                    helperText="Enter topics separated by commas"
                  />
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setPlanDialog(false)}>Cancel</Button>
              <Button 
                onClick={generateStudyPlan} 
                variant="contained" 
                disabled={loading || !planForm.name || planForm.subjects.length === 0}
                startIcon={<AutoAwesome />}
              >
                Generate Plan
              </Button>
            </DialogActions>
          </Dialog>

          {/* Event Creation Dialog */}
          <Dialog open={eventDialog} onClose={() => setEventDialog(false)} maxWidth="md" fullWidth>
            <DialogTitle>Add Study Event</DialogTitle>
            <DialogContent>
              <Grid container spacing={2} sx={{ mt: 1 }}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Event Title"
                    value={eventForm.title}
                    onChange={(e) => setEventForm({...eventForm, title: e.target.value})}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TimePicker
                    label="Start Time"
                    value={eventForm.startTime}
                    onChange={(time) => setEventForm({...eventForm, startTime: time})}
                    renderInput={(params) => <TextField {...params} fullWidth />}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <TimePicker
                    label="End Time"
                    value={eventForm.endTime}
                    onChange={(time) => setEventForm({...eventForm, endTime: time})}
                    renderInput={(params) => <TextField {...params} fullWidth />}
                  />
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Event Type</InputLabel>
                    <Select
                      value={eventForm.type}
                      onChange={(e) => setEventForm({...eventForm, type: e.target.value})}
                      label="Event Type"
                    >
                      {eventTypes.map((type) => (
                        <MenuItem key={type.value} value={type.value}>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {type.icon}
                            <Typography sx={{ ml: 1 }}>{type.label}</Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <FormControl fullWidth>
                    <InputLabel>Subject</InputLabel>
                    <Select
                      value={eventForm.subject}
                      onChange={(e) => setEventForm({...eventForm, subject: e.target.value})}
                      label="Subject"
                    >
                      {subjects.map((subject) => (
                        <MenuItem key={subject.name} value={subject.name}>
                          {subject.name}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                </Grid>
                
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Topic"
                    value={eventForm.topic}
                    onChange={(e) => setEventForm({...eventForm, topic: e.target.value})}
                  />
                </Grid>
              </Grid>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setEventDialog(false)}>Cancel</Button>
              <Button variant="contained">Add Event</Button>
            </DialogActions>
          </Dialog>
        </Container>
      </LocalizationProvider>
    </Layout>
  );
};

export default Calendar; 