# Enterprise Windows Monitoring Agent - Architecture & Implementation Guide

## Executive Summary

This document provides a complete architecture for transforming your clipboard monitoring prototype into a production-ready, enterprise-grade Windows monitoring agent suitable for commercial deployment.

---

## 1. SYSTEM ARCHITECTURE OVERVIEW

### 1.1 Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ENTERPRISE MONITORING AGENT              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Windows    │  │   Watchdog   │  │  Admin UI    │     │
│  │   Service    │  │   Monitor    │  │  (Protected) │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                  │             │
│         └────────┬────────┴──────────────────┘             │
│                  │                                         │
│         ┌────────▼─────────────────────┐                   │
│         │   Monitoring Engine Core     │                   │
│         ├──────────────────────────────┤                   │
│         │ • Clipboard Monitor          │                   │
│         │ • App Usage Tracker          │                   │
│         │ • Browser Activity Tracker   │                   │
│         │ • Screen Recorder            │                   │
│         │ • Event Aggregator           │                   │
│         └────────┬─────────────────────┘                   │
│                  │                                         │
│         ┌────────▼─────────────────────┐                   │
│         │   Data Management Layer      │                   │
│         ├──────────────────────────────┤                   │
│         │ • Encrypted Storage          │                   │
│         │ • Database Manager           │                   │
│         │ • Export Engine              │                   │
│         │ • Upload Queue (Future)      │                   │
│         └──────────────────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Multi-Process Architecture

**Process 1: Windows Service** (MonitoringService.exe)
- Runs with SYSTEM privileges
- Auto-starts on boot
- Cannot be stopped by regular users
- Manages core monitoring components
- Handles watchdog and health checks

**Process 2: Tray Agent** (MonitoringTray.exe)
- User-space application
- System tray icon with basic status
- Communicates with service via named pipes
- Admin UI launcher
- Auto-restarts if terminated

**Process 3: Admin Console** (AdminConsole.exe)
- Launched on-demand with UAC elevation
- Requires admin password/credentials
- Settings management
- Export functionality
- Service control (stop/restart)

---

## 2. DETAILED COMPONENT DESIGN

### 2.1 Windows Service Implementation

**Technology Stack:**
- `pywin32` for Windows service APIs
- `servicemanager` for service control
- `win32serviceutil` for installation

**Service Architecture:**
```python
# service_core.py
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import sys
import logging
from pathlib import Path

class MonitoringService(win32serviceutil.ServiceFramework):
    _svc_name_ = "EnterpriseMonitoringAgent"
    _svc_display_name_ = "Enterprise Activity Monitoring Service"
    _svc_description_ = "Monitors user activity for compliance and productivity tracking"
    
    # Service cannot be stopped by users (only admins)
    _svc_deps_ = []
    _svc_startup_type_ = win32service.SERVICE_AUTO_START
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        
    def SvcStop(self):
        # Only allow stop if called with admin privileges
        # Additional verification can be added here
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.running = False
        
    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()
        
    def main(self):
        # Initialize all monitoring components
        from monitoring_engine import MonitoringEngine
        
        engine = MonitoringEngine()
        engine.start_all_monitors()
        
        # Keep service running
        while self.running:
            rc = win32event.WaitForSingleObject(self.stop_event, 5000)
            if rc == win32event.WAIT_OBJECT_0:
                break
                
        engine.stop_all_monitors()
```

**Service Installation:**
```python
# service_installer.py
import win32serviceutil
import win32service
import sys

def install_service():
    """Install Windows service with proper permissions"""
    try:
        # Install service
        win32serviceutil.HandleCommandLine(
            MonitoringService,
            argv=['', 'install']
        )
        
        # Set service to auto-start
        win32serviceutil.SetServiceCustomOption(
            MonitoringService._svc_name_,
            'StartType',
            win32service.SERVICE_AUTO_START
        )
        
        # Set recovery options (auto-restart on failure)
        configure_service_recovery()
        
        print("Service installed successfully")
        return True
    except Exception as e:
        print(f"Service installation failed: {e}")
        return False

def configure_service_recovery():
    """Configure service to auto-restart on failure"""
    import subprocess
    
    service_name = MonitoringService._svc_name_
    
    # Configure first failure: restart after 1 minute
    # Second failure: restart after 2 minutes
    # Subsequent failures: restart after 5 minutes
    
    cmd = [
        'sc', 'failure', service_name,
        'reset=', '86400',  # Reset failure count after 1 day
        'actions=', 'restart/60000/restart/120000/restart/300000'
    ]
    
    subprocess.run(cmd, check=True)
```

