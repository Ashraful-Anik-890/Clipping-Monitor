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

# Fix Python path to find modules
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "enterprise"))

# Import centralized path management FIRST
try:
    from enterprise.paths import (
        initialize_all_directories,
        get_logs_dir,
        get_data_dir,
        get_database_path,
        get_keystroke_storage_dir
    )
    # Initialize all required directories
    initialize_all_directories()
except ImportError as e:
    print(f"Error importing paths module: {e}")
    # Fallback to basic directory creation
    from pathlib import Path
    program_data_dir = Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) / 'EnterpriseMonitoring'
    program_data_dir.mkdir(parents=True, exist_ok=True)
    (program_data_dir / 'logs').mkdir(parents=True, exist_ok=True)
    (program_data_dir / 'data').mkdir(parents=True, exist_ok=True)
    (program_data_dir / 'config').mkdir(parents=True, exist_ok=True)

# Configure logging for service
try:
    log_dir = get_logs_dir()
except:
    log_dir = Path(os.environ.get('PROGRAMDATA', 'C:/ProgramData')) / 'EnterpriseMonitoring' / 'logs'
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
    
    def __init__(self, config=None):
        """
        Initialize monitoring engine.
        
        Args:
            config: Optional Config instance. If None, will create default.
        """
        self.is_running = False
        self.monitors = []
        self.config = config
        
        # Import monitoring components
        try:
            from clipboard_monitor import ClipboardMonitor
            from enterprise.app_usage_tracker import ApplicationUsageTracker
            from enterprise.browser_tracker import BrowserActivityTracker
            from enterprise.database_manager import DatabaseManager
            from enterprise.keystroke_recorder import KeystrokeRecorder
            from enterprise.config import Config
            
            # Load config if not provided
            if self.config is None:
                try:
                    self.config = Config()
                except Exception as e:
                    logger.error(f"Error loading config: {e}")
                    self.config = None
            
            # Initialize database
            try:
                db_path = get_database_path()
                db_path.parent.mkdir(parents=True, exist_ok=True)
                self.db = DatabaseManager(db_path, enable_encryption=True)
                logger.info(f"Database initialized at {db_path}")
            except Exception as e:
                logger.error(f"Error initializing database: {e}")
                raise
            
            # Initialize monitors based on config
            # Clipboard Monitor
            if self._is_monitor_enabled('clipboard'):
                try:
                    self.clipboard_monitor = ClipboardMonitor(
                        callback=self.on_clipboard_event,
                        polling_interval=0.5
                    )
                    self.monitors.append(('clipboard', self.clipboard_monitor))
                    logger.info("Clipboard monitor initialized")
                except Exception as e:
                    logger.error(f"Error initializing clipboard monitor: {e}")
            
            # Application Tracker
            if self._is_monitor_enabled('applications'):
                try:
                    self.app_tracker = ApplicationUsageTracker(
                        callback=self.on_app_usage_event
                    )
                    self.monitors.append(('app_usage', self.app_tracker))
                    logger.info("Application tracker initialized")
                except Exception as e:
                    logger.error(f"Error initializing application tracker: {e}")
            
            # Browser Tracker
            if self._is_monitor_enabled('browser'):
                try:
                    self.browser_tracker = BrowserActivityTracker(
                        callback=self.on_browser_event
                    )
                    self.monitors.append(('browser', self.browser_tracker))
                    logger.info("Browser tracker initialized")
                except Exception as e:
                    logger.error(f"Error initializing browser tracker: {e}")
            
            # Keystroke Recorder (if enabled)
            if self._is_monitor_enabled('keystrokes'):
                try:
                    keystroke_config = self.config.get('keystrokes', {}) if self.config else {}
                    self.keystroke_recorder = KeystrokeRecorder(
                        storage_dir=get_keystroke_storage_dir(),
                        callback=self.on_keystroke_event,
                        enable_encryption=keystroke_config.get('encryption_enabled', True),
                        buffer_flush_interval=keystroke_config.get('buffer_flush_interval', 60)
                    )
                    self.monitors.append(('keystrokes', self.keystroke_recorder))
                    logger.info("Keystroke recorder initialized")
                except Exception as e:
                    logger.error(f"Error initializing keystroke recorder: {e}")
            
            logger.info(f"Monitoring engine initialized with {len(self.monitors)} monitors")
            
        except ImportError as e:
            logger.error(f"Error importing monitoring components: {e}")
            raise
    
    def _is_monitor_enabled(self, monitor_name: str) -> bool:
        """
        Check if a monitor is enabled in config.
        
        Args:
            monitor_name: Name of monitor
            
        Returns:
            True if enabled (defaults to True if config not available)
        """
        if self.config is None:
            # Default to enabled if no config
            return monitor_name != 'keystrokes'  # Keystrokes disabled by default
        
        try:
            return self.config.is_monitor_enabled(monitor_name)
        except Exception as e:
            logger.warning(f"Error checking monitor status for {monitor_name}: {e}")
            return monitor_name != 'keystrokes'
    
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
        """Start all monitoring components with graceful degradation"""
        logger.info("Starting all monitors...")
        self.is_running = True
        
        started_count = 0
        failed_monitors = []
        
        for monitor_name, monitor in self.monitors:
            try:
                monitor.start()
                logger.info(f"Started: {monitor_name}")
                started_count += 1
            except Exception as e:
                logger.error(f"Failed to start {monitor_name}: {e}")
                failed_monitors.append(monitor_name)
        
        if failed_monitors:
            logger.warning(f"Some monitors failed to start: {', '.join(failed_monitors)}")
        
        logger.info(f"Started {started_count}/{len(self.monitors)} monitors successfully")
    
    def stop_all_monitors(self):
        """Stop all monitoring components"""
        logger.info("Stopping all monitors...")
        self.is_running = False
        
        for monitor_name, monitor in self.monitors:
            try:
                monitor.stop()
                logger.info(f"Stopped: {monitor_name}")
            except Exception as e:
                logger.error(f"Error stopping {monitor_name}: {e}")
        
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
                        for monitor_name, monitor in self.engine.monitors:
                            try:
                                if hasattr(monitor, 'is_monitoring'):
                                    if not monitor.is_monitoring():
                                        logger.warning(f"Monitor {monitor_name} stopped unexpectedly - attempting restart")
                                        try:
                                            monitor.start()
                                            logger.info(f"Successfully restarted {monitor_name}")
                                        except Exception as e:
                                            logger.error(f"Failed to restart {monitor_name}: {e}")
                            except Exception as e:
                                logger.error(f"Error checking {monitor_name}: {e}")
                    
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
        # Syntax: sc failure <service> reset= <seconds> actions= <action1>/delay1/action2/delay2/...
        cmd = [
            'sc', 'failure', service_name,
            'reset=', '86400',
            'actions=', 'restart/60000/restart/120000/restart/300000'
        ]
        
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info("Service recovery configured successfully")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to configure service recovery: {e}")
        logger.error(f"stderr: {e.stderr}")


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
        win32serviceutil.StopService(EnterpriseMonitoringService._svc_name_)
        logger.info("Service stopped successfully")
        print("Service stopped successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to stop service: {e}")
        print(f"ERROR: Failed to stop service - {e}")
        return False


def remove_service():
    """Remove the service"""
    try:
        logger.info("Removing service...")
        
        # Stop service first
        try:
            stop_service()
        except Exception as e:
            logger.warning(f"Error stopping service before removal: {e}")
            
        # Remove service
        win32serviceutil.HandleCommandLine(
            EnterpriseMonitoringService,
            argv=['', 'remove']
        )
        
        logger.info("Service removed successfully")
        print("Service removed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to remove service: {e}")
        print(f"ERROR: Failed to remove service - {e}")
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