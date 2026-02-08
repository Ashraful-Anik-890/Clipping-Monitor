"""
Path utilities for Enterprise Monitoring Agent
Provides centralized path management for service configuration and data
"""

import os
from pathlib import Path


def get_config_dir() -> Path:
    r"""
    Get the configuration directory for the Enterprise Monitoring Agent.
    Uses C:\ProgramData for Windows service compatibility.
    
    This allows the service running as SYSTEM to access configuration files.
    
    Returns:
        Path: Configuration directory path (C:\ProgramData\EnterpriseMonitoring\config)
    """
    if os.name == 'nt':  # Windows
        config_dir = Path('C:/ProgramData/EnterpriseMonitoring/config')
    else:  # Linux/Unix fallback
        config_dir = Path('/etc/enterprise-monitoring')
    
    # Ensure directory exists
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_user_config_dir() -> Path:
    """
    Get the user-specific configuration directory.
    Used for non-service applications.
    
    Returns:
        Path: User configuration directory path
    """
    return Path.home() / ".clipboard_monitor"


def get_data_dir() -> Path:
    r"""
    Get the data directory for the Enterprise Monitoring Agent.
    
    Returns:
        Path: Data directory path (C:\ProgramData\EnterpriseMonitoring\data)
    """
    if os.name == 'nt':  # Windows
        data_dir = Path('C:/ProgramData/EnterpriseMonitoring/data')
    else:  # Linux/Unix fallback
        data_dir = Path('/var/lib/enterprise-monitoring')
    
    # Ensure directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_dir() -> Path:
    r"""
    Get the log directory for the Enterprise Monitoring Agent.
    
    Returns:
        Path: Log directory path (C:\ProgramData\EnterpriseMonitoring\logs)
    """
    if os.name == 'nt':  # Windows
        log_dir = Path('C:/ProgramData/EnterpriseMonitoring/logs')
    else:  # Linux/Unix fallback
        log_dir = Path('/var/log/enterprise-monitoring')
    
    # Ensure directory exists
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
