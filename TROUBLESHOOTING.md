# Service Troubleshooting Guide

## Common Service Issues and Solutions

### Issue 1: Service Installs but Immediately Crashes

**Symptoms:**
- Service installs successfully
- Service "starts" but shows as stopped when checked
- Error 1062: "The service has not been started" when trying to stop
- No monitoring activity occurs

**Root Cause:**
Service crashes during initialization due to import errors or initialization failures.

**Solution:**
1. Check service log file: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
2. Look for import errors or initialization errors
3. Verify all paths are accessible with SYSTEM privileges

**Recent Fix Applied:**
- ✅ Fixed incorrect import paths in `service_core.py`
- ✅ Replaced hardcoded paths with environment-aware functions

---

### Issue 2: Import Errors in Service

**Symptoms:**
- Service fails to start
- Log shows `ImportError` or `ModuleNotFoundError`

**Solution:**
1. Verify Python path configuration
2. Ensure all modules are in correct locations:
   - `clipboard_monitor.py` → `src/`
   - `app_usage_tracker.py` → `src/enterprise/`
   - `browser_tracker.py` → `src/enterprise/`
   - `keystroke_recorder.py` → `src/enterprise/`
   - `database_manager.py` → `src/enterprise/`
   - `config.py` → `src/enterprise/`

3. Run import test: `python test_service_imports.py`

---

### Issue 3: Path Not Found Errors

**Symptoms:**
- Service crashes with `FileNotFoundError`
- Hardcoded path errors like `C:\ProgramData\...`

**Solution:**
All paths now use centralized path management from `enterprise/paths.py`:
- Database: `get_database_path()`
- Logs: `get_logs_dir()`
- Data: `get_data_dir()`
- Keystrokes: `get_keystroke_storage_dir()`

No more hardcoded paths!

---

### Issue 4: Service Won't Install

**Symptoms:**
- "File not found" error during installation
- Service install command fails

**Solution:**
1. Run as Administrator
2. Verify service_main.py exists: `src/enterprise/service_main.py`
3. Check Python path is correct
4. Install command: `python src\enterprise\service_main.py install`

---

### Issue 5: Admin Console Service Control Not Working

**Symptoms:**
- Buttons don't respond
- Service status shows "Unknown"
- Error 1060: Service doesn't exist

**Solution:**
1. Ensure running Admin Console as Administrator
2. Install service first before trying to start/stop
3. Check service is actually installed: `sc query EnterpriseMonitoringAgent`

---

## Verification Steps

### Step 1: Test Imports
```bash
python test_service_imports.py
```
Should show all imports successful.

### Step 2: Install Service (as Admin)
```bash
python src\enterprise\service_main.py install
```
Should show: "Service installed successfully"

### Step 3: Check Service Exists
```bash
sc query EnterpriseMonitoringAgent
```
Should show service exists (even if stopped).

### Step 4: Start Service
```bash
python src\enterprise\service_main.py start
```
OR
```bash
net start EnterpriseMonitoringAgent
```

### Step 5: Verify Service is Running
```bash
sc query EnterpriseMonitoringAgent
```
Should show: `STATE: 4 RUNNING`

### Step 6: Check Service Logs
```bash
type C:\ProgramData\EnterpriseMonitoring\logs\service.log
```
Should show:
- "Monitoring engine initialized"
- "Started: clipboard"
- "Started: app_usage"
- "Started: browser"
- "Service running - monitoring active"

---

## Debug Mode

To run service in debug mode (see console output):
```bash
python src\enterprise\service_core.py debug
```

This will:
- Show all log output in console
- Not run as Windows service
- Can be stopped with Ctrl+C
- Good for testing monitors

---

## Common Error Codes

- **1060**: Service doesn't exist (not installed)
- **1062**: Service has not been started (crashed or stopped)
- **5**: Access denied (need Administrator)
- **1053**: Service did not respond (crashed immediately)

---

## Log Locations

- **Service logs**: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
- **Admin Console logs**: `C:\ProgramData\EnterpriseMonitoring\logs\admin.log`
- **Database**: `C:\ProgramData\EnterpriseMonitoring\data\monitoring.db`
- **Keystroke data**: `C:\ProgramData\EnterpriseMonitoring\data\keystrokes\`

---

## Clean Reinstall

If service is completely broken:

```bash
# 1. Stop service (if running)
net stop EnterpriseMonitoringAgent

# 2. Remove service
python src\enterprise\service_main.py remove

# 3. Delete data (optional - CAREFUL!)
rmdir /s C:\ProgramData\EnterpriseMonitoring

# 4. Reinstall
python src\enterprise\service_main.py install

# 5. Start
net start EnterpriseMonitoringAgent
```

---

## Getting Help

1. **Check logs first**: Most issues are logged
2. **Run import test**: `python test_service_imports.py`
3. **Try debug mode**: `python src\enterprise\service_core.py debug`
4. **Check Windows Event Viewer**: Application logs for service errors
5. **Report issue**: Include service.log contents

---

## Recent Fixes Applied (2024-02-08)

✅ **Fixed Import Paths** - Service was crashing due to incorrect module imports
✅ **Removed Hardcoded Paths** - Now uses environment variables
✅ **Added Path Verification** - Service checks paths on startup
✅ **Improved Error Handling** - Better logging of initialization errors

After these fixes, the service should:
- Start successfully without crashing
- Run all enabled monitors
- Log activity properly
- Be manageable from Admin Console
