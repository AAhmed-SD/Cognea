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
  Paper,
  Alert,
  Tabs,
  Tab,
  Rating,
  Fab,
  Zoom
} from '@mui/material';
import { 
  Add, 
  Edit, 
  Delete, 
  School,
  Psychology,
  Refresh,
  Check,
  Close,
  Visibility,
  VisibilityOff,
  TrendingUp,
  Schedule,
  EmojiEvents,
  Star,
  Book,
  Timer
} from '@mui/icons-material';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';

// Mock data for demonstration
const mockFlashcards = [
  {
    id: 1,
    front: 'What is the capital of France?',
    back: 'Paris',
    deck: 'Geography',
    difficulty: 2,
    lastReviewed: '2024-01-10',
    nextReview: '2024-01-12',
    reviewCount: 5,
    mastery: 0.8
  },
  {
    id: 2,
    front: 'What is the formula for the area of a circle?',
    back: 'A = πr²',
    deck: 'Mathematics',
    difficulty: 3,
    lastReviewed: '2024-01-09',
    nextReview: '2024-01-11',
    reviewCount: 3,
    mastery: 0.6
  },
  {
    id: 3,
    front: 'What is the largest planet in our solar system?',
    back: 'Jupiter',
    deck: 'Science',
    difficulty: 1,
    lastReviewed: '2024-01-08',
    nextReview: '2024-01-15',
    reviewCount: 8,
    mastery: 0.9
  }
];

const mockDecks = [
  { id: 1, name: 'Geography', cardCount: 25, mastered: 18 },
  { id: 2, name: 'Mathematics', cardCount: 30, mastered: 22 },
  { id: 3, name: 'Science', cardCount: 20, mastered: 15 },
  { id: 4, name: 'History', cardCount: 15, mastered: 8 }
];

const difficultyLevels = [
  { value: 1, label: 'Easy', color: '#4caf50' },
  { value: 2, label: 'Medium', color: '#ff9800' },
  { value: 3, label: 'Hard', color: '#f44336' },
  { value: 4, label: 'Expert', color: '#9c27b0' }
];

const personaLearningStyles = {
  student: {
    recommendedDecks: ['Mathematics', 'Science', 'History'],
    studyTips: ['Study in 25-minute sessions', 'Review before bed', 'Use active recall']
  },
  founder: {
    recommendedDecks: ['Business Strategy', 'Leadership', 'Finance'],
    studyTips: ['Focus on practical applications', 'Review during commutes', 'Connect concepts to real scenarios']
  },
  neurodivergent: {
    recommendedDecks: ['Personal Organization', 'Social Skills', 'Executive Function'],
    studyTips: ['Use visual aids', 'Take frequent breaks', 'Create structured study routines']
  },
  lifestyle: {
    recommendedDecks: ['Islamic History', 'Quran Memorization', 'Islamic Ethics'],
    studyTips: ['Study after prayers', 'Connect to daily practices', 'Review with family']
  }
};

