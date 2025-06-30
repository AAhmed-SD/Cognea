require('dotenv').config()

const { createClient } = require('@supabase/supabase-js')
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const winston = require('winston');

const supabaseUrl = process.env.SUPABASE_URL
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY
const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Example usage
console.log('Supabase client initialized:', supabase)

// Configure Winston logger
const logger = winston.createLogger({
  level: 'error',
  format: winston.format.json(),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'error.log' })
  ],
});

app.get('/', (req, res) => {
  res.send('Hello, World!');
});

// Middleware to check if user is authenticated
const authenticate = (req, res, next) => {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).json({ error: 'Unauthorized' });

  supabase.auth.api.getUser(token)
    .then(({ user, error }) => {
      if (error || !user) return res.status(401).json({ error: 'Unauthorized' });
      req.user = user;
      next();
    });
};

// Protect task routes
app.use('/tasks', authenticate);

// Create Task
app.post('/tasks', async (req, res) => {
  try {
    const { title, description, status, dueDate } = req.body;
    const { data, error } = await supabase.from('tasks').insert([{ title, description, status, dueDate }]);
    if (error) throw error;
    res.status(201).json(data);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Read Tasks
app.get('/tasks', async (req, res) => {
  try {
    const { data, error } = await supabase.from('tasks').select('*');
    if (error) throw error;
    res.status(200).json(data);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Update Task
app.put('/tasks/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { title, description, status, dueDate } = req.body;
    const { data, error } = await supabase.from('tasks').update({ title, description, status, dueDate }).eq('id', id);
    if (error) throw error;
    res.status(200).json(data);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Delete Task
app.delete('/tasks/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { data, error } = await supabase.from('tasks').delete().eq('id', id);
    if (error) throw error;
    res.status(200).json(data);
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

// Smart Scheduler Algorithm - Real Implementation
const smartScheduler = (tasks) => {
  if (!tasks || tasks.length === 0) return [];
  
  // Calculate priority scores for each task
  const priorityScores = {
    'high': 3,
    'medium': 2,
    'low': 1
  };
  
  // Calculate urgency scores based on due date
  const calculateUrgencyScore = (task) => {
    if (!task.dueDate) return 1; // No due date = low urgency
    
    const now = new Date();
    const dueDate = new Date(task.dueDate);
    const daysUntilDue = Math.ceil((dueDate - now) / (1000 * 60 * 60 * 24));
    
    if (daysUntilDue < 0) return 5; // Overdue = highest urgency
    if (daysUntilDue === 0) return 4; // Due today
    if (daysUntilDue <= 1) return 3; // Due tomorrow
    if (daysUntilDue <= 3) return 2; // Due this week
    return 1; // Due later
  };
  
  // Calculate complexity scores based on estimated duration
  const calculateComplexityScore = (task) => {
    const duration = task.estimatedDuration || 30; // Default 30 minutes
    if (duration <= 30) return 1; // Quick tasks
    if (duration <= 60) return 2; // Medium tasks
    if (duration <= 120) return 3; // Long tasks
    return 4; // Very long tasks
  };
  
  // Score each task
  const scoredTasks = tasks.map(task => {
    const priorityScore = priorityScores[task.priority] || 1;
    const urgencyScore = calculateUrgencyScore(task);
    const complexityScore = calculateComplexityScore(task);
    
    // Weighted scoring: priority (40%) + urgency (40%) + complexity (20%)
    const totalScore = (priorityScore * 0.4) + (urgencyScore * 0.4) + (complexityScore * 0.2);
    
    return {
      ...task,
      score: totalScore
    };
  });
  
  // Sort by score (highest first), then by due date for tie-breaks
  return scoredTasks.sort((a, b) => {
    if (Math.abs(a.score - b.score) < 0.1) {
      // If scores are very close, sort by due date
      if (!a.dueDate && !b.dueDate) return 0;
      if (!a.dueDate) return 1;
      if (!b.dueDate) return -1;
      return new Date(a.dueDate) - new Date(b.dueDate);
    }
    return b.score - a.score;
  });
};

// Example usage of smartScheduler
app.get('/schedule', (req, res) => {
  const tasks = req.user ? req.user.tasks : [];
  const scheduledTasks = smartScheduler(tasks);
  res.json(scheduledTasks);
});

// Centralized Error Handling Middleware
app.use((err, req, res, next) => {
  logger.error(err.stack); // Log the error
  res.status(err.status || 500).json({
    error: {
      code: err.code || 'INTERNAL_SERVER_ERROR',
      message: err.message || 'An unexpected error occurred.',
    },
  });
});

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
}); 