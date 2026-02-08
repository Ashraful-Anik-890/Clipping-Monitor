# Quick Start Guide - Enterprise Monitoring Agent

## Choose Your Installation Method

### 🏆 Method 1: NSSM (RECOMMENDED)
**Most reliable, production-ready method**

```powershell
# 1. Download NSSM from https://nssm.cc/download
# 2. Extract to C:\Tools\nssm\
# 3. Run as Administrator:
.\install_nssm_service.ps1

# Management:
nssm status EnterpriseMonitoringAgent
nssm start EnterpriseMonitoringAgent
nssm stop EnterpriseMonitoringAgent
nssm remove EnterpriseMonitoringAgent confirm
```

**Logs:** `C:\ProgramData\EnterpriseMonitoring\logs\nssm_stdout.log`

---

### 🏆 Method 2: Task Scheduler (ALSO RECOMMENDED)
**Built into Windows, no downloads needed**

```powershell
# Run as Administrator:
.\install_scheduled_task.ps1

# Management:
Start-ScheduledTask -TaskName "EnterpriseMonitoringAgent"
Stop-ScheduledTask -TaskName "EnterpriseMonitoringAgent"
Get-ScheduledTask -TaskName "EnterpriseMonitoringAgent" | Get-ScheduledTaskInfo
Unregister-ScheduledTask -TaskName "EnterpriseMonitoringAgent" -Confirm:$false
```

**Logs:** `C:\ProgramData\EnterpriseMonitoring\logs\standalone_*.log`

---

### ⚠️ Method 3: Native Service (FALLBACK)
**Use only if NSSM/Task Scheduler not available**

```powershell
# Run as Administrator:
cd src\enterprise
python service_main.py install
python service_main.py start

# Management:
python service_main.py status
python service_main.py stop
python service_main.py remove
```

**Logs:** `C:\ProgramData\EnterpriseMonitoring\logs\service.log`

---

## Testing (Run First!)

### Test Standalone Runner
```powershell
# See if it works before installing as service
python standalone_runner.py
# Press Ctrl+C to stop
```

### Test Imports
```powershell
# Verify all modules can be imported
python test_service_imports.py
```

---

## Troubleshooting

### Service Won't Start?
**→ Use NSSM or Task Scheduler instead!**

See: `ALTERNATIVE_SERVICE_METHODS.md`

### Check Logs
```powershell
# NSSM logs
type C:\ProgramData\EnterpriseMonitoring\logs\nssm_stdout.log

# Task Scheduler logs
type C:\ProgramData\EnterpriseMonitoring\logs\standalone_*.log

# Native service logs
type C:\ProgramData\EnterpriseMonitoring\logs\service.log
```

### Get Help
- README.md - Quick overview
- ALTERNATIVE_SERVICE_METHODS.md - Complete guide
- TROUBLESHOOTING.md - Detailed troubleshooting
- SERVICE_RELIABILITY_SOLUTION.md - Full solution summary

---

## Quick Commands Reference

### Check if Running

**NSSM:**
```powershell
nssm status EnterpriseMonitoringAgent
# Should show: SERVICE_RUNNING
```

**Task Scheduler:**
```powershell
Get-ScheduledTask -TaskName "EnterpriseMonitoringAgent" | Get-ScheduledTaskInfo
# Check LastTaskResult: 0 = success
```

**Native Service:**
```powershell
sc query EnterpriseMonitoringAgent
# Should show: STATE: 4 RUNNING
```

---

## Common Issues

### Error 1053 - Service didn't respond
**Solution:** Use NSSM or Task Scheduler instead

### Error 1063 - Couldn't connect to controller
**Solution:** Use NSSM or Task Scheduler instead

### ImportError or ModuleNotFoundError
**Solution:** Run `python test_service_imports.py` to diagnose

### Service installs but doesn't work
**Solution:** Check logs at `C:\ProgramData\EnterpriseMonitoring\logs\`

---

## After Installation

### Verify Monitoring is Active

```powershell
# Check database has data
type C:\ProgramData\EnterpriseMonitoring\data\monitoring.db
# Should exist and grow over time

# Check logs show activity
type C:\ProgramData\EnterpriseMonitoring\logs\*.log | Select-String "monitor"
```

### Admin Console

```powershell
# Access admin interface
python src\enterprise\admin_console.py
```

---

## Need More Help?

1. **Quick Start:** This file
2. **Complete Guide:** ALTERNATIVE_SERVICE_METHODS.md
3. **Troubleshooting:** TROUBLESHOOTING.md
4. **Full Solution:** SERVICE_RELIABILITY_SOLUTION.md
5. **Issues:** https://github.com/Ashraful-Anik-890/Clipping-Monitor/issues

---

**TIP:** For production, use NSSM. For testing, run `python standalone_runner.py` directly.