export default function Memory() {
  const { persona } = usePersona();
  const [flashcards, setFlashcards] = useState(mockFlashcards);
  const [decks, setDecks] = useState(mockDecks);
  const [openDialog, setOpenDialog] = useState(false);
  const [editingCard, setEditingCard] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [currentCardIndex, setCurrentCardIndex] = useState(0);
  const [showAnswer, setShowAnswer] = useState(false);
  const [studyMode, setStudyMode] = useState(false);
  const [formData, setFormData] = useState({
    front: '',
    back: '',
    deck: 'General',
    difficulty: 2
  });

  const handleAddCard = () => {
    setEditingCard(null);
    setFormData({
      front: '',
      back: '',
      deck: 'General',
      difficulty: 2
    });
    setOpenDialog(true);
  };

  const handleEditCard = (card) => {
    setEditingCard(card);
    setFormData({
      front: card.front,
      back: card.back,
      deck: card.deck,
      difficulty: card.difficulty
    });
    setOpenDialog(true);
  };

  const handleSaveCard = () => {
    if (editingCard) {
      // Update existing card
      setFlashcards(cards => 
        cards.map(card => 
          card.id === editingCard.id 
            ? { ...card, ...formData }
            : card
        )
      );
    } else {
      // Add new card
      const newCard = {
        id: Date.now(),
        ...formData,
        lastReviewed: null,
        nextReview: new Date().toISOString().split('T')[0],
        reviewCount: 0,
        mastery: 0
      };
      setFlashcards(cards => [...cards, newCard]);
    }
    setOpenDialog(false);
  };

  const handleDeleteCard = (cardId) => {
    setFlashcards(cards => cards.filter(card => card.id !== cardId));
  };

  const startStudySession = () => {
    setStudyMode(true);
    setCurrentCardIndex(0);
    setShowAnswer(false);
  };

  const handleCardResponse = (difficulty) => {
    const currentCard = flashcards[currentCardIndex];
    const now = new Date();
    
    // Update card based on response
    const updatedCard = {
      ...currentCard,
      lastReviewed: now.toISOString().split('T')[0],
      reviewCount: currentCard.reviewCount + 1,
      mastery: Math.min(1, currentCard.mastery + (difficulty === 1 ? 0.1 : difficulty === 2 ? 0.05 : -0.1))
    };

    // Calculate next review date using spaced repetition
    const daysToAdd = difficulty === 1 ? 7 : difficulty === 2 ? 3 : 1;
    const nextReview = new Date(now);
    nextReview.setDate(nextReview.getDate() + daysToAdd);
    updatedCard.nextReview = nextReview.toISOString().split('T')[0];

    setFlashcards(cards => 
      cards.map(card => 
        card.id === currentCard.id ? updatedCard : card
      )
    );

    // Move to next card or end session
    if (currentCardIndex < flashcards.length - 1) {
      setCurrentCardIndex(currentCardIndex + 1);
      setShowAnswer(false);
    } else {
      setStudyMode(false);
    }
  };

  const getDifficultyColor = (difficulty) => {
    const level = difficultyLevels.find(d => d.value === difficulty);
    return level ? level.color : '#757575';
  };

  const getDifficultyLabel = (difficulty) => {
    const level = difficultyLevels.find(d => d.value === difficulty);
    return level ? level.label : 'Unknown';
  };

  const getDueCards = () => {
    const today = new Date().toISOString().split('T')[0];
    return flashcards.filter(card => card.nextReview <= today);
  };

  const dueCards = getDueCards();
  const learningStyle = persona ? personaLearningStyles[persona.id] : null;

  if (studyMode) {
    const currentCard = flashcards[currentCardIndex];
    return (
      <Layout>
        <Container maxWidth="md" sx={{ py: 3 }}>
          <Box sx={{ textAlign: 'center', mb: 4 }}>
            <Typography variant="h4" gutterBottom>
              Study Session
            </Typography>
            <Typography variant="body1" color="text.secondary">
              Card {currentCardIndex + 1} of {flashcards.length}
            </Typography>
          </Box>

          <Card sx={{ mb: 4, minHeight: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <CardContent sx={{ textAlign: 'center', width: '100%' }}>
              <Typography variant="h5" gutterBottom>
                {currentCard.front}
              </Typography>
              
              {showAnswer && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" color="primary" gutterBottom>
                    Answer:
                  </Typography>
                  <Typography variant="h5">
                    {currentCard.back}
                  </Typography>
                </Box>
              )}

              <Box sx={{ mt: 4 }}>
                {!showAnswer ? (
                  <Button
                    variant="contained"
                    size="large"
                    onClick={() => setShowAnswer(true)}
                    startIcon={<Visibility />}
                  >
                    Show Answer
                  </Button>
                ) : (
                  <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
                    <Button
                      variant="contained"
                      color="error"
                      onClick={() => handleCardResponse(3)}
                      startIcon={<Close />}
                    >
                      Hard
                    </Button>
                    <Button
                      variant="contained"
                      color="warning"
                      onClick={() => handleCardResponse(2)}
                      startIcon={<Refresh />}
                    >
                      Medium
                    </Button>
                    <Button
                      variant="contained"
                      color="success"
                      onClick={() => handleCardResponse(1)}
                      startIcon={<Check />}
                    >
                      Easy
                    </Button>
                  </Box>
                )}
              </Box>
            </CardContent>
          </Card>

          <Box sx={{ textAlign: 'center' }}>
            <Button
              variant="outlined"
              onClick={() => setStudyMode(false)}
            >
              End Session
            </Button>
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
              Memory & Learning
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleAddCard}
              >
                Add Card
              </Button>
              {dueCards.length > 0 && (
                <Button
                  variant="contained"
                  color="secondary"
                  startIcon={<School />}
                  onClick={startStudySession}
                >
                  Study Due Cards ({dueCards.length})
                </Button>
              )}
            </Box>
          </Box>

          {/* Progress Overview */}
          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Total Cards
                  </Typography>
                  <Typography variant="h4" color="primary">
                    {flashcards.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Due Today
                  </Typography>
                  <Typography variant="h4" color="warning.main">
                    {dueCards.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Mastered
                  </Typography>
                  <Typography variant="h4" color="success.main">
                    {flashcards.filter(card => card.mastery >= 0.8).length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={3}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Decks
                  </Typography>
                  <Typography variant="h4" color="info.main">
                    {decks.length}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Tabs */}
          <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
            <Tab label="All Cards" />
            <Tab label="Due for Review" />
            <Tab label="Decks" />
            <Tab label="Analytics" />
          </Tabs>
        </Box>

        {/* Content */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            {activeTab === 0 && (
              <Box>
                {flashcards.map((card) => (
                  <Card key={card.id} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <Box sx={{ flexGrow: 1 }}>
                          <Typography variant="h6" gutterBottom>
                            {card.front}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                            {card.back}
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
                            <Chip label={card.deck} size="small" />
                            <Chip 
                              label={getDifficultyLabel(card.difficulty)} 
                              size="small"
                              sx={{ backgroundColor: getDifficultyColor(card.difficulty), color: 'white' }}
                            />
                            <Chip 
                              label={`${Math.round(card.mastery * 100)}%`} 
                              size="small"
                              color={card.mastery >= 0.8 ? 'success' : 'default'}
                            />
                          </Box>
                          <Typography variant="caption" color="text.secondary">
                            Last reviewed: {card.lastReviewed || 'Never'} • 
                            Next review: {card.nextReview} • 
                            Reviews: {card.reviewCount}
                          </Typography>
                        </Box>
                        <Box>
                          <IconButton onClick={() => handleEditCard(card)}>
                            <Edit />
                          </IconButton>
                          <IconButton onClick={() => handleDeleteCard(card.id)}>
                            <Delete />
                          </IconButton>
                        </Box>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}

            {activeTab === 1 && (
              <Box>
                {dueCards.length > 0 ? (
                  dueCards.map((card) => (
                    <Card key={card.id} sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {card.front}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Due for review today
                        </Typography>
                      </CardContent>
                    </Card>
                  ))
                ) : (
                  <Alert severity="success">
                    No cards due for review today! Great job staying on top of your studies.
                  </Alert>
                )}
              </Box>
            )}

            {activeTab === 2 && (
              <Box>
                {decks.map((deck) => (
                  <Card key={deck.id} sx={{ mb: 2 }}>
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Box>
                          <Typography variant="h6" gutterBottom>
                            {deck.name}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {deck.cardCount} cards • {deck.mastered} mastered
                          </Typography>
                          <LinearProgress 
                            variant="determinate" 
                            value={(deck.mastered / deck.cardCount) * 100} 
                            sx={{ mt: 1, height: 8, borderRadius: 4 }}
                          />
                        </Box>
                        <Button variant="outlined">
                          Study Deck
                        </Button>
                      </Box>
                    </CardContent>
                  </Card>
                ))}
              </Box>
            )}

            {activeTab === 3 && (
              <Box>
                <Card sx={{ mb: 3 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      Learning Progress
                    </Typography>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Average Mastery
                        </Typography>
                        <Typography variant="h4">
                          {Math.round(flashcards.reduce((acc, card) => acc + card.mastery, 0) / flashcards.length * 100)}%
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">
                          Total Reviews
                        </Typography>
                        <Typography variant="h4">
                          {flashcards.reduce((acc, card) => acc + card.reviewCount, 0)}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Box>
            )}
          </Grid>

          <Grid item xs={12} md={4}>
            {/* Persona Learning Tips */}
            {learningStyle && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {persona.title} Learning Tips
                  </Typography>
                  <List dense>
                    {learningStyle.studyTips.map((tip, index) => (
                      <ListItem key={index} sx={{ py: 0.5 }}>
                        <ListItemText primary={tip} />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            )}

            {/* Quick Actions */}
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Button variant="outlined" fullWidth startIcon={<School />}>
                    Study All Cards
                  </Button>
                  <Button variant="outlined" fullWidth startIcon={<TrendingUp />}>
                    View Progress
                  </Button>
                  <Button variant="outlined" fullWidth startIcon={<Schedule />}>
                    Set Reminders
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Add/Edit Card Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="md" fullWidth>
          <DialogTitle>
            {editingCard ? 'Edit Card' : 'Add New Card'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Question/Front"
                value={formData.front}
                onChange={(e) => setFormData({...formData, front: e.target.value})}
                multiline
                rows={3}
                fullWidth
              />
              <TextField
                label="Answer/Back"
                value={formData.back}
                onChange={(e) => setFormData({...formData, back: e.target.value})}
                multiline
                rows={3}
                fullWidth
              />
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Deck"
                  value={formData.deck}
                  onChange={(e) => setFormData({...formData, deck: e.target.value})}
                  fullWidth
                />
                <FormControl fullWidth>
                  <InputLabel>Difficulty</InputLabel>
                  <Select
                    value={formData.difficulty}
                    onChange={(e) => setFormData({...formData, difficulty: e.target.value})}
                    label="Difficulty"
                  >
                    {difficultyLevels.map((level) => (
                      <MenuItem key={level.value} value={level.value}>
                        {level.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Box>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveCard} variant="contained">
              {editingCard ? 'Update' : 'Add'} Card
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Layout>
  );
} 