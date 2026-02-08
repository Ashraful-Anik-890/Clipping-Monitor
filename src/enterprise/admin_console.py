"""
Admin Console Application - FIXED VERSION

Protected admin console for controlling the monitoring service.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
from pathlib import Path
import sys
import logging
from datetime import datetime
from typing import Optional
import ctypes
import os

# Fix Python path to find modules
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "src" / "enterprise"))

try:
    from admin_auth import AdminAuthManager, is_admin, request_uac_elevation
    from database_manager import DatabaseManager
    from config import Config
    from paths import (
        get_keystroke_storage_dir,
        get_data_dir,
        get_logs_dir,
        get_database_path
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Current directory: {Path(__file__).parent}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

logger = logging.getLogger(__name__)

def is_admin():
    """Check if running with administrator privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def request_uac_elevation():
    """Request UAC elevation and restart"""
    try:
        from win32com.shell.shell import ShellExecuteEx
        from win32com.shell import shellcon
        import win32con
        
        # Get script path
        if getattr(sys, 'frozen', False):
            script = sys.executable
            params = ''
        else:
            script = sys.executable
            params = f'"{Path(__file__).absolute()}"'
        
        # Request elevation
        ShellExecuteEx(
            nShow=win32con.SW_SHOWNORMAL,
            fMask=shellcon.SEE_MASK_NOCLOSEPROCESS,
            lpVerb='runas',
            lpFile=script,
            lpParameters=params
        )
        
    except Exception as e:
        print(f"UAC elevation error: {e}")
        raise
