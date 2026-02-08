# Enterprise Clipping Monitor

A secure, enterprise-grade user activity monitoring agent for Windows. This application monitors clipboard usage, application activity, browser history, and keystrokes for compliance and productivity tracking.

## 🚀 Features

### Core Monitoring
- **Clipboard Monitoring**: Tracks copy/paste operations (text and images).
- **Application Usage**: Logs active window titles and duration.
- **Browser Activity**: Monitors visited websites (Chrome, Edge, Firefox).
- **Keystroke Logging**: Securely records keystrokes (Admin access only, disabled by default).

### Security & Privacy
- **Encryption**: All sensitive data is encrypted using Fernet (AES).
- **Admin Authentication**: Secure login system with PBKDF2 password hashing.
- **UAC Elevation**: Requires administrator privileges for service management.
- **Service Protection**: Runs as a Windows Service (SYSTEM privileges).
- **Centralized Path Management**: Environment-aware paths using %PROGRAMDATA%.

### Administrator Console
- **Service Control**: Install, Start, Stop, and Remove the monitoring service.
- **Statistics**: Real-time stats on recording status and storage usage.
- **Export Data**: Export logs to JSON or CSV (Encrypted/Decrypted).
- **Data Security**: Secure "First-Run" password setup system.

### Architecture Improvements
- **Modular Design**: Each monitor can be enabled/disabled independently via configuration.
- **Graceful Degradation**: Service continues running even if individual monitors fail.
- **Centralized Configuration**: Single source of truth for all settings.
- **Health Monitoring**: Automatic restart of failed monitors.

---

## 📋 Requirements

- **OS**: Windows 10/11 (64-bit recommended)
- **Python**: 3.8 or higher
- **Administrator Privileges**: Required for service installation

---

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Ashraful-Anik-890/Clipping-Monitor.git
cd Clipping-Monitor
```

### 2. Install Dependencies
```bash
# Install runtime dependencies
pip install -r requirements.txt

# For development/building (optional)
pip install -r requirements-dev.txt
```

### 3. Verify Installation
```bash
# Run the verification script to check everything is set up correctly
python verify_installation.py
```

This will check:
- Python version compatibility
- Required dependencies
- Directory structure
- Module imports
- Configuration validity
- Administrator privileges

---

## 🛠️ Usage

### 1. First-Time Setup

#### Option A: Run from Source (Development)
```bash
# Run the Admin Console
python src/enterprise/admin_console.py
```

#### Option B: Build Executable (Production)
```bash
# Build the executables
python build_deployment.py --all

