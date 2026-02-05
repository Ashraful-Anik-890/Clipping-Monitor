"""
Browser Activity Tracker

Tracks browser tabs and URLs across multiple browsers including:
- Google Chrome
- Microsoft Edge
- Mozilla Firefox
- Brave Browser
- Opera

Monitors active tab changes and records:
- Browser name
- Tab title
- URL (when available)
- Start and end times
- Duration
"""

import win32gui
import win32process
import psutil
from datetime import datetime
from typing import Dict, Optional, Callable, List
import threading
import time
import logging
import re
import sqlite3
from pathlib import Path
import shutil
import os

logger = logging.getLogger(__name__)


class BrowserActivityTracker:
    """
    Tracks browser activity across multiple browsers.
    
    Features:
    - Multi-browser support
    - Tab title extraction
    - URL extraction from window titles and history
    - Session tracking
    """
    
    # Browser identification patterns
    BROWSER_PATTERNS = {
        'chrome.exe': {
            'name': 'Google Chrome',
            'title_pattern': r'^(.*?) [-–—] Google Chrome$',
            'history_path': lambda: Path(os.getenv('LOCALAPPDATA')) / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'History'
        },
        'msedge.exe': {
            'name': 'Microsoft Edge',
            'title_pattern': r'^(.*?) [-–—] Microsoft​?\s*Edge$',
            'history_path': lambda: Path(os.getenv('LOCALAPPDATA')) / 'Microsoft' / 'Edge' / 'User Data' / 'Default' / 'History'
        },
        'firefox.exe': {
            'name': 'Mozilla Firefox',
            'title_pattern': r'^(.*?) [-–—] Mozilla Firefox$',
            'history_path': lambda: Path(os.getenv('APPDATA')) / 'Mozilla' / 'Firefox' / 'Profiles'
        },
        'brave.exe': {
            'name': 'Brave Browser',
            'title_pattern': r'^(.*?) [-–—] Brave$',
            'history_path': lambda: Path(os.getenv('LOCALAPPDATA')) / 'BraveSoftware' / 'Brave-Browser' / 'User Data' / 'Default' / 'History'
        },
        'opera.exe': {
            'name': 'Opera',
            'title_pattern': r'^(.*?) [-–—] Opera$',
            'history_path': lambda: Path(os.getenv('APPDATA')) / 'Opera Software' / 'Opera Stable' / 'History'
        }
    }
    
    def __init__(self, callback: Callable[[Dict], None], polling_interval: float = 1.0):
        """
        Initialize browser activity tracker.
        
        Args:
            callback: Function to call when browser activity event occurs
            polling_interval: How often to check active window (seconds)
        """
        self.callback = callback
        self.polling_interval = polling_interval
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Current session tracking
        self.current_tab_id = None
        self.current_tab_info = None
        self.session_start_time = None
        
        # URL cache for better URL tracking
        self.url_cache = {}
        
        # Statistics
        self.total_sessions = 0
    
    def _get_browser_window_info(self) -> Optional[Dict]:
        """
        Extract browser and tab information from active window.
        
        Returns:
            Dictionary with browser and tab info, or None if not a browser
        """
        try:
            # Get active window
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return None
            
            # Get process information
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().lower()
            
            # Check if it's a known browser
            if process_name not in self.BROWSER_PATTERNS:
                return None
            
            browser_info = self.BROWSER_PATTERNS[process_name]
            window_title = win32gui.GetWindowText(hwnd)
            
            if not window_title:
                return None
            
            # Extract tab title from window title
            pattern = browser_info['title_pattern']
            match = re.match(pattern, window_title)
            
            if match:
                tab_title = match.group(1).strip()
            else:
                # Fallback: use full window title
                tab_title = window_title
            
            # Extract URL from title if present
            url = self._extract_url_from_title(tab_title)
            
            # Try to get URL from browser history (more reliable)
            if not url:
                url = self._get_current_url_from_history(process_name, tab_title)
            
            return {
                'browser_name': browser_info['name'],
                'browser_process': process_name,
                'tab_title': tab_title,
                'url': url,
                'pid': pid,
                'hwnd': hwnd,
                'timestamp': datetime.now()
            }
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.debug(f"Process access error: {e}")
            return None
        except Exception as e:
            logger.debug(f"Error getting browser window info: {e}")
            return None
    
    def _extract_url_from_title(self, title: str) -> Optional[str]:
        """
        Extract URL from tab title if present.
        
        Many websites include their URL or domain in the page title.
        
        Args:
            title: Tab title
            
        Returns:
            Extracted URL or None
        """
        # Pattern for full URLs
        url_pattern = r'(https?://[^\s\)]+)'
        match = re.search(url_pattern, title)
        if match:
            return match.group(1)
        
        # Pattern for domains (e.g., "example.com")
        domain_pattern = r'\b([a-zA-Z0-9-]+\.(?:com|org|net|edu|gov|io|co|uk|de|fr|jp|cn|in|au|ca|br|ru|nl|se|no|dk|fi|it|es|pl|ch|at|be|cz|gr|pt|ro|hu|tr))\b'
        match = re.search(domain_pattern, title, re.IGNORECASE)
        if match:
            domain = match.group(1)
            # Check if it's likely a domain (not just words that happen to match)
            if '.' in domain and len(domain.split('.')[0]) > 2:
                return f"https://{domain}"
        
        return None
    
    def _get_current_url_from_history(self, browser_process: str, tab_title: str) -> Optional[str]:
        """
        Get current URL from browser history database.
        
        This is more reliable than title parsing but requires accessing
        the browser's SQLite history database.
        
        Args:
            browser_process: Browser process name
            tab_title: Current tab title
            
        Returns:
            URL or None
        """
        try:
            browser_config = self.BROWSER_PATTERNS.get(browser_process)
            if not browser_config:
                return None
            
            # Get history database path
            history_path = browser_config['history_path']()
            
            if not history_path or not history_path.exists():
                return None
            
            # For Firefox, need to find the profile directory
            if browser_process == 'firefox.exe':
                # Firefox stores history in profiles
                profiles = list(history_path.glob('*.default*/places.sqlite'))
                if not profiles:
                    return None
                history_path = profiles[0]
            
            # Check cache first
            cache_key = f"{browser_process}:{tab_title}"
            if cache_key in self.url_cache:
                cache_time, cached_url = self.url_cache[cache_key]
                # Use cache if less than 5 seconds old
                if (datetime.now() - cache_time).total_seconds() < 5:
                    return cached_url
            
            # Copy history file (browser locks it)
            temp_history = Path(f'temp_history_{os.getpid()}.db')
            try:
                shutil.copy2(history_path, temp_history)
            except (PermissionError, FileNotFoundError):
                return None
            
            # Query history database
            try:
                conn = sqlite3.connect(str(temp_history), timeout=1.0)
                cursor = conn.cursor()
                
                # Query for recent URLs matching the title
                if browser_process == 'firefox.exe':
                    # Firefox uses different schema
                    query = """
                        SELECT url FROM moz_places 
                        WHERE title LIKE ? 
                        ORDER BY last_visit_date DESC 
                        LIMIT 1
                    """
                else:
                    # Chrome, Edge, Brave use similar schema
                    query = """
                        SELECT url FROM urls 
                        WHERE title LIKE ? 
                        ORDER BY last_visit_time DESC 
                        LIMIT 1
                    """
                
                cursor.execute(query, (f'%{tab_title[:50]}%',))
                result = cursor.fetchone()
                
                conn.close()
                temp_history.unlink()
                
                if result:
                    url = result[0]
                    # Update cache
                    self.url_cache[cache_key] = (datetime.now(), url)
                    return url
                
            except sqlite3.Error as e:
                logger.debug(f"SQLite error reading history: {e}")
                if temp_history.exists():
                    temp_history.unlink()
                return None
            
        except Exception as e:
            logger.debug(f"Error getting URL from history: {e}")
            return None
    
    def _create_tab_identifier(self, tab_info: Dict) -> str:
        """
        Create unique identifier for a browser tab session.
        
        Args:
            tab_info: Tab information dictionary
            
        Returns:
            Unique identifier string
        """
        browser = tab_info.get('browser_process', 'unknown')
        title = tab_info.get('tab_title', '')
        url = tab_info.get('url', '')
        
        # Use URL if available for more accurate tracking
        if url:
            return f"{browser}|{url}"
        else:
            return f"{browser}|{title}"
    
    def _log_session_end(self):
        """Log the end of the current browser session"""
        if self.current_tab_id and self.session_start_time and self.current_tab_info:
            end_time = datetime.now()
            duration = (end_time - self.session_start_time).total_seconds()
            
            # Only log if duration is meaningful (> 1 second)
            if duration >= 1.0:
                event = {
                    'event_type': 'browser_activity',
                    'session_id': self.current_tab_id,
                    'start_time': self.session_start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'duration_seconds': round(duration, 2),
                    'browser_name': self.current_tab_info.get('browser_name'),
                    'browser_process': self.current_tab_info.get('browser_process'),
                    'tab_title': self.current_tab_info.get('tab_title'),
                    'url': self.current_tab_info.get('url'),
                    'pid': self.current_tab_info.get('pid'),
                }
                
                # Call callback to log event
                self.callback(event)
                
                # Update statistics
                self.total_sessions += 1
                
                logger.debug(
                    f"Browser session ended: {self.current_tab_info.get('browser_name')} - "
                    f"{self.current_tab_info.get('tab_title')[:50]} - "
                    f"Duration: {duration:.1f}s"
                )
    
    def _monitor_loop(self):
        """Main monitoring loop that tracks browser tab changes"""
        logger.info("Browser activity tracking started")
        
        consecutive_errors = 0
        max_consecutive_errors = 10
        
        while self.is_running:
            try:
                # Get current browser window
                current_info = self._get_browser_window_info()
                
                if current_info:
                    # Reset error counter
                    consecutive_errors = 0
                    
                    # Create identifier for current tab
                    current_id = self._create_tab_identifier(current_info)
                    
                    # Check if tab has changed
                    if current_id != self.current_tab_id:
                        # Log previous session end
                        self._log_session_end()
                        
                        # Start new session
                        self.current_tab_id = current_id
                        self.current_tab_info = current_info
                        self.session_start_time = datetime.now()
                        
                        logger.debug(
                            f"New browser session: {current_info.get('browser_name')} - "
                            f"{current_info.get('tab_title')[:50]} - "
                            f"URL: {current_info.get('url', 'N/A')}"
                        )
                else:
                    # No browser active - end current session if any
                    if self.current_tab_id:
                        self._log_session_end()
                        self.current_tab_id = None
                        self.current_tab_info = None
                        self.session_start_time = None
                
                # Clean old cache entries (older than 60 seconds)
                current_time = datetime.now()
                self.url_cache = {
                    k: v for k, v in self.url_cache.items()
                    if (current_time - v[0]).total_seconds() < 60
                }
                
                # Sleep until next check
                time.sleep(self.polling_interval)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in browser monitoring loop: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"Too many consecutive errors ({consecutive_errors}), stopping tracker")
                    self.is_running = False
                    break
                
                # Sleep longer on error
                time.sleep(self.polling_interval * 2)
        
        # Log final session when stopping
        self._log_session_end()
        
        logger.info(f"Browser activity tracking stopped. Total sessions: {self.total_sessions}")
    
    def start(self):
        """Start browser activity tracking"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True,
                name="BrowserTrackerThread"
            )
            self.monitor_thread.start()
            logger.info("Browser activity tracker started")
    
    def stop(self):
        """Stop browser activity tracking"""
        if self.is_running:
            logger.info("Stopping browser activity tracker...")
            self.is_running = False
            
            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)
            
            logger.info("Browser activity tracker stopped")
    
    def is_monitoring(self) -> bool:
        """Check if tracker is currently monitoring"""
        return self.is_running and (self.monitor_thread is not None) and self.monitor_thread.is_alive()
    
    def get_statistics(self) -> Dict:
        """Get tracking statistics"""
        return {
            'total_sessions': self.total_sessions,
            'currently_tracking': self.current_tab_id,
            'current_browser': self.current_tab_info.get('browser_name') if self.current_tab_info else None,
            'current_url': self.current_tab_info.get('url') if self.current_tab_info else None,
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
        print(f"\n{'='*70}")
        print(f"BROWSER ACTIVITY EVENT:")
        print(f"  Browser: {event['browser_name']}")
        print(f"  Tab Title: {event['tab_title'][:60]}")
        print(f"  URL: {event.get('url', 'N/A')}")
        print(f"  Duration: {event['duration_seconds']:.1f} seconds")
        print(f"  Start: {event['start_time']}")
        print(f"  End: {event['end_time']}")
        print(f"{'='*70}\n")
    
    # Create and start tracker
    tracker = BrowserActivityTracker(callback=test_callback, polling_interval=1.0)
    tracker.start()
    
    try:
        print("Browser activity tracker running... (Ctrl+C to stop)")
        print("Open different browser tabs to see tracking in action\n")
        
        # Keep running and print statistics every 30 seconds
        while True:
            time.sleep(30)
            stats = tracker.get_statistics()
            print(f"\n--- Statistics ---")
            print(f"Total sessions: {stats['total_sessions']}")
            print(f"Current browser: {stats['current_browser']}")
            print(f"Current URL: {stats['current_url']}")
            print(f"Current session: {stats['current_session_duration']:.1f}s\n")
    
    except KeyboardInterrupt:
        print("\nStopping tracker...")
        tracker.stop()
        print("Tracker stopped")