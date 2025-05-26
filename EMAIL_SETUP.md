# Email Setup Guide

This guide explains how to configure and use the email list functionality for your AI News Crawler.

## 🚀 Quick Start

1. **Configure your email list** in `src/config/emailLists.js`
2. **Set your Resend API key** in `.env`
3. **Test the system** with `npm run test-email-list`
4. **Enjoy daily AI digests** at 6 PM automatically!

## 📧 Email List Configuration

### 1. Edit Email Lists

Open `src/config/emailLists.js` and add your email addresses:

```javascript
const emailLists = {
  // Main AI News Digest List
  main: [
    'your-email@gmail.com',
    'friend1@example.com',
    'colleague@company.com',
    // Add more emails here
  ],
  
  // Team/Company List
  team: [
    'team-member1@company.com',
    'team-member2@company.com',
  ],
  
  // VIP/Priority List
  vip: [
    'ceo@company.com',
    'important-client@example.com',
  ]
};
```

### 2. Choose Active List

Set which list to use for daily emails:

```javascript
const config = {
  activeList: 'main', // Options: 'main', 'team', 'vip', 'test', or 'all'
  includeRegisteredUsers: true, // Also send to registered users
};
```

## 🎯 Available Email Lists

| List Name | Purpose | Example Use Case |
|-----------|---------|------------------|
| `main` | Primary recipients | Personal friends, main subscribers |
| `team` | Team/Company | Work colleagues, team members |
| `vip` | High priority | Important clients, executives |
| `test` | Testing | Test emails, development |
| `all` | Everyone | Combines all lists |

## 🛠️ Testing Commands

### Test Current Configuration
```bash
npm run test-email-list
```

### Test Specific List
```bash
npm run test-email-list main    # Test main list
npm run test-email-list team    # Test team list
npm run test-email-list vip     # Test VIP list
npm run test-email-list all     # Test all lists combined
```

### Test Individual Email Sending
```bash
npm run test-email              # Test with registered users
```

## 📊 Resend Free Plan Limits

- **100 emails per day**
- **3,000 emails per month**
- **Up to 50 recipients per email**
- **Automatic batching** handles large lists

### Cost Examples:
- **50 people = 1 email** (very efficient!)
- **100 people = 2 emails**
- **500 people = 10 emails**

## ⚙️ Configuration Options

### Basic Configuration
```javascript
const config = {
  activeList: 'main',              // Which list to use
  includeRegisteredUsers: true,    // Also send to app users
  customSubject: null,             // Custom email subject
};
```

### Advanced Usage
```javascript
// Send to multiple specific lists
const emailList = getEmailLists(['main', 'vip']);
await emailService.sendToEmailList(emailList, content);

// Send to all lists
const allEmails = getEmailLists('all');
await emailService.sendToEmailList(allEmails, content);
```

## 🕕 Automatic Scheduling

The system automatically sends emails **every day at 6 PM** to:
1. **Email list** (from configuration)
2. **Registered users** (if enabled)

### Change Schedule
Edit `src/server.js`:
```javascript
// Current: 6 PM daily
cron.schedule('0 18 * * *', async () => {
  // Change to 8 AM: '0 8 * * *'
  // Change to twice daily: '0 8,18 * * *'
});
```

## 🔧 Troubleshooting

### No Emails Received?
1. **Check spam folder**
2. **Verify Resend API key** in `.env`
3. **Check email addresses** in configuration
4. **Test with** `npm run test-email-list`

### Email Limits Exceeded?
1. **Monitor usage** in Resend dashboard
2. **Reduce email list size**
3. **Consider upgrading** Resend plan

### Configuration Issues?
1. **Check syntax** in `emailLists.js`
2. **Verify list names** match exactly
3. **Test with** `npm run test-email-list test`

## 📝 Best Practices

### 1. Start Small
- Begin with `test` list
- Add real emails gradually
- Monitor delivery rates

### 2. Organize Lists
- Use descriptive list names
- Separate personal/business
- Keep VIP lists small

### 3. Monitor Performance
- Check Resend dashboard
- Watch for bounces/complaints
- Keep lists clean

### 4. Respect Recipients
- Only add consenting recipients
- Provide unsubscribe options
- Monitor engagement

## 🚀 Production Deployment

### 1. Environment Variables
```bash
# .env
RESEND_API_KEY=your_actual_api_key
```

### 2. Update Email Lists
Replace test emails with real addresses in `src/config/emailLists.js`

### 3. Set Active List
```javascript
const config = {
  activeList: 'main', // Change from 'test' to 'main'
};
```

### 4. Deploy & Monitor
- Deploy to your server
- Monitor first few sends
- Check recipient feedback

## 💡 Pro Tips

1. **Use test emails first**: Always test with `delivered@resend.dev`
2. **Batch efficiently**: Lists are automatically batched for optimal delivery
3. **Monitor metrics**: Check open rates and engagement
4. **Keep lists updated**: Remove bounced/inactive emails
5. **Personalize content**: Consider user preferences for future versions

## 🆘 Support

If you need help:
1. Check this guide first
2. Test with `npm run test-email-list test`
3. Verify configuration in `src/config/emailLists.js`
4. Check Resend dashboard for delivery status

---

**Happy emailing! 📧✨** 