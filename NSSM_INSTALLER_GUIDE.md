# NSSM + Inno Setup Installer - Implementation Guide

## Overview
This guide provides the complete implementation for bundling the Enterprise Monitoring Agent as a Windows Service using NSSM (Non-Sucking Service Manager) and Inno Setup.

---

## STEP 1: Config Paths - COMPLETED ✓

### Changes Made:
1. **Created `src/enterprise/paths.py`**
   - Added `get_config_dir()` function that returns `C:\ProgramData\EnterpriseMonitoring\config`
   - Added `get_data_dir()` function that returns `C:\ProgramData\EnterpriseMonitoring\data`
   - Added `get_log_dir()` function that returns `C:\ProgramData\EnterpriseMonitoring\logs`
   - Added `get_user_config_dir()` function for backward compatibility

2. **Updated `src/enterprise/config.py`**
   - Modified `__init__` method to use `get_config_dir()` instead of `Path.home() / ".clipboard_monitor"`
   - Imported `get_config_dir` from `paths.py`

### Corrected `__init__` Method Code:
```python
def __init__(self):
    self.config_dir = get_config_dir()
    self.config_file = self.config_dir / "config.json"
    self.config: Dict[str, Any] = {}
    self.load()
```

This ensures the service running as SYSTEM can read configs from `C:\ProgramData\EnterpriseMonitoring\config`.

---

## STEP 2: Compile the EXE

### PyInstaller Command:
```bash
pyinstaller ^
  --name=EnterpriseAgent ^
  --onefile ^
  --noconsole ^
  --hidden-import=win32timezone ^
  --hidden-import=win32service ^
  --hidden-import=win32serviceutil ^
  --hidden-import=win32event ^
  --hidden-import=win32api ^
  --hidden-import=win32con ^
  --hidden-import=win32security ^
  --hidden-import=pywintypes ^
  --hidden-import=psutil ^
  --hidden-import=cryptography ^
  --hidden-import=cryptography.fernet ^
  --hidden-import=sqlite3 ^
  --hidden-import=pynput ^
  --hidden-import=pynput.keyboard ^
  --add-data="src/enterprise;enterprise" ^
  standalone_runner.py
```

### For Linux/Unix (use colon instead of semicolon):
```bash
pyinstaller \
  --name=EnterpriseAgent \
  --onefile \
  --noconsole \
  --hidden-import=win32timezone \
  --hidden-import=win32service \
  --hidden-import=win32serviceutil \
  --hidden-import=win32event \
  --hidden-import=win32api \
  --hidden-import=win32con \
  --hidden-import=win32security \
  --hidden-import=pywintypes \
  --hidden-import=psutil \
  --hidden-import=cryptography \
  --hidden-import=cryptography.fernet \
  --hidden-import=sqlite3 \
  --hidden-import=pynput \
  --hidden-import=pynput.keyboard \
  --add-data="src/enterprise:enterprise" \
  standalone_runner.py
```

### Output:
- Executable: `dist\EnterpriseAgent.exe`

### Requirements:
Before running PyInstaller, ensure you have all dependencies installed:
```bash
pip install pyinstaller pywin32 psutil cryptography pynput
```

---

## STEP 3: Inno Setup Script - COMPLETED ✓

### Created `setup_script.iss`

The Inno Setup script includes all required features:

#### ✓ 1. Admin Privilege Check
```pascal
function InitializeSetup(): Boolean;
begin
  Result := True;
  if not IsAdminLoggedOn() then
  begin
    MsgBox('This installer requires administrator privileges...', mbError, MB_OK);
    Result := False;
  end;
end;
```

#### ✓ 2. Installation Directory
- Installs to: `{commonpf}\Enterprise Monitoring Agent` (e.g., `C:\Program Files\Enterprise Monitoring Agent`)

#### ✓ 3. ProgramData Folders
Creates folders in `C:\ProgramData\EnterpriseMonitoring`:
- `logs` - Service logs
- `data` - Database and application data
- `config` - Configuration files

#### ✓ 4. NSSM Service Installation
```
nssm.exe install "EnterpriseMonitoringAgent" "{app}\EnterpriseAgent.exe"
```

#### ✓ 5. Service Log Configuration - stdout
```
nssm.exe set "EnterpriseMonitoringAgent" AppStdout "C:\ProgramData\EnterpriseMonitoring\logs\service.log"
```

#### ✓ 6. Service Log Configuration - stderr
```
nssm.exe set "EnterpriseMonitoringAgent" AppStderr "C:\ProgramData\EnterpriseMonitoring\logs\service_error.log"
```

#### ✓ 7. Service Startup
```
nssm.exe start "EnterpriseMonitoringAgent"
```