### 2.2 Application Usage Tracker

**Implementation Strategy:**
```python
# app_usage_tracker.py
import win32gui
import win32process
import psutil
from datetime import datetime
from typing import Dict, Optional
import threading
import time

class ApplicationUsageTracker:
    """Tracks active application usage with precise timing"""
    
    def __init__(self, callback):
        self.callback = callback
        self.current_app = None
        self.app_start_time = None
        self.is_running = False
        self.polling_interval = 1.0  # Check every second
        
    def _get_active_window_info(self) -> Optional[Dict]:
        """Get detailed information about active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd == 0:
                return None
                
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process information
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            
            # Get executable path and name
            exe_path = process.exe()
            exe_name = process.name()
            
            return {
                'process_name': exe_name,
                'process_path': exe_path,
                'window_title': window_title,
                'pid': pid,
                'hwnd': hwnd,
                'timestamp': datetime.now()
            }
        except Exception as e:
            return None
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                current = self._get_active_window_info()
                
                if current is None:
                    time.sleep(self.polling_interval)
                    continue
                
                # Create unique app identifier
                app_id = f"{current['process_name']}|{current['window_title']}"
                
                # Check if app changed
                if self.current_app != app_id:
                    # Log previous app session end
                    if self.current_app and self.app_start_time:
                        end_time = datetime.now()
                        duration = (end_time - self.app_start_time).total_seconds()
                        
                        self.callback({
                            'event_type': 'app_usage',
                            'app_identifier': self.current_app,
                            'start_time': self.app_start_time.isoformat(),
                            'end_time': end_time.isoformat(),
                            'duration_seconds': duration,
                            **self._parse_app_info(self.current_app)
                        })
                    
                    # Start tracking new app
                    self.current_app = app_id
                    self.app_start_time = datetime.now()
                
                time.sleep(self.polling_interval)
                
            except Exception as e:
                time.sleep(self.polling_interval)
    
    def _parse_app_info(self, app_id: str) -> Dict:
        """Parse app identifier back to components"""
        parts = app_id.split('|', 1)
        return {
            'process_name': parts[0],
            'window_title': parts[1] if len(parts) > 1 else ''
        }
    
    def start(self):
        """Start tracking"""
        if not self.is_running:
            self.is_running = True
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
    
    def stop(self):
        """Stop tracking"""
        self.is_running = False
```

### 2.3 Browser Activity Tracker

**Multi-Browser Support:**
```python
# browser_tracker.py
import win32gui
import win32process
import psutil
from typing import Dict, Optional, List
import re
from collections import defaultdict

class BrowserActivityTracker:
    """Track browser tabs and URLs across multiple browsers"""
    
    # Browser-specific title patterns
    BROWSER_PATTERNS = {
        'chrome.exe': {
            'name': 'Google Chrome',
            'title_pattern': r'^(.*?) - Google Chrome$'
        },
        'msedge.exe': {
            'name': 'Microsoft Edge',
            'title_pattern': r'^(.*?) - Microsoft​ Edge$'
        },
        'firefox.exe': {
            'name': 'Mozilla Firefox',
            'title_pattern': r'^(.*?) - Mozilla Firefox$'
        },
        'brave.exe': {
            'name': 'Brave Browser',
            'title_pattern': r'^(.*?) - Brave$'
        },
        'opera.exe': {
            'name': 'Opera',
            'title_pattern': r'^(.*?) - Opera$'
        }
    }
    
    def __init__(self, callback):
        self.callback = callback
        self.active_tabs = {}  # tab_id -> tab_info
        self.is_running = False
        
    def _get_browser_window_info(self) -> Optional[Dict]:
        """Extract browser and tab information from active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            process = psutil.Process(pid)
            process_name = process.name().lower()
            
            # Check if it's a known browser
            if process_name not in self.BROWSER_PATTERNS:
                return None
            
            browser_info = self.BROWSER_PATTERNS[process_name]
            window_title = win32gui.GetWindowText(hwnd)
            
            # Extract tab title from window title
            pattern = browser_info['title_pattern']
            match = re.match(pattern, window_title)
            
            if match:
                tab_title = match.group(1)
                
                # Extract URL if present in title
                url = self._extract_url_from_title(tab_title)
                
                return {
                    'browser_name': browser_info['name'],
                    'browser_process': process_name,
                    'tab_title': tab_title,
                    'url': url,
                    'pid': pid,
                    'hwnd': hwnd
                }
            
            return None
            
        except Exception:
            return None
    
    def _extract_url_from_title(self, title: str) -> Optional[str]:
        """Extract URL from tab title if present"""
        # Many sites include URL or domain in title
        url_pattern = r'(https?://[^\s]+)'
        match = re.search(url_pattern, title)
        if match:
            return match.group(1)
        
        # Try to extract domain
        domain_pattern = r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})'
        match = re.search(domain_pattern, title)
        if match:
            return f"https://{match.group(1)}"
        
        return None
    
    def _monitor_loop(self):
        """Monitor browser activity"""
        current_tab = None
        current_start_time = None
        
        while self.is_running:
            try:
                browser_info = self._get_browser_window_info()
                
                if browser_info:
                    tab_id = f"{browser_info['browser_process']}|{browser_info['tab_title']}"
                    
                    if current_tab != tab_id:
                        # Log previous tab
                        if current_tab and current_start_time:
                            self.callback({
                                'event_type': 'browser_activity',
                                'tab_end': True,
                                'tab_id': current_tab,
                                'start_time': current_start_time.isoformat(),
                                'end_time': datetime.now().isoformat(),
                                'duration': (datetime.now() - current_start_time).total_seconds(),
                                **self.active_tabs.get(current_tab, {})
                            })
                        
                        # Start new tab
                        current_tab = tab_id
                        current_start_time = datetime.now()
                        self.active_tabs[tab_id] = browser_info
                        
                        self.callback({
                            'event_type': 'browser_activity',
                            'tab_start': True,
                            'tab_id': tab_id,
                            'start_time': current_start_time.isoformat(),
                            **browser_info
                        })
                
                else:
                    # No browser active - close current tab if any
                    if current_tab:
                        self.callback({
                            'event_type': 'browser_activity',
                            'tab_end': True,
                            'tab_id': current_tab,
                            'start_time': current_start_time.isoformat(),
                            'end_time': datetime.now().isoformat(),
                            **self.active_tabs.get(current_tab, {})
                        })
                        current_tab = None
                        current_start_time = None
                
                time.sleep(1.0)
                
            except Exception:
                time.sleep(1.0)
```