class AdminLoginDialog:
    """Admin authentication dialog"""
    
    def __init__(self, auth_manager: AdminAuthManager):
        self.auth_manager = auth_manager
        self.authenticated = False
        self.is_setup_mode = not self.auth_manager.get_credential_info().get('exists', False)
        
        self.root = tk.Tk()
        self.root.title("Admin Authentication Required" if not self.is_setup_mode else "Setup Administrator")
        self.root.geometry("450x300" if self.is_setup_mode else "450x250")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 225
        y = (self.root.winfo_screenheight() // 2) - 150
        self.root.geometry(f"+{x}+{y}")
        
        # Set window icon (optional)
        try:
            icon_path = project_root / "resources" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        self._create_ui()
    
    def _create_ui(self):
        """Create login or setup UI"""
        # Header
        header_frame = tk.Frame(self.root, bg="#34495e", height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_text = "🔒 Administrator Access" if not self.is_setup_mode else "🛡️ Setup Administrator"
        
        tk.Label(
            header_frame,
            text=header_text,
            font=("Arial", 16, "bold"),
            bg="#34495e",
            fg="white"
        ).pack(pady=20)
        
        # Form
        form_frame = tk.Frame(self.root, padx=40, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        if self.is_setup_mode:
            # Registration Mode
            tk.Label(
                form_frame,
                text="New Password:",
                font=("Arial", 11)
            ).grid(row=0, column=0, sticky='w', pady=10)
            
            self.new_password_entry = tk.Entry(
                form_frame,
                show="●",
                width=30,
                font=("Arial", 11)
            )
            self.new_password_entry.grid(row=0, column=1, pady=10, padx=10)
            
            tk.Label(
                form_frame,
                text="Confirm Password:",
                font=("Arial", 11)
            ).grid(row=1, column=0, sticky='w', pady=10)
            
            self.confirm_password_entry = tk.Entry(
                form_frame,
                show="●",
                width=30,
                font=("Arial", 11)
            )
            self.confirm_password_entry.grid(row=1, column=1, pady=10, padx=10)
            self.confirm_password_entry.bind('<Return>', lambda e: self.create_admin())
            
            # Buttons for Setup
            btn_frame = tk.Frame(form_frame)
            btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
            
            tk.Button(
                btn_frame,
                text="Create Account",
                command=self.create_admin,
                width=15,
                height=2,
                bg="#27ae60",
                fg="white",
                font=("Arial", 10, "bold"),
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)
            
        else:
            # Login Mode
            tk.Label(
                form_frame,
                text="Password:",
                font=("Arial", 11)
            ).grid(row=0, column=0, sticky='w', pady=10)
            
            self.password_entry = tk.Entry(
                form_frame,
                show="●",
                width=30,
                font=("Arial", 11)
            )
            self.password_entry.grid(row=0, column=1, pady=10, padx=10)
            self.password_entry.bind('<Return>', lambda e: self.verify())
            
            # Buttons for Login
            btn_frame = tk.Frame(form_frame)
            btn_frame.grid(row=1, column=0, columnspan=2, pady=20)
            
            tk.Button(
                btn_frame,
                text="Login",
                command=self.verify,
                width=12,
                height=2,
                bg="#27ae60",
                fg="white",
                font=("Arial", 10, "bold"),
                cursor="hand2"
            ).pack(side=tk.LEFT, padx=5)
            
        # Cancel Button (Common)
        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.cancel,
            width=12,
            height=2,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=5)
        
        # Initial focus
        if self.is_setup_mode:
            self.new_password_entry.focus()
        else:
            self.password_entry.focus()
            
            # Initial password hint (Only show if file exists AND in login mode)
            initial_file = self.auth_manager.config_dir / 'ADMIN_INITIAL_PASSWORD.txt'
            if initial_file.exists():
                tk.Label(
                    form_frame,
                    text="ℹ️ Check ADMIN_INITIAL_PASSWORD.txt for first-time password",
                    font=("Arial", 8),
                    fg="#7f8c8d"
                ).grid(row=2, column=0, columnspan=2, pady=5)
    
    def create_admin(self):
        """Create new admin account"""
        p1 = self.new_password_entry.get()
        p2 = self.confirm_password_entry.get()
        
        if not p1 or not p2:
            messagebox.showwarning("Warning", "Please enter both passwords", parent=self.root)
            return
            
        if p1 != p2:
            messagebox.showerror("Error", "Passwords do not match", parent=self.root)
            return
            
        if len(p1) < 8:
            messagebox.showwarning("Warning", "Password must be at least 8 characters", parent=self.root)
            return
        
        if self.auth_manager.set_admin_password(p1):
            messagebox.showinfo("Success", "Administrator account created successfully!", parent=self.root)
            self.authenticated = True
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Failed to create administrator account", parent=self.root)
    
    def _create_keystroke_tab(self):
        """Create keystroke export tab"""
        frame = tk.LabelFrame(
            self.keystroke_tab,
            text="⚠️ Keystroke Data Export (Admin Only)",
            padx=20,
            pady=20,
            font=("Arial", 11, "bold"),
            fg="red"
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Warning
        warning_label = tk.Label(
            frame,
            text="⚠️ SENSITIVE DATA: Keystroke logs contain sensitive information.\n"
                "Only export when necessary for security audits.\n"
                "All exports are logged and require admin authentication.",
            font=("Arial", 10),
            fg="red",
            justify=tk.LEFT
        )
        warning_label.pack(pady=20)
        
        # Export buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="📄 Export to JSON (Encrypted)",
            command=lambda: self.export_keystrokes('json', decrypt=False),
            width=30,
            height=2,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=5)
        
        tk.Button(
            btn_frame,
            text="📄 Export to JSON (Decrypted)",
            command=lambda: self.export_keystrokes('json', decrypt=True),
            width=30,
            height=2,
            bg="#c0392b",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=5)
        
        tk.Button(
            btn_frame,
            text="📊 Export to CSV",
            command=lambda: self.export_keystrokes('csv'),
            width=30,
            height=2,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=5)
        
        # Statistics display
        stats_frame = tk.LabelFrame(frame, text="Statistics", padx=15, pady=15)
        stats_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.keystroke_stats_text = scrolledtext.ScrolledText(
            stats_frame,
            width=70,
            height=10,
            font=("Courier New", 9),
            wrap=tk.WORD
        )
        self.keystroke_stats_text.pack(fill=tk.BOTH, expand=True)
        
        tk.Button(
            stats_frame,
            text="🔄 Refresh Statistics",
            command=self._update_keystroke_statistics,
            width=20,
            bg="#3498db",
            fg="white",
            font=("Arial", 9),
            cursor="hand2"
        ).pack(pady=5)
        
        self._update_keystroke_statistics()

    def export_keystrokes(self, format_type: str, decrypt: bool = False):
        """Export keystroke data"""
        try:
            from keystroke_recorder import KeystrokeRecorder
            from datetime import timedelta
            
            # Confirm action
            if decrypt:
                if not messagebox.askyesno(
                    "⚠️ Export Decrypted Data",
                    "You are about to export DECRYPTED keystroke data.\n\n"
                    "This will contain plain-text keystrokes.\n\n"
                    "This action will be logged.\n\nContinue?",
                    icon='warning'
                ):
                    return
            
            # Get date range
            days = simpledialog.askinteger(
                "Date Range",
                "Export data from last N days:",
                initialvalue=7,
                minvalue=1,
                maxvalue=90
            )
            
            if not days:
                return
            
            start_date = datetime.now() - timedelta(days=days)
            
            # Initialize recorder for export
            keystroke_dir = get_keystroke_storage_dir()
            recorder = KeystrokeRecorder(
                storage_dir=keystroke_dir,
                enable_encryption=True
            )
            
            if format_type == 'json':
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json")],
                    initialfile=f"keystrokes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                
                if file_path:
                    recorder.export_to_json(
                        Path(file_path),
                        start_date=start_date,
                        decrypt=decrypt
                    )
                    messagebox.showinfo("Success", f"Keystrokes exported to:\n{file_path}")
            
            elif format_type == 'csv':
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv")],
                    initialfile=f"keystrokes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )
                
                if file_path:
                    recorder.export_to_csv(
                        Path(file_path),
                        start_date=start_date
                    )
                    messagebox.showinfo("Success", f"Keystrokes exported to:\n{file_path}")
            
            # Log export action
            self.database.log_system_event(
                event_type='keystroke_export',
                severity='WARNING',
                message=f'Keystroke data exported by admin (decrypt={decrypt}, format={format_type})',
                details={'days': days, 'decrypt': decrypt}
            )
            
        except Exception as e:
            logger.error(f"Keystroke export error: {e}")
            messagebox.showerror("Error", f"Failed to export keystrokes:\n{e}")

    def _update_keystroke_statistics(self):
        """Update keystroke statistics display"""
        try:
            from keystroke_recorder import KeystrokeRecorder
            
            keystroke_dir = get_keystroke_storage_dir()
            recorder = KeystrokeRecorder(
                storage_dir=keystroke_dir,
                enable_encryption=True
            )
            
            stats = recorder.get_statistics()
            
            stats_text = f"""
    {'='*70}
    KEYSTROKE STATISTICS
    {'='*70}

    Database Information:
    Location: {stats.get('database_path', 'N/A')}
    
    Recording Status:
    Currently Recording: {stats.get('is_recording', False)}
    Current Session: {stats.get('total_keystrokes_session', 0)} keystrokes
    Buffer Size: {stats.get('buffer_size', 0)} events
    
    Historical Data:
    Total Keystrokes (DB): {stats.get('total_keystrokes_db', 0):,}
    Earliest Event: {stats.get('earliest_event', 'N/A')}
    Latest Event: {stats.get('latest_event', 'N/A')}

    Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

    {'='*70}
            """
            
            self.keystroke_stats_text.delete(1.0, tk.END)
            self.keystroke_stats_text.insert(1.0, stats_text.strip())
            
        except Exception as e:
            logger.error(f"Error updating keystroke statistics: {e}")
            error_text = f"Error loading statistics:\n{str(e)}"
            self.keystroke_stats_text.delete(1.0, tk.END)
            self.keystroke_stats_text.insert(1.0, error_text)
        
    def verify(self):
        """Verify password and login"""
        password = self.password_entry.get()
        
        if not password:
            messagebox.showwarning(
                "Empty Password",
                "Please enter a password",
                parent=self.root
            )
            return
        
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
        """Cancel login"""
        self.authenticated = False
        self.root.destroy()
    
    def show(self) -> bool:
        """Show dialog and return authentication result"""
        self.root.mainloop()
        return self.authenticated

class ServiceController:
    """Windows service controller"""
    
    def __init__(self, service_name: str = "EnterpriseMonitoringAgent"):
        self.service_name = service_name
    
    def get_status(self) -> str:
        """Get service status"""
        try:
            import win32serviceutil
            status = win32serviceutil.QueryServiceStatus(self.service_name)[1]
            
            status_map = {
                1: "Stopped",
                2: "Start Pending",
                3: "Stop Pending",
                4: "Running",
                5: "Continue Pending",
                6: "Pause Pending",
                7: "Paused"
            }
            
            return status_map.get(status, "Unknown")
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return "Not Installed"
    
    def start_service(self) -> bool:
        """Start service"""
        try:
            import win32serviceutil
            win32serviceutil.StartService(self.service_name)
            logger.info(f"Started service: {self.service_name}")
            return True
        except Exception as e:
            logger.error(f"Error starting service: {e}")
            return False
    
    def stop_service(self) -> bool:
        """Stop service"""
        try:
            import win32serviceutil
            win32serviceutil.StopService(self.service_name)
            logger.info(f"Stopped service: {self.service_name}")
            return True
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            return False
    
    def restart_service(self) -> bool:
        """Restart service"""
        try:
            import win32serviceutil
            win32serviceutil.RestartService(self.service_name)
            logger.info(f"Restarted service: {self.service_name}")
            return True
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return False

    def install_service(self) -> bool:
        """Install the service"""
        try:
            import subprocess
            import sys
            
            # Determine path to service script
            if getattr(sys, 'frozen', False):
                # If running as compiled exe, we assume duplicate exe for service or same exe with arguments
                # For this setup, we'll assume there is a separate 'EnterpriseMonitoringService.exe'
                service_exe = Path(sys.executable).parent / "EnterpriseMonitoringService.exe"
                cmd = [str(service_exe), "install"]
            else:
                # Running as script
                service_script = Path(__file__).parent / "service_main.py"
                cmd = [sys.executable, str(service_script), "install"]
            
            logger.info(f"Installing service with command: {cmd}")
            
            # Run installation command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                logger.info("Service installed successfully")
                return True
            else:
                logger.error(f"Failed to install service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing service: {e}")
            return False

    def remove_service(self) -> bool:
        """Remove the service"""
        try:
            import subprocess
            import sys
            
            # Determine path to service script/exe
            if getattr(sys, 'frozen', False):
                service_exe = Path(sys.executable).parent / "EnterpriseMonitoringService.exe"
                cmd = [str(service_exe), "remove"]
            else:
                service_script = Path(__file__).parent / "service_main.py"
                cmd = [sys.executable, str(service_script), "remove"]
            
            logger.info(f"Removing service with command: {cmd}")
            
            # Run removal command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                logger.info("Service removed successfully")
                return True
            else:
                # 1060 means service doesn't exist, which is fine for removal
                if "1060" in result.stderr:
                    return True
                logger.error(f"Failed to remove service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing service: {e}")
            return False


class AdminConsole:
    """Main admin console application"""
    
    def __init__(self):
        # Check UAC elevation
        if not is_admin():
            print("Requesting administrator privileges...")
            try:
                request_uac_elevation()
            except Exception as e:
                logger.error(f"Failed to request UAC elevation: {e}")
            # If we get here, elevation was cancelled
            sys.exit(1)

    
    # If we get here, we ARE admin - continue normally
        print("Running with administrator privileges ✓")
    
    # Initialize components
        config_dir = Path.home() / ".clipboard_monitor"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        self.auth_manager = AdminAuthManager(config_dir)
        self.config = Config()
        
        # Authenticate
        login_dialog = AdminLoginDialog(self.auth_manager)
        if not login_dialog.show():
            logger.info("Authentication cancelled")
            sys.exit(0)
        

        
        # Initialize service controller
        self.service_controller = ServiceController()
        
        # Initialize database
        db_path = get_database_path()
        self.database = DatabaseManager(db_path, enable_encryption=True)
        
        # Create main window
        self.root = tk.Tk()
        self.root.title("Admin Console - Enterprise Monitoring Agent")
        self.root.geometry("900x700")
        
        # Set icon
        try:
            icon_path = project_root / "resources" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass
        
        self._create_ui()
        
        # Start status update loop
        self._update_status()
    
    def _create_ui(self):
        """Create admin console UI"""
        # Header
        header = tk.Frame(self.root, bg="#34495e", height=70)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="⚙️ Administrator Console",
            font=("Arial", 18, "bold"),
            bg="#34495e",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=20)
        
        # User info
        tk.Label(
            header,
            text=f"Logged in as: Administrator",
            font=("Arial", 10),
            bg="#34495e",
            fg="#bdc3c7"
        ).pack(side=tk.RIGHT, padx=20)
        
        # Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.service_tab = tk.Frame(notebook)
        self.stats_tab = tk.Frame(notebook)
        self.export_tab = tk.Frame(notebook)
        self.settings_tab = tk.Frame(notebook)
        self.security_tab = tk.Frame(notebook)
        
        notebook.add(self.service_tab, text="  Service Control  ")
        notebook.add(self.stats_tab, text="  Statistics  ")
        notebook.add(self.export_tab, text="  Export Data  ")
        notebook.add(self.settings_tab, text="  Settings  ")
        notebook.add(self.security_tab, text="  Security  ")
        
        # Build tabs
        self._create_service_tab()
        self._create_stats_tab()
        self._create_export_tab()
        self._create_settings_tab()
        self._create_security_tab()
    
    def _create_service_tab(self):
        """Create service control tab"""
        frame = tk.LabelFrame(
            self.service_tab,
            text="Service Status and Control",
            padx=20,
            pady=20,
            font=("Arial", 11, "bold")
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Status display
        status_frame = tk.Frame(frame)
        status_frame.pack(pady=20)
        
        tk.Label(
            status_frame,
            text="Service Status:",
            font=("Arial", 12)
        ).pack(side=tk.LEFT, padx=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="● Unknown",
            font=("Arial", 14, "bold"),
            fg="gray"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        # Control buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="➕ Install Service",
            command=self.install_service,
            width=15,
            height=2,
            bg="#2980b9",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="▶️ Start Service",
            command=self.start_service,
            width=15,
            height=2,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="⏹️ Stop Service",
            command=self.stop_service,
            width=15,
            height=2,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="🔄 Restart Service",
            command=self.restart_service,
            width=15,
            height=2,
            bg="#f39c12",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)

        tk.Button(
            btn_frame,
            text="❌ Remove Service",
            command=self.remove_service,
            width=15,
            height=2,
            bg="#c0392b",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=10)
        
        # Service info
        info_frame = tk.LabelFrame(frame, text="Service Information", padx=15, pady=15)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        self.service_info_text = scrolledtext.ScrolledText(
            info_frame,
            width=70,
            height=10,
            font=("Courier New", 9),
            wrap=tk.WORD
        )
        self.service_info_text.pack(fill=tk.BOTH, expand=True)
        
        self._update_service_info()

    def install_service(self):
        """Install service"""
        if self.service_controller.install_service():
            messagebox.showinfo("Success", "Service installed successfully")
            self._update_status()
        else:
            messagebox.showerror("Error", "Failed to install service")
            
    def remove_service(self):
        """Remove service"""
        if messagebox.askyesno("Confirm Removal", "Are you sure you want to remove the monitoring service?"):
            if self.service_controller.remove_service():
                messagebox.showinfo("Success", "Service removed successfully")
                self._update_status()
            else:
                messagebox.showerror("Error", "Failed to remove service")
    
    def _create_stats_tab(self):
        """Create statistics tab"""
        frame = tk.LabelFrame(
            self.stats_tab,
            text="Monitoring Statistics",
            padx=20,
            pady=20,
            font=("Arial", 11, "bold")
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Stats display
        self.stats_text = scrolledtext.ScrolledText(
            frame,
            width=80,
            height=25,
            font=("Courier New", 10),
            wrap=tk.WORD
        )
        self.stats_text.pack(fill=tk.BOTH, expand=True)
        
        # Refresh button
        tk.Button(
            frame,
            text="🔄 Refresh Statistics",
            command=self._update_statistics,
            width=20,
            height=2,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=10)
        
        self._update_statistics()
    
    def _create_export_tab(self):
        """Create export data tab"""
        frame = tk.LabelFrame(
            self.export_tab,
            text="Export Monitoring Data",
            padx=20,
            pady=20,
            font=("Arial", 11, "bold")
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Export options
        tk.Label(
            frame,
            text="Export Format:",
            font=("Arial", 11)
        ).pack(anchor='w', pady=5)
        
        self.export_format = tk.StringVar(value="json")
        
        tk.Radiobutton(
            frame,
            text="JSON (Complete data with structure)",
            variable=self.export_format,
            value="json",
            font=("Arial", 10)
        ).pack(anchor='w', padx=20)
        
        tk.Radiobutton(
            frame,
            text="CSV (Spreadsheet compatible)",
            variable=self.export_format,
            value="csv",
            font=("Arial", 10)
        ).pack(anchor='w', padx=20)
        
        # Export buttons
        btn_frame = tk.Frame(frame)
        btn_frame.pack(pady=30)
        
        tk.Button(
            btn_frame,
            text="📄 Export Clipboard Data",
            command=lambda: self.export_data('clipboard'),
            width=25,
            height=2,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=5)
        
        tk.Button(
            btn_frame,
            text="💻 Export Application Usage",
            command=lambda: self.export_data('apps'),
            width=25,
            height=2,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=5)
        
        tk.Button(
            btn_frame,
            text="🌐 Export Browser Activity",
            command=lambda: self.export_data('browser'),
            width=25,
            height=2,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=5)
        
        tk.Button(
            btn_frame,
            text="📊 Export All Data",
            command=lambda: self.export_data('all'),
            width=25,
            height=2,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=5)
    
    def _create_settings_tab(self):
        """Create settings tab"""
        frame = tk.LabelFrame(
            self.settings_tab,
            text="System Settings",
            padx=20,
            pady=20,
            font=("Arial", 11, "bold")
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            frame,
            text="Settings management coming soon...",
            font=("Arial", 12)
        ).pack(pady=50)
    
    def _create_security_tab(self):
        """Create security tab"""
        frame = tk.LabelFrame(
            self.security_tab,
            text="Security Settings",
            padx=20,
            pady=20,
            font=("Arial", 11, "bold")
        )
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Change password section
        pwd_frame = tk.LabelFrame(frame, text="Change Admin Password", padx=15, pady=15)
        pwd_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(
            pwd_frame,
            text="🔐 Change Password",
            command=self.change_password,
            width=20,
            height=2,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        ).pack(pady=10)
    
    def _update_status(self):
        """Update service status periodically"""
        try:
            status = self.service_controller.get_status()
            
            if status == "Running":
                self.status_label.config(text="● Running", fg="green")
            elif status == "Stopped":
                self.status_label.config(text="● Stopped", fg="red")
            elif status == "Not Installed":
                self.status_label.config(text="● Not Installed", fg="orange")
            else:
                self.status_label.config(text=f"● {status}", fg="orange")
            
            # Schedule next update
            self.root.after(5000, self._update_status)
            
        except Exception as e:
            logger.error(f"Error updating status: {e}")
    
    def _update_service_info(self):
        """Update service information display"""
        try:
            info = f"""
Service Name: EnterpriseMonitoringAgent
Display Name: Enterprise Activity Monitoring Service
Status: {self.service_controller.get_status()}

Description:
Monitors user activity including clipboard operations, application usage,
and browser activity for compliance and productivity tracking.

Configuration:
- Database: {get_database_path()}
- Logs: {get_logs_dir()}
- Startup Type: Automatic
- Service Account: LocalSystem

Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            
            self.service_info_text.delete(1.0, tk.END)
            self.service_info_text.insert(1.0, info.strip())
            
        except Exception as e:
            logger.error(f"Error updating service info: {e}")
    
    def _update_statistics(self):
        """Update statistics display"""
        try:
            stats = self.database.get_statistics()
            
            stats_text = f"""
{'='*70}
MONITORING STATISTICS
{'='*70}

Database Information:
  Location: {self.database.db_path}
  Size: {stats.get('database_size_mb', 0)} MB
  
Event Counts:
  Clipboard Events: {stats.get('clipboard_events_count', 0):,}
  Application Usage Sessions: {stats.get('app_usage_count', 0):,}
  Browser Activity Sessions: {stats.get('browser_activity_count', 0):,}
  Screen Recordings: {stats.get('screen_recordings_count', 0):,}
  System Events: {stats.get('system_events_count', 0):,}

Date Range:
  Oldest Event: {stats.get('oldest_event', 'N/A')}
  Newest Event: {stats.get('newest_event', 'N/A')}

Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*70}
            """
            
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, stats_text.strip())
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            messagebox.showerror("Error", f"Failed to load statistics:\n{e}")
    
    def start_service(self):
        """Start monitoring service"""
        if messagebox.askyesno(
            "Start Service",
            "Start the monitoring service?"
        ):
            if self.service_controller.start_service():
                messagebox.showinfo("Success", "Service started successfully")
                self._update_service_info()
            else:
                messagebox.showerror("Error", "Failed to start service")
    
    def stop_service(self):
        """Stop monitoring service"""
        if messagebox.askyesno(
            "Stop Service",
            "Stop the monitoring service?\n\nThis will stop all monitoring activities."
        ):
            if self.service_controller.stop_service():
                messagebox.showinfo("Success", "Service stopped successfully")
                self._update_service_info()
            else:
                messagebox.showerror("Error", "Failed to stop service")
    
    def restart_service(self):
        """Restart monitoring service"""
        if messagebox.askyesno(
            "Restart Service",
            "Restart the monitoring service?"
        ):
            if self.service_controller.restart_service():
                messagebox.showinfo("Success", "Service restarted successfully")
                self._update_service_info()
            else:
                messagebox.showerror("Error", "Failed to restart service")
    
    def export_data(self, data_type: str):
        """Export monitoring data"""
        try:
            format_type = self.export_format.get()
            
            if format_type == "json":
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".json",
                    filetypes=[("JSON files", "*.json")],
                    initialfile=f"monitoring_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                )
                
                if file_path:
                    table_map = {
                        'clipboard': 'clipboard_events',
                        'apps': 'app_usage',
                        'browser': 'browser_activity',
                        'all': None
                    }
                    
                    self.database.export_to_json(
                        Path(file_path),
                        table_name=table_map.get(data_type)
                    )
                    
                    messagebox.showinfo("Success", f"Data exported to:\n{file_path}")
            
            else:  # CSV
                dir_path = filedialog.askdirectory(
                    title="Select export directory"
                )
                
                if dir_path:
                    self.database.export_to_csv(Path(dir_path))
                    messagebox.showinfo("Success", f"Data exported to:\n{dir_path}")
        
        except Exception as e:
            logger.error(f"Export error: {e}")
            messagebox.showerror("Error", f"Failed to export data:\n{e}")
    
    def change_password(self):
        """Change admin password"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Change Admin Password")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        
        tk.Label(dialog, text="New Password:", font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        new_pwd = tk.Entry(dialog, show="●", width=25, font=("Arial", 10))
        new_pwd.grid(row=0, column=1, padx=10, pady=10)
        
        tk.Label(dialog, text="Confirm Password:", font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=10, sticky='w')
        confirm_pwd = tk.Entry(dialog, show="●", width=25, font=("Arial", 10))
        confirm_pwd.grid(row=1, column=1, padx=10, pady=10)
        
        def save_password():
            if new_pwd.get() != confirm_pwd.get():
                messagebox.showerror("Error", "Passwords do not match", parent=dialog)
                return
            
            if len(new_pwd.get()) < 8:
                messagebox.showerror("Error", "Password must be at least 8 characters", parent=dialog)
                return
            
            if self.auth_manager.set_admin_password(new_pwd.get()):
                messagebox.showinfo("Success", "Password changed successfully", parent=dialog)
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to change password", parent=dialog)
        
        tk.Button(dialog, text="Save", command=save_password, width=12, bg="#27ae60", fg="white").grid(row=2, column=0, pady=20)
        tk.Button(dialog, text="Cancel", command=dialog.destroy, width=12, bg="#e74c3c", fg="white").grid(row=2, column=1, pady=20)
    
    def run(self):
        """Run admin console"""
        self.root.mainloop()


def main():
    """Main entry point"""
    # Configure logging
    log_dir = get_logs_dir()
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'admin.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    try:
        app = AdminConsole()
        app.run()
    except Exception as e:
        logger.error(f"Admin console error: {e}", exc_info=True)
        messagebox.showerror("Error", f"Application error:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()