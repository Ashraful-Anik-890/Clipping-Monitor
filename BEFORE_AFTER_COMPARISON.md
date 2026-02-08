# BEFORE & AFTER COMPARISON

## STEP 1: Config Paths

### BEFORE (src/enterprise/config.py)
```python
import os
import json
from pathlib import Path
from typing import Dict, Any

class Config:
    """Application configuration manager"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".clipboard_monitor"  # ❌ User home directory
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = {}
        self.load()
```

**Problem:** Service running as SYSTEM cannot access user home directory.

---

### AFTER (src/enterprise/config.py)
```python
import os
import json
from pathlib import Path
from typing import Dict, Any
from .paths import get_config_dir  # ✅ Import new path utility

class Config:
    """Application configuration manager"""
    
    def __init__(self):
        self.config_dir = get_config_dir()  # ✅ System-wide directory
        self.config_file = self.config_dir / "config.json"
        self.config: Dict[str, Any] = {}
        self.load()
```

**Solution:** Service now reads configs from `C:\ProgramData\EnterpriseMonitoring\config`

---

### NEW FILE: src/enterprise/paths.py
```python
"""
Path utilities for Enterprise Monitoring Agent
Provides centralized path management for service configuration and data
"""

import os
from pathlib import Path


def get_config_dir() -> Path:
    r"""
    Get the configuration directory for the Enterprise Monitoring Agent.
    Uses C:\ProgramData for Windows service compatibility.
    
    Returns:
        Path: Configuration directory path (C:\ProgramData\EnterpriseMonitoring\config)
    """
    if os.name == 'nt':  # Windows
        config_dir = Path('C:/ProgramData/EnterpriseMonitoring/config')
    else:  # Linux/Unix fallback
        config_dir = Path('/etc/enterprise-monitoring')
    
    # Ensure directory exists
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_data_dir() -> Path:
    r"""
    Get the data directory for the Enterprise Monitoring Agent.
    
    Returns:
        Path: Data directory path (C:\ProgramData\EnterpriseMonitoring\data)
    """
    if os.name == 'nt':  # Windows
        data_dir = Path('C:/ProgramData/EnterpriseMonitoring/data')
    else:  # Linux/Unix fallback
        data_dir = Path('/var/lib/enterprise-monitoring')
    
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_log_dir() -> Path:
    r"""
    Get the log directory for the Enterprise Monitoring Agent.
    
    Returns:
        Path: Log directory path (C:\ProgramData\EnterpriseMonitoring\logs)
    """
    if os.name == 'nt':  # Windows
        log_dir = Path('C:/ProgramData/EnterpriseMonitoring/logs')
    else:  # Linux/Unix fallback
        log_dir = Path('/var/log/enterprise-monitoring')
    
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_user_config_dir() -> Path:
    """
    Get the user-specific configuration directory.
    Used for non-service applications.
    
    Returns:
        Path: User configuration directory path
    """
    return Path.home() / ".clipboard_monitor"
```

---

## STEP 2: Standalone Runner

### NEW FILE: standalone_runner.py
```python
r"""
Standalone Runner for Enterprise Monitoring Agent
Entry point for NSSM (Non-Sucking Service Manager) Windows Service

This script is designed to be compiled with PyInstaller and run as a Windows service
using NSSM instead of win32serviceutil.

Usage:
    nssm.exe install "EnterpriseMonitoringAgent" "C:\Path\To\EnterpriseAgent.exe"
"""

import sys
import logging
import time
from pathlib import Path

# Add project paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir / "src"))
sys.path.insert(0, str(current_dir / "src" / "enterprise"))

# Import path utilities to ensure directories exist
from enterprise.paths import get_config_dir, get_data_dir, get_log_dir

# Configure logging
log_dir = get_log_dir()
log_file = log_dir / "standalone_runner.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# ... (rest of the implementation)
```

**Key Features:**
- ✅ Does NOT use `win32serviceutil`
- ✅ Uses `get_config_dir()` for proper path handling
- ✅ Sets up logging to `C:\ProgramData\EnterpriseMonitoring\logs\`
- ✅ Handles service lifecycle without Windows service API
- ✅ Perfect for NSSM service management

---

### PyInstaller Command
```bash
pyinstaller \
  --name=EnterpriseAgent \
  --onefile \
  --noconsole \
  --hidden-import=win32timezone \
  --hidden-import=win32service \
  --hidden-import=win32serviceutil \
  --hidden-import=win32event \
  --add-data="src/enterprise;enterprise" \
  standalone_runner.py
