"""
Admin Console Application - FIXED VERSION

Protected admin console for controlling the monitoring service.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
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
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Current directory: {Path(__file__).parent}")
    print(f"Project root: {project_root}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

logger = logging.getLogger(__name__)


class AdminLoginDialog:
    """Admin authentication dialog"""
    
    def __init__(self, auth_manager: AdminAuthManager):
        self.auth_manager = auth_manager
        self.authenticated = False
        
        self.root = tk.Tk()
        self.root.title("Admin Authentication Required")
        self.root.geometry("450x250")
        self.root.resizable(False, False)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 225
        y = (self.root.winfo_screenheight() // 2) - 125
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
        """Create login UI"""
        # Header
        header_frame = tk.Frame(self.root, bg="#34495e", height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🔒 Administrator Access",
            font=("Arial", 16, "bold"),
            bg="#34495e",
            fg="white"
        ).pack(pady=20)
        
        # Login form
        form_frame = tk.Frame(self.root, padx=40, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
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
        
        # Buttons
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
        
        # Initial password hint
        initial_file = self.auth_manager.config_dir / 'ADMIN_INITIAL_PASSWORD.txt'
        if initial_file.exists():
            tk.Label(
                form_frame,
                text="ℹ️ Check ADMIN_INITIAL_PASSWORD.txt for first-time password",
                font=("Arial", 8),
                fg="#7f8c8d"
            ).grid(row=2, column=0, columnspan=2, pady=5)
        
        self.password_entry.focus()
    
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


class AdminConsole:
    """Main admin console application"""
    
    def __init__(self):
        # Check UAC elevation
        if not is_admin():
            # Hide the root window so we just see the error
            temp_root = tk.Tk()
            temp_root.withdraw() 
            messagebox.showerror(
                "Administrator Privileges Required",
                "CRITICAL ERROR: Access Denied.\n\n"
                "This application interacts with system services and writes to "
                "C:\\ProgramData. It MUST be run as Administrator.\n\n"
                "Please right-click the application and select 'Run as Administrator'."
            )
            temp_root.destroy()
            sys.exit(1) # Stop here. Do not try to auto-restart.
        
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
        data_dir = Path('C:/ProgramData/EnterpriseMonitoring/data')
        data_dir.mkdir(parents=True, exist_ok=True)
        
        db_path = data_dir / 'monitoring.db'
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
- Database: C:/ProgramData/EnterpriseMonitoring/data/monitoring.db
- Logs: C:/ProgramData/EnterpriseMonitoring/logs/
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
    log_dir = Path('C:/ProgramData/EnterpriseMonitoring/logs')
    log_dir.mkdir(parents=True, exist_ok=True)
    
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