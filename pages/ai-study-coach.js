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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  Alert,
  LinearProgress,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Badge,
  Tooltip,
  Switch,
  FormControlLabel
} from '@mui/material';
import {
  School,
  Psychology,
  Timer,
  TrendingUp,
  Assignment,
  Quiz,
  Lightbulb,
  Schedule,
  Star,
  PlayArrow,
  Pause,
  Stop,
  Refresh,
  Add,
  Edit,
  Delete,
  Save,
  Download,
  Share,
  Visibility,
  VisibilityOff,
  ExpandMore,
  CheckCircle,
  Warning,
  Info,
  EmojiEvents,
  LocalFireDepartment,
  Timeline,
  BarChart,
  PieChart,
  ShowChart,
  Book,
  MenuBook,
  AutoStories,
  Science,
  Calculate,
  Language,
  History,
  Public,
  Code,
  Brush,
  MusicNote,
  FitnessCenter,
  Business,
  PsychologyAlt,
  Biotech,
  Architecture,
  Engineering,
  Computer,
  SchoolOutlined,
  PsychologyOutlined,
  TimerOutlined,
  TrendingUpOutlined,
  AssignmentOutlined,
  QuizOutlined,
  LightbulbOutlined,
  ScheduleOutlined,
  StarOutlined,
  PlayArrowOutlined,
  PauseOutlined,
  StopOutlined,
  RefreshOutlined,
  AddOutlined,
  EditOutlined,
  DeleteOutlined,
  SaveOutlined,
  DownloadOutlined,
  ShareOutlined,
  VisibilityOutlined,
  VisibilityOffOutlined,
  ExpandMoreOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  InfoOutlined,
  EmojiEventsOutlined,
  LocalFireDepartmentOutlined,
  TimelineOutlined,
  BarChartOutlined,
  PieChartOutlined,
  ShowChartOutlined,
  BookOutlined,
  MenuBookOutlined,
  AutoStoriesOutlined,
  ScienceOutlined,
  CalculateOutlined,
  LanguageOutlined,
  HistoryOutlined,
  PublicOutlined,
  CodeOutlined,
  BrushOutlined,
  MusicNoteOutlined,
  FitnessCenterOutlined,
  BusinessOutlined,
  PsychologyAltOutlined,
  BiotechOutlined,
  ArchitectureOutlined,
  EngineeringOutlined,
  ComputerOutlined
} from '@mui/icons-material';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';
import apiService from '../services/api';

const subjects = [
  { name: 'Mathematics', icon: <Calculate />, color: '#2196f3' },
  { name: 'Physics', icon: <Science />, color: '#ff9800' },
  { name: 'Chemistry', icon: <Biotech />, color: '#4caf50' },
  { name: 'Biology', icon: <PsychologyAlt />, color: '#9c27b0' },
  { name: 'Computer Science', icon: <Code />, color: '#607d8b' },
  { name: 'Literature', icon: <Book />, color: '#795548' },
  { name: 'History', icon: <History />, color: '#e91e63' },
  { name: 'Geography', icon: <Public />, color: '#00bcd4' },
  { name: 'Economics', icon: <Business />, color: '#ff5722' },
  { name: 'Psychology', icon: <Psychology />, color: '#673ab7' },
  { name: 'Engineering', icon: <Engineering />, color: '#3f51b5' },
  { name: 'Architecture', icon: <Architecture />, color: '#009688' },
  { name: 'Art', icon: <Brush />, color: '#f44336' },
  { name: 'Music', icon: <MusicNote />, color: '#8bc34a' },
  { name: 'Physical Education', icon: <FitnessCenter />, color: '#ffc107' }
];

const learningStyles = [
  { value: 'visual', label: 'Visual Learner', icon: <Visibility /> },
  { value: 'auditory', label: 'Auditory Learner', icon: <MusicNote /> },
  { value: 'kinesthetic', label: 'Kinesthetic Learner', icon: <FitnessCenter /> },
  { value: 'reading', label: 'Reading/Writing', icon: <Book /> }
];

const difficultyLevels = [
  { value: 'beginner', label: 'Beginner', color: '#4caf50' },
  { value: 'intermediate', label: 'Intermediate', color: '#ff9800' },
  { value: 'advanced', label: 'Advanced', color: '#f44336' }
];

