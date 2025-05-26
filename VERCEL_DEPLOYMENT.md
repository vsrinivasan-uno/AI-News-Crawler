# Vercel Deployment Guide for AI News Crawler

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Push your code to GitHub
3. **Environment Variables**: Prepare your environment variables

## 🚀 Deployment Steps

### 1. Connect to Vercel

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click "New Project"
3. Import your GitHub repository
4. Vercel will automatically detect it as a Node.js project

### 2. Configure Environment Variables

In your Vercel project dashboard, go to Settings → Environment Variables and add:

```
NODE_ENV=production
RESEND_API_KEY=your_resend_api_key_here
JWT_SECRET=your_jwt_secret_here
DATABASE_URL=your_database_url_here
```

### 3. Database Considerations

⚠️ **IMPORTANT**: SQLite files don't persist on Vercel's serverless environment. You have several options:

#### Option A: Use Vercel Postgres (Recommended)
```bash
# Install Vercel Postgres
npm install @vercel/postgres
```

#### Option B: Use PlanetScale (MySQL)
```bash
# Install MySQL driver
npm install mysql2
```

#### Option C: Use Supabase (PostgreSQL)
```bash
# Install PostgreSQL driver
npm install pg pg-hstore
```

### 4. Update Database Configuration

You'll need to update `src/config/database.js` to use a cloud database instead of SQLite.

## ⚠️ Important Limitations on Vercel

### 1. Cron Jobs Don't Work
- Vercel functions are stateless and don't support long-running processes
- The `node-cron` scheduled task in `src/server.js` won't work

### 2. Solutions for Scheduled Tasks

#### Option A: Vercel Cron Jobs (Pro Plan)
Add to `vercel.json`:
```json
{
  "crons": [
    {
      "path": "/api/scrape/daily",
      "schedule": "0 18 * * *"
    }
  ]
}
```

#### Option B: External Cron Service
Use services like:
- [cron-job.org](https://cron-job.org)
- [EasyCron](https://www.easycron.com)
- [Uptime Robot](https://uptimerobot.com)

Set them to call: `https://your-app.vercel.app/api/scrape/daily`

#### Option C: GitHub Actions
Create `.github/workflows/daily-scrape.yml`:
```yaml
name: Daily AI News Scrape
on:
  schedule:
    - cron: '0 18 * * *'  # 6 PM UTC daily
jobs:
  scrape:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger scrape
        run: |
          curl -X POST https://your-app.vercel.app/api/scrape/daily
```

## 🔧 Required Code Changes for Vercel

### 1. Create Separate Cron Endpoint

Create `src/routes/cron.js`:
```javascript
const express = require('express');
const router = express.Router();
const scrapeController = require('../controllers/scrapeController');

// Daily digest endpoint for external cron services
router.post('/daily', async (req, res) => {
  try {
    await scrapeController.sendDailyDigest();
    res.json({ success: true, message: 'Daily digest sent successfully' });
  } catch (error) {
    console.error('Daily digest failed:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

module.exports = router;
```

### 2. Update Routes in api/index.js
Add the cron route:
```javascript
app.use('/api/cron', require('../src/routes/cron'));
```

## 📦 File Structure for Vercel

```
your-project/
├── api/
│   └── index.js          # Vercel entry point
├── src/
│   ├── config/
│   ├── controllers/
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
├── vercel.json           # Vercel configuration
├── package.json
└── README.md
```

## 🚀 Deploy Command

```bash
# Install Vercel CLI (optional)
npm i -g vercel

# Deploy from command line
vercel

# Or just push to GitHub and Vercel will auto-deploy
```

## 🔍 Testing Your Deployment

1. **Health Check**: Visit `https://your-app.vercel.app/`
2. **API Test**: Visit `https://your-app.vercel.app/api/scrape`
3. **Manual Trigger**: `curl -X POST https://your-app.vercel.app/api/cron/daily`

## 📧 Email Configuration

Make sure your Resend API key is properly set in Vercel environment variables. Test with:
```bash
curl -X POST https://your-app.vercel.app/api/emails/test
```

## 🐛 Common Issues

1. **Database Connection**: Ensure your cloud database URL is correct
2. **Environment Variables**: Double-check all env vars are set in Vercel
3. **Function Timeout**: Large scraping operations might timeout (max 10s on free plan)
4. **Memory Limits**: Puppeteer might hit memory limits on free plan

## 💡 Optimization Tips

1. **Reduce Scraping Load**: Limit concurrent requests
2. **Use Caching**: Cache results to reduce API calls
3. **Optimize Images**: Disable image loading in Puppeteer
4. **Error Handling**: Add robust error handling for network issues

## 📞 Support

If you encounter issues:
1. Check Vercel function logs in the dashboard
2. Test endpoints individually
3. Verify environment variables
4. Check database connectivity 