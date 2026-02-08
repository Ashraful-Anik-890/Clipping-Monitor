# Changelog

All notable changes to the Enterprise Monitoring Agent project.

## [Unreleased] - 2024-02-08

### 🎉 Major Architectural Overhaul

This release represents a complete refactoring of the application to address critical stability, path management, and architectural issues that prevented the application from reaching production readiness.

### ✅ Fixed - Critical Issues

#### Blocking Issues (Prevented Execution)
- **Fixed:** Missing `keystroke_recorder.py` module that was referenced but didn't exist
  - Created complete implementation with encryption, buffering, and thread-safety
  - Added AES encryption support (Fernet)
  - Implemented per-application keystroke tracking
  - Added configurable buffer flushing and retention policies
  - Implemented `is_monitoring()` health check interface

- **Fixed:** Import path errors throughout the codebase
  - Created centralized `paths.py` module for consistent path resolution
  - Added PyInstaller compatibility checks (`is_frozen()`)
  - Removed all hardcoded path handling

- **Fixed:** Hardcoded absolute paths (`C:/ProgramData/...`)
  - Now uses environment variables (`%PROGRAMDATA%`, `%LOCALAPPDATA%`, `%APPDATA%`)
  - All paths dynamically resolved at runtime
  - Works correctly in both development and packaged modes

- **Fixed:** No graceful handling for missing Windows APIs
  - Added fallback handling for pywin32 import errors
  - Service continues with available monitors if some fail
  - Better error messages for debugging

#### Configuration Issues
- **Fixed:** Duplicate "monitoring" key in `config.py` (lines 11 & 28)
  - Consolidated into single configuration section
  - Added deep merge for configuration updates
  - Added `validate()` method for config verification
  - Added `is_monitor_enabled()` helper method

#### Service Architecture
- **Fixed:** Wrong PyInstaller entry point
  - Changed from `service_core.py` to `service_main.py`
  - Updated build_deployment.py spec generation
  - Added all necessary hidden imports

- **Fixed:** Tight coupling in MonitoringEngine
  - Monitors now loaded based on configuration
  - Added dependency injection (config parameter)
  - Implemented graceful degradation per monitor
  - Monitors tracked as `(name, instance)` tuples for better error reporting

- **Fixed:** SC command syntax error in `configure_service_recovery()`
  - Corrected Windows SC command syntax for service failure recovery
  - Added stderr output for debugging failures

#### Health Monitoring
- **Fixed:** Missing `is_monitoring()` interface on monitors
  - Implemented in all monitor classes including KeystrokeRecorder
  - Health check thread now properly restarts failed monitors
  - Better error handling in health check loop

### 🏗️ Added - New Infrastructure

#### Path Management System
- **Added:** `src/enterprise/paths.py` - Centralized path management
  - `get_application_path()` - Application root directory
  - `get_resource_path()` - Resource file resolution
  - `get_program_data_dir()` - ProgramData directory
  - `get_logs_dir()` - Logs directory
  - `get_data_dir()` - Data storage directory
  - `get_config_dir()` - Configuration directory
  - `get_user_config_dir()` - User-specific config
  - `get_keystroke_storage_dir()` - Keystroke logs directory
  - `get_database_path()` - Main database file path
  - `initialize_all_directories()` - Startup directory creation
  - All functions include proper error handling and logging

#### Build & Development
- **Added:** `.gitignore` - Comprehensive Python project gitignore
  - Python cache files
  - Virtual environments
  - Build artifacts
  - IDE files
  - Log files and databases
  - OS-specific files

- **Added:** `requirements-dev.txt` - Separated development dependencies
  - PyInstaller for building
  - pytest for testing
  - Code quality tools (black, flake8, pylint, mypy)
  - Documentation tools (sphinx)

- **Updated:** `requirements.txt` - Clean runtime dependencies
  - Version pinning for stability
  - Platform-specific dependencies (pywin32 only on Windows)
  - Removed development tools

