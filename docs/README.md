# Enterprise Monitoring Agent

Professional-grade Windows monitoring software for enterprise deployment.

## Overview

Enterprise Monitoring Agent is a Windows service-based application that monitors user activity including:

- **Clipboard Operations**: Copy and paste events with metadata
- **Application Usage**: Active window tracking with precise timing
- **Browser Activity**: Multi-browser tab and URL tracking
- **Screen Recording**: Optional screen capture (metadata tracking ready)

## Features

- ✅ **Windows Service**: Runs continuously, starts with OS
- ✅ **Admin Protected**: Password-protected admin console with UAC
- ✅ **Encrypted Storage**: SQLite database with Fernet encryption
- ✅ **Multi-Browser Support**: Chrome, Edge, Firefox, Brave, Opera
- ✅ **Professional Installer**: NSIS/MSI packages for deployment
- ✅ **Export Functionality**: JSON and CSV export formats
- ✅ **Enterprise Ready**: Group Policy deployment support

## System Requirements

- **Operating System**: Windows 10 or Windows 11 (64-bit)
- **Privileges**: Administrator rights for installation
- **Disk Space**: Minimum 100MB, recommended 1GB for data
- **Memory**: 100MB RAM minimum
- **Python** (for development): 3.11 or higher

## Quick Start

### For End Users (Installation)

1. Download `EnterpriseMonitoring_1.0.0_Setup.exe`
2. Run installer as Administrator
3. Follow installation wizard
4. Service starts automatically
5. Open Admin Console to configure settings

### For Developers (Setup)

```bash
# 1. Clone repository
git clone <your-repo-url>
cd enterprise-monitoring-agent

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run service (development mode)
python src/service_core.py debug

# 5. Run admin console
python src/admin_console.py
```

## Project Structure

```
enterprise-monitoring-agent/
├── src/
│   ├── service_core.py              # Windows service (main)
│   ├── app_usage_tracker.py         # Application tracking
│   ├── browser_tracker.py           # Browser activity tracking
│   ├── database_manager.py          # SQLite database manager
│   ├── admin_auth.py                # Authentication & security
│   ├── admin_console.py             # Admin UI
│   ├── clipboard_monitor.py         # Clipboard monitoring
│   ├── storage.py                   # Legacy storage (deprecated)
│   ├── config.py                    # Configuration manager
│   ├── permissions.py               # Permission management
│   ├── tray_icon.py                 # System tray icon
│   ├── gui.py                       # Legacy GUI (deprecated)
│   └── error_handler.py             # Error handling
│
├── build/
│   └── build_enterprise.spec        # PyInstaller build spec
│
├── installers/
│   └── installer.nsi                # NSIS installer script
│
├── resources/                       # Icons and images
│   ├── icon.ico
│   ├── header.bmp
│   └── welcome.bmp
│
├── docs/
│   ├── ENTERPRISE_ARCHITECTURE.md
│   ├── IMPLEMENTATION_GUIDE.md
│   ├── DEPLOYMENT_GUIDE.md
│   └── API_REFERENCE.md
│
├── build_deployment.py              # Automated build script
├── requirements.txt                 # Python dependencies
├── LICENSE.txt
└── README.md
```

## Development Workflow

### Phase 1: Service Development (Current)

```bash
# Install dependencies
pip install -r requirements.txt

# Test service locally
python src/service_core.py debug

# Test components individually
python src/app_usage_tracker.py
python src/browser_tracker.py
```

### Phase 2: Building Executables

```bash
# Build all executables
python build_deployment.py --all

# Output: dist/EnterpriseMonitoringAgent/
# - MonitoringService.exe
# - AdminConsole.exe
# - MonitoringTray.exe
```

### Phase 3: Creating Installer

```bash
# Install NSIS from https://nsis.sourceforge.io/

# Build installer
makensis installers/installer.nsi

# Output: EnterpriseMonitoring_1.0.0_Setup.exe
```

### Phase 4: Testing

```bash
# Run tests
pytest tests/

# Test installation
EnterpriseMonitoring_1.0.0_Setup.exe

# Verify service
sc query EnterpriseMonitoringAgent

# Open admin console
"C:\Program Files\Enterprise Monitoring Agent\AdminConsole.exe"
```

## Configuration

### Service Configuration

Location: `C:\ProgramData\EnterpriseMonitoring\config\config.json`

```json
{
  "version": "1.0.0",
  "monitoring": {
    "clipboard": true,
    "applications": true,
    "browser": true,
    "screen_recording": false
  },
  "storage": {
    "encryption_enabled": true,
    "retention_days": 90,
    "max_database_size_mb": 1000
  }
}
```

### Admin Authentication

- Default password generated during installation
- Found in: `C:\Users\<user>\.clipboard_monitor\ADMIN_INITIAL_PASSWORD.txt`
- **IMPORTANT**: Change password immediately after first login

### Database Location

- Path: `C:\ProgramData\EnterpriseMonitoring\data\monitoring.db`
- Encrypted: Yes (Fernet encryption)
- Format: SQLite 3

### Log Files

- Service Log: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
- Admin Log: `C:\ProgramData\EnterpriseMonitoring\logs\admin.log`
- Error Log: `C:\ProgramData\EnterpriseMonitoring\logs\error.log`

## Usage

### Starting/Stopping Service

**Via Admin Console:**
1. Open Admin Console
2. Navigate to "Service Control" tab
3. Click Start/Stop/Restart buttons

**Via Command Line:**
```cmd
# Start service
sc start EnterpriseMonitoringAgent

# Stop service (requires admin)
sc stop EnterpriseMonitoringAgent

# Check status
sc query EnterpriseMonitoringAgent
```

### Exporting Data

