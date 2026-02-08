"""
Standalone Runner for Enterprise Monitoring Agent

This script runs the monitoring agent WITHOUT using Windows Service APIs.
It can be:
1. Run directly from command line
2. Wrapped as a service using NSSM (Non-Sucking Service Manager)
3. Run via Windows Task Scheduler
4. Used with any other service management tool

This is more reliable than native Windows services for Python applications.

Usage:
    python standalone_runner.py                    # Run interactively
    pythonw standalone_runner.py                   # Run hidden (no console)
    nssm install MonitoringAgent python standalone_runner.py  # Via NSSM
"""

import sys
import os
import time
import logging
from pathlib import Path
from datetime import datetime
import traceback
import signal

# Add project paths
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(src_dir / "enterprise"))

# Import path management
try:
    from enterprise.paths import (
        initialize_all_directories,
        get_logs_dir,
        get_data_dir
    )
    initialize_all_directories()
    log_dir = get_logs_dir()
except Exception as e:
    print(f"Error initializing paths: {e}")
    # Fallback
    log_dir = Path(os.getenv('PROGRAMDATA', 'C:/ProgramData')) / 'EnterpriseMonitoring' / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)

# Setup logging
log_file = log_dir / f'standalone_{datetime.now().strftime("%Y%m%d")}.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('StandaloneRunner')

# Global flag for graceful shutdown
should_stop = False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global should_stop
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    should_stop = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def main():
    """Main execution function"""
    global should_stop
    
    logger.info("="*80)
    logger.info("Enterprise Monitoring Agent - Standalone Runner Starting")
    logger.info(f"Python: {sys.version}")
    logger.info(f"Working Directory: {os.getcwd()}")
    logger.info(f"Log File: {log_file}")
    logger.info("="*80)
    
    # Import monitoring components
    try:
        logger.info("Importing monitoring components...")
        from clipboard_monitor import ClipboardMonitor
        from enterprise.app_usage_tracker import ApplicationUsageTracker
        from enterprise.browser_tracker import BrowserActivityTracker
        from enterprise.database_manager import DatabaseManager
        from enterprise.keystroke_recorder import KeystrokeRecorder
        from enterprise.config import Config
        from enterprise.paths import get_database_path, get_keystroke_storage_dir
        logger.info("✓ All components imported successfully")
    except ImportError as e:
        logger.error(f"✗ Failed to import components: {e}")
        logger.error(traceback.format_exc())
        return 1
    
    # Load configuration
    try:
        logger.info("Loading configuration...")
        config = Config()
        logger.info("✓ Configuration loaded")
    except Exception as e:
        logger.warning(f"Could not load config: {e}, using defaults")
        config = None
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        db_path = get_database_path()
        db = DatabaseManager(db_path, enable_encryption=True)
        logger.info(f"✓ Database initialized at {db_path}")
    except Exception as e:
        logger.error(f"✗ Database initialization failed: {e}")
        return 1
    
    # Initialize monitors
    monitors = []
    
    # Clipboard monitor
    try:
        logger.info("Initializing clipboard monitor...")
        clipboard_monitor = ClipboardMonitor(
            callback=lambda event: db.log_clipboard_event(**event),
            polling_interval=0.5
        )
        monitors.append(('clipboard', clipboard_monitor))
        logger.info("✓ Clipboard monitor ready")
    except Exception as e:
        logger.warning(f"Clipboard monitor disabled: {e}")
    
    # Application tracker
    try:
        logger.info("Initializing application tracker...")
        app_tracker = ApplicationUsageTracker(
            callback=lambda event: db.log_app_usage(**event)
        )
        monitors.append(('app_usage', app_tracker))
        logger.info("✓ Application tracker ready")
    except Exception as e:
        logger.warning(f"Application tracker disabled: {e}")
    
    # Browser tracker
    try:
        logger.info("Initializing browser tracker...")
        browser_tracker = BrowserActivityTracker(
            callback=lambda event: db.log_browser_activity(**event)
        )
        monitors.append(('browser', browser_tracker))
        logger.info("✓ Browser tracker ready")
    except Exception as e:
        logger.warning(f"Browser tracker disabled: {e}")
    
    # Keystroke recorder (if enabled)
    if config and config.get('monitoring', {}).get('keystrokes', {}).get('enabled', False):
        try:
            logger.info("Initializing keystroke recorder...")
            keystroke_config = config.get('keystrokes', {})
            keystroke_recorder = KeystrokeRecorder(
                storage_dir=get_keystroke_storage_dir(),
                enable_encryption=keystroke_config.get('encryption_enabled', True),
                buffer_flush_interval=keystroke_config.get('buffer_flush_interval', 60)
            )
            monitors.append(('keystrokes', keystroke_recorder))
            logger.info("✓ Keystroke recorder ready")
        except Exception as e:
            logger.warning(f"Keystroke recorder disabled: {e}")
    
    logger.info(f"Starting {len(monitors)} monitors...")
    
    # Start all monitors
    for name, monitor in monitors:
        try:
            monitor.start()
            logger.info(f"✓ Started: {name}")
        except Exception as e:
            logger.error(f"✗ Failed to start {name}: {e}")
    
    logger.info("="*80)
    logger.info("MONITORING AGENT RUNNING")
    logger.info(f"Active monitors: {len(monitors)}")
    logger.info("Press Ctrl+C to stop")
    logger.info("="*80)
    
    # Main loop - keep running until stop signal
    try:
        last_health_check = time.time()
        health_check_interval = 300  # 5 minutes
        
        while not should_stop:
            time.sleep(1)
            
            # Periodic health check
            current_time = time.time()
            if current_time - last_health_check >= health_check_interval:
                running_count = 0
                for name, monitor in monitors:
                    try:
                        if hasattr(monitor, 'is_monitoring') and monitor.is_monitoring():
                            running_count += 1
                        elif hasattr(monitor, 'is_running') and monitor.is_running:
                            running_count += 1
                    except:
                        pass
                
                logger.info(f"Health check: {running_count}/{len(monitors)} monitors running")
                last_health_check = current_time
                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Error in main loop: {e}")
        logger.error(traceback.format_exc())
    
    # Shutdown
    logger.info("Shutting down monitors...")
    for name, monitor in monitors:
        try:
            monitor.stop()
            logger.info(f"✓ Stopped: {name}")
        except Exception as e:
            logger.error(f"Error stopping {name}: {e}")
    
    logger.info("Enterprise Monitoring Agent stopped")
    return 0

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        logger.critical(traceback.format_exc())
        sys.exit(1)
