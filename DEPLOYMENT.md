# Enterprise Monitoring Agent - Deployment Guide

## Overview

This guide walks you through deploying the Enterprise Monitoring Agent in a production Windows environment.

---

## Prerequisites

### System Requirements
- **Operating System**: Windows 10 or Windows 11 (64-bit recommended)
- **Python**: 3.8 or higher
- **Privileges**: Administrator access required for installation
- **Disk Space**: 500MB free space recommended
- **Memory**: 200MB RAM (configurable)
- **Network**: None required (local storage only)

### Software Requirements
- Python 3.8+ installed
- pip package manager
- Internet connection for initial setup (dependency installation)

---

## Deployment Steps

### Phase 1: Pre-Deployment Verification

#### Step 1: Check Python Installation
```powershell
python --version
# Should output: Python 3.8.x or higher
```

#### Step 2: Verify Administrator Privileges
```powershell
# Run PowerShell as Administrator
whoami /priv
# Should show elevated privileges
```

#### Step 3: Clone or Download Repository
```powershell
# Option A: Clone with Git
git clone https://github.com/Ashraful-Anik-890/Clipping-Monitor.git
cd Clipping-Monitor

# Option B: Download and extract ZIP
# Download from: https://github.com/Ashraful-Anik-890/Clipping-Monitor
# Extract to: C:\Program Files\EnterpriseMonitoring
```

---

### Phase 2: Installation

#### Step 4: Install Dependencies
```powershell
# Navigate to project directory
cd C:\Path\To\Clipping-Monitor

# Install runtime dependencies
pip install -r requirements.txt

# Verify installation
pip list | Select-String "pywin32|psutil|cryptography|pynput"
```

#### Step 5: Run Installation Verification
```powershell
python verify_installation.py
```

**Expected Output:**
```
Enterprise Monitoring Agent - Installation Verification
======================================================================

1. Checking Python Version
✓ Python version is compatible (3.8+)

2. Checking Platform
✓ Running on Windows (win32)

3. Checking Dependencies
✓ pywin32 is installed
✓ psutil is installed
✓ cryptography is installed
...

VERIFICATION SUMMARY
  Python Version................ PASS
  Platform...................... PASS
  Dependencies.................. PASS
  ...

8/8 checks passed
✓ All verification checks passed!
```

**If Any Checks Fail:**
- Review error messages carefully
- Install missing dependencies: `pip install [package-name]`
- Ensure running as Administrator
- Re-run verification script

---

### Phase 3: Configuration

#### Step 6: Review Configuration
Configuration file will be created at: `%USERPROFILE%\.clipboard_monitor\config.json`

**Default Configuration:**
```json
{
  "version": "1.0.0",
  "monitoring": {
    "clipboard": true,
    "applications": true,
    "browser": true,
    "keystrokes": false,
    "screen_recording": false
  },
  "storage": {
    "encryption_enabled": true,
    "retention_days": 90
  },
  "keystrokes": {
    "enabled": false,
    "encryption_enabled": true,
    "buffer_flush_interval": 60,
    "retention_days": 30
  }
}
```

#### Step 7: Customize Configuration (Optional)

**To Enable Keystroke Logging:**
1. Edit: `%USERPROFILE%\.clipboard_monitor\config.json`
2. Set: `"monitoring": { "keystrokes": true }`
3. Set: `"keystrokes": { "enabled": true }`
4. **IMPORTANT**: Ensure proper legal consent and compliance

**To Adjust Retention:**
```json
{
  "storage": {
    "retention_days": 30  // Keep data for 30 days
  }
}
```

---

### Phase 4: Service Installation

#### Step 8: Launch Admin Console
```powershell
# Run as Administrator
python src\enterprise\admin_console.py
```

#### Step 9: First-Time Setup
1. **Create Administrator Password**
   - Choose a strong password (minimum 8 characters)
   - Store securely (password recovery not available)
   - Password is hashed using PBKDF2

2. **Login**
   - Enter the password you just created
   - Console will open

#### Step 10: Install Windows Service
1. In Admin Console, go to **Service Control** tab
2. Click **"Install Service"** (Blue button)
3. Wait for confirmation: "Service installed successfully"
4. Status should show: **Stopped**

#### Step 11: Start Service
1. In Admin Console, click **"Start Service"** (Green button)
2. Status should change to: **Running**
3. Check logs at: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`

---

### Phase 5: Verification

#### Step 12: Verify Service is Running
```powershell
# Check service status
sc query EnterpriseMonitoringAgent

# Expected output:
# STATE              : 4  RUNNING
```

#### Step 13: Monitor Logs
```powershell
# View service logs
type C:\ProgramData\EnterpriseMonitoring\logs\service.log

# Expected to see:
# INFO - Monitoring engine initialized
# INFO - Started: clipboard
# INFO - Started: app_usage
# INFO - Started: browser
# INFO - Service running - monitoring active
```

#### Step 14: Verify Data Collection
```powershell
# Check database created
dir C:\ProgramData\EnterpriseMonitoring\data\

# Should show:
# monitoring.db
# .db_encryption_key
```

---

### Phase 6: Testing

#### Step 15: Test Clipboard Monitoring
1. Copy some text (Ctrl+C)
2. In Admin Console, go to **Statistics** tab
3. Should show clipboard events

#### Step 16: Test Application Tracking
1. Switch between different applications
2. Check statistics tab
3. Should show application usage events

#### Step 17: Test Browser Tracking
1. Open a browser and visit some websites
2. Check statistics tab
3. Should show browser activity

---

## Post-Deployment

### Ongoing Maintenance

#### Daily Checks
- Service status (should be Running)
- Log file for errors
- Disk space usage

#### Weekly Tasks
- Review statistics in Admin Console
- Check log rotation
- Verify backup storage

#### Monthly Tasks
- Review retention policies
- Export historical data
- Update software if available

### Backup Procedures

#### What to Backup
```
C:\ProgramData\EnterpriseMonitoring\data\
  - monitoring.db (main database)
  - .db_encryption_key (encryption key)
  - keystrokes\ (if enabled)