# Executables will be in: dist/EnterpriseMonitoringAgent/
```

### 2. Admin Console Setup
1. **First Run**: You will be prompted to create an Administrator Password.
2. **Login**: Use your newly created password to access the console.
3. **Configure**: Review and adjust settings in the configuration file if needed.

### 3. Setting up the Service

⚠️ **IMPORTANT:** Always use `src/enterprise/service_main.py` for service operations!

1. Go to the **Service Control** tab in Admin Console.
2. Click **"Install Service"** (Blue Button).
   - *Service will be installed with auto-start configuration*
   - *Uses correct entry point (`service_main.py`)*
3. Click **"Start Service"** (Green Button).
   - *Status should change to "Running"*

**Alternative: Command Line Installation**
```powershell
# Run PowerShell as Administrator
python src\enterprise\service_main.py install
net start EnterpriseMonitoringAgent
```

**Verify Service is Running:**
```powershell
sc query EnterpriseMonitoringAgent
# Should show: STATE: 4 RUNNING
```

### 4. Monitoring & Exporting
- The service runs in the background continuously.
- Use the **Admin Console** to:
  - View statistics
  - Export collected data
  - Control the service
- **Warning**: Decrypted exports contain sensitive plain-text data.

---

## ⚙️ Configuration

Configuration file location: `%USERPROFILE%\.clipboard_monitor\config.json`

### Key Settings

```json
{
  "monitoring": {
    "clipboard": true,
    "applications": true,
    "browser": true,
    "keystrokes": false,
    "screen_recording": false
  },
  "keystrokes": {
    "enabled": false,
    "encryption_enabled": true,
    "buffer_flush_interval": 60,
    "retention_days": 30
  },
  "storage": {
    "encryption_enabled": true,
    "retention_days": 90
  }
}
```

### Enabling/Disabling Monitors

Edit the config file to enable or disable specific monitors:
- Set `"keystrokes": true` to enable keystroke logging
- Set `"screen_recording": true` to enable screen recording
- Restart the service for changes to take effect

---

## 📂 Project Structure

```
Clipping-Monitor/
├── src/
│   ├── enterprise/
│   │   ├── admin_console.py        # Admin GUI
│   │   ├── service_main.py         # Service entry point
│   │   ├── service_core.py         # Core monitoring logic
│   │   ├── admin_auth.py           # Authentication handler
│   │   ├── config.py               # Configuration manager
│   │   ├── paths.py                # Centralized path management
│   │   ├── keystroke_recorder.py   # Keystroke logging
│   │   ├── database_manager.py     # Database operations
│   │   ├── app_usage_tracker.py    # Application monitoring
│   │   └── browser_tracker.py      # Browser monitoring
│   ├── clipboard_monitor.py        # Clipboard monitoring
│   ├── screen_recorder.py          # Screen recording
│   └── ...
├── build_deployment.py             # Build script
├── verify_installation.py          # Installation verification
├── requirements.txt                # Runtime dependencies
├── requirements-dev.txt            # Development dependencies
└── README.md
```

---

## 🔒 Security Considerations

1. **Encryption**: All sensitive data is encrypted at rest using AES (Fernet).
2. **Admin Only**: Service requires SYSTEM privileges; console requires administrator.
3. **Local Storage**: Currently stores all data locally (no network transmission).
4. **Keystroke Logging**: Disabled by default; requires explicit configuration.
5. **Key Management**: Encryption keys stored with restricted file permissions.

---

## 🐛 Troubleshooting

### Service Installs but Immediately Crashes (FIXED)

**Problem**: Service appears to "start" successfully but Error 1062 occurs when trying to stop.

**Recent Fix (2024-02-08)**: 
✅ **RESOLVED** - Fixed incorrect import paths that caused immediate service crash.
✅ Service now starts successfully and runs continuously.

**If still experiencing issues**:

1. **Test imports first**:
   ```bash
   python test_service_imports.py
   ```
   This verifies all module imports work correctly.

2. **Check service logs**:
   ```bash
   type C:\ProgramData\EnterpriseMonitoring\logs\service.log
   ```
   Look for errors during initialization.

3. **Reinstall service** (run as Administrator):
   ```bash
   # Remove old service
   python src\enterprise\service_main.py remove
   
   # Install fresh
   python src\enterprise\service_main.py install
   
   # Start service
   net start EnterpriseMonitoringAgent
   ```

4. **Verify service is actually running**:
   ```bash
   sc query EnterpriseMonitoringAgent
   ```
   Should show: `STATE: 4 RUNNING`

### Service Won't Start

**Problem**: Service fails to start or crashes immediately.

**Solutions**:
1. Run verification script: `python verify_installation.py`
2. Run import test: `python test_service_imports.py`
3. Check service logs: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
4. Ensure all dependencies installed: `pip install -r requirements.txt`
5. Verify admin privileges
6. Check Windows Event Viewer for service errors

### Import Errors

**Problem**: `ModuleNotFoundError` or `ImportError`

**Solutions**:
1. Run import test: `python test_service_imports.py` - will identify which imports fail
2. Ensure running correct Python version: `python --version` (must be 3.8+)
3. Install dependencies: `pip install -r requirements.txt`
4. On Windows, ensure pywin32 installed: `pip install pywin32`
5. Run post-install for pywin32: `python -m win32com.client.Makefile -i`

### Path-Related Errors

**Problem**: "Path not found" or directory errors

**Solutions**:
1. All paths now use environment variables automatically
2. Check ProgramData directory exists: `C:\ProgramData\EnterpriseMonitoring\`
3. Ensure write permissions to ProgramData
4. Run Admin Console as Administrator

### Configuration Issues

**Problem**: Service starts but monitors don't work

**Solutions**:
1. Check config file: `%USERPROFILE%\.clipboard_monitor\config.json`
2. Verify monitors are enabled in config
3. Check individual monitor logs
4. Ensure no conflicting software (e.g., other clipboard managers)

### Complete Troubleshooting Guide

For comprehensive troubleshooting including:
- Detailed error code explanations (1060, 1062, 5, 1053)
- Debug mode instructions  
- Clean reinstall procedures
- Log analysis tips

See **`TROUBLESHOOTING.md`** in the repository root.

---

## 💻 Development Status

- **OS**: Windows Only
- **Language**: Python 3.8+
- **Architecture**: Service-based with modular monitors
- **Status**: Beta - Stable core functionality
- **Recent Fixes** (2024-02-08):
  - ✅ **CRITICAL FIX #1**: Corrected import paths causing immediate service crash
  - ✅ **CRITICAL FIX #2**: Fixed Error 1063 by removing duplicate entry point from service_core.py
  - ✅ **CRITICAL FIX #3**: Service now uses correct entry point (service_main.py)
  - ✅ Service now starts and runs continuously without errors
  - ✅ Fixed hardcoded paths in admin console
  - ✅ Added service import test script (`test_service_imports.py`)
  - ✅ Added comprehensive troubleshooting guide (`TROUBLESHOOTING.md`)
  - ✅ Added service operations guide (`SERVICE_GUIDE.md`)
  - ✅ Fixed all path-related issues
  - ✅ Added centralized path management
  - ✅ Implemented graceful monitor degradation
  - ✅ Fixed service entry point
  - ✅ Added missing keystroke recorder module
  - ✅ Fixed configuration duplicates
  - ✅ Improved error handling

---

## 📝 Known Limitations

1. **Windows Only**: Uses Windows-specific APIs (pywin32)
2. **Python Performance**: Slightly higher resource usage than native code
3. **Executable Size**: PyInstaller executables are 50-100MB
4. **Browser URL Extraction**: Best-effort from history (may not capture all URLs)
5. **Screen Recording**: Currently disabled by default (high resource usage)

---

## 🚧 Planned Features

- [ ] Cloud sync for collected data
- [ ] Real-time dashboard with web interface
- [ ] Advanced analytics and reporting
- [ ] Multi-user support with role-based access
- [ ] Compliance report generation
- [ ] Email/Slack notifications

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## ⚠️ Legal & Ethical Notice

**IMPORTANT**: This software is designed for legitimate monitoring purposes in enterprise/corporate environments where:
1. Employees are informed about monitoring
2. Proper legal consent is obtained
3. Local laws and regulations are followed
4. Company policies permit such monitoring

**DO NOT USE** for unauthorized surveillance, illegal monitoring, or privacy invasion. Users are solely responsible for ensuring compliance with applicable laws and regulations.

---

## 🤝 Contributing

Contributions are welcome! Please ensure:
1. Code follows existing architecture patterns
2. All tests pass
3. Documentation is updated
4. Security best practices are maintained

---

## 📞 Support

For issues, questions, or contributions:
- **GitHub Issues**: [Report a bug or request a feature](https://github.com/Ashraful-Anik-890/Clipping-Monitor/issues)
- **Documentation**: See `/docs` folder for detailed guides

---

## 🎯 Quick Start Checklist

- [ ] Python 3.8+ installed
- [ ] Run as Administrator
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Verify installation: `python verify_installation.py`
- [ ] Run Admin Console: `python src/enterprise/admin_console.py`
- [ ] Create admin password
- [ ] Install service
- [ ] Start service
- [ ] Verify service status in Admin Console