**Via Admin Console:**
1. Open Admin Console
2. Navigate to "Export Data" tab
3. Select format (JSON or CSV)
4. Click export button for desired data type

**Programmatically:**
```python
from database_manager import DatabaseManager
from pathlib import Path

db = DatabaseManager(Path('C:/ProgramData/EnterpriseMonitoring/data/monitoring.db'))
db.export_to_json(Path('export.json'))
```

### Changing Admin Password

1. Open Admin Console
2. Navigate to "Security" tab
3. Click "Change Password"
4. Enter new password (minimum 8 characters)
5. Confirm password

## Deployment

### Single Computer Installation

1. Run `EnterpriseMonitoring_1.0.0_Setup.exe` as Administrator
2. Follow installation wizard
3. Service starts automatically
4. Configure via Admin Console

### Enterprise Deployment (Group Policy)

1. Build MSI package:
   ```bash
   python build_deployment.py --msi
   ```

2. Copy MSI to network share:
   ```
   \\server\share\EnterpriseMonitoring_1.0.0.msi
   ```

3. Create GPO:
   - Computer Configuration → Policies → Software Settings
   - Software Installation → New → Package
   - Select MSI file
   - Assign to computer group

4. Computers auto-install on next reboot

### Silent Installation

```cmd
# Silent install
EnterpriseMonitoring_1.0.0_Setup.exe /S

# Silent uninstall
"C:\Program Files\Enterprise Monitoring Agent\Uninstall.exe" /S
```

## Security

### Data Protection

- **Encryption**: All sensitive data encrypted with Fernet (AES-128)
- **Password Hashing**: PBKDF2-SHA256 with 100,000 iterations
- **Access Control**: Admin console requires UAC elevation + password
- **Service Isolation**: Runs as LocalSystem with restricted access

### Privacy Compliance

- Local storage only (no automatic cloud uploads)
- User consent required during installation
- Clear uninstall process
- Full data access for users
- Configurable retention policies

### Best Practices

1. **Change default admin password immediately**
2. **Limit admin access to authorized personnel**
3. **Regular database backups**
4. **Review logs periodically**
5. **Update software regularly**
6. **Monitor disk space usage**

## Troubleshooting

### Service Won't Start

1. Check logs: `C:\ProgramData\EnterpriseMonitoring\logs\service.log`
2. Verify service installation:
   ```cmd
   sc query EnterpriseMonitoringAgent
   ```
3. Reinstall service:
   ```cmd
   "C:\Program Files\Enterprise Monitoring Agent\MonitoringService.exe" remove
   "C:\Program Files\Enterprise Monitoring Agent\MonitoringService.exe" install
   ```

### Admin Console Won't Open

1. Run as Administrator
2. Check UAC settings
3. Verify password file exists
4. Review admin logs

### Database Issues

1. Check disk space
2. Verify encryption key exists
3. Run database optimization:
   ```python
   from database_manager import DatabaseManager
   db = DatabaseManager(...)
   db.optimize_database()
   ```

### High CPU/Memory Usage

1. Check polling intervals in config
2. Review active monitors
3. Check database size
4. Disable unnecessary features

## API Reference

### Database Manager

```python
from database_manager import DatabaseManager
from pathlib import Path

# Initialize
db = DatabaseManager(Path('monitoring.db'), enable_encryption=True)

# Log events
db.log_clipboard_event(event_dict)
db.log_app_usage(event_dict)
db.log_browser_activity(event_dict)

# Query events
events = db.get_events('clipboard_events', limit=100)

# Export data
db.export_to_json(Path('export.json'))
db.export_to_csv(Path('export_dir'))

# Statistics
stats = db.get_statistics()

# Cleanup
db.cleanup_old_data(retention_days=90)
db.optimize_database()
```

### Admin Authentication

```python
from admin_auth import AdminAuthManager
from pathlib import Path

# Initialize
auth = AdminAuthManager(Path('config_dir'))

# Set password
auth.set_admin_password('NewPassword123')

# Verify password
if auth.verify_admin_password('password'):
    print("Authenticated!")

# Check admin status
if auth.is_user_admin():
    print("Running as admin")
```

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8

# Run tests
pytest tests/ -v

# Code formatting
black src/

# Linting
flake8 src/
```

## License

This software is proprietary and licensed for commercial use.

Copyright © 2024 Your Company Name. All rights reserved.

## Support

### Community Support
- GitHub Issues: [Report bugs and request features]
- Documentation: See `docs/` directory

### Commercial Support
- Email: support@yourcompany.com
- Phone: +1-XXX-XXX-XXXX
- Website: https://yourcompany.com/support

### Support Tiers

**Standard** (Included with license)
- Email support
- 48-hour response time
- Software updates

**Priority** (Additional cost)
- Email + Phone support
- 24-hour response time
- Priority bug fixes

**Enterprise** (Custom pricing)
- 24/7 support
- Dedicated account manager
- Custom features
- On-site deployment assistance

## Changelog

### Version 1.0.0 (2024-XX-XX)
- Initial release
- Windows service architecture
- Multi-browser tracking
- SQLite database with encryption
- Admin console with authentication
- NSIS installer
- Export functionality (JSON/CSV)

## Roadmap

### Version 1.1.0 (Planned)
- [ ] Server sync functionality
- [ ] Centralized dashboard
- [ ] Multi-agent management
- [ ] Advanced reporting
- [ ] Email alerts

### Version 2.0.0 (Future)
- [ ] Machine learning insights
- [ ] Productivity analytics
- [ ] Custom integrations
- [ ] Mobile app
- [ ] Real-time monitoring

## Acknowledgments

- PyInstaller team for excellent packaging tools
- NSIS developers for installer framework
- Python community for amazing libraries
- All contributors and testers

---

**Built with ❤️ for enterprise productivity and compliance monitoring**
