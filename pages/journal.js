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
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Paper,
  Alert,
  Tabs,
  Tab,
  Rating,
  Fab,
  Zoom,
  Avatar,
  Tooltip
} from '@mui/material';
import { 
  Add, 
  Edit, 
  Delete, 
  SentimentSatisfied,
  SentimentDissatisfied,
  SentimentVerySatisfied,
  SentimentVeryDissatisfied,
  SentimentNeutral,
  Psychology,
  Lightbulb,
  Book,
  CalendarToday,
  EmojiEvents,
  Star,
  Refresh,
  Download,
  Share,
  Timeline,
  BarChart,
  PieChart,
  ShowChart,
  Mood,
  EditNote,
  History
} from '@mui/icons-material';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';

// Mock data for demonstration
const mockEntries = [
  {
    id: 1,
    date: '2024-01-10',
    title: 'Productive Morning Session',
    content: 'Had an amazing focus session this morning. Completed 3 major tasks before 11 AM. The deep work technique really works for me. Feeling accomplished and ready for the rest of the day.',
    mood: 4,
    tags: ['productivity', 'focus', 'accomplishment'],
    type: 'reflection'
  },
  {
    id: 2,
    date: '2024-01-09',
    title: 'Team Meeting Insights',
    content: 'Great team meeting today. We discussed the new project timeline and I shared my ideas for improving the workflow. The team was receptive and we made good progress.',
    mood: 3,
    tags: ['teamwork', 'collaboration', 'ideas'],
    type: 'work'
  },
  {
    id: 3,
    date: '2024-01-08',
    title: 'Learning Breakthrough',
    content: 'Finally understood the concept I\'ve been struggling with for weeks. It clicked today during my study session. Sometimes you need to step back and approach things differently.',
    mood: 5,
    tags: ['learning', 'breakthrough', 'growth'],
    type: 'learning'
  }
];

const moodOptions = [
  { value: 1, label: 'Very Dissatisfied', icon: <SentimentVeryDissatisfied />, color: '#f44336' },
  { value: 2, label: 'Dissatisfied', icon: <SentimentDissatisfied />, color: '#ff9800' },
  { value: 3, label: 'Neutral', icon: <SentimentNeutral />, color: '#ffc107' },
  { value: 4, label: 'Satisfied', icon: <SentimentSatisfied />, color: '#4caf50' },
  { value: 5, label: 'Very Satisfied', icon: <SentimentVerySatisfied />, color: '#2196f3' }
];

const entryTypes = [
  { value: 'reflection', label: 'Reflection', icon: <Psychology /> },
  { value: 'work', label: 'Work', icon: <EditNote /> },
  { value: 'personal', label: 'Personal', icon: <Star /> },
  { value: 'learning', label: 'Learning', icon: <Book /> },
  { value: 'gratitude', label: 'Gratitude', icon: <EmojiEvents /> }
];

const reflectionPrompts = {
  student: [
    'What did I learn today that challenged my thinking?',
    'How did I overcome any obstacles in my studies?',
    'What study technique worked best for me today?',
    'How can I apply what I learned to real-world situations?'
  ],
  founder: [
    'What strategic decision did I make today?',
    'How did I lead my team today?',
    'What business insight did I gain?',
    'How did I move closer to my vision?'
  ],
  neurodivergent: [
    'How did I manage my energy levels today?',
    'What sensory input helped or hindered my focus?',
    'How did I handle unexpected changes?',
    'What routine worked well for me today?'
  ],
  lifestyle: [
    'How did I strengthen my spiritual connection today?',
    'What act of kindness did I perform?',
    'How did I contribute to my community?',
    'What am I grateful for today?'
  ]
};

const moodTrends = [
  { date: '2024-01-05', mood: 3 },
  { date: '2024-01-06', mood: 4 },
  { date: '2024-01-07', mood: 3 },
  { date: '2024-01-08', mood: 5 },
  { date: '2024-01-09', mood: 3 },
  { date: '2024-01-10', mood: 4 }
];

