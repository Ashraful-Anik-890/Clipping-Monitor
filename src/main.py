import sys
import logging
from pathlib import Path
import threading
import shutil

# Create .clipboard_monitor directory first (before logging setup)
config_dir = Path.home() / ".clipboard_monitor"
config_dir.mkdir(parents=True, exist_ok=True)

# Configure logging
log_file = config_dir / "app.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Setup global exception handling
try:
    from error_handler import setup_exception_handling
    setup_exception_handling()
except ImportError:
    logger.warning("Error handler not available")

from config import Config
from permissions import PermissionManager
from storage import ClipboardStorage
from clipboard_monitor import ClipboardMonitor
from gui import MainWindow, ConsentDialog
from tray_icon import TrayIcon


class ClipboardMonitorApp:
    """Main application controller"""
    
    def __init__(self):
        logger.info("Initializing Clipboard Monitor Application")
        
        # Initialize configuration
        self.config = Config()
        
        # Initialize permission manager
        self.permission_manager = PermissionManager(self.config.config_dir)
        
        # Initialize storage
        self.storage = ClipboardStorage(
            log_dir=self.config.get_log_dir(),
            enable_encryption=self.config.get("enable_encryption", True),
            max_size_mb=self.config.get("max_log_size_mb", 50)
        )
        
        # Initialize GUI first
        self.main_window = MainWindow(
            on_start_monitoring=self.start_monitoring,
            on_stop_monitoring=self.stop_monitoring,
            on_export_logs=self.export_logs,
            on_settings_change=self.on_settings_change,
            on_clear_logs=self.clear_logs
        )
        
        # Initialize clipboard monitor (but don't start yet)
        self.monitor = ClipboardMonitor(
            callback=self.on_clipboard_event,
            polling_interval=self.config.get("polling_interval_ms", 500) / 1000
        )
        
        # Initialize tray icon
        self.tray_icon = TrayIcon(
            on_show=self.show_window,
            on_start=self.start_monitoring,
            on_stop=self.stop_monitoring,
            on_quit=self.quit_application
        )
        
        # Check for consent AFTER GUI is initialized
        if not self.permission_manager.has_consent():
            self.request_consent()
    
    def request_consent(self):
        """Request user consent"""
        logger.info("Requesting user consent")
        
        # Ensure main window is visible
        self.main_window.show()
        
        consent_dialog = ConsentDialog(self.main_window.root)
        if consent_dialog.show():
            self.permission_manager.request_consent()
            logger.info("User consent granted")
        else:
            logger.warning("User declined consent")
            self.quit_application()
    
    def on_clipboard_event(self, event):
        """Handle clipboard event - THREAD-SAFE"""
        logger.debug(f"Clipboard event: {event['event_type']}")
        
        try:
            # Store the event immediately
            self.storage.log_event(event)
            
            # Update GUI using thread-safe method
            if hasattr(self.main_window, 'root') and self.main_window.root.winfo_exists():
                # Schedule GUI update in main thread
                self.main_window.root.after(0, lambda e=event: self._update_gui_safe(e))
        except Exception as e:
            logger.error(f"Error handling clipboard event: {e}", exc_info=True)
    
    def _update_gui_safe(self, event):
        """Thread-safe GUI update"""
        try:
            self.main_window.add_event(event)
        except Exception as e:
            logger.error(f"Error updating GUI: {e}")
    
    def start_monitoring(self):
        """Start clipboard monitoring"""
        if not self.permission_manager.has_consent():
            logger.warning("Cannot start monitoring without consent")
            self.main_window.show_error("No Consent", "Please grant permission to start monitoring.")
            return
        
        logger.info("Starting clipboard monitoring")
        try:
            self.monitor.start()
            self.tray_icon.update_monitoring_state(True)
            self.main_window.set_monitoring_state(True)
        except Exception as e:
            logger.error(f"Error starting monitor: {e}")
            self.main_window.show_error("Error", f"Failed to start monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop clipboard monitoring"""
        logger.info("Stopping clipboard monitoring")
        try:
            self.monitor.stop()
            self.tray_icon.update_monitoring_state(False)
            self.main_window.set_monitoring_state(False)
        except Exception as e:
            logger.error(f"Error stopping monitor: {e}")
    
    def export_logs(self, output_path: Path):
        """Export logs to file"""
        logger.info(f"Exporting logs to {output_path}")
        try:
            # Force flush any pending logs
            self.storage.flush()
            
            # Export
            self.storage.export_logs(output_path, decrypt=True)
            logger.info(f"Successfully exported logs to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting logs: {e}", exc_info=True)
            raise
    
    def clear_logs(self):
        """Clear all logs"""
        logger.info("Clearing all logs")
        try:
            self.storage.clear_all_logs()
            self.main_window.clear_events()
            logger.info("Logs cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")
            raise
    
    def on_settings_change(self, settings):
        """Handle settings change"""
        logger.info("Settings changed")
        # Update configuration
        for key, value in settings.items():
            self.config.set(key, value)
    
    def show_window(self):
        """Show main window"""
        self.main_window.show()
    
    def quit_application(self):
        """Quit the application"""
        logger.info("Quitting application")
        
        # Stop monitoring
        self.stop_monitoring()
        
        # Stop tray icon
        try:
            self.tray_icon.stop()
        except:
            pass
        
        # Destroy GUI
        try:
            if hasattr(self.main_window, 'root'):
                self.main_window.root.quit()
                self.main_window.root.destroy()
        except:
            pass
        
        sys.exit(0)
    
    def run(self):
        """Run the application"""
        logger.info("Starting application")
        
        # Start tray icon in separate thread
        tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        tray_thread.start()
        
        # Run main GUI loop
        try:
            self.main_window.run()
        except KeyboardInterrupt:
            self.quit_application()
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            self.quit_application()


def main():
    """Application entry point"""
    try:
        app = ClipboardMonitorApp()
        app.run()
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()