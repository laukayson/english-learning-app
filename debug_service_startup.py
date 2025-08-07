#!/usr/bin/env python3
"""
Simplified test of app startup to debug service initialization
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

print("Starting service initialization test...")

# Test each service individually
services_status = {}

print("\n1. Testing ConversationalAI...")
try:
    from conversational_ai import ConversationalAI
    conversational_ai = ConversationalAI()
    services_status['conversational_ai'] = True
    print("✓ ConversationalAI: SUCCESS")
except Exception as e:
    services_status['conversational_ai'] = False
    print(f"✗ ConversationalAI: FAILED - {e}")

print("\n2. Testing TranslationService...")
try:
    from translation_service import TranslationService
    translation_service = TranslationService()
    services_status['translation_service'] = True
    print("✓ TranslationService: SUCCESS")
    
    # Check translate_text method
    if hasattr(translation_service, 'translate_text'):
        print("✓ translate_text method: EXISTS")
    else:
        print("✗ translate_text method: MISSING")
        available_methods = [m for m in dir(translation_service) if not m.startswith('_')]
        print(f"Available methods: {available_methods}")
        
except Exception as e:
    services_status['translation_service'] = False
    print(f"✗ TranslationService: FAILED - {e}")

print("\n3. Testing VoiceService...")
try:
    from voice_service import VoiceService
    voice_service = VoiceService()
    services_status['voice_service'] = True
    print("✓ VoiceService: SUCCESS")
except Exception as e:
    services_status['voice_service'] = False
    print(f"✗ VoiceService: FAILED - {e}")

print("\n4. Testing ProgressTracker...")
try:
    from services.progress_tracker import ProgressTracker
    # Use a test database path
    test_db_path = os.path.join(os.path.dirname(__file__), 'data', 'db', 'test_language_app.db')
    os.makedirs(os.path.dirname(test_db_path), exist_ok=True)
    
    progress_tracker = ProgressTracker(test_db_path)
    services_status['progress_tracker'] = True
    print("✓ ProgressTracker: SUCCESS")
except Exception as e:
    services_status['progress_tracker'] = False
    print(f"✗ ProgressTracker: FAILED - {e}")

print("\n5. Testing RateLimiter...")
try:
    from rate_limiter import RateLimiter
    rate_limiter = RateLimiter()
    services_status['rate_limiter'] = True
    print("✓ RateLimiter: SUCCESS")
except Exception as e:
    services_status['rate_limiter'] = False
    print(f"✗ RateLimiter: FAILED - {e}")

print(f"\n=== SUMMARY ===")
for service, status in services_status.items():
    status_str = "✓ SUCCESS" if status else "✗ FAILED"
    print(f"{service}: {status_str}")

success_count = sum(services_status.values())
total_count = len(services_status)
print(f"\nOverall: {success_count}/{total_count} services initialized successfully")

if success_count == total_count:
    print("\n🎉 All services should work correctly in the main app!")
else:
    print(f"\n⚠️  {total_count - success_count} services need fixing before the app will work properly")
