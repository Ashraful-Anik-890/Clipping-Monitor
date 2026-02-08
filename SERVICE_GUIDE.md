# Service Quick Reference Guide

## ⚠️ IMPORTANT: Always Use service_main.py

**DO NOT** run `service_core.py` directly! It will cause Error 1063.

**Always** use `service_main.py` for all service operations.

---

## Service Installation & Management

### Install Service
```powershell
python src\enterprise\service_main.py install
```

### Start Service
```powershell
# Method 1: Using service_main.py
python src\enterprise\service_main.py start

# Method 2: Using Windows net command
net start EnterpriseMonitoringAgent

# Method 3: Using Windows sc command
sc start EnterpriseMonitoringAgent
```

### Stop Service
```powershell
# Method 1: Using service_main.py
python src\enterprise\service_main.py stop

# Method 2: Using Windows net command
net stop EnterpriseMonitoringAgent

# Method 3: Using Windows sc command
sc stop EnterpriseMonitoringAgent
```

### Restart Service
```powershell
python src\enterprise\service_main.py restart
```

### Remove Service
```powershell
python src\enterprise\service_main.py remove
```

### Check Service Status
```powershell
sc query EnterpriseMonitoringAgent
```

**Expected Output When Running:**
```
SERVICE_NAME: EnterpriseMonitoringAgent
        TYPE               : 10  WIN32_OWN_PROCESS
        STATE              : 4  RUNNING
        WIN32_EXIT_CODE    : 0  (0x0)
        SERVICE_EXIT_CODE  : 0  (0x0)
        CHECKPOINT         : 0x0
        WAIT_HINT          : 0x0
```

---

## Debug Mode (Not as Service)

Run the monitoring engine in console/debug mode:

```powershell
python src\enterprise\service_main.py debug
```

This is useful for:
- Testing the monitoring engine without installing as service
- Seeing real-time log output in console
- Debugging initialization issues
- Testing monitor functionality

**To stop:** Press `Ctrl+C`

---

## Common Workflows

### First-Time Setup
```powershell
# 1. Install service
python src\enterprise\service_main.py install

# 2. Start service
net start EnterpriseMonitoringAgent

# 3. Verify running
sc query EnterpriseMonitoringAgent

# 4. Check logs
type C:\ProgramData\EnterpriseMonitoring\logs\service.log
```

### Reinstall Service (After Code Changes)
```powershell
# 1. Stop service
python src\enterprise\service_main.py stop

# 2. Remove service
python src\enterprise\service_main.py remove

# 3. Reinstall service
python src\enterprise\service_main.py install

# 4. Start service
python src\enterprise\service_main.py start
```

### Troubleshooting
```powershell
# 1. Check service status
sc query EnterpriseMonitoringAgent

# 2. Check logs
type C:\ProgramData\EnterpriseMonitoring\logs\service.log

# 3. Try debug mode
python src\enterprise\service_main.py debug
```

---

## File Locations

### Service Executable
- **Correct Entry Point:** `src\enterprise\service_main.py`
- **Service Class:** `src\enterprise\service_core.py` (internal, don't run directly)

### Logs
- **Service Log:** `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
- **Admin Console Log:** `C:\ProgramData\EnterpriseMonitoring\logs\admin.log`

### Data
- **Database:** `C:\ProgramData\EnterpriseMonitoring\data\monitoring.db`
- **Keystrokes:** `C:\ProgramData\EnterpriseMonitoring\data\keystrokes\`

### Configuration
- **User Config:** `%USERPROFILE%\.clipboard_monitor\config.json`

---

## Common Errors

### Error 1063
**Message:** "The service process could not connect to the service controller"

**Cause:** Running `service_core.py` directly instead of `service_main.py`

**Fix:** Remove and reinstall using `service_main.py`:
```powershell
python src\enterprise\service_main.py remove
python src\enterprise\service_main.py install
```

### Error 1060
**Message:** "The specified service does not exist as an installed service"

**Cause:** Service not installed

**Fix:** Install the service:
```powershell
python src\enterprise\service_main.py install
```

### Error 1062
**Message:** "The service has not been started"

**Cause:** Service crashed or not running

**Fix:** Check logs and restart:
```powershell
type C:\ProgramData\EnterpriseMonitoring\logs\service.log
python src\enterprise\service_main.py start
```

### Error 5
**Message:** "Access denied"

**Cause:** Not running as Administrator

**Fix:** Run PowerShell as Administrator

---

## Best Practices

✅ **DO:**
- Always use `service_main.py` for service operations
- Run PowerShell as Administrator for service management
- Check logs after starting service
- Use debug mode for testing

❌ **DON'T:**
- Run `service_core.py` directly
- Try to start service without Administrator privileges
- Modify service while it's running
- Delete log/data directories while service is running

---

## Quick Checklist

Before reporting issues, verify:

- [ ] Used `service_main.py` (not `service_core.py`)
- [ ] Running PowerShell as Administrator
- [ ] Service installed successfully
- [ ] Checked service logs
- [ ] Tried debug mode
- [ ] No conflicting software

---

**For more detailed troubleshooting, see `TROUBLESHOOTING.md`**
