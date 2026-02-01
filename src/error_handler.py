import sys
import traceback
import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

logger = logging.getLogger(__name__)

def show_error_dialog(title: str, message: str, details: str = None):
    """Show error dialog to user"""
    try:
        root = tk.Tk()
        root.withdraw()
        
        error_msg = message
        if details:
            error_msg += f"\n\nDetails:\n{details}"
        
        messagebox.showerror(title, error_msg)
        root.destroy()
    except:
        print(f"ERROR: {title}\n{message}")
        if details:
            print(f"Details: {details}")

def handle_exception(exc_type, exc_value, exc_traceback):
    """Global exception handler"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical("Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    show_error_dialog(
        "Clipboard Monitor Error",
        "An unexpected error occurred. The application will now close.",
        error_msg
    )

def setup_exception_handling():
    """Setup global exception handling"""
    sys.excepthook = handle_exception