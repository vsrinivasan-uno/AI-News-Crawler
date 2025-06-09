# GitHub Actions Setup Guide

## 🚀 Automated AI News Digest with GitHub Actions

This guide will help you set up automated daily email digests using GitHub Actions (free tier).

## ⏰ Schedule Details

- **Automatic Run**: Every day at **10:00 AM Omaha Time** (Central Time)
- **Manual Trigger**: Available anytime via GitHub Actions interface
- **Free Tier**: ~2,000 minutes/month (this workflow uses ~5-10 minutes per run)

## 📋 Setup Steps

### 1. Repository Setup

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Add AI News Crawler with GitHub Actions"
   git push origin main
   ```

2. **Verify workflow file exists**:
   - File: `.github/workflows/daily-digest.yml` ✅
   - This file is already created and configured

### 2. Configure Secrets

Go to your GitHub repository → **Settings** → **Secrets and variables** → **Actions**

#### Required Secrets:

1. **`EMAIL_PROVIDER`** (Optional - defaults to 'google')
   - Value: `google` or `resend`
   - Chooses primary email service

2. **`RESEND_API_KEY`** (Primary email service)
   - Value: Your Resend API key from [resend.com](https://resend.com)
   - Example: `re_123abc456def789ghi`

#### Optional Secrets (SMTP Fallback):

3. **`EMAIL_USER`**
   - Value: Your Gmail address (e.g., `youremail@gmail.com`)

4. **`EMAIL_PASSWORD`** 
   - Value: Your Gmail App Password (not regular password)
   - [How to create App Password](https://support.google.com/accounts/answer/185833)

5. **`SMTP_SERVER`**
   - Value: `smtp.gmail.com` (or your SMTP server)

6. **`SMTP_PORT`**
   - Value: `587`

### 3. Test the Workflow

#### Manual Test Run:

1. Go to **Actions** tab in your GitHub repository
2. Click **"AI News Daily Digest"** workflow
3. Click **"Run workflow"** button
4. Select "Run in test mode" if desired
5. Click **"Run workflow"**

#### Check Results:

1. Monitor the workflow execution in the Actions tab
2. Check the logs for any errors
3. Verify email delivery to your configured recipients
4. Download artifacts (logs & database) if needed

## 🔧 Workflow Features

### Automatic Schedule
- **Time**: 10:00 AM Central Time (Omaha)
- **UTC Time**: 15:00 UTC (accounts for daylight saving)
- **Frequency**: Daily
- **Days**: Monday through Sunday

### Manual Triggers
- **Location**: GitHub → Actions → AI News Daily Digest → Run workflow
- **Options**: 
  - Normal mode (default)
  - Test mode (checkbox option)

### System Setup
- **OS**: Ubuntu Latest
- **Python**: 3.11
- **Chrome**: Latest stable version
- **ChromeDriver**: Auto-matched to Chrome version
- **Dependencies**: Cached for faster runs

### Logging & Monitoring
- **Logs**: Uploaded as artifacts (7-day retention)
- **Database**: SQLite file with run history
- **Email Reports**: Success/failure notifications in logs

## 📊 Resource Usage (GitHub Free Tier)

- **Runtime**: ~5-10 minutes per execution
- **Daily Usage**: ~10 minutes
- **Monthly Usage**: ~300 minutes (well within 2,000 limit)
- **Storage**: Minimal (logs only, 7-day retention)

## 🛠️ Customization Options

### Change Schedule Time

Edit `.github/workflows/daily-digest.yml`:

```yaml
schedule:
  - cron: '0 16 * * *'  # 11 AM Central Time (4 PM UTC)
  - cron: '0 14 * * *'  # 9 AM Central Time (2 PM UTC)
```

### Change Email Recipients

Edit `email_config.py` or `main.py`:

```python
'main': [
    'your-email@example.com',
    'another-email@example.com'
]
```

### Add Multiple Schedules

```yaml
schedule:
  - cron: '0 15 * * *'    # 10 AM Central (daily)
  - cron: '0 19 * * 1'    # 2 PM Central (Mondays only)
```

## 🔍 Troubleshooting

### Common Issues:

1. **Secrets not configured**
   - Error: "RESEND_API_KEY not configured"
   - Solution: Add required secrets in repository settings

2. **Chrome/ChromeDriver issues**
   - Error: "WebDriver not found"
   - Solution: Workflow auto-installs latest versions

3. **Email delivery failures**
   - Error: "Failed to send email"
   - Solution: Check API key validity, verify recipient emails

4. **Workflow not triggering**
   - Check: Repository must be public OR you need GitHub Pro for private repos
   - Check: Workflow file syntax and location

### Debug Steps:

1. **Check workflow logs**:
   - Go to Actions → Failed workflow → View logs

2. **Download artifacts**:
   - Actions → Workflow run → Artifacts section
   - Download logs and database files

3. **Test locally first**:
   ```bash
   python main.py test
   ```

4. **Verify environment**:
   ```bash
   python test_setup.py
   ```

## 📈 Monitoring Success

### GitHub Actions Dashboard
- **Success**: Green checkmark ✅
- **Failure**: Red X ❌
- **Running**: Yellow dot 🟡

### Email Delivery Confirmation
- Check logs for "Email sent successfully"
- Verify actual email receipt
- Monitor bounce rates (if any)

### Database Logging
- SQLite database tracks all runs
- Available in workflow artifacts
- Contains success/failure history

## 🎯 Best Practices

1. **Test thoroughly** before deploying
2. **Monitor first few runs** to ensure stability
3. **Keep secrets secure** - never commit API keys
4. **Use specific Python versions** for consistency
5. **Cache dependencies** for faster runs
6. **Set reasonable log retention** (7 days default)

## 🔐 Security Notes

- ✅ All sensitive data stored in GitHub Secrets
- ✅ Secrets are encrypted and only accessible to workflows
- ✅ No API keys or passwords in code
- ✅ Temporary environment variables only
- ✅ Logs exclude sensitive information

## 📞 Support

If you encounter issues:

1. **Check workflow logs** in GitHub Actions
2. **Test locally** with `python main.py test`
3. **Verify secrets** are correctly configured
4. **Review email delivery** logs
5. **Check GitHub Actions quotas** (if hitting limits)

---

**Status**: ✅ Ready for deployment
**Estimated Setup Time**: 10-15 minutes
**Maintenance Required**: Minimal (occasional secret renewal) 