**Advanced Browser URL Extraction (Using Browser Automation):**

For production environments requiring accurate URL tracking, use browser-specific automation:

```python
# browser_url_extractor.py (Advanced)
import sqlite3
from pathlib import Path
import json
import os

class ChromeURLExtractor:
    """Extract URLs from Chrome history (read-only)"""
    
    @staticmethod
    def get_chrome_history_path():
        """Get Chrome history database path"""
        appdata = os.getenv('LOCALAPPDATA')
        return Path(appdata) / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'History'
    
    @staticmethod
    def get_recent_urls(limit=10):
        """Get recent URLs from Chrome history"""
        try:
            history_path = ChromeURLExtractor.get_chrome_history_path()
            
            # Chrome locks the database, so copy it first
            import shutil
            temp_history = Path('temp_history')
            shutil.copy2(history_path, temp_history)
            
            conn = sqlite3.connect(temp_history)
            cursor = conn.cursor()
            
            query = """
                SELECT url, title, last_visit_time
                FROM urls
                ORDER BY last_visit_time DESC
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            results = cursor.fetchall()
            
            conn.close()
            temp_history.unlink()
            
            return results
            
        except Exception as e:
            return []
```

### 2.4 Admin Access Control System

**Secure Admin Authentication:**
```python
# admin_auth.py
import hashlib
import secrets
import json
from pathlib import Path
from cryptography.fernet import Fernet
import win32security
import win32api
import win32con

class AdminAuthManager:
    """Secure admin authentication and authorization"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.auth_file = config_dir / '.admin_credentials'
        self.cipher = self._init_encryption()
        
        # Initialize admin credentials if not exists
        if not self.auth_file.exists():
            self._create_default_admin()
    
    def _init_encryption(self):
        """Initialize encryption for credentials"""
        key_file = self.config_dir / '.auth_key'
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Hide key file
            win32api.SetFileAttributes(
                str(key_file),
                win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM
            )
        
        return Fernet(key)
    
    def _create_default_admin(self):
        """Create default admin credentials"""
        # Generate random initial password
        initial_password = secrets.token_urlsafe(16)
        
        # Store encrypted credentials
        self.set_admin_password(initial_password)
        
        # Write initial password to setup file (one-time)
        setup_file = self.config_dir / 'ADMIN_INITIAL_PASSWORD.txt'
        setup_file.write_text(
            f"INITIAL ADMIN PASSWORD\n"
            f"Please change this immediately after first login!\n\n"
            f"Password: {initial_password}\n"
        )
    
    def _hash_password(self, password: str, salt: bytes = None) -> tuple:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # Use PBKDF2 with SHA-256
        hashed = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000  # iterations
        )
        
        return hashed, salt
    
    def set_admin_password(self, password: str):
        """Set admin password"""
        hashed, salt = self._hash_password(password)
        
        credentials = {
            'password_hash': hashed.hex(),
            'salt': salt.hex()
        }
        
        # Encrypt and save
        encrypted = self.cipher.encrypt(json.dumps(credentials).encode())
        self.auth_file.write_bytes(encrypted)
    
    def verify_admin_password(self, password: str) -> bool:
        """Verify admin password"""
        try:
            if not self.auth_file.exists():
                return False
            
            # Decrypt credentials
            encrypted = self.auth_file.read_bytes()
            decrypted = self.cipher.decrypt(encrypted)
            credentials = json.loads(decrypted)
            
            # Hash input password with stored salt
            salt = bytes.fromhex(credentials['salt'])
            hashed, _ = self._hash_password(password, salt)
            
            # Compare hashes
            return hashed.hex() == credentials['password_hash']
            
        except Exception:
            return False
    
    def is_user_admin(self) -> bool:
        """Check if current user has admin privileges"""
        try:
            return win32security.IsUserAnAdmin()
        except:
            return False
    
    def require_admin_rights(self):
        """Require admin rights or raise exception"""
        if not self.is_user_admin():
            raise PermissionError("Administrator rights required")
```

