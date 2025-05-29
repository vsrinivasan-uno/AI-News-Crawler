# AI News Crawler - Python Version

A comprehensive AI news scraping and email digest system built in pure Python. This application automatically collects and summarizes the latest AI news, research papers, and community discussions from various online sources.

## 🚀 Features

- **Multi-source scraping**: Reddit, arXiv research papers, and AI news sites
- **Smart content filtering**: Only significant AI-related content
- **Beautiful email digests**: Professional HTML email templates
- **Flexible scheduling**: Run once, scheduled, or daemon mode
- **Multiple email providers**: Resend API or SMTP support
- **Database logging**: Track all scraping runs and statistics
- **Configurable email lists**: Multiple recipient groups

## 📋 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Chrome/Chromium for Selenium (optional)
# On Ubuntu/Debian:
sudo apt-get update && sudo apt-get install -y chromium-browser

# On macOS with Homebrew:
brew install --cask google-chrome
```

### 2. Configure Environment Variables

Create a `.env` file in the project root:

```bash
# Email configuration (choose one method)

# Method 1: Resend API (Recommended)
RESEND_API_KEY=your_resend_api_key_here

# Method 2: SMTP (Fallback)
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

### 3. Configure Email Lists

Edit `email_config.py` to add your email recipients:

```python
EMAIL_LISTS = {
    'main': [
        'your_email@gmail.com',
        'friend@example.com',
    ],
    'team': [
        'team_member@company.com',
    ]
}

CONFIG = {
    'active_list': 'main',  # Which list to use
    'custom_subject': None  # Optional custom subject
}
```

### 4. Run the Application

```bash
# Run once and send digest immediately
python main.py

# Test mode (same as above)
python main.py test

# Schedule daily digest at 6 PM
python main.py schedule

# Run once + schedule daily
python main.py daemon
```

## 🎯 Usage Examples

### Single Run
Perfect for testing or manual execution:
```bash
python main.py
```

### Scheduled Mode
Runs daily at 6 PM:
```bash
python main.py schedule
```

### Daemon Mode
Runs immediately once, then schedules daily:
```bash
python main.py daemon
```

## 📊 What Gets Scraped

### Reddit Sources
- r/artificial - General AI discussions
- r/MachineLearning - ML research and discussions
- r/OpenAI - OpenAI related content
- r/deeplearning - Deep learning topics
- r/ChatGPT - ChatGPT discussions
- r/LocalLLaMA - Local LLM development
- And more...

### Research Papers
- arXiv categories: AI, ML, Computer Vision, NLP, Robotics
- Papers from the last 3 days
- Filtered for significance

### News Sources
- VentureBeat AI
- TechCrunch AI
- MIT Technology Review AI
- RSS feeds from major tech publications

## 🔧 Configuration

### Email Lists

The application supports multiple email lists in `email_config.py`:

```python
EMAIL_LISTS = {
    'main': ['primary@email.com'],      # Main subscribers
    'team': ['team@company.com'],       # Team members
    'vip': ['ceo@company.com'],         # VIP recipients
    'test': ['test@email.com'],         # Testing
}
```

### Active List Selection

```python
CONFIG = {
    'active_list': 'main',  # Options: 'main', 'team', 'vip', 'test', 'all'
    'custom_subject': 'My Custom AI Brief',  # Optional
}
```

### Content Filtering

The scraper automatically filters content based on:
- **Recency**: Last 24 hours for news/Reddit, 3 days for research
- **Significance**: AI-related keywords and importance indicators
- **Quality**: Minimum scores/engagement thresholds

## 📧 Email Configuration

### Option 1: Resend API (Recommended)

1. Sign up at [resend.com](https://resend.com)
2. Get your API key
3. Add to `.env`: `RESEND_API_KEY=your_key_here`

**Benefits:**
- Easy setup
- High deliverability
- Free tier: 3,000 emails/month
- No SMTP configuration needed

### Option 2: SMTP (Gmail, etc.)

```bash
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password  # Use App Password for Gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

**Gmail Setup:**
1. Enable 2-factor authentication
2. Generate an App Password
3. Use the App Password (not your regular password)

## 🗄️ Database

The application uses SQLite to track:
- Scraping run timestamps
- Content counts by source
- Email delivery status
- Error logging

Database file: `ai_news_crawler.db`

## 📝 Logging

Logs are written to:
- `ai_news_crawler.log` (file)
- Console output

Log levels: INFO, WARNING, ERROR

## 🔄 Automation Options

### Cron Job (Linux/macOS)
```bash
# Run daily at 6 PM
0 18 * * * cd /path/to/ai-news-crawler && python main.py

# Run in daemon mode (starts immediately + schedules)
@reboot cd /path/to/ai-news-crawler && python main.py daemon
```

### Task Scheduler (Windows)
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at 6:00 PM
4. Action: Start a program
5. Program: `python`
6. Arguments: `main.py`
7. Start in: `C:\path\to\ai-news-crawler`

### Systemd Service (Linux)
Create `/etc/systemd/system/ai-news-crawler.service`:

```ini
[Unit]
Description=AI News Crawler
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/ai-news-crawler
ExecStart=/usr/bin/python3 main.py daemon
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable ai-news-crawler
sudo systemctl start ai-news-crawler
```

## 🚨 Troubleshooting

### Common Issues

1. **Selenium WebDriver Error**
   - Install Chrome/Chromium browser
   - Check ChromeDriver compatibility
   - Solution: Selenium now uses automatic driver management

2. **Email Not Sending**
   - Check environment variables
   - Verify API key/SMTP credentials
   - Check logs for specific errors

3. **No Content Found**
   - Sources might be temporarily unavailable
   - Check internet connection
   - Review content filtering criteria

4. **Permission Errors**
   - Ensure write permissions for log files
   - Check database file permissions

### Debug Mode

Add verbose logging:
```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 🔐 Security Notes

- Never commit `.env` file to version control
- Use App Passwords for email services
- Regularly rotate API keys
- Limit email list access

## 📈 Performance

- **Memory usage**: ~50-100MB during execution
- **Execution time**: 2-5 minutes depending on sources
- **Network requests**: ~100-200 per run
- **Email limits**: Respects provider limits (50 recipients per batch)

## 🎨 Email Template

The email digest includes:
- **Header**: AI Intelligence Brief with date
- **Research Papers**: Latest arXiv papers with abstracts
- **Industry News**: News articles from major sources
- **Community Discussions**: Trending Reddit posts
- **Footer**: Branding and generation info

## 🔄 Migration from Node.js

This Python version replaces the previous Node.js/Express API version:

**Removed:**
- Express.js server and API endpoints
- Vercel deployment configuration
- Database models (User, preferences)
- Authentication routes
- Web interface

**Added:**
- Pure Python implementation
- Command-line interface
- Built-in scheduling
- Simplified configuration
- Better error handling

## 📞 Support

If you encounter issues:

1. Check the logs: `tail -f ai_news_crawler.log`
2. Verify configuration: `email_config.py` and `.env`
3. Test email sending manually
4. Check internet connectivity
5. Review source availability

## 🎯 Future Enhancements

Potential improvements:
- Web dashboard for configuration
- More news sources
- Content summarization with AI
- User preference management
- Webhook notifications
- Docker containerization

## 📄 License

MIT License - see LICENSE file for details.

---

**Happy AI news reading! 🤖📧** 