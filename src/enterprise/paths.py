"""
Centralized Path Management Module

Provides consistent, environment-aware path resolution for all application components.
Handles both development and PyInstaller-packaged execution modes.
"""

import os
import sys
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def is_frozen() -> bool:
    """
    Check if running as PyInstaller executable.
    
    Returns:
        True if frozen/packaged, False if running as script
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_application_path() -> Path:
    """
    Get the application root directory.
    
    Returns:
        Path to application root (executable dir if frozen, project root if script)
    """
    if is_frozen():
        # Running as compiled executable
        return Path(sys.executable).parent
    else:
        # Running as script - go up from src/enterprise/ to project root
        return Path(__file__).parent.parent.parent


def get_resource_path(relative_path: str) -> Path:
    """
    Get path to a resource file (works both in dev and frozen mode).
    
    Args:
        relative_path: Relative path to resource from project root
        
    Returns:
        Absolute path to resource
    """
    if is_frozen():
        # PyInstaller extracts files to sys._MEIPASS
        base_path = Path(sys._MEIPASS)
    else:
        base_path = get_application_path()
    
    return base_path / relative_path


def get_program_data_dir() -> Path:
    """
    Get the ProgramData directory for application data (Windows).
    
    Uses environment variable if available, falls back to standard location.
    Creates directory if it doesn't exist.
    
    Returns:
        Path to ProgramData/EnterpriseMonitoring
    """
    # Use environment variable if available
    program_data = os.environ.get('PROGRAMDATA', 'C:/ProgramData')
    
    app_data_dir = Path(program_data) / 'EnterpriseMonitoring'
    
    # Ensure directory exists
    try:
        app_data_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Could not create ProgramData directory: {e}")
    
    return app_data_dir


def get_logs_dir() -> Path:
    """
    Get the logs directory.
    
    Returns:
        Path to logs directory (creates if needed)
    """
    log_dir = get_program_data_dir() / 'logs'
    
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Could not create logs directory: {e}")
    
    return log_dir


def get_data_dir() -> Path:
    """
    Get the data directory for databases and collected data.
    
    Returns:
        Path to data directory (creates if needed)
    """
    data_dir = get_program_data_dir() / 'data'
    
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Could not create data directory: {e}")
    
    return data_dir


def get_config_dir() -> Path:
    """
    Get the configuration directory.
    
    Returns:
        Path to config directory (creates if needed)
    """
    config_dir = get_program_data_dir() / 'config'
    
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Could not create config directory: {e}")
    
    return config_dir


def get_user_config_dir() -> Path:
    """
    Get user-specific configuration directory (in user profile).
    
    Returns:
        Path to ~/.clipboard_monitor (creates if needed)
    """
    user_config = Path.home() / '.clipboard_monitor'
    
    try:
        user_config.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Could not create user config directory: {e}")
    
    return user_config


def get_keystroke_storage_dir() -> Path:
    """
    Get keystroke logs storage directory.
    
    Returns:
        Path to keystroke storage (creates if needed)
    """
    keystroke_dir = get_data_dir() / 'keystrokes'
    
    try:
        keystroke_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.error(f"Could not create keystroke storage directory: {e}")
    
    return keystroke_dir


def get_database_path() -> Path:
    """
    Get the main database file path.
    
    Returns:
        Path to monitoring.db
    """
    return get_data_dir() / 'monitoring.db'


def initialize_all_directories():
    """
    Initialize all required directories.
    Should be called on application startup.
    """
    directories = [
        get_program_data_dir(),
        get_logs_dir(),
        get_data_dir(),
        get_config_dir(),
        get_user_config_dir(),
        get_keystroke_storage_dir(),
    ]
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Initialized directory: {directory}")
        except Exception as e:
            logger.error(f"Failed to initialize directory {directory}: {e}")


# Module-level initialization for when imported
try:
    # Ensure critical directories exist when module is loaded
    get_program_data_dir()
except Exception as e:
    logger.warning(f"Could not initialize directories on module load: {e}")


if __name__ == "__main__":
    # Test path resolution
    print("Path Resolution Test")
    print("=" * 60)
    print(f"Is Frozen: {is_frozen()}")
    print(f"Application Path: {get_application_path()}")
    print(f"ProgramData Dir: {get_program_data_dir()}")
    print(f"Logs Dir: {get_logs_dir()}")
    print(f"Data Dir: {get_data_dir()}")
    print(f"Config Dir: {get_config_dir()}")
    print(f"User Config Dir: {get_user_config_dir()}")
    print(f"Keystroke Storage Dir: {get_keystroke_storage_dir()}")
    print(f"Database Path: {get_database_path()}")
    print("=" * 60)
    
    # Initialize all directories
    print("\nInitializing all directories...")
    initialize_all_directories()
    print("Done!")
