import os
import json
from pathlib import Path
from typing import Dict, Any

class Config:
    """Application configuration manager"""
    
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "log_location": str(Path.home() / "Documents" / "ClipboardMonitor" / "logs"),
        "max_log_size_mb": 50,
        "enable_encryption": True,
        "run_on_startup": False,
        "start_minimized": False,
        "log_retention_days": 30,
        "polling_interval_ms": 500
    }
    
    def __init__(self):
        self.config_dir = Path.home() / ".clipboard_monitor"
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from file or create default"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
                # Merge with defaults for any missing keys
                for key, value in self.DEFAULT_CONFIG.items():
                    if key not in self.config:
                        self.config[key] = value
        else:
            self.config = self.DEFAULT_CONFIG.copy()
            self.save()
    
    def save(self):
        """Save configuration to file"""
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def get(self, key: str, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save()
    
    def get_log_dir(self) -> Path:
        """Get log directory path"""
        log_dir = Path(self.config["log_location"])
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir