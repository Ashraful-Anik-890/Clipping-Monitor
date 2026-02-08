# Production Deployment Guide
## Enterprise Monitoring Agent - NSSM + Inno Setup

This guide explains how to build and deploy the Enterprise Monitoring Agent as a professional Windows service using NSSM and Inno Setup, similar to commercial applications like Grammarly.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│  USER INSTALLS SETUP.EXE                                     │
│  ↓                                                           │
│  INNO SETUP INSTALLER                                        │
│  ├─ Extracts EnterpriseAgent.exe to Program Files           │
│  ├─ Extracts nssm.exe                                        │
│  ├─ Creates ProgramData directories with permissions        │
│  ├─ Uses NSSM to install Windows service                    │
│  ├─ Configures service (auto-start, restart, logs)          │
│  └─ Starts the service                                       │
│  ↓                                                           │
│  SERVICE RUNNING AS SYSTEM                                   │
│  ├─ Runs EnterpriseAgent.exe (standalone_runner.py)         │
│  ├─ Uses C:\ProgramData\EnterpriseMonitoring (not user)     │
│  ├─ Logs to service.log                                      │
│  ├─ Auto-restarts on failure                                 │
│  └─ Survives user logout/reboot                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Development Machine Requirements

1. **Python 3.8+** with packages:
   ```bash
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Inno Setup 6.x** (Download from https://jrsoftware.org/isdl.php)
   - Use the Unicode version
   - Install to default location

3. **NSSM 2.24+** (Download from https://nssm.cc/download)
   - Download the 64-bit version: `nssm-2.24-101-g897c7ad.zip`
   - Extract `nssm.exe` from `win64` folder
   - Place in `installer/` directory

### Target System Requirements

- Windows 10 version 1809 (build 17763) or later
- Windows 11 (all versions)
- Administrator access for installation

---

## STEP 1: Fix Config Paths ✅

**What Changed:**
The `Config` class in `src/enterprise/config.py` now uses `get_config_dir()` instead of `get_user_config_dir()`.

**Why:**
- `get_user_config_dir()` → Points to user profile (`C:\Users\YourName\.clipboard_monitor`)
- `get_config_dir()` → Points to system directory (`C:\ProgramData\EnterpriseMonitoring\config`)

**Result:**
Service can run as SYSTEM without needing access to a user profile.

**Code Changes:**
```python
# OLD (Won't work as SYSTEM service)
from enterprise.paths import get_user_config_dir
self.config_dir = get_user_config_dir()

# NEW (Works as SYSTEM service)
from enterprise.paths import get_config_dir
self.config_dir = get_config_dir()
```

---

## STEP 2: Build the Executable

### Method 1: Using the Build Script (Recommended)

```bash
# Ensure you're in the project root
cd /path/to/Clipping-Monitor

# Run the build script
python build_production.py
```

**Output:**
- `dist/EnterpriseAgent.exe` (single-file executable, ~50-80 MB)

### Method 2: Manual PyInstaller Command

```bash
pyinstaller EnterpriseAgent.spec --clean --noconfirm
```

### What's Included in the Executable

The `.spec` file includes:
- ✅ Main script: `standalone_runner.py`
- ✅ All enterprise modules (config, paths, database, etc.)
- ✅ Hidden import: `win32timezone`
- ✅ Data folder: `src/enterprise` mapped to `enterprise`
- ✅ No console window (`--noconsole`)
- ✅ All required DLLs and dependencies

### Testing the Executable

Before creating the installer, test the executable:

```bash
# Run directly (should show no console window)
dist\EnterpriseAgent.exe

# Check if it's running (look in Task Manager)
# Check logs
type C:\ProgramData\EnterpriseMonitoring\logs\standalone_*.log

# Stop it (use Task Manager or wait for Ctrl+C if console attached)
```

---

## STEP 3: Prepare NSSM

### Download and Extract NSSM

1. **Download:** https://nssm.cc/release/nssm-2.24.zip
2. **Extract** the ZIP file
3. **Copy** `win64/nssm.exe` to `installer/nssm.exe` in your project

**Directory structure:**
```
Clipping-Monitor/
├── dist/
│   └── EnterpriseAgent.exe       ← Built in Step 2
├── installer/
│   └── nssm.exe                   ← Place here
├── EnterpriseAgent.iss            ← Inno Setup script
└── build_production.py
```

---

## STEP 4: Build the Installer

### Using Inno Setup GUI

1. **Open** Inno Setup Compiler
2. **File** → **Open** → Select `EnterpriseAgent.iss`
3. **Build** → **Compile**

**Output:**
- `installer/output/EnterpriseAgent-Setup-1.0.0.exe`

### Using Command Line

```bash
# Assuming Inno Setup is in PATH
iscc EnterpriseAgent.iss

