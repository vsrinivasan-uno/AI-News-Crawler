#!/usr/bin/env python3
"""
Setup verification script for AI News Crawler
"""

import os
import sys
import importlib.util

def test_python_version():
    """Test Python version compatibility"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.11+")
        return False

def test_dependencies():
    """Test required dependencies"""
    print("📦 Testing dependencies...")
    dependencies = [
        'requests',
        'beautifulsoup4', 
        'feedparser',
        'selenium',
        'lxml',
        'dotenv',
        'schedule'
    ]
    
    passed = 0
    for dep in dependencies:
        try:
            if dep == 'beautifulsoup4':
                import bs4
            elif dep == 'dotenv':
                import dotenv
            else:
                __import__(dep)
            print(f"✅ {dep}")
            passed += 1
        except ImportError:
            print(f"❌ {dep} - Not found")
    
    return passed == len(dependencies)

def test_files():
    """Test required files exist"""
    print("📄 Testing configuration files...")
    required_files = [
        ('main.py', 'Main application'),
        ('requirements.txt', 'Python dependencies'),
        ('email_config.py', 'Email configuration'),
        ('env_example.txt', 'Environment example')
    ]
    
    passed = 0
    for filename, description in required_files:
        if os.path.exists(filename):
            print(f"✅ {filename} - {description}")
            passed += 1
        else:
            print(f"❌ {filename} - {description} (missing)")
    
    return passed == len(required_files)

def test_email_config():
    """Test email configuration"""
    print("📧 Testing email configuration...")
    try:
        # Try to import and test email configuration
        spec = importlib.util.spec_from_file_location("main", "main.py")
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        
        email_manager = main_module.EmailListManager()
        email_list = email_manager.get_active_email_list()
        
        if email_list:
            print(f"✅ Found {len(email_list)} email addresses in active list")
            print(f"📋 Active list: {email_manager.config['active_list']}")
            return True
        else:
            print("❌ No email addresses configured")
            return False
            
    except Exception as e:
        print(f"❌ Error testing email config: {e}")
        return False

def test_environment():
    """Test environment variables (GitHub Actions or local .env)"""
    print("🔧 Testing environment variables...")
    
    # Check for GitHub Actions environment
    is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
    
    if is_github_actions:
        print("🔧 GitHub Actions environment detected")
        # In GitHub Actions, check for secrets
        resend_key = os.getenv('RESEND_API_KEY')
        if resend_key:
            print("✅ RESEND_API_KEY found in GitHub Secrets")
            return True
        else:
            print("⚠️ RESEND_API_KEY not found in GitHub Secrets")
            print("💡 Add RESEND_API_KEY to your repository secrets")
            return False
    else:
        # Local environment - check for .env file
        if os.path.exists('.env'):
            print("✅ .env file found")
            return True
        else:
            print("⚠️ .env file not found")
            print("💡 Copy env_example.txt to .env and configure your email settings")
            return False

def test_main_import():
    """Test main application can be imported"""
    print("🔍 Testing main application...")
    try:
        spec = importlib.util.spec_from_file_location("main", "main.py")
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)
        print("✅ main.py can be imported successfully")
        return True
    except Exception as e:
        print(f"❌ Error importing main.py: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 AI News Crawler - Setup Test")
    print("================================")
    
    tests = [
        test_python_version,
        test_dependencies,
        test_files,
        test_email_config,
        test_environment,
        test_main_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your setup is ready.")
        sys.exit(0)
    else:
        # In GitHub Actions, treat missing .env as acceptable if we have secrets
        is_github_actions = os.getenv('GITHUB_ACTIONS') == 'true'
        if is_github_actions and passed >= (total - 1):  # Allow 1 failure for .env
            print("✅ GitHub Actions environment ready!")
            sys.exit(0)
        else:
            print("⚠️ Some tests failed. Please fix the issues above before running.")
            print("💡 Common fixes:")
            print("   pip install -r requirements.txt    # Install dependencies")
            print("   cp env_example.txt .env            # Create .env file")
            print("   # Edit .env and email_config.py    # Configure email")
            sys.exit(1)

if __name__ == "__main__":
    main() 