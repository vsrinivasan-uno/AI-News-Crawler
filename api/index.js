require('dotenv').config();
const express = require('express');
const cors = require('cors');
const sequelize = require('../src/config/database');
const User = require('../src/models/User');

const app = express();

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Database initialization
sequelize.sync()
  .then(() => console.log('Database synchronized'))
  .catch(err => console.error('Database sync error:', err));

// Routes
app.use('/api/auth', require('../src/routes/auth'));
app.use('/api/preferences', require('../src/routes/preferences'));
app.use('/api/emails', require('../src/routes/emails'));
app.use('/api/scrape', require('../src/routes/scrape'));
app.use('/api/cron', require('../src/routes/cron'));

// Health check endpoint
app.get('/', (req, res) => {
  res.json({ 
    message: 'AI News Crawler API is running!',
    timestamp: new Date().toISOString(),
    environment: process.env.NODE_ENV || 'development'
  });
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ message: 'Something went wrong!' });
});

// Export the Express app for Vercel
module.exports = app; 