### Additional Features:
- **Auto-restart on failure**: Service automatically restarts if it crashes
- **Service description**: Sets display name and description
- **Clean uninstall**: Properly stops and removes service on uninstall
- **Data retention option**: Asks user if they want to keep data during uninstall

---

## STEP 4: Build and Installation Process

### 4.1 Download NSSM
1. Download NSSM from: https://nssm.cc/download
2. Extract `nssm.exe` (64-bit version) to `dist\` folder

### 4.2 Build Process
```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# 2. Compile the executable
pyinstaller --name=EnterpriseAgent --onefile --noconsole ^
  --hidden-import=win32timezone --hidden-import=win32service ^
  --hidden-import=win32serviceutil --hidden-import=win32event ^
  --add-data="src/enterprise;enterprise" standalone_runner.py

# 3. Copy NSSM to dist folder
copy path\to\nssm.exe dist\nssm.exe

# 4. Verify files exist
dir dist\EnterpriseAgent.exe
dir dist\nssm.exe

# 5. Compile Inno Setup installer
# Open Inno Setup Compiler and compile setup_script.iss
# Or use command line:
iscc setup_script.iss
```

### 4.3 Installation
1. Run the generated installer: `installer_output\EnterpriseMonitoringAgent_Setup_1.0.0.exe`
2. Follow the installation wizard
3. The service will be automatically installed and started

### 4.4 Verify Installation
```bash
# Check service status
nssm status EnterpriseMonitoringAgent

# Check service logs
type C:\ProgramData\EnterpriseMonitoring\logs\service.log
type C:\ProgramData\EnterpriseMonitoring\logs\service_error.log

# View service in Windows Services
services.msc
```

---

## File Structure

```
Clipping-Monitor/
├── standalone_runner.py          # NSSM service entry point (NEW)
├── setup_script.iss              # Inno Setup installer script (NEW)
├── src/
│   └── enterprise/
│       ├── paths.py              # Path utilities (NEW)
│       ├── config.py             # Updated to use get_config_dir()
│       ├── service_core.py       # Existing monitoring service
│       └── ...                   # Other enterprise modules
├── dist/                         # Build output (after PyInstaller)
│   ├── EnterpriseAgent.exe       # Compiled service executable
│   └── nssm.exe                  # NSSM service manager
└── installer_output/             # Installer output (after Inno Setup)
    └── EnterpriseMonitoringAgent_Setup_1.0.0.exe
```

---

## Service Management Commands

### Using NSSM directly:
```bash
# Start service
nssm start EnterpriseMonitoringAgent

# Stop service
nssm stop EnterpriseMonitoringAgent

# Restart service
nssm restart EnterpriseMonitoringAgent

# Check status
nssm status EnterpriseMonitoringAgent

# Remove service
nssm remove EnterpriseMonitoringAgent confirm
```

### Using Windows Services:
```bash
# Start service
net start EnterpriseMonitoringAgent

# Stop service
net stop EnterpriseMonitoringAgent

# Check status
sc query EnterpriseMonitoringAgent
```

---

## Troubleshooting

### Service won't start:
1. Check logs: `C:\ProgramData\EnterpriseMonitoring\logs\service_error.log`
2. Verify executable exists: `C:\Program Files\Enterprise Monitoring Agent\EnterpriseAgent.exe`
3. Check permissions on ProgramData folder
4. Run manually to test: `"C:\Program Files\Enterprise Monitoring Agent\EnterpriseAgent.exe"`

### Configuration issues:
1. Check config file: `C:\ProgramData\EnterpriseMonitoring\config\config.json`
2. Verify folder permissions
3. Check logs for config loading errors

### Build issues:
1. Ensure all dependencies are installed
2. Check PyInstaller version compatibility
3. Verify Python version (recommend Python 3.9+)
4. Check for missing hidden imports

---

## Security Considerations

1. **Service runs as SYSTEM**: The service has elevated privileges
2. **Data encryption**: Config should enable encryption for sensitive data
3. **Log rotation**: Implement log rotation to prevent disk space issues
4. **Access control**: ProgramData folder has appropriate permissions
5. **Update mechanism**: Consider implementing secure update mechanism

---

## Next Steps

1. **Test the PyInstaller build** on a clean Windows machine
2. **Test the installer** on a clean Windows machine
3. **Verify service starts automatically** after reboot
4. **Test uninstaller** to ensure clean removal
5. **Add digital signature** to executable and installer (recommended)
6. **Create user documentation** for end users
7. **Implement update mechanism** for future versions

---

## Notes

- The `standalone_runner.py` is designed specifically for NSSM and does NOT use `win32serviceutil`
- All configuration and data is stored in `C:\ProgramData\EnterpriseMonitoring` for service compatibility
- The service automatically creates all required directories on first run
- Logs are written to both file and console (captured by NSSM)
- The Inno Setup script handles all service installation and configuration automatically
