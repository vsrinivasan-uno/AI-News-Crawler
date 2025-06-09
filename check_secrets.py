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
    
    # Check email provider selection
    email_provider = os.getenv('EMAIL_PROVIDER', 'google').lower()
    print(f"🔧 Email Provider Selection:")
    print(f"   📧 EMAIL_PROVIDER: {email_provider}")
    
    if email_provider not in ['google', 'resend']:
        print(f"   ⚠️ Warning: Unknown provider '{email_provider}'. Using 'google' as default.")
        email_provider = 'google'
    
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
    if email_provider == 'google':
        if any([smtp_secrets['EMAIL_USER'], smtp_secrets['EMAIL_PASSWORD']]):
            missing_smtp = [k for k, v in smtp_secrets.items() if not v or not v.strip()]
            if missing_smtp:
                print(f"⚠️  Google (SMTP) partially configured. Missing: {', '.join(missing_smtp)}")
            else:
                print("✅ Google (SMTP) fully configured! Primary email provider ready.")
                if resend_key:
                    print("✅ Resend also configured as fallback.")
        else:
            print("❌ Google selected but SMTP not configured!")
            print("   🎯 Add EMAIL_USER + EMAIL_PASSWORD secrets for Gmail")
            if resend_key:
                print("   ✅ Resend available as fallback")
            else:
                print("   🔧 Or add RESEND_API_KEY as fallback")
                
    elif email_provider == 'resend':
        if resend_key:
            print("✅ Resend API configured! Primary email provider ready.")
            smtp_configured = all([smtp_secrets['EMAIL_USER'], smtp_secrets['EMAIL_PASSWORD']])
            if smtp_configured:
                print("✅ SMTP also configured as fallback.")
        else:
            print("❌ Resend selected but API key not configured!")
            print("   🎯 Add RESEND_API_KEY secret")
            smtp_configured = all([smtp_secrets['EMAIL_USER'], smtp_secrets['EMAIL_PASSWORD']])
            if smtp_configured:
                print("   ✅ SMTP available as fallback")
            else:
                print("   🔧 Or add EMAIL_USER + EMAIL_PASSWORD as fallback")
    
    print()
    print("🚀 Next: Run the workflow to test email delivery!")

if __name__ == "__main__":
    check_secrets() 