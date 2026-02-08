# Installation Guide - Clipping Monitor

This guide will walk you through the complete process of pulling and setting up the Clipping Monitor on your device.

> **⚡ Quick Setup?** For experienced users, check out [QUICK_SETUP.md](QUICK_SETUP.md) for a condensed version.

## Setup Process Overview

```
┌─────────────────────────────────────────────────────────────┐
│  1. Install Prerequisites (Python 3.8+, Git)                │
│                         ↓                                    │
│  2. Clone Repository from GitHub                            │
│                         ↓                                    │
│  3. Create Virtual Environment                              │
│                         ↓                                    │
│  4. Install Dependencies (pip install -r requirements.txt)  │
│                         ↓                                    │
│  5. Run Application as Administrator                        │
│                         ↓                                    │
│  6. Complete First-Time Setup (Create password)             │
│                         ↓                                    │
│  7. Install & Start Windows Service                         │
│                         ↓                                    │
│  ✓ Ready to Monitor! 🎉                                     │
└─────────────────────────────────────────────────────────────┘
```

## Table of Contents
- [Prerequisites](#prerequisites)
- [Installation Steps](#installation-steps)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before you begin, ensure you have the following installed on your Windows device:

### Required Software
1. **Python 3.8 or higher**
   - Download from: https://www.python.org/downloads/
   - ⚠️ **Important**: During installation, check "Add Python to PATH"
   - Verify installation:
     ```cmd
     python --version
     ```

2. **Git** (for cloning the repository)
   - Download from: https://git-scm.com/download/win
   - Verify installation:
     ```cmd
     git --version
     ```

3. **pip** (Python package installer - usually comes with Python)
   - Verify installation:
     ```cmd
     pip --version
     ```

### System Requirements
- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: At least 500MB free space
- **Administrator Privileges**: Required for service installation

---

## Installation Steps

### Step 1: Clone the Repository

Open **Command Prompt** or **PowerShell** and navigate to where you want to install the application:

```cmd
cd %USERPROFILE%\Documents
```

Clone the repository:

```cmd
git clone https://github.com/Ashraful-Anik-890/Clipping-Monitor.git
```

Navigate into the project directory:

```cmd
cd Clipping-Monitor
```

### Step 2: Create a Virtual Environment (Recommended)

Creating a virtual environment isolates the project dependencies:

```cmd
python -m venv venv
```

Activate the virtual environment:

**On Command Prompt:**
```cmd
venv\Scripts\activate
```

**On PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

> **Note**: If you get an error about execution policy in PowerShell, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

You should see `(venv)` at the beginning of your command prompt.

### Step 3: Install Dependencies

Install all required Python packages:

```cmd
pip install -r requirements.txt
```

This will install:
- pywin32 (Windows API Access)
- psutil (System monitoring)
- cryptography (Encryption)
- pystray (System tray icon)
- Pillow (Image processing)
- requests (HTTP requests)
- pynput (Input monitoring)

Wait for all packages to download and install. This may take a few minutes.

### Step 4: Verify Installation

Check that all key modules are available:

```cmd
python -c "import win32com.client, psutil, cryptography, pystray; print('All dependencies installed successfully!')"
```

If you see the success message, you're ready to proceed!

---

## Configuration

### Step 5: Initial Setup

The application requires administrator privileges for certain features. Before running, you may need to:

1. **Check Project Structure**:
   ```cmd
   dir
   ```
   You should see folders like `src`, `docs`, `build`, etc.

2. **Review Configuration** (Optional):
   - Configuration files are typically created on first run
   - Default settings work for most users

---

## Running the Application

### For Enterprise Version (With Service)

If you're using the enterprise version with the monitoring service:

#### Step 6: Run the Admin Console

**Open Command Prompt as Administrator** (Right-click → Run as administrator), then:

```cmd
cd %USERPROFILE%\Documents\Clipping-Monitor
venv\Scripts\activate
python src/enterprise/admin_console.py
```

#### Step 7: First-Time Setup

1. **Set Admin Password**: On first run, you'll be prompted to create an administrator password
2. **Login**: Enter your newly created password
3. **Install Service**: 
   - Go to the "Service Control" tab
   - Click "Install Service" (Blue button)
   - Wait for confirmation
4. **Start Service**:
   - Click "Start Service" (Green button)
   - Status should change to "Running"

### For Standard Version

If you're using the basic clipboard monitor:

```cmd
cd %USERPROFILE%\Documents\Clipping-Monitor
venv\Scripts\activate
python src/clipboard_monitor.py
```

### Running in Background

To run the application in the background:

```cmd
pythonw src/enterprise/admin_console.py
```

The `pythonw` command runs Python scripts without showing a console window.

---

## Troubleshooting

### Common Issues and Solutions

#### Issue 1: "python is not recognized"
**Cause**: Python not in PATH

**Solution**:
1. Reinstall Python and check "Add Python to PATH"
2. Or manually add Python to PATH:
   - Search "Environment Variables" in Windows
   - Edit System PATH
   - Add: `%LOCALAPPDATA%\Programs\Python\Python311` (adjust version as needed)

#### Issue 2: "No module named 'win32com'"
**Cause**: pywin32 not installed correctly

**Solution**:
```cmd
pip install --upgrade pywin32
python venv\Scripts\pywin32_postinstall.py -install
```

#### Issue 3: "Access Denied" when installing service
**Cause**: Not running as Administrator

**Solution**:
1. Close Command Prompt
2. Right-click on Command Prompt
3. Select "Run as administrator"
4. Try again

#### Issue 4: "Failed to start - file not found"
**Cause**: Service can't find the Python script

**Solution**:
1. Check that you're in the correct directory:
   ```cmd
   cd %USERPROFILE%\Documents\Clipping-Monitor
   ```
2. Verify the file exists:
   ```cmd
   dir src\enterprise\service_main.py
   ```
3. Try manual service installation:
   ```cmd
   python src\enterprise\service_main.py install
   ```

#### Issue 5: Virtual environment activation fails in PowerShell
**Cause**: Execution policy restriction

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Issue 6: Import errors after installation
**Cause**: Dependencies not installed in virtual environment

**Solution**:
1. Make sure virtual environment is activated (you should see `(venv)`)
2. Reinstall dependencies:
   ```cmd
   pip install --force-reinstall -r requirements.txt
   ```

### Getting Help

If you encounter issues not covered here:

1. **Check Logs**:
   - Service logs: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
   - Application logs: Usually in your user directory under `.clipboard_monitor`

2. **Review Documentation**:
   - Main README: [README.md](README.md)
   - Quick Start: [docs/QUICKSTART.md](docs/QUICKSTART.md)
   - Enterprise Architecture: [docs/ENTERPRISE_ARCHITECTURE.md](docs/ENTERPRISE_ARCHITECTURE.md)

3. **Report Issues**:
   - Open an issue on GitHub with:
     - Your Windows version
     - Python version
     - Complete error message
     - Steps to reproduce

---

## Next Steps

After successful installation:

1. **Read the Usage Guide**: Check [README.md](README.md) for features and usage
2. **Configure Settings**: Customize monitoring options in the Admin Console
3. **Set Up Autostart**: Configure the service to start automatically with Windows
4. **Review Security**: Change default passwords and configure encryption

---

## Updating the Application

To update to the latest version:

```cmd
cd %USERPROFILE%\Documents\Clipping-Monitor
git pull origin main
venv\Scripts\activate
pip install --upgrade -r requirements.txt
```

If the service is running, stop it before updating, then restart after the update completes.

---

## Uninstalling

To completely remove the application:

1. **Stop and Remove Service** (if installed):
   ```cmd
   python src\enterprise\service_main.py remove
   ```

2. **Deactivate Virtual Environment**:
   ```cmd
   deactivate
   ```

3. **Delete Project Folder**:
   ```cmd
   cd ..
   rmdir /s Clipping-Monitor
   ```

4. **Remove Data** (optional):
   - Delete: `C:\ProgramData\EnterpriseMonitoring\`
   - Delete: `%USERPROFILE%\.clipboard_monitor\`

---

## Quick Reference Commands

```cmd
# Clone repository
git clone https://github.com/Ashraful-Anik-890/Clipping-Monitor.git
cd Clipping-Monitor

# Setup virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application (as Administrator)
python src/enterprise/admin_console.py

# Update application
git pull origin main
pip install --upgrade -r requirements.txt
```

---

**You're all set! 🎉**

The Clipping Monitor is now installed and ready to use on your device.
