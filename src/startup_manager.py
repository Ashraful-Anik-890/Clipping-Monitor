"""
Windows Service Integration Module
Enables background execution with startup registration

Note: For transparency and user control, this implementation uses
Task Scheduler instead of true Windows Services, which provides:
- Visible presence in Task Manager
- User-controllable startup behavior
- Clear uninstall process
- No service installation complexity
"""

import os
import sys
import win32com.client
import win32api
import win32con
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class StartupManager:
    """
    Manages application startup behavior using Windows Task Scheduler
    
    More transparent than Windows Services and easier for users to control
    """
    
    TASK_NAME = "ClipboardMonitor_Startup"
    
    def __init__(self, exe_path: Optional[Path] = None):
        """
        Initialize startup manager
        
        Args:
            exe_path: Path to the executable (auto-detected if None)
        """
        if exe_path:
            self.exe_path = Path(exe_path)
        else:
            # Auto-detect executable path
            if getattr(sys, 'frozen', False):
                # Running as compiled executable
                self.exe_path = Path(sys.executable)
            else:
                # Running as script
                self.exe_path = Path(sys.argv[0]).absolute()
        
        logger.info(f"StartupManager initialized with exe: {self.exe_path}")
    
    def enable_startup(self) -> bool:
        """
        Enable application to start on system boot
        
        Returns:
            True if successful, False otherwise
        """
        try:
            scheduler = win32com.client.Dispatch('Schedule.Service')
            scheduler.Connect()
            
            root_folder = scheduler.GetFolder('\\')
            task_def = scheduler.NewTask(0)
            
            # Task settings
            task_def.RegistrationInfo.Description = "Clipboard Monitor - Screen Recording and Clipboard Tracking"
            task_def.RegistrationInfo.Author = "ClipboardMonitor"
            
            # Set to run whether user is logged in or not
            task_def.Principal.LogonType = 3  # TASK_LOGON_INTERACTIVE_TOKEN
            task_def.Principal.RunLevel = 0   # TASK_RUNLEVEL_LUA (standard user)
            
            # Task settings
            settings = task_def.Settings
            settings.Enabled = True
            settings.StartWhenAvailable = True
            settings.Hidden = False  # Visible for transparency
            settings.DisallowStartIfOnBatteries = False
            settings.StopIfGoingOnBatteries = False
            settings.AllowDemandStart = True
            settings.AllowHardTerminate = False
            settings.MultipleInstances = 0  # TASK_INSTANCES_PARALLEL
            
            # Trigger: At logon
            triggers = task_def.Triggers
            trigger = triggers.Create(9)  # TASK_TRIGGER_LOGON
            trigger.Enabled = True
            trigger.Delay = "PT30S"  # 30 second delay after logon
            
            # Action: Start program
            actions = task_def.Actions
            action = actions.Create(0)  # TASK_ACTION_EXEC
            action.Path = str(self.exe_path)
            action.Arguments = "--background"  # Run in background mode
            action.WorkingDirectory = str(self.exe_path.parent)
            
            # Register task
            root_folder.RegisterTaskDefinition(
                self.TASK_NAME,
                task_def,
                6,  # TASK_CREATE_OR_UPDATE
                None,
                None,
                3  # TASK_LOGON_INTERACTIVE_TOKEN
            )
            
            logger.info("Startup task registered successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error enabling startup: {e}", exc_info=True)
            return False
    
    def disable_startup(self) -> bool:
        """
        Disable application startup on boot
        
        Returns:
            True if successful, False otherwise
        """
        try:
            scheduler = win32com.client.Dispatch('Schedule.Service')
            scheduler.Connect()
            
            root_folder = scheduler.GetFolder('\\')
            root_folder.DeleteTask(self.TASK_NAME, 0)
            
            logger.info("Startup task removed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error disabling startup: {e}", exc_info=True)
            return False
    
    def is_startup_enabled(self) -> bool:
        """
        Check if startup is currently enabled
        
        Returns:
            True if startup task exists and is enabled
        """
        try:
            scheduler = win32com.client.Dispatch('Schedule.Service')
            scheduler.Connect()
            
            root_folder = scheduler.GetFolder('\\')
            task = root_folder.GetTask(self.TASK_NAME)
            
            return task.Enabled
            
        except Exception as e:
            # Task doesn't exist
            logger.debug(f"Startup task check: {e}")
            return False
    
    def add_to_registry_run(self) -> bool:
        """
        Alternative method: Add to Windows Registry Run key
        Less recommended than Task Scheduler, but simpler
        
        Returns:
            True if successful
        """
        try:
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            winreg.SetValueEx(
                key,
                "ClipboardMonitor",
                0,
                winreg.REG_SZ,
                f'"{self.exe_path}" --background'
            )
            
            winreg.CloseKey(key)
            logger.info("Added to registry run key")
            return True
            
        except Exception as e:
            logger.error(f"Error adding to registry: {e}")
            return False
    
    def remove_from_registry_run(self) -> bool:
        """
        Remove from Windows Registry Run key
        
        Returns:
            True if successful
        """
        try:
            import winreg
            
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                key_path,
                0,
                winreg.KEY_SET_VALUE
            )
            
            try:
                winreg.DeleteValue(key, "ClipboardMonitor")
            except FileNotFoundError:
                pass  # Already removed
            
            winreg.CloseKey(key)
            logger.info("Removed from registry run key")
            return True
            
        except Exception as e:
            logger.error(f"Error removing from registry: {e}")
            return False


