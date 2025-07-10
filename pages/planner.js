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
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  Alert
} from '@mui/material';
import { 
  Add, 
  Schedule, 
  Edit, 
  Delete, 
  PlayArrow,
  Pause,
  Stop,
  CalendarToday,
  ViewWeek,
  ViewDay,
  Today,
  DateRange
} from '@mui/icons-material';
import Layout from '../components/Layout/Layout';
import { usePersona } from '../contexts/PersonaContext';

// Mock data for demonstration
const mockTimeBlocks = [
  {
    id: 1,
    title: 'Morning Focus Session',
    startTime: '09:00',
    endTime: '11:00',
    type: 'deep-work',
    status: 'completed',
    description: 'Work on the most important tasks of the day'
  },
  {
    id: 2,
    title: 'Team Meeting',
    startTime: '11:30',
    endTime: '12:30',
    type: 'meeting',
    status: 'upcoming',
    description: 'Weekly team sync and project updates'
  },
  {
    id: 3,
    title: 'Lunch Break',
    startTime: '12:30',
    endTime: '13:30',
    type: 'break',
    status: 'upcoming',
    description: 'Take a break and recharge'
  },
  {
    id: 4,
    title: 'Afternoon Deep Work',
    startTime: '14:00',
    endTime: '16:00',
    type: 'deep-work',
    status: 'upcoming',
    description: 'Continue with focused work'
  }
];

const timeBlockTypes = [
  { value: 'deep-work', label: 'Deep Work', color: '#2196f3' },
  { value: 'meeting', label: 'Meeting', color: '#ff9800' },
  { value: 'break', label: 'Break', color: '#4caf50' },
  { value: 'exercise', label: 'Exercise', color: '#9c27b0' },
  { value: 'learning', label: 'Learning', color: '#607d8b' }
];