%USERPROFILE%\.clipboard_monitor\
  - config.json (configuration)
  - admin_credentials.dat (admin password)
```

#### Backup Script (PowerShell)
```powershell
# Create backup directory
$backupDir = "C:\Backups\EnterpriseMonitoring\$(Get-Date -Format 'yyyy-MM-dd')"
New-Item -ItemType Directory -Path $backupDir -Force

# Backup data
Copy-Item "C:\ProgramData\EnterpriseMonitoring\data\*" -Destination $backupDir -Recurse

# Backup config
Copy-Item "$env:USERPROFILE\.clipboard_monitor\*" -Destination "$backupDir\config" -Recurse
```

---

## Troubleshooting

### Service Won't Start

**Symptom**: Service status shows "Stopped" or "Error"

**Solutions**:
1. Check logs: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
2. Verify dependencies: `python verify_installation.py`
3. Check Windows Event Viewer: `eventvwr.msc`
4. Ensure running as Administrator
5. Try debug mode:
   ```powershell
   python src\enterprise\service_core.py debug
   ```

### High Resource Usage

**Symptom**: CPU or memory usage too high

**Solutions**:
1. Adjust polling intervals in config:
   ```json
   {
     "performance": {
       "polling_interval_ms": 2000,
       "max_cpu_usage_percent": 5
     }
   }
   ```
2. Disable unnecessary monitors
3. Increase buffer flush interval for keystroke logging

### Data Not Being Collected

**Symptom**: No events in statistics

**Solutions**:
1. Verify monitors enabled in config
2. Check monitor-specific logs
3. Ensure no permission issues
4. Test individual monitors:
   ```powershell
   python src\clipboard_monitor.py
   ```

---

## Security Considerations

### Access Control
- ✅ Service runs as SYSTEM (highest privileges)
- ✅ Admin Console requires administrator privileges
- ✅ Password protected admin access
- ✅ Encrypted data at rest

### Data Protection
- ✅ AES encryption (Fernet) for sensitive data
- ✅ Encryption keys stored with restricted permissions
- ✅ Key files hidden on Windows
- ✅ No network transmission (local storage only)

### Compliance
- ⚠️ **Legal Requirements**: Ensure compliance with local laws
- ⚠️ **Employee Consent**: Inform employees about monitoring
- ⚠️ **Data Retention**: Follow company/legal retention policies
- ⚠️ **Access Control**: Restrict admin console access

---

## Uninstallation

### Complete Removal

```powershell
# 1. Stop service
python src\enterprise\service_main.py stop

# 2. Remove service
python src\enterprise\service_main.py remove

# 3. Delete data (CAREFUL - CANNOT BE UNDONE)
Remove-Item "C:\ProgramData\EnterpriseMonitoring" -Recurse -Force

# 4. Delete config
Remove-Item "$env:USERPROFILE\.clipboard_monitor" -Recurse -Force

# 5. Uninstall Python packages (optional)
pip uninstall pywin32 psutil cryptography pystray pillow pynput
```

---

## Support

### Getting Help

1. **Check Logs First**:
   - Service logs: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
   - Application logs: Look for ERROR or WARNING entries

2. **Run Verification**:
   ```powershell
   python verify_installation.py
   ```

3. **GitHub Issues**:
   - Report bugs: https://github.com/Ashraful-Anik-890/Clipping-Monitor/issues
   - Search existing issues for solutions

4. **Documentation**:
   - README.md - Overview and quick start
   - CHANGELOG.md - Recent changes and fixes
   - docs/ - Detailed guides

---

## Deployment Checklist

- [ ] Python 3.8+ installed
- [ ] Administrator privileges confirmed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Verification passed (`python verify_installation.py`)
- [ ] Configuration reviewed and customized
- [ ] Admin Console tested (password created)
- [ ] Service installed successfully
- [ ] Service started and running
- [ ] Logs verified (no errors)
- [ ] Data collection confirmed
- [ ] Backup procedures documented
- [ ] Security considerations reviewed
- [ ] Compliance requirements met
- [ ] Users informed about monitoring
- [ ] Support contacts documented

---

## Quick Reference

### Important Paths
```
Service Logs:      C:\ProgramData\EnterpriseMonitoring\logs\service.log
Database:          C:\ProgramData\EnterpriseMonitoring\data\monitoring.db
Configuration:     %USERPROFILE%\.clipboard_monitor\config.json
Keystroke Logs:    C:\ProgramData\EnterpriseMonitoring\data\keystrokes\
```

### Common Commands
```powershell
# Service Management
python src\enterprise\service_main.py install
python src\enterprise\service_main.py start
python src\enterprise\service_main.py stop
python src\enterprise\service_main.py remove

# Admin Console
python src\enterprise\admin_console.py

# Verification
python verify_installation.py

# Debug Mode
python src\enterprise\service_core.py debug
```

### Service Status Codes
```
Running (4)    - Service is active and monitoring
Stopped (1)    - Service is installed but not running
Start Pending  - Service is starting up
Stop Pending   - Service is shutting down
```

---

**Document Version:** 1.0
**Last Updated:** 2024-02-08
**Applies To:** Enterprise Monitoring Agent v1.0.0+
