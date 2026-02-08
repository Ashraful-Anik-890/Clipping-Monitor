import os
import json
from pathlib import Path
from typing import Dict, Any
import logging

# Import centralized path management
try:
    from enterprise.paths import get_database_path, get_user_config_dir
except ImportError:
    # Fallback for development
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    from paths import get_database_path, get_user_config_dir

logger = logging.getLogger(__name__)


class Config:
    """Application configuration manager with centralized path support"""
    
    DEFAULT_CONFIG = {
        "version": "1.0.0",
        "monitoring": {
            "clipboard": True,
            "applications": True,
            "browser": True,
            "screen_recording": False,
            "keystrokes": False  # Disabled by default for privacy
        },
        "storage": {
            "database_path": None,  # Will be set dynamically from paths.py
            "encryption_enabled": True,
            "retention_days": 90,
            "max_database_size_mb": 1000
        },
        "performance": {
            "polling_interval_ms": 1000,
            "max_cpu_usage_percent": 10,
            "max_memory_mb": 200
        },
        "keystrokes": {
            "enabled": False,  # Must be explicitly enabled
            "encryption_enabled": True,
            "buffer_flush_interval": 60,
            "retention_days": 30,
            "export_requires_auth": True,
            "max_buffer_size": 1000
        },
        "screen_recording": {
            "enabled": False,
            "fps": 10,
            "quality": "medium",  # low, medium, high
            "video_chunk_minutes": 10,
            "video_retention_days": 30,
            "resolution_scale": 0.5
        },
        "application": {
            "run_on_startup": False,
            "start_minimized": False,
            "log_level": "INFO"
        }
    }
    
    def __init__(self):
        try:
            self.config_dir = get_user_config_dir()
        except Exception as e:
            logger.warning(f"Could not get user config dir: {e}")
            self.config_dir = Path.home() / ".clipboard_monitor"
            self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from file or create default"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
                    # Merge with defaults for any missing keys (deep merge)
                    self.config = self._deep_merge(self.DEFAULT_CONFIG, self.config)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                self.config = self.DEFAULT_CONFIG.copy()
        else:
            self.config = self.DEFAULT_CONFIG.copy()
        
        # Set dynamic paths
        self._set_dynamic_paths()
        self.save()
    
    def _deep_merge(self, default: Dict, override: Dict) -> Dict:
        """
        Deep merge two dictionaries.
        
        Args:
            default: Default configuration
            override: Override configuration
            
        Returns:
            Merged configuration
        """
        result = default.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _set_dynamic_paths(self):
        """Set paths dynamically using centralized path management"""
        try:
            if self.config['storage']['database_path'] is None:
                self.config['storage']['database_path'] = str(get_database_path())
        except Exception as e:
            logger.error(f"Error setting dynamic paths: {e}")
    
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
        try:
            from enterprise.paths import get_logs_dir
            return get_logs_dir()
        except ImportError:
            # Fallback
            log_dir = Path.home() / ".clipboard_monitor" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            return log_dir
    
    def is_monitor_enabled(self, monitor_name: str) -> bool:
        """
        Check if a specific monitor is enabled.
        
        Args:
            monitor_name: Name of monitor (clipboard, applications, browser, keystrokes, screen_recording)
            
        Returns:
            True if enabled
        """
        return self.config.get('monitoring', {}).get(monitor_name, False)
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if valid
        """
        try:
            # Check required keys exist
            required_keys = ['version', 'monitoring', 'storage', 'performance']
            for key in required_keys:
                if key not in self.config:
                    logger.error(f"Missing required config key: {key}")
                    return False
            
            # Validate monitoring section
            if not isinstance(self.config['monitoring'], dict):
                logger.error("monitoring section must be a dictionary")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Config validation error: {e}")
            return False