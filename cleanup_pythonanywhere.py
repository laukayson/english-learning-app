#!/usr/bin/env python3
"""
Cleanup script for PythonAnywhere-only deployment
Identifies and optionally removes files that are no longer needed
"""
import os
import shutil
from pathlib import Path

# Files and directories that are no longer needed for PythonAnywhere-only deployment
CLEANUP_ITEMS = {
    'files_to_remove': [
        # Old local selenium files (now using Render service)
        'backend/selenium_chatbot.py',
        'backend/chatbot.py', 
        'backend/chatbot_manager.py',
        'backend/chatbot_config.py',
        
        # Backup files
        'backend/free_speech_service_BACKUP_OLD_STT.py',
        'backend/voice_service_BACKUP_OLD_STT.py',
        
        # Old configuration files
        'backend/config.py',  # Using config_pythonanywhere.py instead
        'backend/config_deployment.py',  # Not needed for PythonAnywhere
        'backend/app.py',  # Using app_pythonanywhere.py instead
        
        # Test and debug files (can be moved to a separate folder)
        'debug_phantom_text.py',
        'debug_stt.py',
        'start_debug.py',
        'test_env.py',
        'test_functionality.py',
        'test_imports.py',
        'test_speechtexter_startup.py',
        'test_start_stop_stt.py',
        'test_stt_sync.py',
        'test_voice_recording.py',
        'debug_service_startup.py',
        'test_services_quick.py',
        'test_backend_startup.py',
        'test_service_initialization.py',
        'test_progress_tracker.py',
        
        # HTML test files
        'test_speechtexter.html',
        'test_web_stt.html',
        
        # Old batch files for local development
        'cleanup_docs.bat',
        'START_BACKEND_ADVANCED_CONFIG.bat',
        'START_BACKEND_DEBUG_AI.bat',
        'START_BACKEND_DEBUG_STT.bat',
        'START_BACKEND_FULL_DEBUG.bat',
        'START_BACKEND_SIMPLE.bat',
        'START_BACKEND_STT.bat',
        'START_BACKEND.bat',
        'START_WITH_SPEECHTEXTER.bat',
        'start_with_venv.bat',
        'TEST_BACKEND_CONNECTION.bat',
        'TEST_STT_SYNC.bat',
        'VIEW_DATABASE_WEB.bat',
        
        # Integration files not needed for PythonAnywhere
        'pythonanywhere_integration.py',
        'pythonanywhere_wsgi_config_template.py',
        'check_production.py',
        
        # Fix scripts that are no longer needed
        'fix_chrome_permissions.py',
    ],
    
    'directories_to_remove': [
        # Replit files not needed for PythonAnywhere
        'replit_files/',
        
        # Render service directory (deployed separately on Render)
        'render_selenium_service/',
    ],
    
    'files_to_keep_as_reference': [
        # Documentation files to keep
        'README.md',
        'QUICK_START.md',
        'DEPLOYMENT_CHECKLIST.md',
        'DEBUGGING_MODE_GUIDE.md',
        'REPOSITORY_CLEANUP_GUIDE.md',
        'STT_VERIFICATION_GUIDE.md',
        'WEB_STT_IMPLEMENTATION.md',
        
        # Summary files
        'CLEANUP_SUMMARY.md',
        'OLD_STT_CLEANUP_SUMMARY.md',
        'SPEECHTEXTER_MIGRATION_SUMMARY.md',
        'BROWSER_PERSISTENCE_FIXES.md',
        
        # Requirements files
        'requirements.txt',
        'requirements_pythonanywhere.txt',
        'setup.py',
        'wsgi.py',
    ]
}

def analyze_workspace():
    """Analyze the workspace and categorize files"""
    workspace_root = Path('.')
    
    print("=== PythonAnywhere Deployment Cleanup Analysis ===\n")
    
    # Files that should be removed
    print("📁 Files recommended for removal (no longer needed):")
    files_to_remove = []
    for file_path in CLEANUP_ITEMS['files_to_remove']:
        full_path = workspace_root / file_path
        if full_path.exists():
            files_to_remove.append(full_path)
            print(f"  ✓ {file_path} ({full_path.stat().st_size // 1024}KB)")
        else:
            print(f"  - {file_path} (not found)")
    
    print(f"\n📂 Directories recommended for removal:")
    dirs_to_remove = []
    for dir_path in CLEANUP_ITEMS['directories_to_remove']:
        full_path = workspace_root / dir_path
        if full_path.exists():
            dirs_to_remove.append(full_path)
            dir_size = sum(f.stat().st_size for f in full_path.rglob('*') if f.is_file())
            print(f"  ✓ {dir_path} ({dir_size // 1024}KB)")
        else:
            print(f"  - {dir_path} (not found)")
    
    print(f"\n📄 Important files to keep:")
    for file_path in CLEANUP_ITEMS['files_to_keep_as_reference']:
        full_path = workspace_root / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  - {file_path} (not found)")
    
    # Essential PythonAnywhere files
    essential_files = [
        'backend/app_pythonanywhere.py',
        'backend/config_pythonanywhere.py',
        'backend/conversational_ai.py',
        'backend/translation_service.py',
        'backend/voice_service.py',
        'backend/rate_limiter.py',
        'backend/services/progress_tracker.py',
        'render_selenium_client.py',
        'frontend/index.html',
        'frontend/js/',
        'frontend/styles/',
    ]
    
    print(f"\n🔧 Essential PythonAnywhere files (must keep):")
    for file_path in essential_files:
        full_path = workspace_root / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ⚠️ {file_path} (MISSING - required!)")
    
    total_removable_size = sum(f.stat().st_size for f in files_to_remove if f.is_file())
    total_removable_size += sum(sum(f.stat().st_size for f in d.rglob('*') if f.is_file()) for d in dirs_to_remove if d.is_dir())
    
    print(f"\n📊 Summary:")
    print(f"  Files to remove: {len(files_to_remove)}")
    print(f"  Directories to remove: {len(dirs_to_remove)}")
    print(f"  Total size to be freed: {total_removable_size // 1024}KB")
    
    return files_to_remove, dirs_to_remove

def perform_cleanup(files_to_remove, dirs_to_remove, dry_run=True):
    """Perform the actual cleanup"""
    if dry_run:
        print(f"\n🔍 DRY RUN - No files will be actually removed")
        return
    
    print(f"\n🗑️ Performing cleanup...")
    
    # Remove files
    for file_path in files_to_remove:
        try:
            file_path.unlink()
            print(f"  ✓ Removed file: {file_path}")
        except Exception as e:
            print(f"  ✗ Failed to remove {file_path}: {e}")
    
    # Remove directories
    for dir_path in dirs_to_remove:
        try:
            shutil.rmtree(dir_path)
            print(f"  ✓ Removed directory: {dir_path}")
        except Exception as e:
            print(f"  ✗ Failed to remove {dir_path}: {e}")
    
    print(f"\n✅ Cleanup completed!")

if __name__ == '__main__':
    # Change to the workspace directory
    os.chdir(Path(__file__).parent)
    
    files_to_remove, dirs_to_remove = analyze_workspace()
    
    print(f"\n" + "="*60)
    print("Would you like to perform the cleanup?")
    print("This will permanently delete the identified files and directories.")
    print("="*60)
    
    # For now, always do a dry run - user can modify this script to actually perform cleanup
    perform_cleanup(files_to_remove, dirs_to_remove, dry_run=True)
    
    print(f"\n💡 To actually perform the cleanup, set dry_run=False in the perform_cleanup call.")
    print(f"⚠️ Make sure you have a backup before doing this!")