const AIStudyCoach = () => {
  const { persona } = usePersona();
  const [activeTab, setActiveTab] = useState(0);
  const [studySession, setStudySession] = useState(null);
  const [studyPlan, setStudyPlan] = useState(null);
  const [flashcards, setFlashcards] = useState([]);
  const [quiz, setQuiz] = useState(null);
  const [progress, setProgress] = useState(null);
  const [recommendations, setRecommendations] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // New state for enhanced features
  const [currentSession, setCurrentSession] = useState(null);
  const [sessionProgress, setSessionProgress] = useState(0);
  const [studyAnalytics, setStudyAnalytics] = useState(null);
  const [studyTemplates, setStudyTemplates] = useState([]);
  const [showSessionTracker, setShowSessionTracker] = useState(false);

  // Study Session Form
  const [sessionForm, setSessionForm] = useState({
    subject: '',
    topic: '',
    duration_minutes: 25,
    difficulty_level: 'medium',
    learning_style: 'visual',
    current_knowledge: 'beginner'
  });

  // Study Plan Form
  const [planForm, setPlanForm] = useState({
    subjects: [],
    exam_date: '',
    available_hours_per_day: 4,
    learning_goals: []
  });

  // Flashcard Form
  const [flashcardForm, setFlashcardForm] = useState({
    content: '',
    subject: '',
    difficulty: 'medium',
    card_type: 'question_answer'
  });

  // Quiz Form
  const [quizForm, setQuizForm] = useState({
    subject: '',
    topic: '',
    difficulty: 'medium',
    question_count: 5
  });

  // New forms for enhanced features
  const [templateForm, setTemplateForm] = useState({
    name: '',
    subject: '',
    duration_minutes: 25,
    difficulty_level: 'medium',
    learning_style: 'visual',
    activities: [],
    materials_needed: [],
    estimated_confidence_boost: 0.15
  });

  const [sessionUpdateForm, setSessionUpdateForm] = useState({
    progress_percentage: 0,
    completed_activities: [],
    confidence_level: 0,
    notes: '',
    mood_rating: 5,
    energy_level: 5
  });

  // Dialogs
  const [sessionDialog, setSessionDialog] = useState(false);
  const [planDialog, setPlanDialog] = useState(false);
  const [flashcardDialog, setFlashcardDialog] = useState(false);
  const [quizDialog, setQuizDialog] = useState(false);
  const [templateDialog, setTemplateDialog] = useState(false);

  useEffect(() => {
    loadInitialData();
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      // Load study progress analysis
      const progressResponse = await apiService.request('/ai-study-coach/analyze-study-progress', {
        method: 'POST'
      });
      setProgress(progressResponse);

      // Load study recommendations
      const recommendationsResponse = await apiService.request('/ai-study-coach/get-study-recommendations', {
        method: 'POST'
      });
      setRecommendations(recommendationsResponse);
    } catch (err) {
      console.error('Error loading initial data:', err);
      setError('Failed to load study data');
    } finally {
      setLoading(false);
    }
  };

  const createStudySession = async () => {
    try {
      setLoading(true);
      const response = await apiService.request('/ai-study-coach/create-study-session', {
        method: 'POST',
        body: JSON.stringify(sessionForm)
      });
      setStudySession(response);
      setSessionDialog(false);
    } catch (err) {
      console.error('Error creating study session:', err);
      setError('Failed to create study session');
    } finally {
      setLoading(false);
    }
  };

  const generateStudyPlan = async () => {
    try {
      setLoading(true);
      const response = await apiService.request('/ai-study-coach/generate-study-plan', {
        method: 'POST',
        body: JSON.stringify(planForm)
      });
      setStudyPlan(response);
      setPlanDialog(false);
    } catch (err) {
      console.error('Error generating study plan:', err);
      setError('Failed to generate study plan');
    } finally {
      setLoading(false);
    }
  };

  const generateFlashcards = async () => {
    try {
      setLoading(true);
      const response = await apiService.request('/ai-study-coach/generate-flashcards', {
        method: 'POST',
        body: JSON.stringify(flashcardForm)
      });
      setFlashcards(response.flashcards);
      setFlashcardDialog(false);
    } catch (err) {
      console.error('Error generating flashcards:', err);
      setError('Failed to generate flashcards');
    } finally {
      setLoading(false);
    }
  };

  const createPracticeQuiz = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams(quizForm);
      const response = await apiService.request(`/ai-study-coach/create-practice-quiz?${params}`, {
        method: 'POST'
      });
      setQuiz(response);
      setQuizDialog(false);
    } catch (err) {
      console.error('Error creating quiz:', err);
      setError('Failed to create quiz');
    } finally {
      setLoading(false);
    }
  };

  // New functions for enhanced features
  const startStudySession = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await apiService.post('/ai-study-coach/start-study-session', sessionForm);
      
      setCurrentSession(response.session_data);
      setStudySession(response.session_content);
      setShowSessionTracker(true);
      setSessionProgress(0);
      
    } catch (err) {
      setError('Failed to start study session');
      console.error('Start session error:', err);
    } finally {
      setLoading(false);
    }
  };

  const updateSessionProgress = async (progress, activities = []) => {
    if (!currentSession) return;
    
    try {
      const updateData = {
        progress_percentage: progress,
        completed_activities: activities,
        confidence_level: sessionUpdateForm.confidence_level,
        notes: sessionUpdateForm.notes,
        mood_rating: sessionUpdateForm.mood_rating,
        energy_level: sessionUpdateForm.energy_level
      };
      
      const response = await apiService.put(`/ai-study-coach/update-study-session/${currentSession.session_id}`, updateData);
      
      setSessionProgress(progress);
      setCurrentSession(response.session);
      
      if (progress >= 100) {
        setShowSessionTracker(false);
        // Show completion message
      }
      
    } catch (err) {
      console.error('Update session error:', err);
    }
  };

  const adjustDifficulty = async (performance, timeSpent, questionsAttempted, questionsCorrect) => {
    if (!currentSession) return;
    
    try {
      const request = {
        session_id: currentSession.session_id,
        current_performance: performance,
        time_spent: timeSpent,
        questions_attempted: questionsAttempted,
        questions_correct: questionsCorrect
      };
      
      const response = await apiService.post(`/ai-study-coach/adaptive-difficulty/${currentSession.session_id}`, request);
      
      // Update session with new content
      setStudySession(response.new_content);
      
      // Show difficulty adjustment notification
      if (response.difficulty_adjustment !== 'maintain') {
        // You could show a toast notification here
        console.log(`Difficulty ${response.difficulty_adjustment}d to ${response.new_difficulty}`);
      }
      
    } catch (err) {
      console.error('Adjust difficulty error:', err);
    }
  };

  const loadStudyAnalytics = async () => {
    try {
      setLoading(true);
      const response = await apiService.get('/ai-study-coach/study-analytics/1'); // Replace with actual user ID
      setStudyAnalytics(response);
    } catch (err) {
      setError('Failed to load study analytics');
      console.error('Analytics error:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadStudyTemplates = async () => {
    try {
      const response = await apiService.get('/ai-study-coach/study-templates/1'); // Replace with actual user ID
      setStudyTemplates(response.templates);
    } catch (err) {
      console.error('Load templates error:', err);
    }
  };

  const createStudyTemplate = async () => {
    try {
      setLoading(true);
      const response = await apiService.post('/ai-study-coach/create-study-template', templateForm);
      setStudyTemplates([...studyTemplates, response.template]);
      setTemplateForm({
        name: '',
        subject: '',
        duration_minutes: 25,
        difficulty_level: 'medium',
        learning_style: 'visual',
        activities: [],
        materials_needed: [],
        estimated_confidence_boost: 0.15
      });
    } catch (err) {
      setError('Failed to create study template');
      console.error('Create template error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSessionFormChange = (field, value) => {
    setSessionForm(prev => ({ ...prev, [field]: value }));
  };

  const handlePlanFormChange = (field, value) => {
    setPlanForm(prev => ({ ...prev, [field]: value }));
  };

  const handleFlashcardFormChange = (field, value) => {
    setFlashcardForm(prev => ({ ...prev, [field]: value }));
  };

  const handleQuizFormChange = (field, value) => {
    setQuizForm(prev => ({ ...prev, [field]: value }));
  };

  const handleTemplateFormChange = (field, value) => {
    setTemplateForm(prev => ({ ...prev, [field]: value }));
  };

  const handleSessionUpdateFormChange = (field, value) => {
    setSessionUpdateForm(prev => ({ ...prev, [field]: value }));
  };

  const getSubjectIcon = (subjectName) => {
    const subject = subjects.find(s => s.name === subjectName);
    return subject ? subject.icon : <School />;
  };

  const getSubjectColor = (subjectName) => {
    const subject = subjects.find(s => s.name === subjectName);
    return subject ? subject.color : '#666';
  };

  return (
    <Layout>
      <Container maxWidth="xl">
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            AI Study Coach
          </Typography>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Your personalized AI-powered learning assistant
          </Typography>
          {persona && (
            <Chip
              icon={<School />}
              label={`${persona.title} Mode`}
              color="primary"
              sx={{ mt: 1 }}
            />
          )}
        </Box>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
          <Tab label="Study Sessions" icon={<Timer />} />
          <Tab label="Study Plans" icon={<Schedule />} />
          <Tab label="Flashcards" icon={<Assignment />} />
          <Tab label="Practice Quizzes" icon={<Quiz />} />
          <Tab label="Progress Analysis" icon={<TrendingUp />} />
          <Tab label="Recommendations" icon={<Lightbulb />} />
          <Tab label="Analytics" icon={<BarChart />} />
          <Tab label="Templates" icon={<Book />} />
        </Tabs>

        {/* Study Sessions Tab */}
        {activeTab === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Create Study Session
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Get a personalized study session tailored to your learning style
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setSessionDialog(true)}
                    fullWidth
                  >
                    New Session
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            {studySession && (
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Current Study Session
                    </Typography>
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle1" color="primary">
                        {studySession.session_plan?.main_study || 'Study Session'}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Estimated time: {studySession.estimated_completion_time} minutes
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Confidence boost: {(studySession.confidence_boost * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Study Materials</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List>
                          {studySession.study_materials?.map((material, index) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <Book />
                              </ListItemIcon>
                              <ListItemText
                                primary={material.type}
                                secondary={material.content}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>

                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Practice Questions</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List>
                          {studySession.practice_questions?.map((question, index) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <Quiz />
                              </ListItemIcon>
                              <ListItemText
                                primary={question.question}
                                secondary={`Answer: ${question.answer}`}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        )}

        {/* Study Plans Tab */}
        {activeTab === 1 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Generate Study Plan
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Create a comprehensive study plan for multiple subjects
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Schedule />}
                    onClick={() => setPlanDialog(true)}
                    fullWidth
                  >
                    New Plan
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            {studyPlan && (
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Your Study Plan
                    </Typography>
                    
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Daily Schedule</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List>
                          {studyPlan.daily_schedule?.map((day, index) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <Schedule />
                              </ListItemIcon>
                              <ListItemText
                                primary={day.day}
                                secondary={day.subjects?.map(s => `${s.subject} (${s.duration}h)`).join(', ')}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>

                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Weekly Goals</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <List>
                          {studyPlan.weekly_goals?.map((goal, index) => (
                            <ListItem key={index}>
                              <ListItemIcon>
                                <CheckCircle />
                              </ListItemIcon>
                              <ListItemText primary={goal} />
                            </ListItem>
                          ))}
                        </List>
                      </AccordionDetails>
                    </Accordion>

                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMore />}>
                        <Typography>Study Techniques</Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {studyPlan.study_techniques?.map((technique, index) => (
                            <Chip key={index} label={technique} color="primary" variant="outlined" />
                          ))}
                        </Box>
                      </AccordionDetails>
                    </Accordion>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        )}

        {/* Flashcards Tab */}
        {activeTab === 2 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Generate Flashcards
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Convert your notes into AI-powered flashcards
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Assignment />}
                    onClick={() => setFlashcardDialog(true)}
                    fullWidth
                  >
                    New Flashcards
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            {flashcards.length > 0 && (
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Generated Flashcards ({flashcards.length})
                    </Typography>
                    <List>
                      {flashcards.map((card, index) => (
                        <ListItem key={index} sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}>
                          <ListItemIcon>
                            <Assignment />
                          </ListItemIcon>
                          <ListItemText
                            primary={card.question}
                            secondary={`Answer: ${card.answer}`}
                          />
                          <Chip label={card.difficulty} size="small" />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        )}

        {/* Practice Quizzes Tab */}
        {activeTab === 3 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Create Practice Quiz
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Generate custom quizzes for any topic
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Quiz />}
                    onClick={() => setQuizDialog(true)}
                    fullWidth
                  >
                    New Quiz
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            {quiz && (
              <Grid item xs={12} md={8}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {quiz.quiz_title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Estimated time: {quiz.estimated_time} minutes | Passing score: {quiz.passing_score}%
                    </Typography>
                    
                    <List>
                      {quiz.questions?.map((question, index) => (
                        <ListItem key={index} sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}>
                          <ListItemIcon>
                            <Quiz />
                          </ListItemIcon>
                          <ListItemText
                            primary={`Question ${index + 1}: ${question.question}`}
                            secondary={
                              <Box>
                                {question.options?.map((option, optIndex) => (
                                  <Typography key={optIndex} variant="body2">
                                    {String.fromCharCode(65 + optIndex)}. {option}
                                  </Typography>
                                ))}
                                <Typography variant="body2" sx={{ mt: 1, fontWeight: 'bold' }}>
                                  Answer: {question.correct_answer}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  {question.explanation}
                                </Typography>
                              </Box>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              </Grid>
            )}
          </Grid>
        )}

        {/* Progress Analysis Tab */}
        {activeTab === 4 && progress && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Your Strengths
                  </Typography>
                  <List>
                    {progress.strengths?.map((strength, index) => (
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
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Areas for Improvement
                  </Typography>
                  <List>
                    {progress.weaknesses?.map((weakness, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Warning color="warning" />
                        </ListItemIcon>
                        <ListItemText primary={weakness} />
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
                    Study Patterns
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {progress.study_patterns?.map((pattern, index) => (
                      <Chip key={index} label={pattern} color="primary" variant="outlined" />
                    ))}
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Performance Prediction
                  </Typography>
                  <Typography variant="body1">
                    Confidence: {(progress.predicted_performance?.confidence * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {progress.predicted_performance?.prediction}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Recommendations Tab */}
        {activeTab === 5 && recommendations && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Study Techniques
                  </Typography>
                  <List>
                    {recommendations.study_techniques?.map((technique, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Lightbulb />
                        </ListItemIcon>
                        <ListItemText primary={technique} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Time Management
                  </Typography>
                  <List>
                    {recommendations.time_management?.map((tip, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <Schedule />
                        </ListItemIcon>
                        <ListItemText primary={tip} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Focus Areas
                  </Typography>
                  <List>
                    {recommendations.focus_areas?.map((area, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <TrendingUp />
                        </ListItemIcon>
                        <ListItemText primary={area} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Motivation Tips
                  </Typography>
                  <List>
                    {recommendations.motivation_tips?.map((tip, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <EmojiEvents />
                        </ListItemIcon>
                        <ListItemText primary={tip} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {loading && (
          <Box sx={{ width: '100%', mt: 2 }}>
            <LinearProgress />
          </Box>
        )}

        {/* Study Session Dialog */}
        <Dialog open={sessionDialog} onClose={() => setSessionDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create Study Session</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={sessionForm.subject}
                    onChange={(e) => handleSessionFormChange('subject', e.target.value)}
                    label="Subject"
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
                <TextField
                  fullWidth
                  label="Topic"
                  value={sessionForm.topic}
                  onChange={(e) => handleSessionFormChange('topic', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Duration (minutes)"
                  value={sessionForm.duration_minutes}
                  onChange={(e) => handleSessionFormChange('duration_minutes', parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Difficulty Level</InputLabel>
                  <Select
                    value={sessionForm.difficulty_level}
                    onChange={(e) => handleSessionFormChange('difficulty_level', e.target.value)}
                    label="Difficulty Level"
                  >
                    {difficultyLevels.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: level.color, mr: 1 }} />
                          {level.label}
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Learning Style</InputLabel>
                  <Select
                    value={sessionForm.learning_style}
                    onChange={(e) => handleSessionFormChange('learning_style', e.target.value)}
                    label="Learning Style"
                  >
                    {learningStyles.map((style) => (
                      <MenuItem key={style.value} value={style.value}>
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {style.icon}
                          <Typography sx={{ ml: 1 }}>{style.label}</Typography>
                        </Box>
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Current Knowledge</InputLabel>
                  <Select
                    value={sessionForm.current_knowledge}
                    onChange={(e) => handleSessionFormChange('current_knowledge', e.target.value)}
                    label="Current Knowledge"
                  >
                    {difficultyLevels.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        {level.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setSessionDialog(false)}>Cancel</Button>
            <Button onClick={createStudySession} variant="contained" disabled={loading}>
              Create Session
            </Button>
          </DialogActions>
        </Dialog>

        {/* Study Plan Dialog */}
        <Dialog open={planDialog} onClose={() => setPlanDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Generate Study Plan</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Subjects</InputLabel>
                  <Select
                    multiple
                    value={planForm.subjects}
                    onChange={(e) => handlePlanFormChange('subjects', e.target.value)}
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
                <TextField
                  fullWidth
                  type="date"
                  label="Exam Date (Optional)"
                  value={planForm.exam_date}
                  onChange={(e) => handlePlanFormChange('exam_date', e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Available Hours per Day"
                  value={planForm.available_hours_per_day}
                  onChange={(e) => handlePlanFormChange('available_hours_per_day', parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={3}
                  label="Learning Goals"
                  value={planForm.learning_goals.join(', ')}
                  onChange={(e) => handlePlanFormChange('learning_goals', e.target.value.split(',').map(s => s.trim()))}
                  helperText="Enter goals separated by commas"
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setPlanDialog(false)}>Cancel</Button>
            <Button onClick={generateStudyPlan} variant="contained" disabled={loading}>
              Generate Plan
            </Button>
          </DialogActions>
        </Dialog>

        {/* Flashcard Dialog */}
        <Dialog open={flashcardDialog} onClose={() => setFlashcardDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Generate Flashcards</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={6}
                  label="Content"
                  value={flashcardForm.content}
                  onChange={(e) => handleFlashcardFormChange('content', e.target.value)}
                  helperText="Paste your notes or content here"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={flashcardForm.subject}
                    onChange={(e) => handleFlashcardFormChange('subject', e.target.value)}
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
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={flashcardForm.difficulty}
                    onChange={(e) => handleFlashcardFormChange('difficulty', e.target.value)}
                    label="Difficulty"
                  >
                    {difficultyLevels.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        {level.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setFlashcardDialog(false)}>Cancel</Button>
            <Button onClick={generateFlashcards} variant="contained" disabled={loading}>
              Generate Flashcards
            </Button>
          </DialogActions>
        </Dialog>

        {/* Quiz Dialog */}
        <Dialog open={quizDialog} onClose={() => setQuizDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create Practice Quiz</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={quizForm.subject}
                    onChange={(e) => handleQuizFormChange('subject', e.target.value)}
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
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Topic"
                  value={quizForm.topic}
                  onChange={(e) => handleQuizFormChange('topic', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={quizForm.difficulty}
                    onChange={(e) => handleQuizFormChange('difficulty', e.target.value)}
                    label="Difficulty"
                  >
                    {difficultyLevels.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        {level.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Number of Questions"
                  value={quizForm.question_count}
                  onChange={(e) => handleQuizFormChange('question_count', parseInt(e.target.value))}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setQuizDialog(false)}>Cancel</Button>
            <Button onClick={createPracticeQuiz} variant="contained" disabled={loading}>
              Create Quiz
            </Button>
          </DialogActions>
        </Dialog>

        {/* Analytics Tab */}
        {activeTab === 6 && (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">Study Analytics</Typography>
                    <Button 
                      variant="outlined" 
                      onClick={loadStudyAnalytics}
                      disabled={loading}
                    >
                      Refresh Analytics
                    </Button>
                  </Box>
                  
                  {studyAnalytics ? (
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={3}>
                        <Card sx={{ bgcolor: 'primary.light', color: 'white' }}>
                          <CardContent>
                            <Typography variant="h4">{studyAnalytics.total_sessions}</Typography>
                            <Typography variant="body2">Total Sessions</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card sx={{ bgcolor: 'success.light', color: 'white' }}>
                          <CardContent>
                            <Typography variant="h4">{studyAnalytics.total_study_time}h</Typography>
                            <Typography variant="body2">Total Study Time</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card sx={{ bgcolor: 'warning.light', color: 'white' }}>
                          <CardContent>
                            <Typography variant="h4">{studyAnalytics.average_session_length}m</Typography>
                            <Typography variant="body2">Avg Session Length</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      <Grid item xs={12} md={3}>
                        <Card sx={{ bgcolor: 'info.light', color: 'white' }}>
                          <CardContent>
                            <Typography variant="h4">{studyAnalytics.subjects_studied.length}</Typography>
                            <Typography variant="body2">Subjects Studied</Typography>
                          </CardContent>
                        </Card>
                      </Grid>
                      
                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardContent>
                            <Typography variant="h6" gutterBottom>Difficulty Distribution</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                              {Object.entries(studyAnalytics.difficulty_distribution).map(([difficulty, count]) => (
                                <Chip 
                                  key={difficulty} 
                                  label={`${difficulty}: ${count}`} 
                                  color="primary" 
                                  variant="outlined" 
                                />
                              ))}
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                      
                      <Grid item xs={12} md={6}>
                        <Card>
                          <CardContent>
                            <Typography variant="h6" gutterBottom>Learning Style Preferences</Typography>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                              {Object.entries(studyAnalytics.learning_style_preferences).map(([style, count]) => (
                                <Chip 
                                  key={style} 
                                  label={`${style}: ${count}`} 
                                  color="secondary" 
                                  variant="outlined" 
                                />
                              ))}
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                      
                      <Grid item xs={12}>
                        <Card>
                          <CardContent>
                            <Typography variant="h6" gutterBottom>AI Recommendations</Typography>
                            <List>
                              {studyAnalytics.recommendations?.map((recommendation, index) => (
                                <ListItem key={index}>
                                  <ListItemIcon>
                                    <Lightbulb color="primary" />
                                  </ListItemIcon>
                                  <ListItemText primary={recommendation} />
                                </ListItem>
                              ))}
                            </List>
                          </CardContent>
                        </Card>
                      </Grid>
                    </Grid>
                  ) : (
                    <Box textAlign="center" py={4}>
                      <Typography variant="body1" color="text.secondary">
                        No analytics data available. Start studying to see your progress!
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Templates Tab */}
        {activeTab === 7 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Study Templates
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Create reusable study session templates
                  </Typography>
                  <Button
                    variant="contained"
                    startIcon={<Add />}
                    onClick={() => setTemplateDialog(true)}
                    fullWidth
                  >
                    Create Template
                  </Button>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={8}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Your Templates
                  </Typography>
                  {studyTemplates.length > 0 ? (
                    <List>
                      {studyTemplates.map((template) => (
                        <ListItem key={template.template_id}>
                          <ListItemIcon>
                            <Book />
                          </ListItemIcon>
                          <ListItemText
                            primary={template.name}
                            secondary={`${template.subject} • ${template.duration_minutes}m • ${template.difficulty_level}`}
                          />
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => {
                              setSessionForm({
                                subject: template.subject,
                                topic: '',
                                duration_minutes: template.duration_minutes,
                                difficulty_level: template.difficulty_level,
                                learning_style: template.learning_style,
                                current_knowledge: 'beginner'
                              });
                              setActiveTab(0);
                            }}
                          >
                            Use Template
                          </Button>
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Box textAlign="center" py={4}>
                      <Typography variant="body1" color="text.secondary">
                        No templates created yet. Create your first template!
                      </Typography>
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Template Dialog */}
        <Dialog open={templateDialog} onClose={() => setTemplateDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>Create Study Template</DialogTitle>
          <DialogContent>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Template Name"
                  value={templateForm.name}
                  onChange={(e) => handleTemplateFormChange('name', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Subject</InputLabel>
                  <Select
                    value={templateForm.subject}
                    onChange={(e) => handleTemplateFormChange('subject', e.target.value)}
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
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Duration (minutes)"
                  value={templateForm.duration_minutes}
                  onChange={(e) => handleTemplateFormChange('duration_minutes', parseInt(e.target.value))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Difficulty Level</InputLabel>
                  <Select
                    value={templateForm.difficulty_level}
                    onChange={(e) => handleTemplateFormChange('difficulty_level', e.target.value)}
                    label="Difficulty Level"
                  >
                    {difficultyLevels.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        {level.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth>
                  <InputLabel>Learning Style</InputLabel>
                  <Select
                    value={templateForm.learning_style}
                    onChange={(e) => handleTemplateFormChange('learning_style', e.target.value)}
                    label="Learning Style"
                  >
                    {learningStyles.map((style) => (
                      <MenuItem key={style.value} value={style.value}>
                        {style.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  type="number"
                  label="Estimated Confidence Boost"
                  value={templateForm.estimated_confidence_boost}
                  onChange={(e) => handleTemplateFormChange('estimated_confidence_boost', parseFloat(e.target.value))}
                  inputProps={{ step: 0.1, min: 0, max: 1 }}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setTemplateDialog(false)}>Cancel</Button>
            <Button onClick={createStudyTemplate} variant="contained" disabled={loading}>
              Create Template
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Layout>
  );
};

export default AIStudyCoach; 