**Admin UI with Authentication:**
```python
# admin_console.py
import tkinter as tk
from tkinter import ttk, messagebox
import ctypes
import sys

class AdminLoginDialog:
    """Admin login dialog"""
    
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.authenticated = False
        self.root = tk.Tk()
        self.root.title("Admin Authentication Required")
        self.root.geometry("400x200")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 100
        self.root.geometry(f"+{x}+{y}")
        
        self._create_ui()
    
    def _create_ui(self):
        # Title
        tk.Label(
            self.root,
            text="🔒 Administrator Access",
            font=("Arial", 14, "bold")
        ).pack(pady=20)
        
        # Password frame
        frame = tk.Frame(self.root)
        frame.pack(pady=10)
        
        tk.Label(frame, text="Password:", font=("Arial", 10)).grid(row=0, column=0, padx=5)
        
        self.password_entry = tk.Entry(frame, show="*", width=25, font=("Arial", 10))
        self.password_entry.grid(row=0, column=1, padx=5)
        self.password_entry.bind('<Return>', lambda e: self.verify())
        
        # Buttons
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="Login",
            command=self.verify,
            width=10,
            bg="#27ae60",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.cancel,
            width=10,
            bg="#e74c3c",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        self.password_entry.focus()
    
    def verify(self):
        password = self.password_entry.get()
        
        if self.auth_manager.verify_admin_password(password):
            self.authenticated = True
            self.root.destroy()
        else:
            messagebox.showerror(
                "Authentication Failed",
                "Incorrect password. Access denied.",
                parent=self.root
            )
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
    
    def cancel(self):
        self.authenticated = False
        self.root.destroy()
    
    def show(self) -> bool:
        self.root.mainloop()
        return self.authenticated


class AdminConsole:
    """Protected admin console"""
    
    def __init__(self, auth_manager, service_controller):
        self.auth_manager = auth_manager
        self.service_controller = service_controller
        
        # Require UAC elevation
        if not self.auth_manager.is_user_admin():
            self._request_uac_elevation()
            sys.exit(0)
        
        # Require password authentication
        login_dialog = AdminLoginDialog(auth_manager)
        if not login_dialog.show():
            print("Authentication failed")
            sys.exit(1)
        
        # Create main admin UI
        self.root = tk.Tk()
        self.root.title("Admin Console - Monitoring Agent")
        self.root.geometry("800x600")
        self._create_ui()
    
    def _request_uac_elevation(self):
        """Request UAC elevation"""
        if ctypes.windll.shell32.IsUserAnAdmin():
            return
        
        # Re-run with admin rights
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            " ".join(sys.argv),
            None,
            1
        )
    
    def _create_ui(self):
        """Create admin console UI"""
        # Header
        header = tk.Frame(self.root, bg="#34495e", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="⚙️ Administrator Console",
            font=("Arial", 16, "bold"),
            bg="#34495e",
            fg="white"
        ).pack(pady=15)
        
        # Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Service Control Tab
        service_tab = tk.Frame(notebook)
        notebook.add(service_tab, text="Service Control")
        self._create_service_control_tab(service_tab)
        
        # Settings Tab
        settings_tab = tk.Frame(notebook)
        notebook.add(settings_tab, text="Settings")
        
        # Export Tab
        export_tab = tk.Frame(notebook)
        notebook.add(export_tab, text="Export Data")
        
        # Security Tab
        security_tab = tk.Frame(notebook)
        notebook.add(security_tab, text="Security")
    
    def _create_service_control_tab(self, parent):
        """Create service control tab"""
        frame = tk.LabelFrame(parent, text="Service Status", padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Status display
        self.status_label = tk.Label(
            frame,
            text="● Running",
            font=("Arial", 14, "bold"),
            fg="green"
        )
        self.status_label.pack(pady=10)
        
        # Control buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="Stop Service",
            command=self.stop_service,
            width=15,
            height=2,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="Restart Service",
            command=self.restart_service,
            width=15,
            height=2,
            bg="#f39c12",
            fg="white",
            font=("Arial", 10, "bold")
        ).pack(side=tk.LEFT, padx=10)
    
    def stop_service(self):
        """Stop monitoring service"""
        if messagebox.askyesno(
            "Confirm Stop",
            "Are you sure you want to stop the monitoring service?"
        ):
            self.service_controller.stop_service()
            self.status_label.config(text="● Stopped", fg="red")
    
    def restart_service(self):
        """Restart monitoring service"""
        self.service_controller.restart_service()
        self.status_label.config(text="● Running", fg="green")
```

