import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ConsentDialog:
    """Dialog to request user consent"""
    
    def __init__(self, parent):
        self.result = False
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Clipboard Monitor - User Consent Required")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        
        # Make sure dialog appears on top
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.lift()
        self.dialog.focus_force()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (500 // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        # Title
        title_label = tk.Label(
            self.dialog,
            text="⚠️ Clipboard Monitoring Consent",
            font=("Arial", 16, "bold"),
            fg="#e74c3c"
        )
        title_label.pack(pady=20)
        
        # Consent text
        consent_text = scrolledtext.ScrolledText(
            self.dialog,
            wrap=tk.WORD,
            width=70,
            height=18,
            font=("Arial", 9)
        )
        consent_text.pack(padx=20, pady=10)
        
        consent_message = """
CLIPBOARD MONITOR - USER CONSENT AGREEMENT

This application monitors clipboard activity on your device to track copy and paste operations.

═══════════════════════════════════════════════════════════════════

WHAT WE MONITOR:
- All clipboard copy operations (Ctrl+C, right-click copy, etc.)
- Clipboard paste operations (Ctrl+V, right-click paste, etc.)
- Data type and size of clipboard content
- Source application names
- File names and destinations for file transfers
- Timestamps of clipboard events

DATA STORAGE:
- All logs are stored locally on your device
- Logs can be encrypted for security
- You control the storage location
- No data is transmitted to external servers

YOUR RIGHTS:
- You can stop monitoring at any time
- You can delete all logs at any time
- You can revoke consent and uninstall the application
- You have full access to view all collected data

PRIVACY NOTICE:
This application operates ONLY with your explicit consent. It is designed for 
legitimate purposes such as productivity tracking, data loss prevention, or 
security monitoring on devices you own or have authorization to monitor.

═══════════════════════════════════════════════════════════════════

By clicking "I Agree", you:
1. Confirm you own this device or have authorization to monitor it
2. Understand what data will be collected
3. Consent to clipboard monitoring as described above
4. Acknowledge this is for legitimate purposes only

Click "I Agree" to provide consent and continue, or "Decline" to exit.
        """
        
        consent_text.insert(1.0, consent_message)
        consent_text.config(state=tk.DISABLED)
        
        # Checkbox
        self.agree_var = tk.BooleanVar()
        agree_check = tk.Checkbutton(
            self.dialog,
            text="✓ I have read and agree to the terms above",
            variable=self.agree_var,
            font=("Arial", 10, "bold")
        )
        agree_check.pack(pady=10)
        
        # Buttons
        button_frame = tk.Frame(self.dialog)
        button_frame.pack(pady=15)
        
        agree_btn = tk.Button(
            button_frame,
            text="✓ I Agree",
            command=self.on_agree,
            width=15,
            height=2,
            bg="#27ae60",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2"
        )
        agree_btn.pack(side=tk.LEFT, padx=10)
        
        decline_btn = tk.Button(
            button_frame,
            text="✗ Decline",
            command=self.on_decline,
            width=15,
            height=2,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11, "bold"),
            cursor="hand2"
        )
        decline_btn.pack(side=tk.LEFT, padx=10)
    
    def on_agree(self):
        if self.agree_var.get():
            self.result = True
            self.dialog.destroy()
        else:
            messagebox.showwarning(
                "Consent Required",
                "Please check the agreement box to continue.",
                parent=self.dialog
            )
    
    def on_decline(self):
        self.result = False
        self.dialog.destroy()
    
    def show(self) -> bool:
        self.dialog.wait_window()
        return self.result