# If not in PATH, use full path
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" EnterpriseAgent.iss
```

---

## What the Installer Does

### Installation Steps (Automatic)

1. **Checks Prerequisites**
   - Verifies Windows 10+ (build 17763+)
   - Requires administrator privileges

2. **Stops Existing Service** (if upgrading)
   - Stops running service
   - Removes old service registration

3. **Extracts Files**
   - `C:\Program Files\Enterprise Monitoring Agent\EnterpriseAgent.exe`
   - `C:\Program Files\Enterprise Monitoring Agent\nssm.exe`
   - Documentation files

4. **Creates Directory Structure**
   ```
   C:\ProgramData\EnterpriseMonitoring\
   ├── config\       ← Configuration files
   ├── data\         ← Database and collected data
   │   └── keystrokes\
   └── logs\         ← Log files
   ```

5. **Installs Windows Service Using NSSM**
   ```bash
   nssm install EnterpriseMonitoringAgent "C:\Program Files\...\EnterpriseAgent.exe"
   nssm set EnterpriseMonitoringAgent DisplayName "Enterprise Activity Monitoring Service"
   nssm set EnterpriseMonitoringAgent Description "Monitors clipboard, apps, browser..."
   nssm set EnterpriseMonitoringAgent Start SERVICE_AUTO_START
   ```

6. **Configures Logging**
   ```bash
   nssm set EnterpriseMonitoringAgent AppStdout "C:\ProgramData\EnterpriseMonitoring\logs\service.log"
   nssm set EnterpriseMonitoringAgent AppStderr "C:\ProgramData\EnterpriseMonitoring\logs\service.log"
   nssm set EnterpriseMonitoringAgent AppRotateFiles 1
   ```

7. **Configures Auto-Restart**
   ```bash
   nssm set EnterpriseMonitoringAgent AppExit Default Restart
   nssm set EnterpriseMonitoringAgent AppRestartDelay 5000  # 5 seconds
   ```

8. **Starts the Service**
   ```bash
   nssm start EnterpriseMonitoringAgent
   ```

9. **Creates Start Menu Shortcuts**
   - Service Manager (opens services.msc)
   - View Logs folder
   - Configuration folder
   - Uninstall

### Uninstallation Steps (Automatic)

1. Stops the service
2. Removes service registration with NSSM
3. Deletes program files
4. Optionally keeps data files (user choice)

---

## Verification After Installation

### Check Service Status

```powershell
# Open PowerShell as Administrator

# Check if service is installed
sc query EnterpriseMonitoringAgent

# Should show:
#   STATE: 4 RUNNING
#   WIN32_EXIT_CODE: 0 (0x0)

# Alternative: Use services.msc GUI
services.msc
# Look for "Enterprise Activity Monitoring Service"
```

### Check Logs

```powershell
# View service logs
notepad C:\ProgramData\EnterpriseMonitoring\logs\service.log

# Should contain:
#   "Enterprise Monitoring Agent - Standalone Runner Starting"
#   "✓ All components imported successfully"
#   "MONITORING AGENT RUNNING"
```

### Verify Monitoring

```powershell
# Check database is being created
dir C:\ProgramData\EnterpriseMonitoring\data

# Should see:
#   monitoring.db
```

### Test Service Control

```powershell
# Stop service
net stop EnterpriseMonitoringAgent

# Start service
net start EnterpriseMonitoringAgent

# Restart service
net stop EnterpriseMonitoringAgent
net start EnterpriseMonitoringAgent

# Using NSSM
nssm restart EnterpriseMonitoringAgent
```

---

## Configuration Details

### NSSM Service Configuration

The installer configures NSSM with these settings:

| Setting | Value | Purpose |
|---------|-------|---------|
| **Service Name** | EnterpriseMonitoringAgent | Internal identifier |
| **Display Name** | Enterprise Activity Monitoring Service | Shown in services.msc |
| **Description** | Monitors clipboard, apps, browser | Help text |
| **Start Type** | Automatic | Starts at boot |
| **Account** | Local System | Runs as SYSTEM |
| **Stdout Log** | `C:\ProgramData\...\service.log` | Capture output |
| **Stderr Log** | `C:\ProgramData\...\service.log` | Capture errors |
| **Log Rotation** | Enabled | Prevents huge logs |
| **Restart on Exit** | Yes | Auto-restart on crash |
| **Restart Delay** | 5 seconds | Wait before restart |

### Directory Permissions

All directories under `C:\ProgramData\EnterpriseMonitoring` are created with:
- **Full Control** for Everyone
- Allows service (running as SYSTEM) to write files
- Allows administrators to access data

---

## Troubleshooting

### Executable Won't Build

**Issue:** PyInstaller fails with "module not found"

**Solution:**
```bash
# Install all dependencies
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller

# Clean previous builds
rmdir /s /q build dist
del *.spec

# Try again
python build_production.py
```

### Executable Crashes Immediately

**Issue:** Missing dependencies or import errors

**Solution:**
```bash
# Run executable from command line to see errors
dist\EnterpriseAgent.exe

# Check if all paths are correct
python -c "from enterprise.paths import *; initialize_all_directories()"

# Verify all imports work
python test_service_imports.py
```

### Installer Build Fails

**Issue:** Inno Setup can't find files

**Solution:**
- Check `dist/EnterpriseAgent.exe` exists
- Check `installer/nssm.exe` exists
- Check file paths in `.iss` script match your structure
- Use Inno Setup GUI to see detailed error messages

### Service Won't Start

**Issue:** Service shows "Error 1053" or fails to start

**Solution:**
```powershell
# Check service installation
sc query EnterpriseMonitoringAgent

# Check NSSM configuration
nssm dump EnterpriseMonitoringAgent

# Try running executable manually
"C:\Program Files\Enterprise Monitoring Agent\EnterpriseAgent.exe"

# Check event viewer
eventvwr.msc
# Go to: Windows Logs → Application
# Look for EnterpriseMonitoringAgent errors
```

### Service Starts but Doesn't Monitor

**Issue:** Service running but no data collected

**Solution:**
```powershell
# Check logs for errors
type C:\ProgramData\EnterpriseMonitoring\logs\service.log

# Check if database exists
dir C:\ProgramData\EnterpriseMonitoring\data

# Verify permissions
icacls C:\ProgramData\EnterpriseMonitoring

# Check if monitors initialized
# Look for "✓ Started: clipboard" etc. in logs
```

---

## Complete Build and Deploy Workflow

### For Developers

```bash
# 1. Fix config paths (already done in Step 1)
git pull  # Get latest changes

# 2. Build executable
python build_production.py
# Output: dist/EnterpriseAgent.exe

# 3. Download NSSM
# Download from https://nssm.cc/download
# Extract win64/nssm.exe to installer/nssm.exe

# 4. Build installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" EnterpriseAgent.iss
# Output: installer/output/EnterpriseAgent-Setup-1.0.0.exe

# 5. Test installer on clean VM
# Run setup, verify service starts

# 6. Distribute
# Share EnterpriseAgent-Setup-1.0.0.exe with users
```

### For End Users

```bash
# 1. Download installer
# Get EnterpriseAgent-Setup-1.0.0.exe

# 2. Run as administrator
# Right-click → "Run as administrator"

# 3. Follow installation wizard
# Click Next → Next → Install → Finish

# 4. Verify service is running
# Check system tray or services.msc

# 5. Done!
# Service automatically starts at boot
```

---

## Comparison: Old vs New Method

### Old Method (pywin32 Service)

❌ **Problems:**
- Complex `win32serviceutil` code
- Fragile imports
- DLL issues
- Error 1053, 1060, 1062
- Hard to debug
- Manual service registration
- User profile dependencies

### New Method (NSSM + Inno Setup)

✅ **Advantages:**
- Simple standalone runner (no service APIs)
- NSSM handles service wrapper
- Professional installer
- Auto-restart on failure
- System-wide paths (no user profile)
- Easy to debug (check service.log)
- One-click installation
- One-click uninstallation
- Similar to commercial software (Grammarly, Dropbox)

---

## File Checklist

Before building installer, verify these files exist:

```
Clipping-Monitor/
├── ✅ dist/EnterpriseAgent.exe           ← From Step 2
├── ✅ installer/nssm.exe                  ← Downloaded
├── ✅ EnterpriseAgent.iss                 ← Created in Step 3
├── ✅ EnterpriseAgent.spec                ← Created in Step 2
├── ✅ build_production.py                 ← Created in Step 2
├── ✅ src/enterprise/config.py            ← Fixed in Step 1
├── ✅ src/enterprise/paths.py             ← Should exist
├── ✅ standalone_runner.py                ← Should exist
├── ✅ README.md                            ← Should exist
├── ✅ LICENSE                              ← Should exist
└── ✅ QUICK_START.md                       ← Should exist
```

---

## Support and Resources

### Documentation
- `README.md` - Project overview
- `QUICK_START.md` - Quick reference
- `ALTERNATIVE_SERVICE_METHODS.md` - Service deployment options
- `TROUBLESHOOTING.md` - Common issues

### Tools
- NSSM: https://nssm.cc/
- Inno Setup: https://jrsoftware.org/isinfo.php
- PyInstaller: https://www.pyinstaller.org/

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share experiences

---

## Summary

This production deployment approach provides:

1. ✅ **Reliable Service** - NSSM wraps Python executable as Windows service
2. ✅ **Professional Installer** - Inno Setup creates single-file installer
3. ✅ **System-Wide Operation** - Uses ProgramData, not user profile
4. ✅ **Auto-Restart** - Service automatically restarts on failure
5. ✅ **Easy Deployment** - One installer file, no manual steps
6. ✅ **Clean Uninstall** - Removes service and files completely
7. ✅ **Commercial Quality** - Similar to Grammarly, Dropbox, etc.

**Result:** A production-ready Windows service that users can install with a single double-click! 🎉
