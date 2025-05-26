require('dotenv').config();
const express = require('express');
const cors = require('cors');
const cron = require('node-cron');
const sequelize = require('./config/database');
const User = require('./models/User');

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
app.use('/api/auth', require('./routes/auth'));
app.use('/api/preferences', require('./routes/preferences'));
app.use('/api/emails', require('./routes/emails'));
app.use('/api/scrape', require('./routes/scrape'));

// Schedule daily scraping at 6 PM every day
cron.schedule('0 18 * * *', async () => {
  try {
    console.log('Running scheduled scraping at 6 PM...');
    const scrapeController = require('./controllers/scrapeController');
    await scrapeController.sendDailyDigest();
  } catch (error) {
    console.error('Scheduled scraping failed:', error);
  }
}, {
  timezone: "America/Chicago" // Adjust this to your timezone
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ message: 'Something went wrong!' });
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
}); 