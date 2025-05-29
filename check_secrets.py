#!/usr/bin/env python3
"""
GitHub Secrets Verification Script
Quick check to see what secrets are available in GitHub Actions
"""

import os

def check_secrets():
    """Check GitHub Actions environment for secrets"""
    print("🔍 GitHub Actions Secrets Check")
    print("===============================")
    
    # Check if running in GitHub Actions
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    print(f"Environment: {'🤖 GitHub Actions' if is_github_actions else '💻 Local Development'}")
    print()
    
    # Check for Resend API Key
    resend_key = os.getenv('RESEND_API_KEY')
    if resend_key:
        # Don't print the actual key, just show it exists
        masked_key = resend_key[:8] + '...' + resend_key[-4:] if len(resend_key) > 12 else '***'
        print(f"✅ RESEND_API_KEY: Found ({masked_key})")
    else:
        print(f"❌ RESEND_API_KEY: Not found")
        print(f"   💡 Add this secret in GitHub: Settings → Secrets → Actions")
        print(f"   🔗 Get free API key: https://resend.com")
    
    print()
    
    # Check SMTP fallback secrets
    smtp_secrets = {
        'EMAIL_USER': os.getenv('EMAIL_USER'),
        'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'), 
        'SMTP_SERVER': os.getenv('SMTP_SERVER'),
        'SMTP_PORT': os.getenv('SMTP_PORT')
    }
    
    print("📧 SMTP Fallback Configuration:")
    for secret_name, secret_value in smtp_secrets.items():
        if secret_value and secret_value.strip():
            if 'PASSWORD' in secret_name:
                print(f"✅ {secret_name}: Found (***)")
            else:
                print(f"✅ {secret_name}: {secret_value}")
        else:
            print(f"❌ {secret_name}: Not found")
    
    print()
    
    # Check Reddit API secrets
    reddit_secrets = {
        'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID'),
        'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET'),
        'REDDIT_USER_AGENT': os.getenv('REDDIT_USER_AGENT')
    }
    
    print("🤖 Reddit API Configuration:")
    reddit_configured = False
    for secret_name, secret_value in reddit_secrets.items():
        if secret_value and secret_value.strip():
            if 'SECRET' in secret_name:
                print(f"✅ {secret_name}: Found (***)")
            else:
                print(f"✅ {secret_name}: {secret_value}")
            reddit_configured = True
        else:
            print(f"❌ {secret_name}: Not found")
    
    if not reddit_configured:
        print("💡 Reddit API not configured - will use RSS feeds (still works!)")
        print("🔗 Optional setup: https://www.reddit.com/prefs/apps")
    
    print()
    
    # Recommendations
    if resend_key:
        print("🎉 Resend API configured! Email delivery should work.")
    elif any(smtp_secrets.values()):
        missing_smtp = [k for k, v in smtp_secrets.items() if not v or not v.strip()]
        if missing_smtp:
            print(f"⚠️  SMTP partially configured. Missing: {', '.join(missing_smtp)}")
        else:
            print("✅ SMTP fully configured! Email delivery should work.")
    else:
        print("❌ No email configuration found!")
        print("   🎯 RECOMMENDED: Add RESEND_API_KEY secret")
        print("   🔧 ALTERNATIVE: Add EMAIL_USER + EMAIL_PASSWORD secrets")
    
    print()
    print("🚀 Next: Run the workflow to test email delivery!")

if __name__ == "__main__":
    check_secrets() 