### 2.5 Enhanced Data Storage with SQLite

**Replace JSON with SQLite for better performance:**

```python
# database_manager.py
import sqlite3
from pathlib import Path
from datetime import datetime
import json
from cryptography.fernet import Fernet
import threading

class DatabaseManager:
    """Centralized database for all monitoring data"""
    
    def __init__(self, db_path: Path, enable_encryption=True):
        self.db_path = db_path
        self.enable_encryption = enable_encryption
        self.lock = threading.Lock()
        
        if enable_encryption:
            self.cipher = self._init_encryption()
        
        self._init_database()
    
    def _init_encryption(self):
        """Initialize encryption"""
        key_file = self.db_path.parent / '.db_key'
        if key_file.exists():
            key = key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
        return Fernet(key)
    
    def _init_database(self):
        """Initialize database schema"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Clipboard events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clipboard_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data_type TEXT,
                    data_size INTEGER,
                    source_app TEXT,
                    source_window TEXT,
                    destination_app TEXT,
                    destination_window TEXT,
                    content_preview TEXT,
                    metadata TEXT,
                    encrypted_content BLOB
                )
            """)
            
            # Application usage table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    process_name TEXT NOT NULL,
                    process_path TEXT,
                    window_title TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Browser activity table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS browser_activity (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    browser_name TEXT NOT NULL,
                    tab_title TEXT,
                    url TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Screen recordings metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screen_recordings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    duration_seconds REAL,
                    file_path TEXT,
                    file_size_mb REAL,
                    resolution TEXT,
                    fps INTEGER
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_clipboard_timestamp 
                ON clipboard_events(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_app_usage_time 
                ON app_usage(start_time, end_time)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_browser_time 
                ON browser_activity(start_time, end_time)
            """)
            
            conn.commit()
            conn.close()
    
    def log_clipboard_event(self, event: dict):
        """Log clipboard event"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Encrypt sensitive content if needed
            encrypted_content = None
            if self.enable_encryption and 'content_full' in event:
                content_bytes = json.dumps(event['content_full']).encode()
                encrypted_content = self.cipher.encrypt(content_bytes)
            
            cursor.execute("""
                INSERT INTO clipboard_events (
                    timestamp, event_type, data_type, data_size,
                    source_app, source_window, destination_app, destination_window,
                    content_preview, metadata, encrypted_content
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event.get('timestamp'),
                event.get('event_type'),
                event.get('data_type'),
                event.get('data_size'),
                event.get('source_application'),
                event.get('source_window'),
                event.get('destination_application'),
                event.get('destination_window'),
                event.get('content_preview'),
                json.dumps(event.get('extra_info', {})),
                encrypted_content
            ))
            
            conn.commit()
            conn.close()
    
    def log_app_usage(self, event: dict):
        """Log application usage"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO app_usage (
                    start_time, end_time, duration_seconds,
                    process_name, process_path, window_title
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.get('start_time'),
                event.get('end_time'),
                event.get('duration_seconds'),
                event.get('process_name'),
                event.get('process_path'),
                event.get('window_title')
            ))
            
            conn.commit()
            conn.close()
    
    def log_browser_activity(self, event: dict):
        """Log browser activity"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO browser_activity (
                    start_time, end_time, duration_seconds,
                    browser_name, tab_title, url
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.get('start_time'),
                event.get('end_time'),
                event.get('duration_seconds'),
                event.get('browser_name'),
                event.get('tab_title'),
                event.get('url')
            ))
            
            conn.commit()
            conn.close()
    
    def export_to_json(self, output_path: Path, table_name: str = None):
        """Export data to JSON"""
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            
            if table_name:
                tables = [table_name]
            else:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table'
                """)
                tables = [row[0] for row in cursor.fetchall()]
            
            export_data = {}
            
            for table in tables:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table}")
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                export_data[table] = [
                    dict(zip(columns, row)) for row in rows
                ]
            
            conn.close()
            
            output_path.write_text(
                json.dumps(export_data, indent=2, default=str),
                encoding='utf-8'
            )
    
    def export_to_csv(self, output_dir: Path):
        """Export each table to separate CSV files"""
        import csv
        
        with self.lock:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table'
            """)
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                csv_path = output_dir / f"{table}.csv"
                with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(columns)
                    writer.writerows(rows)
            
            conn.close()
```

