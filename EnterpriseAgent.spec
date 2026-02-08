# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for Enterprise Monitoring Agent
Builds a single-file executable for use with NSSM service deployment

Build command:
    pyinstaller EnterpriseAgent.spec

This creates:
    dist/EnterpriseAgent.exe - Single-file executable ready for NSSM deployment
"""

import sys
from pathlib import Path

# Get paths
project_root = Path(SPECPATH)
src_dir = project_root / 'src'
enterprise_dir = src_dir / 'enterprise'

block_cipher = None

# Collect all Python files from src/enterprise as data files
enterprise_data = []
if enterprise_dir.exists():
    for py_file in enterprise_dir.glob('*.py'):
        if py_file.name != '__init__.py':
            enterprise_data.append((str(py_file), 'enterprise'))
    # Include __init__.py if it exists
    init_file = enterprise_dir / '__init__.py'
    if init_file.exists():
        enterprise_data.append((str(init_file), 'enterprise'))

a = Analysis(
    ['standalone_runner.py'],
    pathex=[
        str(src_dir),
        str(enterprise_dir),
    ],
    binaries=[],
    datas=enterprise_data,
    hiddenimports=[
        'win32timezone',
        'win32api',
        'win32con',
        'win32event',
        'win32file',
        'win32gui',
        'win32process',
        'pywintypes',
        'clipboard_monitor',
        'enterprise.app_usage_tracker',
        'enterprise.browser_tracker',
        'enterprise.database_manager',
        'enterprise.keystroke_recorder',
        'enterprise.config',
        'enterprise.paths',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'PIL',
        'cryptography',
        'cryptography.fernet',
        'sqlite3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'setuptools',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EnterpriseAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (runs silently as service)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'resources/icon.ico'
    version_file=None,  # Add version info if needed
)
