const express = require('express');
const router = express.Router();
const scrapeController = require('../controllers/scrapeController');

// Daily digest endpoint for external cron services
router.post('/daily', async (req, res) => {
  try {
    console.log('🚀 Manual daily digest triggered via API');
    await scrapeController.sendDailyDigest();
    res.json({ 
      success: true, 
      message: 'Daily digest sent successfully',
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error('Daily digest failed:', error);
    res.status(500).json({ 
      success: false, 
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
});

// Health check for cron services
router.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    service: 'AI News Crawler Cron Service',
    timestamp: new Date().toISOString(),
    nextScheduled: '6:00 PM Chicago Time (Daily)'
  });
});

module.exports = router; 