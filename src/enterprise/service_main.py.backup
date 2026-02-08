"""
Service Entry Point - Use this file to install/manage the Windows service

This is the ONLY file that should be used to control the Windows service.
DO NOT run service_core.py directly as it will cause service startup errors.

Usage:
    python service_main.py install   - Install the service
    python service_main.py start     - Start the service  
    python service_main.py stop      - Stop the service
    python service_main.py remove    - Remove the service
    python service_main.py restart   - Restart the service
    python service_main.py debug     - Run in debug mode (not as service)
"""

import sys
import logging
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enterprise.service_core import (
    EnterpriseMonitoringService,
    install_service,
    start_service,
    stop_service,
    remove_service,
    MonitoringEngine
)

if __name__ == '__main__':
    # Service entry point
    import win32serviceutil
    import win32service
    import servicemanager
    
    if len(sys.argv) == 1:
        # No arguments - run as service (called by Windows SCM)
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(EnterpriseMonitoringService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Command-line arguments provided
        command = sys.argv[1].lower()
        
        if command == 'install':
            install_service()
        elif command == 'start':
            start_service()
        elif command == 'stop':
            stop_service()
        elif command == 'remove' or command == 'uninstall':
            remove_service()
        elif command == 'restart':
            stop_service()
            time.sleep(2)
            start_service()
        elif command == 'debug':
            # Run in debug mode (not as Windows service)
            print("Running service in debug mode...")
            print("Press Ctrl+C to stop")
            try:
                engine = MonitoringEngine()
                engine.start_all_monitors()
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping...")
                engine.stop_all_monitors()
        else:
            # Use default handler for standard service commands
            win32serviceutil.HandleCommandLine(EnterpriseMonitoringService)