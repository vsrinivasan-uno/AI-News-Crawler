#!/usr/bin/env python3
"""
Email Configuration for AI News Crawler
========================================

This file exists for GitHub Actions compatibility.
The actual email configuration is now integrated into main.py.

Email Setup:
- EmailService class handles both SMTP and Resend API
- EmailListManager class manages recipient lists
- Configuration is done via environment variables

Required Environment Variables:
- EMAIL_PROVIDER: 'google' or 'resend' (default: 'google')
- RESEND_API_KEY: API key for Resend email service
- EMAIL_USER: SMTP email username (for Google)
- EMAIL_PASSWORD: SMTP email password (for Google)
- SMTP_SERVER: SMTP server (default: smtp.gmail.com)
- SMTP_PORT: SMTP port (default: 587)

GitHub Actions Setup:
Add RESEND_API_KEY to your repository secrets for email functionality.
"""

# This file is for compatibility only
# All email logic is implemented in main.py
CONFIGURED = True 