---

## 3. PACKAGING & INSTALLATION

### 3.1 Professional Installer with NSIS

**NSIS Script (installer.nsi):**
```nsis
; Enterprise Monitoring Agent Installer
!include "MUI2.nsh"
!include "FileFunc.nsh"

; Configuration
!define APP_NAME "Enterprise Monitoring Agent"
!define APP_VERSION "1.0.0"
!define APP_PUBLISHER "Your Company"
!define APP_EXE "MonitoringService.exe"

; Installer attributes
Name "${APP_NAME}"
OutFile "EnterpriseMonitoringAgent_Setup.exe"
InstallDir "$PROGRAMFILES64\${APP_NAME}"
RequestExecutionLevel admin

; Modern UI Configuration
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "English"

; Installer Sections
Section "Main Application" SecMain
    SetOutPath "$INSTDIR"
    
    ; Install files
    File /r "dist\*.*"
    
    ; Install Windows Service
    ExecWait '"$INSTDIR\${APP_EXE}" --install-service'
    
    ; Start service
    ExecWait 'sc start "EnterpriseMonitoringAgent"'
    
    ; Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Add to Programs and Features
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "UninstallString" "$\"$INSTDIR\Uninstall.exe$\""
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "DisplayVersion" "${APP_VERSION}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
        "Publisher" "${APP_PUBLISHER}"
    
    ; Create Start Menu shortcuts
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Admin Console.lnk" "$INSTDIR\AdminConsole.exe"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    
SectionEnd

; Uninstaller
Section "Uninstall"
    ; Stop and remove service
    ExecWait 'sc stop "EnterpriseMonitoringAgent"'
    ExecWait '"$INSTDIR\${APP_EXE}" --remove-service'
    
    ; Delete files
    RMDir /r "$INSTDIR"
    
    ; Remove shortcuts
    RMDir /r "$SMPROGRAMS\${APP_NAME}"
    
    ; Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd
```

### 3.2 PyInstaller Build Configuration

**build_enterprise.spec:**
```python
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# Service executable
service_analysis = Analysis(
    ['src/service_main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('resources', 'resources')
    ],
    hiddenimports=[
        'win32serviceutil',
        'win32service',
        'win32event',
        'servicemanager',
        'win32security',
        'pywintypes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

service_pyz = PYZ(service_analysis.pure, service_analysis.zipped_data, cipher=block_cipher)

service_exe = EXE(
    service_pyz,
    service_analysis.scripts,
    [],
    exclude_binaries=True,
    name='MonitoringService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Admin Console executable
admin_analysis = Analysis(
    ['src/admin_console_main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('resources', 'resources')
    ],
    hiddenimports=['tkinter', 'tkinter.ttk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

admin_pyz = PYZ(admin_analysis.pure, admin_analysis.zipped_data, cipher=block_cipher)

admin_exe = EXE(
    admin_pyz,
    admin_analysis.scripts,
    [],
    exclude_binaries=True,
    name='AdminConsole',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,  # Request UAC elevation
)

# Tray application
tray_analysis = Analysis(
    ['src/tray_main.py'],
    pathex=['src'],
    binaries=[],
    datas=[
        ('resources', 'resources')
    ],
    hiddenimports=['pystray', 'PIL'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

tray_pyz = PYZ(tray_analysis.pure, tray_analysis.zipped_data, cipher=block_cipher)

tray_exe = EXE(
    tray_pyz,
    tray_analysis.scripts,
    [],
    exclude_binaries=True,
    name='MonitoringTray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Collect all binaries
coll = COLLECT(
    service_exe,
    service_analysis.binaries,
    service_analysis.zipfiles,
    service_analysis.datas,
    admin_exe,
    admin_analysis.binaries,
    admin_analysis.zipfiles,
    admin_analysis.datas,
    tray_exe,
    tray_analysis.binaries,
    tray_analysis.zipfiles,
    tray_analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EnterpriseMonitoringAgent',
)
```

