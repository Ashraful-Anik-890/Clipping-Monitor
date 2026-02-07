# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

# Absolute paths
ROOT_DIR = Path(r'D:\Codes\Skillers_Zone_LTD\Clipping-Monitor')
SRC_DIR = ROOT_DIR / 'src'
ENTERPRISE_DIR = SRC_DIR / 'enterprise'
RESOURCES_DIR = ROOT_DIR / 'resources'

# Service executable
service_a = Analysis(
    [r'D:\Codes\Skillers_Zone_LTD\Clipping-Monitor\src\enterprise\service_core.py'],
    pathex=[r'D:\Codes\Skillers_Zone_LTD\Clipping-Monitor\src', r'D:\Codes\Skillers_Zone_LTD\Clipping-Monitor\src\enterprise'],
    binaries=[],
    datas=[
        (str(RESOURCES_DIR), 'resources') if RESOURCES_DIR.exists() else ([], []),
    ],
    hiddenimports=[
        'win32serviceutil',
        'win32service',
        'win32event',
        'servicemanager',
        'win32security',
        'win32api',
        'win32process',
        'win32gui',
        'win32con',
        'pywintypes',
        'psutil',
        'cryptography',
        'cryptography.fernet',
        'sqlite3',
        'pynput',
        'pynput.keyboard',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

service_pyz = PYZ(service_a.pure, service_a.zipped_data, cipher=block_cipher)

service_exe = EXE(
    service_pyz,
    service_a.scripts,
    [],
    exclude_binaries=True,
    name='MonitoringService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# Admin Console executable
admin_a = Analysis(
    [r'D:\Codes\Skillers_Zone_LTD\Clipping-Monitor\src\enterprise\admin_console.py'],
    pathex=[r'D:\Codes\Skillers_Zone_LTD\Clipping-Monitor\src', r'D:\Codes\Skillers_Zone_LTD\Clipping-Monitor\src\enterprise'],
    binaries=[],
    datas=[
        (str(RESOURCES_DIR), 'resources') if RESOURCES_DIR.exists() else ([], []),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        'tkinter.simpledialog',
        'win32security',
        'win32api',
        'win32con',
        'win32serviceutil',
        'cryptography',
        'cryptography.fernet',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

admin_pyz = PYZ(admin_a.pure, admin_a.zipped_data, cipher=block_cipher)

admin_exe = EXE(
    admin_pyz,
    admin_a.scripts,
    [],
    exclude_binaries=True,
    name='AdminConsole',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    uac_admin=True,
    icon=str(RESOURCES_DIR / 'icon.ico') if (RESOURCES_DIR / 'icon.ico').exists() else None,
)

# Collect all
coll = COLLECT(
    service_exe,
    service_a.binaries,
    service_a.zipfiles,
    service_a.datas,
    admin_exe,
    admin_a.binaries,
    admin_a.zipfiles,
    admin_a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='EnterpriseMonitoringAgent',
)
