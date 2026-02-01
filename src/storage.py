import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from cryptography.fernet import Fernet
import logging
import threading

logger = logging.getLogger(__name__)

class ClipboardStorage:
    """Handles storage and encryption of clipboard logs"""
    
    def __init__(self, log_dir: Path, enable_encryption: bool = True, max_size_mb: int = 50):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.enable_encryption = enable_encryption
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Thread safety
        self.lock = threading.Lock()
        
        # In-memory cache for better performance
        self.events_cache = []
        self.cache_max_size = 50
        
        # Initialize encryption
        self.cipher = None
        if enable_encryption:
            self._init_encryption()
        
        self.current_log_file = self._get_current_log_file()
        
        # Load existing events from current file
        self._load_current_file()
    
    def _init_encryption(self):
        """Initialize or load encryption key"""
        key_file = self.log_dir / ".encryption_key"
        
        try:
            if key_file.exists():
                with open(key_file, 'rb') as f:
                    key = f.read()
            else:
                key = Fernet.generate_key()
                with open(key_file, 'wb') as f:
                    f.write(key)
                # Hide the key file on Windows
                try:
                    import win32api
                    import win32con
                    win32api.SetFileAttributes(str(key_file), win32con.FILE_ATTRIBUTE_HIDDEN)
                except:
                    pass
            
            self.cipher = Fernet(key)
        except Exception as e:
            logger.error(f"Error initializing encryption: {e}")
            self.enable_encryption = False
    
    def _get_current_log_file(self) -> Path:
        """Get current log file path with rotation"""
        timestamp = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"clipboard_log_{timestamp}.json"
    
    def _load_current_file(self):
        """Load events from current log file into cache"""
        with self.lock:
            try:
                if self.current_log_file.exists():
                    self.events_cache = self._read_log_file(self.current_log_file)
                    logger.info(f"Loaded {len(self.events_cache)} events from {self.current_log_file}")
                else:
                    self.events_cache = []
            except Exception as e:
                logger.error(f"Error loading current file: {e}")
                self.events_cache = []
    
    def _read_log_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Read and decrypt log file"""
        try:
            if not file_path.exists():
                return []
            
            with open(file_path, 'rb' if self.enable_encryption else 'r', encoding=None if self.enable_encryption else 'utf-8') as f:
                if self.enable_encryption:
                    encrypted_data = f.read()
                    if not encrypted_data:
                        return []
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    return json.loads(decrypted_data.decode('utf-8'))
                else:
                    content = f.read()
                    if not content:
                        return []
                    return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading log file {file_path}: {e}")
            return []
    
    def _write_log_file(self, file_path: Path, logs: List[Dict[str, Any]]):
        """Write and encrypt log file"""
        try:
            if self.enable_encryption:
                json_data = json.dumps(logs, indent=2, ensure_ascii=False)
                encrypted_data = self.cipher.encrypt(json_data.encode('utf-8'))
                with open(file_path, 'wb') as f:
                    f.write(encrypted_data)
            else:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error writing log file {file_path}: {e}")
            raise
    
    def _rotate_if_needed(self):
        """Rotate log file if size limit exceeded"""
        try:
            if self.current_log_file.exists():
                file_size = self.current_log_file.stat().st_size
                if file_size >= self.max_size_bytes:
                    # Flush current cache before rotation
                    self._flush_cache()
                    
                    # Create new file with counter
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    self.current_log_file = self.log_dir / f"clipboard_log_{timestamp}.json"
                    self.events_cache = []
                    logger.info(f"Rotated to new log file: {self.current_log_file}")
        except Exception as e:
            logger.error(f"Error rotating log file: {e}")
    
    def _flush_cache(self):
        """Flush cache to disk"""
        try:
            if self.events_cache:
                self._write_log_file(self.current_log_file, self.events_cache)
                logger.debug(f"Flushed {len(self.events_cache)} events to disk")
        except Exception as e:
            logger.error(f"Error flushing cache: {e}")
    
    def log_event(self, event: Dict[str, Any]):
        """Log a clipboard event"""
        with self.lock:
            try:
                # Check if we need to rotate to a new day
                expected_file = self._get_current_log_file()
                if expected_file != self.current_log_file:
                    # Flush old file
                    self._flush_cache()
                    # Switch to new file
                    self.current_log_file = expected_file
                    self._load_current_file()
                
                # Add to cache
                self.events_cache.append(event)
                
                # Flush if cache is getting large
                if len(self.events_cache) >= self.cache_max_size:
                    self._flush_cache()
                else:
                    # Write immediately for reliability (optional: can be optimized)
                    self._flush_cache()
                
                # Check rotation after write
                self._rotate_if_needed()
                
                logger.debug(f"Logged event: {event['event_type']} - {event.get('data_type', 'unknown')}")
            
            except Exception as e:
                logger.error(f"Error logging event: {e}", exc_info=True)
    
    def flush(self):
        """Force flush all pending events"""
        with self.lock:
            self._flush_cache()
    
    def get_all_logs(self) -> List[Dict[str, Any]]:
        """Retrieve all logs from all files"""
        with self.lock:
            # Flush current cache first
            self._flush_cache()
            
            all_logs = []
            
            # Get all log files sorted by date
            log_files = sorted(self.log_dir.glob("clipboard_log_*.json"))
            
            for log_file in log_files:
                try:
                    logs = self._read_log_file(log_file)
                    all_logs.extend(logs)
                except Exception as e:
                    logger.error(f"Error reading {log_file}: {e}")
            
            logger.info(f"Retrieved {len(all_logs)} total events from {len(log_files)} files")
            return all_logs
    
    def export_logs(self, output_path: Path, decrypt: bool = True):
        """Export logs to a readable JSON file"""
        logs = self.get_all_logs()
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(logs, f, indent=2, ensure_ascii=False)
            logger.info(f"Exported {len(logs)} events to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting logs: {e}")
            raise
    
    def clear_all_logs(self):
        """Clear all log files"""
        with self.lock:
            try:
                # Clear cache
                self.events_cache = []
                
                # Delete all log files
                for log_file in self.log_dir.glob("clipboard_log_*.json"):
                    try:
                        log_file.unlink()
                        logger.info(f"Deleted log file: {log_file}")
                    except Exception as e:
                        logger.error(f"Error deleting {log_file}: {e}")
                
                # Reset current file
                self.current_log_file = self._get_current_log_file()
                logger.info("All logs cleared")
            except Exception as e:
                logger.error(f"Error clearing logs: {e}")
                raise