export default function Journal() {
  const { persona } = usePersona();
  const [entries, setEntries] = useState(mockEntries);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [formData, setFormData] = useState({
    title: '',
    content: '',
    mood: 3,
    tags: [],
    type: 'reflection'
  });

  const handleAddEntry = () => {
    setEditingEntry(null);
    setFormData({
      title: '',
      content: '',
      mood: 3,
      tags: [],
      type: 'reflection'
    });
    setOpenDialog(true);
  };

  const handleEditEntry = (entry) => {
    setEditingEntry(entry);
    setFormData({
      title: entry.title,
      content: entry.content,
      mood: entry.mood,
      tags: entry.tags,
      type: entry.type
    });
    setOpenDialog(true);
  };

  const handleSaveEntry = () => {
    if (editingEntry) {
      // Update existing entry
      setEntries(entriesList => 
        entriesList.map(entry => 
          entry.id === editingEntry.id 
            ? { ...entry, ...formData, date: new Date().toISOString().split('T')[0] }
            : entry
        )
      );
    } else {
      // Add new entry
      const newEntry = {
        id: Date.now(),
        ...formData,
        date: new Date().toISOString().split('T')[0]
      };
      setEntries(entriesList => [newEntry, ...entriesList]);
    }
    setOpenDialog(false);
  };

  const handleDeleteEntry = (entryId) => {
    setEntries(entriesList => entriesList.filter(entry => entry.id !== entryId));
  };

  const getMoodIcon = (mood) => {
    const moodOption = moodOptions.find(m => m.value === mood);
    return moodOption ? moodOption.icon : <SentimentNeutral />;
  };

  const getMoodColor = (mood) => {
    const moodOption = moodOptions.find(m => m.value === mood);
    return moodOption ? moodOption.color : '#757575';
  };

  const getMoodLabel = (mood) => {
    const moodOption = moodOptions.find(m => m.value === mood);
    return moodOption ? moodOption.label : 'Unknown';
  };

  const getTypeLabel = (type) => {
    const typeOption = entryTypes.find(t => t.value === type);
    return typeOption ? typeOption.label : type;
  };

  const getAverageMood = () => {
    if (entries.length === 0) return 0;
    const total = entries.reduce((sum, entry) => sum + entry.mood, 0);
    return Math.round(total / entries.length);
  };

  const getMoodTrend = () => {
    if (entries.length < 2) return 'stable';
    const recent = entries.slice(0, 3).reduce((sum, entry) => sum + entry.mood, 0) / 3;
    const older = entries.slice(3, 6).reduce((sum, entry) => sum + entry.mood, 0) / 3;
    return recent > older ? 'improving' : recent < older ? 'declining' : 'stable';
  };

  const prompts = persona ? reflectionPrompts[persona.id] || [] : [];
  const averageMood = getAverageMood();
  const moodTrend = getMoodTrend();

  return (
    <Layout>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h4" component="h1">
              Journal & Reflection
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleAddEntry}
              >
                New Entry
              </Button>
            </Box>
          </Box>

          {/* Mood Overview */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Average Mood
                  </Typography>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                    {getMoodIcon(averageMood)}
                    <Typography variant="h4" color="primary">
                      {averageMood}/5
                    </Typography>
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    {getMoodLabel(averageMood)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Total Entries
                  </Typography>
                  <Typography variant="h4" color="primary">
                    {entries.length}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Journal entries
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Mood Trend
                  </Typography>
                  <Typography variant="h4" color={moodTrend === 'improving' ? 'success.main' : moodTrend === 'declining' ? 'error.main' : 'primary'}>
                    {moodTrend.charAt(0).toUpperCase() + moodTrend.slice(1)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Over the last week
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Tabs */}
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
            <Tab label="Recent Entries" />
            <Tab label="Mood Tracking" />
            <Tab label="Reflection Prompts" />
            <Tab label="Analytics" />
          </Tabs>
        </Box>

        {/* Content */}
        {activeTab === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              {entries.map((entry) => (
                <Card key={entry.id} sx={{ mb: 3 }}>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box sx={{ flexGrow: 1 }}>
                        <Typography variant="h6" gutterBottom>
                          {entry.title}
                        </Typography>
                        <Typography variant="body2" color="text.secondary" gutterBottom>
                          {new Date(entry.date).toLocaleDateString()} • {getTypeLabel(entry.type)}
                        </Typography>
                        <Typography variant="body1" sx={{ mb: 2 }}>
                          {entry.content}
                        </Typography>
                        <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                          {entry.tags.map((tag, index) => (
                            <Chip key={index} label={tag} size="small" />
                          ))}
                        </Box>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getMoodIcon(entry.mood)}
                          <Typography variant="body2" color="text.secondary">
                            {getMoodLabel(entry.mood)}
                          </Typography>
                        </Box>
                      </Box>
                      <Box>
                        <IconButton onClick={() => handleEditEntry(entry)}>
                          <Edit />
                        </IconButton>
                        <IconButton onClick={() => handleDeleteEntry(entry.id)}>
                          <Delete />
                        </IconButton>
                      </Box>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Grid>

            <Grid item xs={12} md={4}>
              {/* Quick Actions */}
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Quick Actions
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Button variant="outlined" fullWidth startIcon={<Mood />}>
                      Mood Check-in
                    </Button>
                    <Button variant="outlined" fullWidth startIcon={<Lightbulb />}>
                      Daily Reflection
                    </Button>
                    <Button variant="outlined" fullWidth startIcon={<History />}>
                      View History
                    </Button>
                  </Box>
                </CardContent>
              </Card>

              {/* Persona Prompts */}
              {prompts.length > 0 && (
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Reflection Prompts
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Questions to guide your reflection:
                    </Typography>
                    <List dense>
                      {prompts.map((prompt, index) => (
                        <ListItem key={index} sx={{ py: 0.5 }}>
                          <ListItemText primary={prompt} />
                        </ListItem>
                      ))}
                    </List>
                  </CardContent>
                </Card>
              )}
            </Grid>
          </Grid>
        )}

        {activeTab === 1 && (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Mood Tracking
                  </Typography>
                  <Grid container spacing={2}>
                    {moodTrends.map((trend) => (
                      <Grid item xs={12} sm={6} md={2} key={trend.date}>
                        <Paper sx={{ p: 2, textAlign: 'center' }}>
                          <Typography variant="h4" color="primary">
                            {trend.mood}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {new Date(trend.date).toLocaleDateString()}
                          </Typography>
                          {getMoodIcon(trend.mood)}
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
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
                    Daily Reflection Prompts
                  </Typography>
                  <Grid container spacing={2}>
                    {prompts.map((prompt, index) => (
                      <Grid item xs={12} md={6} key={index}>
                        <Paper sx={{ p: 2, cursor: 'pointer', '&:hover': { backgroundColor: '#f5f5f5' } }}>
                          <Typography variant="body1" gutterBottom>
                            {prompt}
                          </Typography>
                          <Button size="small" variant="outlined">
                            Use This Prompt
                          </Button>
                        </Paper>
                      </Grid>
                    ))}
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {activeTab === 3 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Entry Types Distribution
                  </Typography>
                  <List>
                    {entryTypes.map((type) => {
                      const count = entries.filter(entry => entry.type === type.value).length;
                      return (
                        <ListItem key={type.value}>
                          <ListItemText 
                            primary={type.label}
                            secondary={`${count} entries`}
                          />
                          <Typography variant="h6" color="primary">
                            {Math.round((count / entries.length) * 100)}%
                          </Typography>
                        </ListItem>
                      );
                    })}
                  </List>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Mood Distribution
                  </Typography>
                  <List>
                    {moodOptions.map((mood) => {
                      const count = entries.filter(entry => entry.mood === mood.value).length;
                      return (
                        <ListItem key={mood.value}>
                          <ListItemText 
                            primary={mood.label}
                            secondary={`${count} entries`}
                          />
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {mood.icon}
                            <Typography variant="h6" color="primary">
                              {Math.round((count / entries.length) * 100)}%
                            </Typography>
                          </Box>
                        </ListItem>
                      );
                    })}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        )}

        {/* Add/Edit Entry Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            {editingEntry ? 'Edit Entry' : 'New Journal Entry'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Title"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                fullWidth
              />
              <FormControl fullWidth>
                <InputLabel>Entry Type</InputLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value})}
                  label="Entry Type"
                >
                  {entryTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="Content"
                value={formData.content}
                onChange={(e) => setFormData({...formData, content: e.target.value})}
                multiline
                rows={6}
                fullWidth
              />
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  How are you feeling?
                </Typography>
                <Rating
                  value={formData.mood}
                  onChange={(event, newValue) => setFormData({...formData, mood: newValue})}
                  max={5}
                  size="large"
                />
                <Typography variant="body2" color="text.secondary">
                  {getMoodLabel(formData.mood)}
                </Typography>
              </Box>
              <TextField
                label="Tags (comma separated)"
                value={formData.tags.join(', ')}
                onChange={(e) => setFormData({...formData, tags: e.target.value.split(',').map(tag => tag.trim()).filter(tag => tag)})}
                fullWidth
                helperText="Add tags to categorize your entry"
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEntry} variant="contained">
              {editingEntry ? 'Update' : 'Save'} Entry
            </Button>
          </DialogActions>
        </Dialog>

        {/* Floating Action Button */}
        <Fab
          color="primary"
          aria-label="add"
          sx={{ position: 'fixed', bottom: 16, right: 16 }}
          onClick={handleAddEntry}
        >
          <Add />
        </Fab>
      </Container>
    </Layout>
  );
} 