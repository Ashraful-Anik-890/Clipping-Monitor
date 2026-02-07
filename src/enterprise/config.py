import os
import json
from pathlib import Path
from typing import Dict, Any

class Config:
    """Application configuration manager"""
    
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "monitoring": {
            "clipboard": True,
            "applications": True,
            "browser": True,
            "screen_recording": False
        },
        "storage": {
            "database_path": "C:/ProgramData/EnterpriseMonitoring/data/monitoring.db",
            "encryption_enabled": True,
            "retention_days": 90,
            "max_database_size_mb": 1000
        },
        "performance": {
            "polling_interval_ms": 1000,
            "max_cpu_usage_percent": 10,
            "max_memory_mb": 200
        },
        "monitoring": {
        "clipboard": True,
        "applications": True,
        "browser": True,
        "screen_recording": False,
        "keystrokes": False  # ADD THIS - disabled by default for privacy
        },
        "keystrokes": {
            "enabled": True,
            "encryption_enabled": True,
            "buffer_flush_interval": 60,
            "retention_days": 30,
            "export_requires_auth": True,
            "enable_encryption": True,
            "run_on_startup": False,
            "start_minimized": False,
            "log_retention_days": 30,
            "polling_interval_ms": 500,
            "enable_screen_recording": True,
            "screen_recording_fps": 10,
            "screen_recording_quality": "medium",  # low, medium, high
            "video_chunk_minutes": 10,
            "video_retention_days": 30,
            "resolution_scale": 0.5,
        }
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