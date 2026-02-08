# Quick Reference: Production Deployment

## STEP 1: Fix Config Paths ✅

**File:** `src/enterprise/config.py`

**Changed:**
```python
# OLD (Won't work as SYSTEM)
from enterprise.paths import get_user_config_dir
self.config_dir = get_user_config_dir()

# NEW (Works as SYSTEM)
from enterprise.paths import get_config_dir
self.config_dir = get_config_dir()
```

**Result:** Service can run as SYSTEM without user profile access.

---

## STEP 2: Build Executable ✅

**Command:**
```bash
python build_production.py
```

**Or manually:**
```bash
pyinstaller EnterpriseAgent.spec --clean --noconfirm
```

**Output:** `dist/EnterpriseAgent.exe` (~50-80 MB)

**Spec File Details:**
- Entry point: `standalone_runner.py`
- Hidden import: `win32timezone`
- Data folder: `src/enterprise` → `enterprise`
- Console: Disabled (`--noconsole`)

---

## STEP 3: Build Installer ✅

**Prerequisites:**
1. Download NSSM from https://nssm.cc/download
2. Extract `win64/nssm.exe` to `installer/nssm.exe`
3. Install Inno Setup from https://jrsoftware.org/isdl.php

**Command:**
```bash
# Using Inno Setup compiler
iscc EnterpriseAgent.iss

# Or full path
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" EnterpriseAgent.iss
```

**Output:** `installer/output/EnterpriseAgent-Setup-1.0.0.exe`

**What Installer Does:**
1. ✅ Requires admin privileges
2. ✅ Installs to `C:\Program Files\Enterprise Monitoring Agent`
3. ✅ Creates `C:\ProgramData\EnterpriseMonitoring` structure
4. ✅ Uses NSSM to install Windows service
5. ✅ Configures stdout/stderr to `C:\ProgramData\...\logs\service.log`
6. ✅ Starts service automatically
7. ✅ Clean uninstall (stops and removes service)

---

## STEP 4: Verify Installation ✅

**Check Service:**
```powershell
sc query EnterpriseMonitoringAgent
# Should show: STATE: 4 RUNNING
```

**Check Logs:**
```powershell
type C:\ProgramData\EnterpriseMonitoring\logs\service.log
# Should contain: "MONITORING AGENT RUNNING"
```

**Check Database:**
```powershell
dir C:\ProgramData\EnterpriseMonitoring\data
# Should see: monitoring.db
```

---

## Quick Build Workflow

```bash
# 1. Build executable
python build_production.py

# 2. Get NSSM
# Download and extract to installer/nssm.exe

# 3. Build installer
iscc EnterpriseAgent.iss

# 4. Test on clean VM
# Run installer/output/EnterpriseAgent-Setup-1.0.0.exe

# 5. Distribute!
```

---

## Files Created

### Core Files
- ✅ `EnterpriseAgent.spec` - PyInstaller spec file
- ✅ `build_production.py` - Build automation script
- ✅ `EnterpriseAgent.iss` - Inno Setup installer script
- ✅ `PRODUCTION_DEPLOYMENT.md` - Complete deployment guide

### Modified Files
- ✅ `src/enterprise/config.py` - Fixed for SYSTEM service

### Output Files (after build)
- ✅ `dist/EnterpriseAgent.exe` - Single-file executable
- ✅ `installer/output/EnterpriseAgent-Setup-1.0.0.exe` - Installer

---

## Service Configuration

**Service Name:** `EnterpriseMonitoringAgent`
**Display Name:** `Enterprise Activity Monitoring Service`
**Start Type:** Automatic
**Account:** Local System
**Log File:** `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
**Auto-Restart:** Yes (5-second delay)

---

## Directories Created

```
C:\Program Files\Enterprise Monitoring Agent\
├── EnterpriseAgent.exe
├── nssm.exe
├── README.md
├── LICENSE
└── QUICK_START.md

C:\ProgramData\EnterpriseMonitoring\
├── config\          ← Configuration files
├── data\            ← Database and collected data
│   └── keystrokes\
└── logs\            ← Service logs
```

---

## Common Commands

```powershell
# Service control
net start EnterpriseMonitoringAgent
net stop EnterpriseMonitoringAgent
sc query EnterpriseMonitoringAgent

# NSSM commands
nssm start EnterpriseMonitoringAgent
nssm stop EnterpriseMonitoringAgent
nssm restart EnterpriseMonitoringAgent
nssm status EnterpriseMonitoringAgent

# View logs
type C:\ProgramData\EnterpriseMonitoring\logs\service.log

# View config
notepad C:\ProgramData\EnterpriseMonitoring\config\config.json
```

---

## Troubleshooting

**Service won't start?**
```powershell
# Run executable manually to see errors
"C:\Program Files\Enterprise Monitoring Agent\EnterpriseAgent.exe"

# Check event viewer
eventvwr.msc
```

**No data collected?**
```powershell
# Check service log
type C:\ProgramData\EnterpriseMonitoring\logs\service.log

# Verify monitors started
# Look for "✓ Started: clipboard" etc.
```

**Build fails?**
```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Clean and rebuild
rmdir /s /q build dist
python build_production.py
```

---

## Advantages Over pywin32 Service

| Aspect | Old (pywin32) | New (NSSM) |
|--------|---------------|------------|
| Reliability | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Setup Complexity | High | Low |
| Debug Difficulty | Hard | Easy |
| Installer | Manual | Automated |
| Auto-Restart | Manual config | Built-in |
| Log Capture | Complex | Automatic |
| User Experience | Poor | Professional |

---

## Next Steps

1. ✅ Test executable: `dist\EnterpriseAgent.exe`
2. ✅ Build installer: `iscc EnterpriseAgent.iss`
3. ✅ Test on clean VM
4. ✅ Distribute to users

---

See `PRODUCTION_DEPLOYMENT.md` for complete details.
