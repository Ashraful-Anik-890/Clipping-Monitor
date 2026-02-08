# Quick Setup Guide - Clipping Monitor

## 🚀 Fast Track Installation (5 minutes)

### Prerequisites
✅ Windows 10/11 (64-bit)  
✅ Python 3.8+ installed with PATH configured  
✅ Git installed  
✅ Administrator access  

### Installation Commands

```cmd
# 1. Open Command Prompt and navigate to your preferred directory
cd %USERPROFILE%\Documents

# 2. Clone repository
git clone https://github.com/Ashraful-Anik-890/Clipping-Monitor.git
cd Clipping-Monitor

# 3. Setup virtual environment
python -m venv venv
venv\Scripts\activate

# 4. Install dependencies (may take 2-3 minutes)
pip install -r requirements.txt

# 5. Run the application (as Administrator)
# Right-click Command Prompt -> Run as Administrator
python src/enterprise/admin_console.py
```

### First Run Setup
1. **Create Admin Password** when prompted
2. **Login** with your password
3. Click **"Install Service"** (Blue button)
4. Click **"Start Service"** (Green button)
5. ✅ Done! Service is now running

---

## 🔧 Common Commands

```cmd
# Activate virtual environment
venv\Scripts\activate

# Run admin console
python src/enterprise/admin_console.py

# Run basic clipboard monitor
python src/clipboard_monitor.py

# Update to latest version
git pull origin main
pip install --upgrade -r requirements.txt

# Deactivate virtual environment
deactivate
```

---

## ❓ Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| "python is not recognized" | Add Python to PATH during installation |
| "No module named 'win32com'" | Run: `pip install --upgrade pywin32` |
| "Access Denied" | Run Command Prompt as Administrator |
| PowerShell script error | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |

---

## 📚 Full Documentation

- **Detailed Installation**: [INSTALLATION.md](INSTALLATION.md)
- **Features & Usage**: [README.md](README.md)
- **Quick Start Guide**: [docs/QUICKSTART.md](docs/QUICKSTART.md)

---

## 🆘 Need Help?

1. Check full [Installation Guide](INSTALLATION.md)
2. Review [Troubleshooting Section](INSTALLATION.md#troubleshooting)
3. Open an issue on GitHub

**You're ready to go! 🎉**
