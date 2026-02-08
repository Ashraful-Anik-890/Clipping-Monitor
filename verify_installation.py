"""
Enterprise Monitoring Agent - Installation Verification Script

This script verifies that the application is correctly installed and configured
before attempting to run as a Windows service.

Run this script to:
1. Check Python version and dependencies
2. Verify directory structure
3. Test module imports
4. Validate configuration
5. Check Windows service prerequisites
"""

import sys
import os
from pathlib import Path
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class Color:
    """ANSI color codes"""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Print section header"""
    print(f"\n{Color.BLUE}{Color.BOLD}{'='*70}")
    print(f"{text}")
    print(f"{'='*70}{Color.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Color.GREEN}✓ {text}{Color.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Color.YELLOW}⚠ {text}{Color.END}")


def print_error(text):
    """Print error message"""
    print(f"{Color.RED}✗ {text}{Color.END}")


def check_python_version():
    """Check Python version"""
    print_header("1. Checking Python Version")
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print_success("Python version is compatible (3.8+)")
        return True
    else:
        print_error("Python 3.8 or higher is required")
        return False


def check_platform():
    """Check if running on Windows"""
    print_header("2. Checking Platform")
    
    if sys.platform == 'win32':
        print_success(f"Running on Windows ({sys.platform})")
        return True
    else:
        print_error(f"This application only runs on Windows (detected: {sys.platform})")
        return False


def check_dependencies():
    """Check if required packages are installed"""
    print_header("3. Checking Dependencies")
    
    required_packages = {
        'pywin32': 'win32api',
        'psutil': 'psutil',
        'cryptography': 'cryptography',
        'pystray': 'pystray',
        'PIL': 'PIL',
        'pynput': 'pynput',
    }
    
    missing = []
    installed = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            installed.append(package_name)
            print_success(f"{package_name} is installed")
        except ImportError:
            missing.append(package_name)
            print_error(f"{package_name} is NOT installed")
    
    if missing:
        print(f"\n{Color.YELLOW}To install missing packages:{Color.END}")
        print(f"  pip install {' '.join(missing)}")
        return False
    else:
        print_success("\nAll required dependencies are installed")
        return True


def check_directory_structure():
    """Check if required directories can be created"""
    print_header("4. Checking Directory Structure")
    
    # Add project to path
    project_root = Path(__file__).parent.absolute()
    sys.path.insert(0, str(project_root / 'src'))
    sys.path.insert(0, str(project_root / 'src' / 'enterprise'))
    
    try:
        from enterprise.paths import (
            get_program_data_dir,
            get_logs_dir,
            get_data_dir,
            get_config_dir,
            initialize_all_directories
        )
        
        print_success("paths.py module loaded successfully")
        
        # Initialize directories
        initialize_all_directories()
        
        # Check each directory
        dirs_to_check = {
            'ProgramData': get_program_data_dir(),
            'Logs': get_logs_dir(),
            'Data': get_data_dir(),
            'Config': get_config_dir(),
        }
        
        all_ok = True
        for name, path in dirs_to_check.items():
            if path.exists():
                print_success(f"{name} directory: {path}")
            else:
                print_error(f"{name} directory does not exist: {path}")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print_error(f"Error checking directories: {e}")
        return False


def check_module_imports():
    """Test importing core modules"""
    print_header("5. Testing Module Imports")
    
    modules_to_test = [
        'enterprise.paths',
        'enterprise.config',
        'enterprise.keystroke_recorder',
        'enterprise.database_manager',
        'enterprise.service_core',
        'enterprise.admin_auth',
    ]
    
    all_ok = True
    for module_name in modules_to_test:
        try:
            __import__(module_name)
            print_success(f"Successfully imported {module_name}")
        except Exception as e:
            print_error(f"Failed to import {module_name}: {e}")
            all_ok = False
    
    return all_ok


def check_config():
    """Validate configuration"""
    print_header("6. Checking Configuration")
    
    try:
        from enterprise.config import Config
        
        config = Config()
        print_success("Configuration loaded successfully")
        
        # Validate config
        if config.validate():
            print_success("Configuration is valid")
        else:
            print_error("Configuration validation failed")
            return False
        
        # Print key settings
        print(f"\nKey Configuration Settings:")
        monitoring = config.get('monitoring', {})
        print(f"  Clipboard: {monitoring.get('clipboard', False)}")
        print(f"  Applications: {monitoring.get('applications', False)}")
        print(f"  Browser: {monitoring.get('browser', False)}")
        print(f"  Keystrokes: {monitoring.get('keystrokes', False)}")
        print(f"  Screen Recording: {monitoring.get('screen_recording', False)}")
        
        return True
        
    except Exception as e:
        print_error(f"Error checking configuration: {e}")
        return False


def check_admin_privileges():
    """Check if running with admin privileges"""
    print_header("7. Checking Administrator Privileges")
    
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        
        if is_admin:
            print_success("Running with administrator privileges")
        else:
            print_warning("NOT running with administrator privileges")
            print("  Note: Administrator privileges are required to install/manage the Windows service")
        
        return is_admin
        
    except Exception as e:
        print_error(f"Could not check admin privileges: {e}")
        return False


def check_service_prerequisites():
    """Check Windows service prerequisites"""
    print_header("8. Checking Service Prerequisites")
    
    try:
        import win32serviceutil
        import win32service
        print_success("pywin32 service modules available")
        
        # Check if service is installed
        try:
            from enterprise.service_core import EnterpriseMonitoringService
            service_name = EnterpriseMonitoringService._svc_name_
            
            status = win32serviceutil.QueryServiceStatus(service_name)
            print_success(f"Service '{service_name}' is installed")
            
            state = status[1]
            if state == win32service.SERVICE_RUNNING:
                print_success("Service is RUNNING")
            elif state == win32service.SERVICE_STOPPED:
                print_warning("Service is STOPPED")
            else:
                print(f"Service state: {state}")
                
        except Exception as e:
            print_warning(f"Service is not installed: {e}")
        
        return True
        
    except Exception as e:
        print_error(f"Error checking service prerequisites: {e}")
        return False


def main():
    """Run all verification checks"""
    print(f"\n{Color.BOLD}Enterprise Monitoring Agent - Installation Verification{Color.END}")
    print("=" * 70)
    
    checks = [
        ("Python Version", check_python_version),
        ("Platform", check_platform),
        ("Dependencies", check_dependencies),
        ("Directory Structure", check_directory_structure),
        ("Module Imports", check_module_imports),
        ("Configuration", check_config),
        ("Admin Privileges", check_admin_privileges),
        ("Service Prerequisites", check_service_prerequisites),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print_error(f"Unexpected error in {name}: {e}")
            results.append((name, False))
    
    # Summary
    print_header("VERIFICATION SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = f"{Color.GREEN}PASS{Color.END}" if result else f"{Color.RED}FAIL{Color.END}"
        print(f"  {name:.<30} {status}")
    
    print(f"\n{passed}/{total} checks passed")
    
    if passed == total:
        print(f"\n{Color.GREEN}{Color.BOLD}✓ All verification checks passed!{Color.END}")
        print(f"\n{Color.BOLD}Next Steps:{Color.END}")
        print("1. Run the Admin Console: python src/enterprise/admin_console.py")
        print("2. Create admin password (first-time setup)")
        print("3. Install the service using the Admin Console")
        print("4. Start the service")
        return 0
    else:
        print(f"\n{Color.RED}{Color.BOLD}✗ Some verification checks failed{Color.END}")
        print(f"\n{Color.BOLD}Action Required:{Color.END}")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Ensure running on Windows as Administrator")
        print("3. Re-run this verification script")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n\n{Color.YELLOW}Verification interrupted by user{Color.END}")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Color.RED}Unexpected error: {e}{Color.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
