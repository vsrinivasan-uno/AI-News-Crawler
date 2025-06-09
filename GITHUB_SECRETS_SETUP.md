# GitHub Repository Secrets Setup

To run the AI News Crawler in GitHub Actions, you need to configure repository secrets for email delivery.

## Required Secrets

### Option 1: Using Resend API (Recommended)
Add this secret to your repository:

```
RESEND_API_KEY=re_xxxxxxxxxxxxx
```

### Option 2: Using Google SMTP
Add these secrets to your repository:

```
EMAIL_USER=your-gmail@gmail.com
EMAIL_PASSWORD=your-app-password
```

## How to Add Secrets

1. Go to your GitHub repository
2. Click **Settings** tab
3. Click **Secrets and variables** → **Actions**
4. Click **New repository secret**
5. Add the secret name and value
6. Click **Add secret**

## Email Configuration Notes

- **Resend API**: Get API key from [resend.com](https://resend.com)
- **Gmail**: Use App Password (not regular password) - [Guide](https://support.google.com/accounts/answer/185833)
- **Reddit API**: Get credentials from [reddit.com/prefs/apps](https://reddit.com/prefs/apps) - Optional but enhances Reddit discovery
- **No Email**: The crawler will run successfully without email credentials and just log the results
- **No Reddit API**: The crawler will use intelligent search instead of API-based discovery

## Optional Secrets

### Reddit API (Optional)
For enhanced Reddit content discovery:

```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=YourApp/1.0 by /u/username
```

### Email Configuration (Optional)
```
EMAIL_PROVIDER=resend          # or 'google' (default: 'google')
SMTP_SERVER=smtp.gmail.com     # (default for Gmail)
SMTP_PORT=587                  # (default for Gmail)
```

## Testing

The GitHub Actions workflow includes setup verification that will:
- ✅ Check for email credentials
- ⚠️ Warn if missing but continue anyway
- 📧 Send digest if credentials are available
- 📄 Log content if no email configuration

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "RESEND_API_KEY not found" | Add RESEND_API_KEY secret or use Gmail |
| "Authentication failed" | Use Gmail App Password, not regular password |
| "No email addresses" | Email list is hardcoded in EmailListManager class |
| Action fails | Check logs - crawler works without email config | 