class ProcessManager:
    """
    Manages process lifecycle and singleton behavior
    """
    
    MUTEX_NAME = "Global\\ClipboardMonitor_SingleInstance"
    
    @staticmethod
    def ensure_single_instance() -> bool:
        """
        Ensure only one instance of the application is running
        
        Returns:
            True if this is the only instance, False if another is running
        """
        try:
            import win32event
            
            # Try to create mutex
            mutex = win32event.CreateMutex(None, False, ProcessManager.MUTEX_NAME)
            last_error = win32api.GetLastError()
            
            if last_error == 183:  # ERROR_ALREADY_EXISTS
                logger.warning("Another instance is already running")
                return False
            
            logger.info("Single instance confirmed")
            return True
            
        except Exception as e:
            logger.error(f"Error checking single instance: {e}")
            return True  # Allow to run if check fails
    
    @staticmethod
    def is_admin() -> bool:
        """
        Check if running with administrator privileges
        
        Returns:
            True if running as admin
        """
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    
    @staticmethod
    def request_admin():
        """
        Request administrator privileges (UAC prompt)
        Restarts the application with admin rights
        """
        try:
            import ctypes
            
            if ProcessManager.is_admin():
                return True
            
            # Re-run the program with admin rights
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                " ".join(sys.argv),
                None,
                1  # SW_SHOWNORMAL
            )
            
            # Exit current process
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"Error requesting admin: {e}")
            return False


class BackgroundRunner:
    """
    Handles background execution mode
    """
    
    def __init__(self, app_instance):
        """
        Initialize background runner
        
        Args:
            app_instance: Main application instance
        """
        self.app = app_instance
        self.is_background_mode = False
        logger.info("BackgroundRunner initialized")
    
    def run_in_background(self):
        """
        Run application in background mode
        - No console window
        - Minimal UI (tray only)
        - Auto-start monitoring if consent given
        """
        self.is_background_mode = True
        logger.info("Running in background mode")
        
        # Hide console window if present
        self._hide_console()
        
        # Don't show main window, only tray
        # Auto-start monitoring if consent given
        if self.app.permission_manager.has_consent():
            logger.info("Auto-starting monitoring (background mode)")
            self.app.start_monitoring()
        
        # Run tray icon (blocking)
        self.app.tray_icon.run()
    
    def _hide_console(self):
        """Hide console window"""
        try:
            import ctypes
            whnd = ctypes.windll.kernel32.GetConsoleWindow()
            if whnd != 0:
                ctypes.windll.user32.ShowWindow(whnd, 0)  # SW_HIDE
                logger.debug("Console window hidden")
        except Exception as e:
            logger.error(f"Error hiding console: {e}")


# Example usage in main.py:
"""
def main():
    import argparse
    
    parser = argparse.ArgumentParser()
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
        else:
            print("Failed to enable startup")
        sys.exit(0)
    
    if args.remove_startup:
        startup_mgr = StartupManager()
        if startup_mgr.disable_startup():
            print("Startup disabled successfully")
        else:
            print("Failed to disable startup")
        sys.exit(0)
    
    # Initialize app
    app = ClipboardMonitorApp()
    
    # Run in background or normal mode
    if args.background:
        background_runner = BackgroundRunner(app)
        background_runner.run_in_background()
    else:
        app.run()
"""
