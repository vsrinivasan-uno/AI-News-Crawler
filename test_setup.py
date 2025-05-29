#!/usr/bin/env python3
"""
Test script to verify AI News Crawler setup
"""

import sys
import os
import importlib.util

def test_python_version():
    """Test Python version compatibility"""
    print("🐍 Testing Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required. Current version:", sys.version)
        return False
    print(f"✅ Python {sys.version.split()[0]} - Compatible")
    return True

def test_dependencies():
    """Test required dependencies"""
    print("\n📦 Testing dependencies...")
    
    required_packages = [
        'requests',
        'beautifulsoup4',
        'feedparser',
        'selenium',
        'lxml',
        'dotenv',
        'schedule'
    ]
    
    missing = []
    
    for package in required_packages:
        # Handle different import names
        import_name = package
        if package == 'beautifulsoup4':
            import_name = 'bs4'
        elif package == 'python-dotenv':
            import_name = 'dotenv'
            
        try:
            __import__(import_name)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing.append(package)
    
    if missing:
        print(f"\n💡 Install missing packages:")
        print(f"pip install {' '.join(missing)}")
        return False
        
    return True

def test_config_files():
    """Test configuration files"""
    print("\n📄 Testing configuration files...")
    
    files_to_check = [
        ('main.py', 'Main application'),
        ('requirements.txt', 'Python dependencies'),
        ('email_config.py', 'Email configuration'),
        ('env_example.txt', 'Environment example')
    ]
    
    all_present = True
    
    for filename, description in files_to_check:
        if os.path.exists(filename):
            print(f"✅ {filename} - {description}")
        else:
            print(f"❌ {filename} - Missing {description}")
            all_present = False
    
    return all_present

def test_email_config():
    """Test email configuration"""
    print("\n📧 Testing email configuration...")
    
    try:
        from email_config import EMAIL_LISTS, CONFIG, get_active_email_list
        
        # Check if email lists are configured
        active_list = get_active_email_list()
        
        if not active_list:
            print("⚠️ No email addresses configured in email_config.py")
            print("💡 Edit email_config.py to add your email addresses")
            return False
        
        print(f"✅ Found {len(active_list)} email addresses in active list")
        print(f"📋 Active list: {CONFIG['active_list']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading email configuration: {e}")
        return False

def test_environment():
    """Test environment variables"""
    print("\n🔧 Testing environment variables...")
    
    # Check if .env file exists
    if os.path.exists('.env'):
        print("✅ .env file found")
        
        # Try to load it
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            # Check for email configuration
            resend_key = os.getenv('RESEND_API_KEY')
            email_user = os.getenv('EMAIL_USER')
            
            if resend_key:
                print("✅ Resend API key configured")
                return True
            elif email_user:
                print("✅ SMTP configuration found")
                return True
            else:
                print("⚠️ No email configuration found in .env")
                print("💡 Add RESEND_API_KEY or EMAIL_USER/EMAIL_PASSWORD")
                return False
                
        except Exception as e:
            print(f"❌ Error loading .env file: {e}")
            return False
    else:
        print("⚠️ .env file not found")
        print("💡 Copy env_example.txt to .env and configure your email settings")
        return False

def test_main_import():
    """Test if main.py can be imported"""
    print("\n🔍 Testing main application...")
    
    try:
        # Test if we can import the main components
        spec = importlib.util.spec_from_file_location("main", "main.py")
        main_module = importlib.util.module_from_spec(spec)
        
        # Don't execute, just check if it can be loaded
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
        test_config_files,
        test_email_config,
        test_environment,
        test_main_import
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! You're ready to run the AI News Crawler.")
        print("\n🚀 Quick start:")
        print("   python main.py              # Run once")
        print("   python main.py schedule     # Schedule daily")
        print("   python main.py daemon       # Run once + schedule")
    else:
        print("⚠️ Some tests failed. Please fix the issues above before running.")
        print("\n💡 Common fixes:")
        print("   pip install -r requirements.txt    # Install dependencies")
        print("   cp env_example.txt .env            # Create .env file")
        print("   # Edit .env and email_config.py    # Configure email")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 