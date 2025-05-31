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

// Smart Scheduler Algorithm Placeholder
const smartScheduler = (tasks) => {
  // Placeholder logic for scheduling tasks
  // This function will be enhanced with AI logic
  return tasks.sort((a, b) => new Date(a.dueDate) - new Date(b.dueDate));
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