---

## 4. PRODUCTION DEPLOYMENT STRATEGY

### 4.1 Silent Deployment for Enterprise

**MSI Package Creation (using WiX Toolset):**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Wix xmlns="http://schemas.microsoft.com/wix/2006/wi">
  <Product Id="*" Name="Enterprise Monitoring Agent" Language="1033" 
           Version="1.0.0" Manufacturer="Your Company" UpgradeCode="YOUR-GUID-HERE">
    
    <Package InstallerVersion="200" Compressed="yes" InstallScope="perMachine" />
    
    <MajorUpgrade DowngradeErrorMessage="A newer version is already installed." />
    
    <MediaTemplate EmbedCab="yes" />
    
    <Feature Id="ProductFeature" Title="Enterprise Monitoring Agent" Level="1">
      <ComponentGroupRef Id="ProductComponents" />
      <ComponentRef Id="ServiceComponent" />
    </Feature>
    
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="INSTALLFOLDER" Name="Enterprise Monitoring Agent" />
      </Directory>
    </Directory>
    
    <ComponentGroup Id="ProductComponents" Directory="INSTALLFOLDER">
      <Component Id="ServiceComponent" Guid="YOUR-GUID-HERE">
        <File Id="ServiceEXE" Source="dist\MonitoringService.exe" KeyPath="yes" />
        
        <!-- Install and start Windows service -->
        <ServiceInstall Id="MonitoringServiceInstall"
                        Type="ownProcess"
                        Name="EnterpriseMonitoringAgent"
                        DisplayName="Enterprise Activity Monitoring Service"
                        Description="Monitors user activity for compliance"
                        Start="auto"
                        Account="LocalSystem"
                        ErrorControl="normal" />
        
        <ServiceControl Id="StartMonitoringService"
                        Name="EnterpriseMonitoringAgent"
                        Start="install"
                        Stop="both"
                        Remove="uninstall" />
      </Component>
    </ComponentGroup>
    
  </Product>
</Wix>
```

**Group Policy Deployment:**
1. Build MSI package
2. Deploy via GPO: Computer Configuration → Policies → Software Settings → Software Installation
3. Assign to computer groups
4. Auto-install on next reboot

### 4.2 Centralized Management (Future Phase)

**Server Communication Architecture:**
```python
# server_sync.py (Future Implementation)
import requests
import json
from pathlib import Path
from datetime import datetime
import threading
import time

class ServerSyncManager:
    """Handles synchronization with central server"""
    
    def __init__(self, server_url: str, agent_id: str, db_manager):
        self.server_url = server_url
        self.agent_id = agent_id
        self.db_manager = db_manager
        self.sync_interval = 300  # 5 minutes
        self.is_running = False
    
    def _sync_loop(self):
        """Periodic sync with server"""
        while self.is_running:
            try:
                self.sync_data()
                time.sleep(self.sync_interval)
            except Exception as e:
                time.sleep(60)  # Retry after 1 minute on error
    
    def sync_data(self):
        """Upload data to central server"""
        # Get unsync'd data from database
        data = self.db_manager.get_unsynced_events()
        
        if not data:
            return
        
        # Upload to server
        response = requests.post(
            f"{self.server_url}/api/agent/upload",
            headers={
                'Authorization': f'Bearer {self.get_auth_token()}',
                'Content-Type': 'application/json'
            },
            json={
                'agent_id': self.agent_id,
                'timestamp': datetime.now().isoformat(),
                'events': data
            },
            timeout=30
        )
        
        if response.status_code == 200:
            # Mark events as synced
            event_ids = [e['id'] for e in data]
            self.db_manager.mark_events_synced(event_ids)
    
    def get_auth_token(self):
        """Get authentication token for server communication"""
        # Implement secure token storage and retrieval
        pass
    
    def start(self):
        """Start sync process"""
        self.is_running = True
        self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
        self.sync_thread.start()
    
    def stop(self):
        """Stop sync process"""
        self.is_running = False