export default function Planner() {
  const { persona, preferences } = usePersona();
  const [timeBlocks, setTimeBlocks] = useState(mockTimeBlocks);
  const [view, setView] = useState('day'); // day, week, month
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [openDialog, setOpenDialog] = useState(false);
  const [editingBlock, setEditingBlock] = useState(null);
  const [formData, setFormData] = useState({
    title: '',
    startTime: '09:00',
    endTime: '10:00',
    type: 'deep-work',
    description: ''
  });

  const handleAddBlock = () => {
    setEditingBlock(null);
    setFormData({
      title: '',
      startTime: '09:00',
      endTime: '10:00',
      type: 'deep-work',
      description: ''
    });
    setOpenDialog(true);
  };

  const handleEditBlock = (block) => {
    setEditingBlock(block);
    setFormData({
      title: block.title,
      startTime: block.startTime,
      endTime: block.endTime,
      type: block.type,
      description: block.description
    });
    setOpenDialog(true);
  };

  const handleSaveBlock = () => {
    if (editingBlock) {
      // Update existing block
      setTimeBlocks(blocks => 
        blocks.map(block => 
          block.id === editingBlock.id 
            ? { ...block, ...formData }
            : block
        )
      );
    } else {
      // Add new block
      const newBlock = {
        id: Date.now(),
        ...formData,
        status: 'upcoming'
      };
      setTimeBlocks(blocks => [...blocks, newBlock]);
    }
    setOpenDialog(false);
  };

  const handleDeleteBlock = (blockId) => {
    setTimeBlocks(blocks => blocks.filter(block => block.id !== blockId));
  };

  const getTypeColor = (type) => {
    const typeConfig = timeBlockTypes.find(t => t.value === type);
    return typeConfig ? typeConfig.color : '#757575';
  };

  const getTypeLabel = (type) => {
    const typeConfig = timeBlockTypes.find(t => t.value === type);
    return typeConfig ? typeConfig.label : type;
  };

  const formatTime = (time) => {
    return new Date(`2000-01-01T${time}`).toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  const getCurrentBlock = () => {
    const now = new Date();
    const currentTime = now.toTimeString().slice(0, 5);
    
    return timeBlocks.find(block => {
      return block.startTime <= currentTime && block.endTime > currentTime;
    });
  };

  const currentBlock = getCurrentBlock();

  return (
    <Layout>
      <Container maxWidth="xl" sx={{ py: 3 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h4" component="h1">
              Planner
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<CalendarToday />}
                onClick={() => setView('day')}
                color={view === 'day' ? 'primary' : 'inherit'}
              >
                Day
              </Button>
              <Button
                variant="outlined"
                startIcon={<ViewWeek />}
                onClick={() => setView('week')}
                color={view === 'week' ? 'primary' : 'inherit'}
              >
                Week
              </Button>
              <Button
                variant="contained"
                startIcon={<Add />}
                onClick={handleAddBlock}
              >
                Add Time Block
              </Button>
            </Box>
          </Box>

          {/* Current Focus */}
          {currentBlock && (
            <Alert severity="info" sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Currently: {currentBlock.title}
              </Typography>
              <Typography variant="body2">
                {formatTime(currentBlock.startTime)} - {formatTime(currentBlock.endTime)}
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Button size="small" startIcon={<PlayArrow />}>
                  Start Focus
                </Button>
                <Button size="small" startIcon={<Pause />} sx={{ ml: 1 }}>
                  Pause
                </Button>
              </Box>
            </Alert>
          )}
        </Box>

        {/* Time Blocks Grid */}
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Today's Schedule
                </Typography>
                <List>
                  {timeBlocks.map((block, index) => (
                    <React.Fragment key={block.id}>
                      <ListItem sx={{ 
                        border: `2px solid ${getTypeColor(block.type)}`,
                        borderRadius: 2,
                        mb: 1,
                        backgroundColor: block.status === 'completed' ? `${getTypeColor(block.type)}10` : 'transparent'
                      }}>
                        <Box sx={{ flexGrow: 1 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                            <Typography variant="h6" sx={{ flexGrow: 1 }}>
                              {block.title}
                            </Typography>
                            <Chip 
                              label={getTypeLabel(block.type)} 
                              size="small"
                              sx={{ 
                                backgroundColor: getTypeColor(block.type),
                                color: 'white',
                                mr: 1
                              }}
                            />
                            <Chip 
                              label={block.status} 
                              size="small"
                              color={block.status === 'completed' ? 'success' : 'default'}
                            />
                          </Box>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            {formatTime(block.startTime)} - {formatTime(block.endTime)}
                          </Typography>
                          <Typography variant="body2">
                            {block.description}
                          </Typography>
                        </Box>
                        <ListItemSecondaryAction>
                          <IconButton onClick={() => handleEditBlock(block)}>
                            <Edit />
                          </IconButton>
                          <IconButton onClick={() => handleDeleteBlock(block.id)}>
                            <Delete />
                          </IconButton>
                        </ListItemSecondaryAction>
                      </ListItem>
                      {index < timeBlocks.length - 1 && <Divider />}
                    </React.Fragment>
                  ))}
                </List>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={4}>
            {/* Quick Actions */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Quick Actions
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  <Button variant="outlined" fullWidth startIcon={<Today />}>
                    Plan Today
                  </Button>
                  <Button variant="outlined" fullWidth startIcon={<Today />}>
                    Plan Tomorrow
                  </Button>
                  <Button variant="outlined" fullWidth startIcon={<DateRange />}>
                    Plan Week
                  </Button>
                </Box>
              </CardContent>
            </Card>

            {/* Persona Insights */}
            {persona && (
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    {persona.title} Insights
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    Based on your {persona.title.toLowerCase()} persona and preferences:
                  </Typography>
                  <List dense>
                    <ListItem>
                      <ListItemText 
                        primary="Focus Hours"
                        secondary={`${preferences?.focusHours?.[0]}:00 - ${preferences?.focusHours?.[1]}:00`}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Energy Peak"
                        secondary={preferences?.energyPeak}
                      />
                    </ListItem>
                    <ListItem>
                      <ListItemText 
                        primary="Recommended"
                        secondary="Schedule deep work during your peak hours"
                      />
                    </ListItem>
                  </List>
                </CardContent>
              </Card>
            )}
          </Grid>
        </Grid>

        {/* Add/Edit Time Block Dialog */}
        <Dialog open={openDialog} onClose={() => setOpenDialog(false)} maxWidth="sm" fullWidth>
          <DialogTitle>
            {editingBlock ? 'Edit Time Block' : 'Add Time Block'}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 1 }}>
              <TextField
                label="Title"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                fullWidth
              />
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Start Time"
                  type="time"
                  value={formData.startTime}
                  onChange={(e) => setFormData({...formData, startTime: e.target.value})}
                  fullWidth
                />
                <TextField
                  label="End Time"
                  type="time"
                  value={formData.endTime}
                  onChange={(e) => setFormData({...formData, endTime: e.target.value})}
                  fullWidth
                />
              </Box>
              <FormControl fullWidth>
                <InputLabel>Type</InputLabel>
                <Select
                  value={formData.type}
                  onChange={(e) => setFormData({...formData, type: e.target.value})}
                  label="Type"
                >
                  {timeBlockTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      {type.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <TextField
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                multiline
                rows={3}
                fullWidth
              />
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpenDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveBlock} variant="contained">
              {editingBlock ? 'Update' : 'Add'} Block
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </Layout>
  );
} 