#### Verification & Documentation
- **Added:** `verify_installation.py` - Installation verification script
  - Checks Python version compatibility
  - Verifies platform (Windows)
  - Tests all dependencies
  - Validates directory structure
  - Tests module imports
  - Checks configuration validity
  - Verifies admin privileges
  - Checks service prerequisites
  - Provides colored output and actionable error messages

- **Updated:** README.md - Comprehensive documentation rewrite
  - Added installation instructions
  - Added configuration guide
  - Added troubleshooting section
  - Added quick start checklist
  - Documented recent fixes
  - Added security considerations
  - Added legal/ethical notice

### 🔄 Changed - Architecture Improvements

#### Service Core (`service_core.py`)
- **Changed:** MonitoringEngine initialization
  - Now accepts optional `config` parameter
  - Loads Config automatically if not provided
  - Monitors conditionally initialized based on config
  - Uses centralized paths from `paths.py`

- **Changed:** Monitor startup behavior
  - Graceful degradation - service continues if individual monitors fail
  - Better error reporting with monitor names
  - Success/failure count logging

- **Changed:** Health check implementation
  - Monitors tracked as tuples: `(name, instance)`
  - Better error handling in health check loop
  - Monitors restarted individually on failure

#### Database Manager (`database_manager.py`)
- **Changed:** Encryption key file handling
  - Better error handling for win32api unavailability
  - Graceful fallback if key file can't be hidden
  - Improved logging

#### Configuration (`config.py`)
- **Changed:** Path resolution
  - Uses `paths.py` for dynamic path resolution
  - Database path set dynamically from `get_database_path()`
  - Added `_set_dynamic_paths()` method

- **Changed:** Configuration loading
  - Implemented deep merge for configuration updates
  - Better handling of missing configuration keys
  - Added validation on load

#### Build System (`build_deployment.py`)
- **Changed:** PyInstaller spec generation
  - Corrected service entry point to `service_main.py`
  - Added enterprise module hidden imports:
    - `enterprise.paths`
    - `enterprise.config`
    - `enterprise.keystroke_recorder`
  - Added pynput submodules:
    - `pynput._util.win32`
  - Added cryptography submodules:
    - `cryptography.hazmat.backends`
  - Added win32com modules for admin console

### 🛡️ Security Improvements

- **Enhanced:** Encryption key management
  - Key files use restricted permissions
  - Key files hidden on Windows (FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM)
  - Graceful handling if hiding fails

- **Enhanced:** Error messages
  - No sensitive data exposed in logs
  - Better debugging information without security risks

### 🎯 Configuration Changes

Default configuration now includes:
```json
{
  "monitoring": {
    "keystrokes": false  // Disabled by default for privacy
  },
  "keystrokes": {
    "enabled": false,
    "encryption_enabled": true,
    "buffer_flush_interval": 60,
    "max_buffer_size": 1000
  }
}
```

### 📋 Migration Guide

For users upgrading from previous versions:

1. **Backup your data:**
   ```
   C:\ProgramData\EnterpriseMonitoring\data\
   %USERPROFILE%\.clipboard_monitor\
   ```

2. **Stop the service:**
   - Use Admin Console or: `net stop EnterpriseMonitoringAgent`

3. **Update the application:**
   ```bash
   git pull
   pip install -r requirements.txt
   ```

4. **Verify installation:**
   ```bash
   python verify_installation.py
   ```

5. **Restart the service:**
   - Use Admin Console or: `net start EnterpriseMonitoringAgent`

### 🐛 Known Issues

None currently blocking production deployment. All critical issues resolved.

### 🔜 Planned for Next Release

- [ ] Automated installation script
- [ ] Windows installer (MSI/NSIS)
- [ ] Comprehensive unit test suite
- [ ] Integration tests
- [ ] Performance benchmarks
- [ ] Documentation improvements

---

## [0.1.0] - Initial Release

- Basic clipboard monitoring
- Application usage tracking
- Browser activity tracking
- Admin console UI
- Windows service implementation

---

**Legend:**
- ✅ Fixed - Bug fixes
- 🏗️ Added - New features
- 🔄 Changed - Changes in existing functionality
- 🛡️ Security - Security improvements
- 📋 Migration - Migration notes
