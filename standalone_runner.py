r"""
Standalone Runner for Enterprise Monitoring Agent
Entry point for NSSM (Non-Sucking Service Manager) Windows Service

This script is designed to be compiled with PyInstaller and run as a Windows service
using NSSM instead of win32serviceutil.

Usage:
    nssm.exe install "EnterpriseMonitoringAgent" "C:\Path\To\EnterpriseAgent.exe"
"""

import sys
import logging
import time
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))
sys.path.insert(0, str(current_dir / "src" / "enterprise"))

# Import path utilities to ensure directories exist
from enterprise.paths import get_config_dir, get_data_dir, get_log_dir

# Configure logging before importing other modules
log_dir = get_log_dir()
log_file = log_dir / "standalone_runner.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_environment():
    """Setup the environment and ensure all required directories exist"""
    try:
        # Ensure all directories exist
        config_dir = get_config_dir()
        data_dir = get_data_dir()
        log_dir = get_log_dir()
        
        logger.info(f"Config directory: {config_dir}")
        logger.info(f"Data directory: {data_dir}")
        logger.info(f"Log directory: {log_dir}")
        
        # Verify directories were created
        if not config_dir.exists():
            raise RuntimeError(f"Failed to create config directory: {config_dir}")
        if not data_dir.exists():
            raise RuntimeError(f"Failed to create data directory: {data_dir}")
        if not log_dir.exists():
            raise RuntimeError(f"Failed to create log directory: {log_dir}")
        
        logger.info("Environment setup completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup environment: {e}", exc_info=True)
        return False


def run_service():
    """Run the enterprise monitoring service"""
    try:
        logger.info("="*70)
        logger.info("Enterprise Monitoring Agent - Starting")
        logger.info("="*70)
        
        # Setup environment
        if not setup_environment():
            logger.error("Environment setup failed. Exiting.")
            return 1
        
        # Import the service components
        logger.info("Importing service components...")
        from enterprise.config import Config
        
        # Load configuration
        logger.info("Loading configuration...")
        config = Config()
        logger.info(f"Configuration loaded: {config.config_file}")
        
        # Create service instance
        logger.info("Creating service instance...")
        
        # Since we're using NSSM, we don't use win32serviceutil
        # We'll create a simple service runner
        service = MonitoringServiceRunner(config)
        
        # Start the service
        logger.info("Starting service...")
        service.start()
        
        # Keep the service running
        logger.info("Service started successfully. Running...")
        
        try:
            while service.is_running():
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received. Stopping service...")
            service.stop()
        
        logger.info("Service stopped")
        return 0
        
    except Exception as e:
        logger.error(f"Service failed with error: {e}", exc_info=True)
        return 1


class MonitoringServiceRunner:
    """
    Simple service runner for NSSM
    This class manages the service lifecycle without using win32serviceutil
    """
    
    def __init__(self, config=None):
        self.running = False
        self.threads = []
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
    def start(self):
        """Start the monitoring service"""
        try:
            self.logger.info("Initializing monitoring components...")
            
            # Import monitoring components
            from enterprise.app_usage_tracker import ApplicationTracker
            from enterprise.browser_tracker import BrowserTracker
            from enterprise.database_manager import DatabaseManager
            
            # Initialize database
            self.logger.info("Initializing database...")
            self.db_manager = DatabaseManager()
            
            # Initialize trackers
            self.logger.info("Initializing application tracker...")
            self.app_tracker = ApplicationTracker()
            
            self.logger.info("Initializing browser tracker...")
            self.browser_tracker = BrowserTracker()
            
            # Start monitoring
            self.logger.info("Starting monitoring...")
            self.app_tracker.start()
            self.browser_tracker.start()
            
            self.running = True
            self.logger.info("All monitoring components started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start service: {e}", exc_info=True)
            raise
    
    def stop(self):
        """Stop the monitoring service"""
        try:
            self.logger.info("Stopping monitoring service...")
            self.running = False
            
            # Stop trackers
            if hasattr(self, 'app_tracker'):
                self.logger.info("Stopping application tracker...")
                self.app_tracker.stop()
            
            if hasattr(self, 'browser_tracker'):
                self.logger.info("Stopping browser tracker...")
                self.browser_tracker.stop()
            
            self.logger.info("Monitoring service stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping service: {e}", exc_info=True)
    
    def is_running(self):
        """Check if service is running"""
        return self.running


def main():
    """Main entry point"""
    try:
        exit_code = run_service()
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
