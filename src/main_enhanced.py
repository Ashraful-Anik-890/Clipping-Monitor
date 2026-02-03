"""
Enhanced Main Application Controller
Integrates clipboard monitoring with screen recording
"""

import sys
import logging
from pathlib import Path
import threading
import argparse

# Create .clipboard_monitor directory first
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

# New imports
from screen_recorder import ScreenRecorder
from video_storage import VideoStorageManager, UploadQueueManager
from startup_manager import StartupManager, ProcessManager, BackgroundRunner


class EnhancedClipboardMonitorApp:
    """
    Enhanced application controller with screen recording
    
    Architecture:
    - Dual monitoring: clipboard + screen recording
    - Unified event correlation and storage
    - Background execution support
    - Upload-ready architecture
    """
    
    def __init__(self):
        logger.info("Initializing Enhanced Clipboard Monitor Application")
        
        # Initialize configuration
        self.config = Config()
        
        # Add new config defaults
        if "enable_screen_recording" not in self.config.config:
            self.config.set("enable_screen_recording", True)
        if "screen_recording_fps" not in self.config.config:
            self.config.set("screen_recording_fps", 10)
        if "screen_recording_quality" not in self.config.config:
            self.config.set("screen_recording_quality", "medium")
        if "video_chunk_minutes" not in self.config.config:
            self.config.set("video_chunk_minutes", 10)
        if "video_retention_days" not in self.config.config:
            self.config.set("video_retention_days", 30)
        
        # Initialize permission manager
        self.permission_manager = PermissionManager(self.config.config_dir)
        
        # Initialize clipboard storage
        self.storage = ClipboardStorage(
            log_dir=self.config.get_log_dir(),
            enable_encryption=self.config.get("enable_encryption", True),
            max_size_mb=self.config.get("max_log_size_mb", 50)
        )
        
        # Initialize video storage manager
        video_storage_dir = Path(self.config.get("log_location")) / "video_storage"
        self.video_storage = VideoStorageManager(
            storage_dir=video_storage_dir,
            retention_days=self.config.get("video_retention_days", 30)
        )
        
        # Initialize upload queue (future use)
        self.upload_queue = UploadQueueManager(self.video_storage.db_path)
        
        # Initialize GUI (may be hidden in background mode)
        self.main_window = MainWindow(
            on_start_monitoring=self.start_monitoring,
            on_stop_monitoring=self.stop_monitoring,
            on_export_logs=self.export_logs,
            on_settings_change=self.on_settings_change,
            on_clear_logs=self.clear_logs
        )
        
        # Initialize clipboard monitor
        self.clipboard_monitor = ClipboardMonitor(
            callback=self.on_clipboard_event,
            polling_interval=self.config.get("polling_interval_ms", 500) / 1000
        )
        
        # Initialize screen recorder
        self.screen_recorder = ScreenRecorder(
            output_dir=self.video_storage.video_dir,
            chunk_duration_minutes=self.config.get("video_chunk_minutes", 10),
            max_chunk_size_mb=100,
            fps=self.config.get("screen_recording_fps", 10),
            resolution_scale=0.5,
            quality=self.config.get("screen_recording_quality", "medium"),
            use_hardware_encoding=True,
            callback=self.on_video_event
        )
        
        # Initialize tray icon
        self.tray_icon = TrayIcon(
            on_show=self.show_window,
            on_start=self.start_monitoring,
            on_stop=self.stop_monitoring,
            on_quit=self.quit_application
        )
        
        # Initialize startup manager
        self.startup_manager = StartupManager()
        
        # Monitoring state
        self.is_monitoring_clipboard = False
        self.is_monitoring_screen = False
        
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
            
            # Register in video index for correlation
            self.video_storage.register_clipboard_event(event)
            
            # Update GUI using thread-safe method
            if hasattr(self.main_window, 'root') and self.main_window.root.winfo_exists():
                self.main_window.root.after(0, lambda e=event: self._update_gui_safe(e))
        except Exception as e:
            logger.error(f"Error handling clipboard event: {e}", exc_info=True)
    
    def on_video_event(self, event):
        """Handle video recording events (chunk completion)"""
        logger.info(f"Video event: {event['event_type']}")
        
        try:
            if event['event_type'] == 'video_chunk_complete':
                metadata = event['metadata']
                
                # Register chunk in database
                chunk_id = self.video_storage.register_chunk(metadata)
                
                # Optionally enqueue for upload (future)
                if self.config.get("auto_upload_enabled", False):
                    self.upload_queue.enqueue_chunk(chunk_id, priority=5)
                
                logger.info(f"Video chunk {chunk_id} registered and indexed")
                
        except Exception as e:
            logger.error(f"Error handling video event: {e}", exc_info=True)
    
    def _update_gui_safe(self, event):
        """Thread-safe GUI update"""
        try:
            self.main_window.add_event(event)
        except Exception as e:
            logger.error(f"Error updating GUI: {e}")
    
    def start_monitoring(self):
        """Start both clipboard and screen monitoring"""
        if not self.permission_manager.has_consent():
            logger.warning("Cannot start monitoring without consent")
            self.main_window.show_error("No Consent", "Please grant permission to start monitoring.")
            return
        
        logger.info("Starting monitoring systems")
        
        try:
            # Start clipboard monitoring
            self.clipboard_monitor.start()
            self.is_monitoring_clipboard = True
            
            # Start screen recording if enabled
            if self.config.get("enable_screen_recording", True):
                self.screen_recorder.start()
                self.is_monitoring_screen = True
                logger.info("Screen recording started")
            
            # Update UI
            self.tray_icon.update_monitoring_state(True)
            self.main_window.set_monitoring_state(True)
            
            logger.info("All monitoring systems started successfully")
            
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}", exc_info=True)
            self.main_window.show_error("Error", f"Failed to start monitoring: {e}")
    
    def stop_monitoring(self):
        """Stop both clipboard and screen monitoring"""
        logger.info("Stopping monitoring systems")
        
        try:
            # Stop clipboard monitoring
            if self.is_monitoring_clipboard:
                self.clipboard_monitor.stop()
                self.is_monitoring_clipboard = False
            
            # Stop screen recording
            if self.is_monitoring_screen:
                self.screen_recorder.stop()
                self.is_monitoring_screen = False
                logger.info("Screen recording stopped")
            
            # Update UI
            self.tray_icon.update_monitoring_state(False)
            self.main_window.set_monitoring_state(False)
            
            # Run cleanup
            self._cleanup_old_data()
            
            logger.info("All monitoring systems stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}", exc_info=True)
    
    def _cleanup_old_data(self):
        """Clean up old chunks based on retention policy"""
        try:
            logger.info("Running data cleanup")
            self.video_storage.cleanup_old_chunks()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def export_logs(self, output_path: Path):
        """Export logs and metadata"""
        logger.info(f"Exporting data to {output_path}")
        
        try:
            # Force flush any pending logs
            self.storage.flush()
            
            # Export clipboard logs
            clipboard_export = output_path.parent / f"{output_path.stem}_clipboard.json"
            self.storage.export_logs(clipboard_export, decrypt=True)
            
            # Export video metadata
            video_export = output_path.parent / f"{output_path.stem}_video_metadata.json"
            self.video_storage.export_metadata(video_export)
            
            logger.info(f"Successfully exported data")
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}", exc_info=True)
            raise
    
    def clear_logs(self):
        """Clear all logs and video chunks"""
        logger.info("Clearing all data")
        
        try:
            # Stop monitoring first
            if self.is_monitoring_clipboard or self.is_monitoring_screen:
                self.stop_monitoring()
            
            # Clear clipboard logs
            self.storage.clear_all_logs()
            
            # Clear video chunks (implement in VideoStorageManager if needed)
            # For now, just clear GUI
            self.main_window.clear_events()
            
            logger.info("All data cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing data: {e}", exc_info=True)
            raise
    
    def on_settings_change(self, settings):
        """Handle settings change"""
        logger.info("Settings changed")
        
        # Check if monitoring needs restart
        needs_restart = False
        
        for key, value in settings.items():
            old_value = self.config.get(key)
            if key in ['screen_recording_fps', 'screen_recording_quality', 'video_chunk_minutes']:
                if old_value != value:
                    needs_restart = True
            
            self.config.set(key, value)
        
        # Restart screen recording if needed
        if needs_restart and self.is_monitoring_screen:
            logger.info("Restarting screen recording with new settings")
            self.screen_recorder.stop()
            
            # Recreate screen recorder with new settings
            self.screen_recorder = ScreenRecorder(
                output_dir=self.video_storage.video_dir,
                chunk_duration_minutes=self.config.get("video_chunk_minutes", 10),
                max_chunk_size_mb=100,
                fps=self.config.get("screen_recording_fps", 10),
                resolution_scale=0.5,
                quality=self.config.get("screen_recording_quality", "medium"),
                use_hardware_encoding=True,
                callback=self.on_video_event
            )
            
            self.screen_recorder.start()
    
    def show_window(self):
        """Show main window"""
        self.main_window.show()
    
    def quit_application(self):
        """Quit the application"""
        logger.info("Quitting application")
        
        # Stop all monitoring
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
    
    def run(self, background_mode=False):
        """Run the application"""
        logger.info(f"Starting application (background={background_mode})")
        
        if background_mode:
            # Background mode: run only tray, auto-start if consent given
            background_runner = BackgroundRunner(self)
            background_runner.run_in_background()
        else:
            # Normal mode: show GUI and tray
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
        # Parse command line arguments
        parser = argparse.ArgumentParser(description='Clipboard Monitor with Screen Recording')
        parser.add_argument('--background', action='store_true', help='Run in background mode')
        parser.add_argument('--install-startup', action='store_true', help='Install startup task')
        parser.add_argument('--remove-startup', action='store_true', help='Remove startup task')
        args = parser.parse_args()
        
        # Check single instance
        if not ProcessManager.ensure_single_instance():
            print("Another instance is already running")
            sys.exit(1)
        
        # Handle startup installation
        if args.install_startup:
            startup_mgr = StartupManager()
            if startup_mgr.enable_startup():
                print("Startup enabled successfully")
                print("The application will now start automatically when you log in.")
            else:
                print("Failed to enable startup")
                print("You may need administrator privileges.")
            sys.exit(0)
        
        if args.remove_startup:
            startup_mgr = StartupManager()
            if startup_mgr.disable_startup():
                print("Startup disabled successfully")
            else:
                print("Failed to disable startup")
            sys.exit(0)
        
        # Initialize and run app
        app = EnhancedClipboardMonitorApp()
        app.run(background_mode=args.background)
        
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
