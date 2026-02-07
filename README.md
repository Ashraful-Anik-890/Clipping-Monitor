# Enterprise Clipping Monitor

A secure, enterprise-grade user activity monitoring agent for Windows. This application monitors clipboard usage, application activity, browser history, and keystrokes for compliance and productivity tracking.

## 🚀 Features

### Core Monitoring
- **Clipboard Monitoring**: Tracks copy/paste operations (text and images).
- **Application Usage**: Logs active window titles and duration.
- **Browser Activity**: Monitors visited websites (Chrome, Edge, Firefox).
- **Keystroke Logging**: Securely records keystrokes (Admin access only).

### Security & Privacy
- **Encryption**: All sensitive data is encrypted using Fernet (AES).
- **Admin Authentication**: Secure login system with PBKDF2 password hashing.
- **UAC Elevation**: Requires administrator privileges for service management.
- **Service Protection**: Runs as a Windows Service (SYSTEM privileges).

### Administrator Console
- **Service Control**: Install, Start, Stop, and Remove the monitoring service.
- **Statistics**: Real-time stats on recording status and storage usage.
- **Export Data**: Export logs to JSON or CSV (Encrypted/Decrypted).
- **Data Security**: Secure "First-Run" password setup system.

---

## 🛠️ Usage

### 1. Installation & First Run
1.  Run the **Admin Console** (`src/enterprise/admin_console.py`).
2.  **First Run Setup**: You will be prompted to create an Administrator Password.
3.  **Login**: Use your newly created password to access the console.

### 2. Setting up the Service
1.  Go to the **Service Control** tab.
2.  Click **"Install Service"** (Blue Button).
    *   *Note: Ensure the service installs successfully (Status: Stopped).*
3.  Click **"Start Service"** (Green Button).
    *   *Status should change to "Running".*

### 3. Monitoring & Exporting
- The service runs in the background.
- Use the **Admin Console** to view statistics or export collected data.
- **Warning**: Decrypted exports contain sensitive plain-text data.

---

## 🚧 Known Issues & Bugs

### 🔴 Critical Bugs
1.  **"Failed to start file not found"**:
    - The "Install Service" button may fail to locate the `service_main.py` file or the executable, leading to a "File not found" error during the `subprocess.run` call.
    - *Workaround*: Run the service installation manually via terminal if the UI fails: `python src/enterprise/service_main.py install`.

2.  **Service Buttons Not Working**:
    - If the service is not properly installed (Error 1060), the "Start", "Stop", and "Export" buttons will fail.
    - *Fix*: Ensure you click "Install Service" first.

3.  **Service Core Path Crashes**:
    - There are reports of "broken paths" in `service_core.py` causing the service to crash immediately after starting log creation. This is likely due to hardcoded paths like `C:/ProgramData/...` conflicting with permissions or environment differences.

### ⚠️ Limitations
- **Unit Testing**: Tests for main files work in terminals, but integration tests within the app flow are incomplete.
- **Restart Required**: Sometimes the console needs a restart to reflect the true service status.

---

## 💻 Development Status

- **OS**: Windows Only.
- **Language**: Python 3.x.
- **Testing**: Unit tests for core logic are passing in terminal environments.
- **Status**: Alpha / Debugging Phase.

---

## 📂 Project Structure

- `src/enterprise/admin_console.py`: Main GUI for management.
- `src/enterprise/service_main.py`: Service entry point.
- `src/enterprise/service_core.py`: Core monitoring logic.
- `src/enterprise/admin_auth.py`: Authentication handler.
