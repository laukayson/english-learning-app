#!/usr/bin/env python3
"""
Production readiness check for PythonAnywhere deployment
"""

import os
import sys

def check_production_readiness():
    """Check if the app is ready for PythonAnywhere deployment"""
    print("🔍 Checking Production Readiness for PythonAnywhere")
    print("="*60)
    
    issues = []
    checks_passed = 0
    total_checks = 0
    
    # Check 1: Required files exist
    total_checks += 1
    required_files = [
        'wsgi.py',
        'requirements_pythonanywhere.txt',
        '.env.production',
        'backend/app_pythonanywhere.py',
        'frontend/index.html'
    ]
    
    print("📁 Checking required files:")
    all_files_exist = True
    for file in required_files:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file}")
            all_files_exist = False
            issues.append(f"Missing required file: {file}")
    
    if all_files_exist:
        checks_passed += 1
    
    # Check 2: No test files remain
    total_checks += 1
    print(f"\n🧹 Checking for test/debug files:")
    test_patterns = ['test_', 'debug_', 'fix_', 'start_']
    found_test_files = []
    
    for file in os.listdir('.'):
        if any(file.startswith(pattern) for pattern in test_patterns):
            found_test_files.append(file)
    
    if found_test_files:
        print(f"   ⚠️  Found test/debug files: {found_test_files}")
        issues.append(f"Test files should be removed: {found_test_files}")
    else:
        print(f"   ✅ No test/debug files found")
        checks_passed += 1
    
    # Check 3: Production environment configuration
    total_checks += 1
    print(f"\n⚙️ Checking production configuration:")
    try:
        with open('.env.production', 'r') as f:
            content = f.read()
            if 'CHATBOT_HEADLESS=true' in content and 'STT_HEADLESS=true' in content:
                print(f"   ✅ Production environment configured (headless browsers)")
                checks_passed += 1
            else:
                print(f"   ❌ Production environment not properly configured")
                issues.append("Production environment file missing headless configuration")
    except Exception as e:
        print(f"   ❌ Error reading .env.production: {e}")
        issues.append("Cannot read production environment file")
    
    # Check 4: WSGI configuration
    total_checks += 1
    print(f"\n🌐 Checking WSGI configuration:")
    try:
        with open('wsgi.py', 'r') as f:
            content = f.read()
            if 'app_pythonanywhere' in content and 'laukayson' in content:
                print(f"   ✅ WSGI configured for PythonAnywhere")
                checks_passed += 1
            else:
                print(f"   ❌ WSGI not properly configured for PythonAnywhere")
                issues.append("WSGI file not configured for PythonAnywhere")
    except Exception as e:
        print(f"   ❌ Error reading wsgi.py: {e}")
        issues.append("Cannot read WSGI file")
    
    # Check 5: Backend configuration
    total_checks += 1
    print(f"\n🔧 Checking backend configuration:")
    sys.path.append('backend')
    try:
        from chatbot_config import ChatbotConfig
        if hasattr(ChatbotConfig, 'CHATBOT_HEADLESS') and hasattr(ChatbotConfig, 'STT_HEADLESS'):
            print(f"   ✅ ChatbotConfig loaded successfully")
            print(f"   ℹ️  Default settings: Chatbot headless={ChatbotConfig.CHATBOT_HEADLESS}, STT headless={ChatbotConfig.STT_HEADLESS}")
            checks_passed += 1
        else:
            print(f"   ❌ ChatbotConfig missing required attributes")
            issues.append("ChatbotConfig not properly configured")
    except Exception as e:
        print(f"   ❌ Error loading ChatbotConfig: {e}")
        issues.append(f"Cannot load ChatbotConfig: {e}")
    
    # Summary
    print(f"\n" + "="*60)
    print(f"📊 Production Readiness Summary:")
    print(f"✅ Checks passed: {checks_passed}/{total_checks}")
    
    if issues:
        print(f"❌ Issues found: {len(issues)}")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print(f"🎉 All checks passed!")
    
    print(f"\n🚀 Deployment Status:")
    if checks_passed == total_checks:
        print(f"✅ READY FOR PYTHONANYWHERE DEPLOYMENT")
        print(f"📱 Upload to: laukayson.pythonanywhere.com")
        print(f"📋 Follow: PYTHONANYWHERE_DEPLOYMENT.md")
    else:
        print(f"⚠️  NEEDS ATTENTION BEFORE DEPLOYMENT")
        print(f"🔧 Fix the issues listed above first")
    
    return checks_passed == total_checks

if __name__ == "__main__":
    check_production_readiness()
