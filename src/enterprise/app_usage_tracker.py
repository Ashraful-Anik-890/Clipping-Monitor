"""
Application Usage Tracker

Tracks which applications are actively used, when they gain/lose focus,
and calculates accurate usage duration for each application window.
"""

import win32gui
import win32process
import psutil
from datetime import datetime
from typing import Dict, Optional, Callable
import threading
import time
import logging

logger = logging.getLogger(__name__)


class ApplicationUsageTracker:
    """
    Tracks active application usage with precise timing.
    
    Records:
    - Process name and path
    - Window title
    - Start time (when app gains focus)
    - End time (when app loses focus)
    - Total duration
    """
    
    def __init__(self, callback: Callable[[Dict], None], polling_interval: float = 1.0):
        """
        Initialize application usage tracker.
        
        Args:
            callback: Function to call when app usage event occurs
            polling_interval: How often to check active window (seconds)
        """
        self.callback = callback
        self.polling_interval = polling_interval
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Current session tracking
        self.current_app_id = None
        self.current_app_info = None
        self.session_start_time = None
        
        # Statistics
        self.total_sessions = 0
        self.total_tracking_time = 0
    
    def _get_active_window_info(self) -> Optional[Dict]:
        """
        Get detailed information about the currently active window.
        
        Returns:
            Dictionary with window and process information, or None if unavailable
        """
        try:
            # Get foreground window handle
            hwnd = win32gui.GetForegroundWindow()
            
            if hwnd == 0:
                return None
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process ID from window
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get process information
            try:
                process = psutil.Process(pid)
                
                # Get process details
                process_name = process.name()
                
                try:
                    process_path = process.exe()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    process_path = "Access Denied"
                
                # Get process command line (useful for identifying specific instances)
                try:
                    cmdline = ' '.join(process.cmdline())
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    cmdline = ""
                
                # Get parent process (useful for understanding context)
                try:
                    parent = process.parent()
                    parent_name = parent.name() if parent else None
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    parent_name = None
                
                return {
                    'hwnd': hwnd,
                    'pid': pid,
                    'process_name': process_name,
                    'process_path': process_path,
                    'window_title': window_title,
                    'cmdline': cmdline,
                    'parent_process': parent_name,
                    'timestamp': datetime.now()
                }
                
            except psutil.NoSuchProcess:
                logger.debug(f"Process {pid} no longer exists")
                return None
            except psutil.AccessDenied:
                # Handle system processes with restricted access
                return {
                    'hwnd': hwnd,
                    'pid': pid,
                    'process_name': 'System Process',
                    'process_path': 'Access Denied',
                    'window_title': window_title,
                    'cmdline': '',
                    'parent_process': None,
                    'timestamp': datetime.now()
                }
        
        except Exception as e:
            logger.debug(f"Error getting active window info: {e}")
            return None
    
    def _create_app_identifier(self, app_info: Dict) -> str:
        """
        Create unique identifier for an application session.
        
        Uses process name and window title to differentiate between
        different windows of the same application.
        
        Args:
            app_info: Application information dictionary
        
        Returns:
            Unique identifier string
        """
        process_name = app_info.get('process_name', 'Unknown')
        window_title = app_info.get('window_title', '')
        
        # Create identifier: process_name|window_title
        # This allows tracking different documents/tabs as separate sessions
        return f"{process_name}|{window_title}"
    
    def _log_session_end(self):
        """Log the end of the current application session"""
        if self.current_app_id and self.session_start_time and self.current_app_info:
            end_time = datetime.now()
            duration = (end_time - self.session_start_time).total_seconds()
            
            # Only log if duration is meaningful (> 1 second)
            if duration >= 1.0:
                event = {
                    'event_type': 'app_usage',
                    'session_id': self.current_app_id,
                    'start_time': self.session_start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': round(duration, 2),
                    'process_name': self.current_app_info.get('process_name'),
                    'process_path': self.current_app_info.get('process_path'),
                    'window_title': self.current_app_info.get('window_title'),
                    'pid': self.current_app_info.get('pid'),
                    'parent_process': self.current_app_info.get('parent_process'),
                }
                
                # Call callback to log event
                self.callback(event)
                
                # Update statistics
                self.total_sessions += 1
                self.total_tracking_time += duration
                
                logger.debug(
                    f"Session ended: {self.current_app_info.get('process_name')} - "
                    f"Duration: {duration:.1f}s"
                )
    
    def _monitor_loop(self):
        """Main monitoring loop that tracks active window changes"""
        logger.info("Application usage tracking started")
        
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.is_running:
            try:
                # Get current active window
                current_info = self._get_active_window_info()
                
                if current_info:
                    # Reset error counter on success
                    consecutive_errors = 0
                    
                    # Create identifier for current app
                    current_id = self._create_app_identifier(current_info)
                    
                    # Check if app has changed
                    if current_id != self.current_app_id:
                        # Log previous session end
                        self._log_session_end()
                        
                        # Start new session
                        self.current_app_id = current_id
                        self.current_app_info = current_info
                        self.session_start_time = datetime.now()
                        
                        logger.debug(
                            f"New session started: {current_info.get('process_name')} - "
                            f"{current_info.get('window_title')[:50]}"
                        )
                else:
                    # No active window - end current session if any
                    if self.current_app_id:
                        self._log_session_end()
                        self.current_app_id = None
                        self.current_app_info = None
                        self.session_start_time = None
                
                # Sleep until next check
                time.sleep(self.polling_interval)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in monitoring loop: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"Too many consecutive errors ({consecutive_errors}), stopping tracker")
                    self.is_running = False
                    break
                
                # Sleep longer on error
                time.sleep(self.polling_interval * 2)
        
        # Log final session when stopping
        self._log_session_end()
        
        logger.info(
            f"Application usage tracking stopped. "
            f"Total sessions: {self.total_sessions}, "
            f"Total time tracked: {self.total_tracking_time:.1f}s"
        )
    
    def start(self):
        """Start application usage tracking"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="AppUsageTrackerThread"
            )
            self.monitor_thread.start()
            logger.info("Application usage tracker started")
    
    def stop(self):
        """Stop application usage tracking"""
        if self.is_running:
            logger.info("Stopping application usage tracker...")
            self.is_running = False
            
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            logger.info("Application usage tracker stopped")
    
    def is_monitoring(self) -> bool:
        """Check if tracker is currently monitoring"""
        return self.is_running and (self.monitor_thread is not None) and self.monitor_thread.is_alive()
    
    def get_statistics(self) -> Dict:
        """Get tracking statistics"""
        return {
            'total_sessions': self.total_sessions,
            'total_tracking_time_seconds': self.total_tracking_time,
            'currently_tracking': self.current_app_id,
            'current_session_duration': (
                (datetime.now() - self.session_start_time).total_seconds()
                if self.session_start_time else 0
            )
        }


# Example usage and testing
if __name__ == "__main__":
    # Setup logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def test_callback(event):
        """Test callback that prints events"""
        print(f"\n{'='*60}")
        print(f"APP USAGE EVENT:")
        print(f"  Process: {event['process_name']}")
        print(f"  Window: {event['window_title'][:50]}")
        print(f"  Duration: {event['duration_seconds']:.1f} seconds")
        print(f"  Start: {event['start_time']}")
        print(f"  End: {event['end_time']}")
        print(f"{'='*60}\n")
    
    # Create and start tracker
    tracker = ApplicationUsageTracker(callback=test_callback, polling_interval=1.0)
    tracker.start()
    
    try:
        print("Application usage tracker running... (Ctrl+C to stop)")
        print("Switch between different applications to see tracking in action\n")
        
        # Keep running and print statistics every 30 seconds
        while True:
            time.sleep(30)
            stats = tracker.get_statistics()
            print(f"\n--- Statistics ---")
            print(f"Total sessions: {stats['total_sessions']}")
            print(f"Total time: {stats['total_tracking_time_seconds']:.1f}s")
            print(f"Currently tracking: {stats['currently_tracking']}")
            print(f"Current session: {stats['current_session_duration']:.1f}s\n")
    
    except KeyboardInterrupt:
        print("\nStopping tracker...")
        tracker.stop()
        print("Tracker stopped")