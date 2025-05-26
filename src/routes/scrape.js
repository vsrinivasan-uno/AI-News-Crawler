const express = require('express');
const router = express.Router();
const auth = require('../middleware/auth');
const scrapeController = require('../controllers/scrapeController');

router.post('/', auth, scrapeController.triggerScraping);

module.exports = router; 