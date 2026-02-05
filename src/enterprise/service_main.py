"""
Service Entry Point
Imports and integrates all existing components
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from enterprise.service_core import EnterpriseMonitoringService

if __name__ == '__main__':
    # Service entry point
    import win32serviceutil
    import win32service
    import servicemanager
    
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(EnterpriseMonitoringService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(EnterpriseMonitoringService)