```

**Output:** `dist\EnterpriseAgent.exe`

---

## STEP 3: Inno Setup Script

### NEW FILE: setup_script.iss

#### Key Features:

**1. Admin Privilege Check** ✅
```pascal
function InitializeSetup(): Boolean;
begin
  if not IsAdminLoggedOn() then
  begin
    MsgBox('This installer requires administrator privileges...', mbError, MB_OK);
    Result := False;
  end;
end;
```

**2. Installation Directory** ✅
```ini
DefaultDirName={commonpf}\Enterprise Monitoring Agent
```
Result: `C:\Program Files\Enterprise Monitoring Agent`

**3. ProgramData Folders** ✅
```ini
[Dirs]
Name: "C:\ProgramData\EnterpriseMonitoring"; Permissions: users-modify
Name: "C:\ProgramData\EnterpriseMonitoring\logs"; Permissions: users-modify
Name: "C:\ProgramData\EnterpriseMonitoring\data"; Permissions: users-modify
Name: "C:\ProgramData\EnterpriseMonitoring\config"; Permissions: users-modify
```

**4. NSSM Service Installation** ✅
```ini
Filename: "{app}\nssm.exe"; 
Parameters: "install ""EnterpriseMonitoringAgent"" ""{app}\EnterpriseAgent.exe""";
```

**5. Service stdout Logging** ✅
```ini
Filename: "{app}\nssm.exe"; 
Parameters: "set ""EnterpriseMonitoringAgent"" AppStdout ""C:\ProgramData\EnterpriseMonitoring\logs\service.log""";
```

**6. Service stderr Logging** ✅
```ini
Filename: "{app}\nssm.exe"; 
Parameters: "set ""EnterpriseMonitoringAgent"" AppStderr ""C:\ProgramData\EnterpriseMonitoring\logs\service_error.log""";
```

**7. Start Service** ✅
```ini
Filename: "{app}\nssm.exe"; 
Parameters: "start ""EnterpriseMonitoringAgent""";
```

**Additional Features:**
- Auto-restart on failure
- Service display name and description
- Clean uninstall (stops and removes service)
- Optional data retention during uninstall

---

## DIRECTORY STRUCTURE

### Before:
```
Clipping-Monitor/
├── src/
│   └── enterprise/
│       ├── config.py (uses Path.home())
│       └── ... (other modules)
```

### After:
```
Clipping-Monitor/
├── standalone_runner.py              ✅ NEW - NSSM service entry point
├── setup_script.iss                  ✅ NEW - Inno Setup installer
├── NSSM_INSTALLER_GUIDE.md           ✅ NEW - Complete documentation
├── IMPLEMENTATION_SUMMARY.md          ✅ NEW - Quick reference
├── .gitignore                        ✅ NEW - Python ignore rules
├── src/
│   └── enterprise/
│       ├── paths.py                  ✅ NEW - Path utilities
│       ├── config.py                 ✅ MODIFIED - Uses get_config_dir()
│       └── ... (other modules)
└── dist/                             (after build)
    ├── EnterpriseAgent.exe           ✅ Compiled service
    └── nssm.exe                      ✅ NSSM executable
```

---

## PATH CHANGES SUMMARY

### Config Path
- **Before:** `C:\Users\<username>\.clipboard_monitor\config.json`
- **After:** `C:\ProgramData\EnterpriseMonitoring\config\config.json` ✅

### Data Path
- **Before:** `C:\Users\<username>\.clipboard_monitor\data\`
- **After:** `C:\ProgramData\EnterpriseMonitoring\data\` ✅

### Log Path
- **Before:** `C:\Users\<username>\.clipboard_monitor\logs\`
- **After:** `C:\ProgramData\EnterpriseMonitoring\logs\` ✅

**Benefit:** All paths are now accessible to Windows service running as SYSTEM.

---

## IMPLEMENTATION STATUS

### ✅ All Requirements Met

1. ✅ **STEP 1:** Config paths fixed to use `get_config_dir()` from `paths.py`
2. ✅ **STEP 2:** `standalone_runner.py` created with PyInstaller command
3. ✅ **STEP 3:** `setup_script.iss` created with all required features

### Next Steps for User

1. Install dependencies: `pip install -r requirements.txt`
2. Build executable: Run the PyInstaller command
3. Download NSSM: Get `nssm.exe` from https://nssm.cc/download
4. Copy NSSM: Place `nssm.exe` in `dist\` folder
5. Compile installer: Run `iscc setup_script.iss`
6. Test installer: Run the generated setup executable
7. Verify service: Check Windows Services for "Enterprise Monitoring Agent"

**For detailed instructions, see `NSSM_INSTALLER_GUIDE.md`**
