# -*- mode: python ; coding: utf-8 -*-
"""
Enhanced Build Specification for Clipboard Monitor with Screen Recording

Build command:
    pyinstaller build_enhanced.spec

Output:
    dist/ClipboardMonitor.exe (~80-100MB with all dependencies)
"""

import sys
from pathlib import Path

block_cipher = None

# Get the source directory
src_path = Path('src').absolute()

# Analysis - collect all modules
a = Analysis(
    [str(src_path / 'main_enhanced.py')],
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        # Include documentation
        ('README.md', '.'),
        ('LICENSE', '.'),
        ('QUICKSTART.md', 'docs'),
    ],
    hiddenimports=[
        # Windows API
        'win32clipboard',
        'win32gui',
        'win32con',
        'win32process',
        'win32api',
        'win32event',
        'win32file',
        'win32com.client',
        'pywintypes',
        
        # GUI components
        'pystray._win32',
        'PIL._tkinter_finder',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.filedialog',
        'tkinter.messagebox',
        
        # Screen recording
        'cv2',
        'mss',
        'mss.windows',
        'numpy',
        'numpy.core._multiarray_umath',
        
        # Database
        'sqlite3',
        
        # Encryption
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat.primitives.ciphers',
        
        # System utilities
        'psutil',
        'queue',
        'threading',
        'logging.handlers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages to reduce size
        'matplotlib',
        'scipy',
        'pandas',
        'tensorflow',
        'torch',
        'pytest',
        'IPython',
        'jupyter',
        'notebook',
        'sympy',
        'sklearn',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Create PYZ archive
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Build executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ClipboardMonitor',
    debug=False,  # Set to True for debugging
    bootloader_ignore_signals=False,
    strip=False,  # Don't strip symbols
    upx=True,  # Compress with UPX
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window (set to True for debugging)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if Path('assets/icon.ico').exists() else None,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)

# Optional: Create a debug build as well
if '--debug' in sys.argv:
    exe_debug = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name='ClipboardMonitor_Debug',
        debug=True,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,  # No compression for debug
        runtime_tmpdir=None,
        console=True,  # Show console for debugging
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