class MainWindow:
    """Main application window"""
    
    def __init__(self, on_start_monitoring, on_stop_monitoring, on_export_logs, 
                 on_settings_change, on_clear_logs):
        self.on_start_monitoring = on_start_monitoring
        self.on_stop_monitoring = on_stop_monitoring
        self.on_export_logs = on_export_logs
        self.on_settings_change = on_settings_change
        self.on_clear_logs = on_clear_logs
        
        self.root = tk.Tk()
        self.root.title("Clipboard Monitor v1.0")
        self.root.geometry("1100x650")
        
        self.is_monitoring = False
        self.event_count = 0
        
        self._create_widgets()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Auto-refresh timer for GUI updates
        self._schedule_refresh()
    
    def _schedule_refresh(self):
        """Schedule periodic GUI refresh"""
        try:
            self.root.update_idletasks()
        except:
            pass
        # Schedule next refresh
        self.root.after(100, self._schedule_refresh)
    
    def _create_widgets(self):
        """Create GUI widgets"""
        
        # Header
        header_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="📋 Clipboard Monitor",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title_label.pack(pady=20)
        
        # Status Frame
        status_frame = tk.LabelFrame(self.root, text="Status", padx=10, pady=10)
        status_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.status_label = tk.Label(
            status_frame,
            text="● Stopped",
            font=("Arial", 12, "bold"),
            fg="red"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)
        
        self.event_count_label = tk.Label(
            status_frame,
            text="Events Logged: 0",
            font=("Arial", 10)
        )
        self.event_count_label.pack(side=tk.LEFT, padx=20)
        
        # Control Frame
        control_frame = tk.LabelFrame(self.root, text="Controls", padx=10, pady=10)
        control_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.start_btn = tk.Button(
            control_frame,
            text="▶ Start Monitoring",
            command=self.toggle_monitoring,
            width=18,
            height=2,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(
            control_frame,
            text="📄 Export Logs",
            command=self.export_logs,
            width=18,
            height=2,
            bg="#3498db",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = tk.Button(
            control_frame,
            text="🗑️ Clear Logs",
            command=self.clear_all_logs,
            width=18,
            height=2,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        settings_btn = tk.Button(
            control_frame,
            text="⚙️ Settings",
            command=self.show_settings,
            width=18,
            height=2,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10, "bold"),
            cursor="hand2"
        )
        settings_btn.pack(side=tk.LEFT, padx=5)
        
        # Recent Events Frame
        events_frame = tk.LabelFrame(self.root, text="Recent Events (Double-click for details)", padx=10, pady=10)
        events_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create treeview for events
        columns = ("Time", "Type", "Size", "Source", "Destination", "Preview")
        self.events_tree = ttk.Treeview(events_frame, columns=columns, show="headings", height=15)
        
        # Configure columns
        self.events_tree.heading("Time", text="Time")
        self.events_tree.heading("Type", text="Type")
        self.events_tree.heading("Size", text="Size")
        self.events_tree.heading("Source", text="Source")
        self.events_tree.heading("Destination", text="Destination")
        self.events_tree.heading("Preview", text="Preview/Files")
        
        self.events_tree.column("Time", width=90)
        self.events_tree.column("Type", width=90)
        self.events_tree.column("Size", width=90)
        self.events_tree.column("Source", width=140)
        self.events_tree.column("Destination", width=220)
        self.events_tree.column("Preview", width=350)
        
        # Scrollbars
        vsb = ttk.Scrollbar(events_frame, orient=tk.VERTICAL, command=self.events_tree.yview)
        hsb = ttk.Scrollbar(events_frame, orient=tk.HORIZONTAL, command=self.events_tree.xview)
        self.events_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.events_tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        events_frame.grid_rowconfigure(0, weight=1)
        events_frame.grid_columnconfigure(0, weight=1)
        
        # Add double-click event to show details
        self.events_tree.bind("<Double-1>", self.show_event_details)
        
        # Store events for detail view
        self.event_details = {}
    
    def show_event_details(self, event):
        """Show detailed information about an event"""
        selection = self.events_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        item = self.events_tree.item(item_id)
        values = item['values']
        
        # Get full event details
        event_detail = self.event_details.get(item_id, {})
        
        # Create detail window
        detail_window = tk.Toplevel(self.root)
        detail_window.title("Event Details")
        detail_window.geometry("700x500")
        
        text_widget = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD, font=("Courier New", 9))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Format details
        details = f"""
{'='*70}
EVENT DETAILS
{'='*70}

Time:        {values[0]}
Type:        {values[1]}
Size:        {values[2]}
Source:      {values[3]}
Destination: {values[4]}

Preview/Files:
{values[5]}

{'='*70}
FULL EVENT DATA
{'='*70}

"""
        
        # Add full event JSON
        if event_detail:
            import json
            details += json.dumps(event_detail, indent=2, ensure_ascii=False)
        else:
            details += "No additional details available"
        
        text_widget.insert(1.0, details)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        close_btn = tk.Button(detail_window, text="Close", command=detail_window.destroy)
        close_btn.pack(pady=5)
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if self.is_monitoring:
            self.on_stop_monitoring()
        else:
            self.on_start_monitoring()
    
    def set_monitoring_state(self, is_monitoring: bool):
        """Set monitoring state from external source"""
        self.is_monitoring = is_monitoring
        if is_monitoring:
            self.status_label.config(text="● Running", fg="green")
            self.start_btn.config(text="■ Stop Monitoring", bg="#e74c3c")
        else:
            self.status_label.config(text="● Stopped", fg="red")
            self.start_btn.config(text="▶ Start Monitoring", bg="#27ae60")
    
    def add_event(self, event):
        """Add event to the display - THREAD-SAFE"""
        try:
            self.event_count += 1
            self.event_count_label.config(text=f"Events Logged: {self.event_count}")
            
            # Format time
            time_str = event["timestamp"].split("T")[1].split(".")[0]
            
            # Format size
            if event["data_type"] == "files":
                size_str = f"{event['data_size']} MB"
            else:
                size_str = f"{event.get('data_size', 0)} chars"
            
            # Format preview/file names
            if event["data_type"] == "files" and "file_names" in event:
                file_names = event["file_names"]
                preview = ", ".join(file_names[:3])
                if len(file_names) > 3:
                    preview += f" ... (+{len(file_names) - 3} more)"
            else:
                preview = str(event.get("content_preview", ""))[:50]
            
            # Get destination
            destination = event.get("destination_window", "N/A")
            if event["event_type"] == "clipboard_copy" and event["data_type"] != "files":
                destination = "N/A"
            
            # Add to treeview
            item_id = self.events_tree.insert("", 0, values=(
                time_str,
                event["data_type"],
                size_str,
                event.get("source_application", "Unknown"),
                destination,
                preview
            ))
            
            # Store full event details
            self.event_details[item_id] = event
            
            # Keep only last 100 events
            children = self.events_tree.get_children()
            if len(children) > 100:
                old_item = children[-1]
                self.event_details.pop(old_item, None)
                self.events_tree.delete(old_item)
            
            # Force GUI update
            self.root.update_idletasks()
            
        except Exception as e:
            logger.error(f"Error adding event to GUI: {e}", exc_info=True)
    
    def clear_events(self):
        """Clear all events from display"""
        for item in self.events_tree.get_children():
            self.events_tree.delete(item)
        self.event_details.clear()
        self.event_count = 0
        self.event_count_label.config(text="Events Logged: 0")
    
    def export_logs(self):
        """Export logs to file"""
        from datetime import datetime
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile=f"clipboard_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        if file_path:
            try:
                self.on_export_logs(Path(file_path))
                messagebox.showinfo("Success", f"Logs exported successfully to:\n{file_path}")
            except Exception as e:
                logger.error(f"Export error: {e}")
                messagebox.showerror("Error", f"Failed to export logs:\n{str(e)}")
    
    def clear_all_logs(self):
        """Clear all logs"""
        if messagebox.askyesno("Confirm Clear", "Are you sure you want to delete all logs?\n\nThis action cannot be undone."):
            try:
                self.on_clear_logs()
                self.clear_events()
                messagebox.showinfo("Success", "All logs have been cleared.")
            except Exception as e:
                logger.error(f"Clear error: {e}")
                messagebox.showerror("Error", f"Failed to clear logs:\n{str(e)}")
    
    def show_settings(self):
        """Show settings dialog"""
        messagebox.showinfo(
            "Settings",
            "Settings dialog would open here.\n\nConfigure:\n• Log location\n• Encryption\n• Startup behavior\n• Retention period\n• Polling interval"
        )
    
    def show_error(self, title: str, message: str):
        """Show error dialog"""
        messagebox.showerror(title, message)
    
    def on_close(self):
        """Handle window close"""
        if self.is_monitoring:
            if messagebox.askokcancel("Minimize to Tray", "Monitoring is active.\n\nMinimize to system tray?"):
                self.root.withdraw()
        else:
            self.root.withdraw()
    
    def show(self):
        """Show the window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def hide(self):
        """Hide the window"""
        self.root.withdraw()
    
    def run(self):
        """Run the main loop"""
        self.root.mainloop()

from datetime import datetime