```

---

## 5. TECHNOLOGY STACK SUMMARY

### Core Technologies
- **Language**: Python 3.11+
- **Service Framework**: `pywin32` (Windows services)
- **GUI Framework**: `tkinter` (admin console)
- **Database**: SQLite with encryption
- **Packaging**: PyInstaller + NSIS/WiX
- **Encryption**: `cryptography` (Fernet)

### Key Libraries
```
pywin32==306
psutil==5.9.5
cryptography==42.0.2
Pillow==10.2.0
pystray==0.19.5
requests==2.31.0
```

### Windows APIs Used
- `win32service` - Service management
- `win32security` - Security and permissions
- `win32gui` - Window detection
- `win32process` - Process information
- `win32api` - System operations

---

## 6. SECURITY & COMPLIANCE

### 6.1 Security Measures

1. **Credential Security**
   - PBKDF2 password hashing (100,000 iterations)
   - Fernet encryption for stored data
   - Protected key storage with hidden file attributes

2. **Access Control**
   - UAC elevation for admin operations
   - Password-protected admin console
   - Service runs as LocalSystem (restricted to admins)

3. **Data Protection**
   - Encrypted database
   - Secure credential storage
   - No plaintext sensitive data

### 6.2 Compliance Considerations

**Transparency Requirements:**
1. Clear consent dialog during installation
2. Documented data collection practices
3. User access to collected data
4. Clear uninstall process

**Privacy Protection:**
1. Local-only storage (no automatic uploads)
2. Encryption at rest
3. No credential or password capture
4. Configurable retention periods

**Legal Requirements:**
1. End User License Agreement (EULA)
2. Privacy Policy
3. Data Processing Agreement (for enterprise)
4. Compliance with GDPR/CCPA if applicable

---

## 7. DEPLOYMENT ROADMAP

### Phase 1: Foundation (Weeks 1-3)
- ✅ Convert to Windows service architecture
- ✅ Implement admin authentication
- ✅ Add application usage tracking
- ✅ Add browser activity tracking
- ✅ Implement SQLite database

### Phase 2: Hardening (Weeks 4-5)
- ⬜ Add watchdog process protection
- ⬜ Implement service recovery mechanisms
- ⬜ Add crash reporting
- ⬜ Implement health monitoring

### Phase 3: Packaging (Weeks 6-7)
- ⬜ Create PyInstaller build scripts
- ⬜ Develop NSIS installer
- ⬜ Create MSI package for enterprise
- ⬜ Digital code signing
- ⬜ Create deployment documentation

### Phase 4: Enterprise Features (Weeks 8-10)
- ⬜ Implement export functionality (JSON/CSV)
- ⬜ Add advanced reporting
- ⬜ Create Group Policy templates
- ⬜ Build silent deployment scripts
- ⬜ Develop admin documentation

### Phase 5: Server Integration (Weeks 11-14)
- ⬜ Design server API
- ⬜ Implement agent-server communication
- ⬜ Add upload queue management
- ⬜ Build central dashboard
- ⬜ Implement multi-agent management

---

## 8. COMMERCIAL CONSIDERATIONS

### 8.1 Licensing Model

**Suggested Pricing:**
- **Per-Agent License**: $49/year/device
- **Enterprise (100+ devices)**: $39/year/device
- **Enterprise (500+ devices)**: $29/year/device
- **Server Dashboard**: Additional $999/year

### 8.2 Support Tiers
- **Basic**: Email support, updates
- **Professional**: Priority support, phone support
- **Enterprise**: 24/7 support, dedicated account manager, custom features

### 8.3 Differentiators
1. **Easy Deployment**: One-click installer, GPO support
2. **Tamper-Proof**: Service-based architecture
3. **Privacy-First**: Local storage, no cloud requirement
4. **Comprehensive**: Clipboard + apps + browser + screen
5. **Enterprise-Ready**: Scalable, centralized management

---

## 9. NEXT STEPS

### Immediate Actions
1. Review this architecture
2. Prioritize features based on market needs
3. Set up development environment
4. Begin Phase 1 implementation
5. Create testing environment

### Development Best Practices
- Use version control (Git)
- Implement unit tests
- Create integration tests
- Document all APIs
- Follow PEP 8 style guide
- Regular security audits

---

## CONCLUSION

This architecture transforms your prototype into a production-ready, enterprise-grade monitoring agent. The modular design allows for incremental development while maintaining a clear path to commercialization.

Key Success Factors:
- **Reliability**: Service-based, self-recovering
- **Security**: Encrypted, authenticated, tamper-proof
- **Scalability**: Database-backed, server-ready
- **Usability**: Simple installation, minimal maintenance
- **Compliance**: Transparent, documented, auditable

The system is designed for 24/7 operation, enterprise deployment, and future centralized management while maintaining security and user privacy.
