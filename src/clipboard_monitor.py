import threading
import time
import win32clipboard
import win32con
import win32gui
import psutil
from datetime import datetime
from typing import Optional, Callable, Dict, Any, List
import logging
import os
import win32process

logger = logging.getLogger(__name__)

class ClipboardMonitor:
    """Monitors Windows clipboard for changes"""
    
    # Clipboard format names
    CLIPBOARD_FORMATS = {
        win32con.CF_TEXT: "text",
        win32con.CF_UNICODETEXT: "unicode_text",
        win32con.CF_BITMAP: "bitmap",
        win32con.CF_DIB: "image",
        win32con.CF_HDROP: "files",
        win32con.CF_OEMTEXT: "oem_text",
    }
    
    def __init__(self, callback: Callable[[Dict[str, Any]], None], polling_interval: float = 0.5):
        self.callback = callback
        self.polling_interval = polling_interval
        self.is_running = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.paste_monitor_thread: Optional[threading.Thread] = None
        self.last_clipboard_data = None
        self.last_copied_files = []
        self.last_copy_timestamp = None
    
    def _get_active_window_info(self) -> Dict[str, str]:
        """Get information about the active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            
            window_title = win32gui.GetWindowText(hwnd)
            
            return {
                "process_name": process.name(),
                "window_title": window_title,
                "pid": pid,
                "hwnd": hwnd
            }
        except Exception as e:
            logger.debug(f"Could not get active window info: {e}")
            return {
                "process_name": "Unknown",
                "window_title": "Unknown",
                "pid": -1,
                "hwnd": 0
            }
    
    def _get_file_info(self, file_paths: List[str]) -> Dict[str, Any]:
        """Get detailed information about files"""
        total_size_bytes = 0
        file_names = []
        valid_files = []
        
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    total_size_bytes += size
                    file_names.append(os.path.basename(file_path))
                    valid_files.append(file_path)
            except Exception as e:
                logger.debug(f"Error getting file info for {file_path}: {e}")
        
        total_size_mb = round(total_size_bytes / (1024 * 1024), 2)
        
        return {
            "total_size_mb": total_size_mb,
            "total_size_bytes": total_size_bytes,
            "file_names": file_names,
            "file_paths": valid_files,
            "file_count": len(valid_files)
        }
    
    def _extract_destination_from_window(self, window_title: str, process_name: str) -> str:
        """Extract destination path from window title"""
        try:
            # For File Explorer
            if process_name.lower() == "explorer.exe":
                # Windows 11/10 format: "folder_name - File Explorer" or just "folder_name"
                if " - " in window_title:
                    folder_name = window_title.split(" - ")[0].strip()
                else:
                    folder_name = window_title.strip()
                
                # Try to get the actual path from the active explorer window
                # This is a best-effort approach
                return f"File Explorer: {folder_name}"
            
            # For other applications
            elif window_title and window_title != "Unknown":
                return f"{process_name}: {window_title}"
            
            return "Unknown destination"
        
        except Exception as e:
            logger.debug(f"Error extracting destination: {e}")
            return "Unknown destination"
    
    def _get_clipboard_data(self) -> Optional[Dict[str, Any]]:
        """Retrieve clipboard data and metadata"""
        try:
            win32clipboard.OpenClipboard()
            
            # Determine available formats
            available_formats = []
            format_id = 0
            while True:
                format_id = win32clipboard.EnumClipboardFormats(format_id)
                if format_id == 0:
                    break
                available_formats.append(format_id)
            
            # Get primary data type
            data_type = "unknown"
            data_content = None
            data_size = 0
            extra_info = {}
            
            # Try to get text data
            if win32con.CF_UNICODETEXT in available_formats:
                try:
                    data_content = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                    data_type = "unicode_text"
                    data_size = len(data_content) if data_content else 0
                except:
                    pass
            
            elif win32con.CF_TEXT in available_formats:
                try:
                    data_content = win32clipboard.GetClipboardData(win32con.CF_TEXT)
                    data_type = "text"
                    data_size = len(data_content) if data_content else 0
                except:
                    pass
            
            # Check for files (PRIORITY)
            elif win32con.CF_HDROP in available_formats:
                try:
                    files = win32clipboard.GetClipboardData(win32con.CF_HDROP)
                    data_type = "files"
                    
                    # Get detailed file information
                    file_info = self._get_file_info(files)
                    
                    data_content = f"{file_info['file_count']} file(s) - {file_info['total_size_mb']} MB"
                    data_size = file_info['total_size_mb']
                    
                    extra_info = {
                        "file_names": file_info['file_names'],
                        "file_paths": file_info['file_paths'],
                        "file_count": file_info['file_count'],
                        "total_size_bytes": file_info['total_size_bytes']
                    }
                    
                    # Store for paste detection
                    self.last_copied_files = file_info['file_paths']
                    self.last_copy_timestamp = datetime.now()
                    
                except Exception as e:
                    logger.error(f"Error getting file data: {e}")
                    pass
            
            # Check for images
            elif win32con.CF_DIB in available_formats or win32con.CF_BITMAP in available_formats:
                data_type = "image"
                data_content = "Image data"
                data_size = 0  # Size estimation would require more processing
            
            win32clipboard.CloseClipboard()
            
            if data_content is not None:
                # Create a hash of the content for change detection
                content_hash = hash(str(data_content)[:1000])
                
                return {
                    "data_type": data_type,
                    "data_size": data_size,
                    "content_preview": str(data_content)[:200] if isinstance(data_content, str) else data_content,
                    "content_hash": content_hash,
                    "extra_info": extra_info
                }
            
            return None
        
        except Exception as e:
            logger.debug(f"Error accessing clipboard: {e}")
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return None
    
    def _monitor_paste_events(self):
        """Monitor for paste events to detect destination"""
        logger.info("Paste monitoring started")
        
        last_active_window = None
        last_check_time = datetime.now()
        
        while self.is_running:
            try:
                # Only check if we have recently copied files (within last 60 seconds)
                if self.last_copied_files and self.last_copy_timestamp:
                    time_since_copy = (datetime.now() - self.last_copy_timestamp).total_seconds()
                    
                    if time_since_copy < 60:  # 60 seconds window
                        current_window = self._get_active_window_info()
                        
                        # Detect if window changed (potential paste location)
                        if (current_window['hwnd'] != 0 and 
                            last_active_window and 
                            current_window['hwnd'] != last_active_window.get('hwnd')):
                            
                            # Check if this is a file explorer or application that could receive files
                            if self._is_file_destination(current_window):
                                destination = self._extract_destination_from_window(
                                    current_window['window_title'],
                                    current_window['process_name']
                                )
                                
                                # Create paste event
                                event = {
                                    "timestamp": datetime.now().isoformat(),
                                    "event_type": "clipboard_paste",
                                    "data_type": "files",
                                    "data_size": self._calculate_total_size(self.last_copied_files),
                                    "content_preview": f"{len(self.last_copied_files)} file(s) pasted",
                                    "source_application": "Clipboard",
                                    "source_window": "Clipboard Cache",
                                    "destination_window": destination,
                                    "destination_application": current_window['process_name'],
                                    "file_names": [os.path.basename(f) for f in self.last_copied_files]
                                }
                                
                                self.callback(event)
                        
                        last_active_window = current_window
                
                time.sleep(0.3)  # Check more frequently for paste events
            
            except Exception as e:
                logger.error(f"Error in paste monitoring loop: {e}")
                time.sleep(1)
        
        logger.info("Paste monitoring stopped")
    
    def _is_file_destination(self, window_info: Dict[str, str]) -> bool:
        """Check if window is a potential file destination"""
        process_name = window_info['process_name'].lower()
        window_title = window_info['window_title'].lower()
        
        # Common file destinations
        file_destinations = [
            'explorer.exe',
            'totalcmd64.exe',  # Total Commander
            'totalcmd.exe',
            'dopus.exe',  # Directory Opus
        ]
        
        return any(dest in process_name for dest in file_destinations)
    
    def _calculate_total_size(self, file_paths: List[str]) -> float:
        """Calculate total size in MB"""
        total_bytes = sum(os.path.getsize(f) for f in file_paths if os.path.exists(f))
        return round(total_bytes / (1024 * 1024), 2)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Clipboard monitoring started")
        
        while self.is_running:
            try:
                clipboard_data = self._get_clipboard_data()
                
                # Check if clipboard has changed
                if clipboard_data and clipboard_data != self.last_clipboard_data:
                    # Get source application info
                    window_info = self._get_active_window_info()
                    
                    # Create event based on data type
                    event = {
                        "timestamp": datetime.now().isoformat(),
                        "event_type": "clipboard_copy",
                        "data_type": clipboard_data["data_type"],
                        "data_size": clipboard_data["data_size"],
                        "content_preview": clipboard_data["content_preview"],
                        "source_application": window_info["process_name"],
                        "source_window": window_info["window_title"],
                    }
                    
                    # Add file-specific information
                    if clipboard_data["data_type"] == "files":
                        extra = clipboard_data.get("extra_info", {})
                        event["file_names"] = extra.get("file_names", [])
                        event["destination_window"] = "Pending paste..."
                    
                    # Call the callback
                    self.callback(event)
                    
                    # Update last known state
                    self.last_clipboard_data = clipboard_data
                
                # Sleep before next check
                time.sleep(self.polling_interval)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(1)
        
        logger.info("Clipboard monitoring stopped")
    
    def start(self):
        """Start monitoring"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
            
            # Start paste monitoring thread
            self.paste_monitor_thread = threading.Thread(target=self._monitor_paste_events, daemon=True)
            self.paste_monitor_thread.start()
            
            logger.info("Clipboard monitor started")
    
    def stop(self):
        """Stop monitoring"""
        if self.is_running:
            self.is_running = False
            if self.monitor_thread:
                self.monitor_thread.join(timeout=2)
            if self.paste_monitor_thread:
                self.paste_monitor_thread.join(timeout=2)
            logger.info("Clipboard monitor stopped")
    
    def is_monitoring(self) -> bool:
        """Check if currently monitoring"""
        return self.is_running