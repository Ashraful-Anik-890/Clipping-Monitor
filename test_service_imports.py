"""
Test script to verify service imports work correctly
Run this to check if the service will be able to import all required modules
"""

import sys
from pathlib import Path

# Add paths like the service does
current_dir = Path(__file__).parent / "src" / "enterprise"
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "enterprise"))

print("Testing imports...")
print(f"Python path: {sys.path[:3]}")
print()

# Test 1: Centralized paths
try:
    from enterprise.paths import (
        initialize_all_directories,
        get_logs_dir,
        get_data_dir,
        get_database_path,
        get_keystroke_storage_dir
    )
    print("✓ enterprise.paths imports OK")
except ImportError as e:
    print(f"✗ enterprise.paths import failed: {e}")
    sys.exit(1)

# Test 2: Config
try:
    from enterprise.config import Config
    print("✓ enterprise.config imports OK")
except ImportError as e:
    print(f"✗ enterprise.config import failed: {e}")
    sys.exit(1)

# Test 3: Database manager
try:
    from enterprise.database_manager import DatabaseManager
    print("✓ enterprise.database_manager imports OK")
except ImportError as e:
    print(f"✗ enterprise.database_manager import failed: {e}")
    sys.exit(1)

# Test 4: Keystroke recorder
try:
    from enterprise.keystroke_recorder import KeystrokeRecorder
    print("✓ enterprise.keystroke_recorder imports OK")
except ImportError as e:
    print(f"✗ enterprise.keystroke_recorder import failed: {e}")
    sys.exit(1)

# Test 5: App usage tracker
try:
    from enterprise.app_usage_tracker import ApplicationUsageTracker
    print("✓ enterprise.app_usage_tracker imports OK")
except ImportError as e:
    print(f"✗ enterprise.app_usage_tracker import failed: {e}")
    sys.exit(1)

# Test 6: Browser tracker
try:
    from enterprise.browser_tracker import BrowserActivityTracker
    print("✓ enterprise.browser_tracker imports OK")
except ImportError as e:
    print(f"✗ enterprise.browser_tracker import failed: {e}")
    sys.exit(1)

# Test 7: Clipboard monitor (in parent src directory)
try:
    from clipboard_monitor import ClipboardMonitor
    print("✓ clipboard_monitor imports OK")
except ImportError as e:
    print(f"✗ clipboard_monitor import failed: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✓ ALL IMPORTS SUCCESSFUL!")
print("=" * 60)
print()
print("The service should now be able to start without import errors.")
print("Next steps:")
print("1. Install service: python src/enterprise/service_main.py install")
print("2. Start service: python src/enterprise/service_main.py start")
print("3. Check logs: C:\\ProgramData\\EnterpriseMonitoring\\logs\\service.log")
