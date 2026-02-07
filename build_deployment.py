"""
Automated Build and Deployment Script - CORRECTED VERSION
Enterprise Monitoring Agent

FIXES:
1. Absolute paths for PyInstaller spec
2. Proper path resolution
3. Better error handling
"""

import sys
import os
import shutil
import subprocess
import argparse
from pathlib import Path
import json
from datetime import datetime


class BuildConfig:
    """Build configuration and paths"""
    
    # Version information
    VERSION = "1.0.0"
    COMPANY = "Skillers Zone LTD"
    PRODUCT_NAME = "Enterprise Monitoring Agent"
    
    # Paths - Use absolute paths
    ROOT_DIR = Path(__file__).parent.absolute()
    SRC_DIR = ROOT_DIR / "src"
    ENTERPRISE_DIR = SRC_DIR / "enterprise"
    BUILD_DIR = ROOT_DIR / "build"
    DIST_DIR = ROOT_DIR / "dist"
    INSTALLER_DIR = ROOT_DIR / "installer"
    RESOURCES_DIR = ROOT_DIR / "resources"
    
    # Output paths
    OUTPUT_DIR = ROOT_DIR / "output"
    PACKAGE_DIR = OUTPUT_DIR / f"EnterpriseMonitoring-{VERSION}"
    
    # Executable names
    SERVICE_EXE = "MonitoringService.exe"
    ADMIN_EXE = "AdminConsole.exe"
    
    # Installer output
    SETUP_EXE = OUTPUT_DIR / f"EnterpriseMonitoring_{VERSION}_Setup.exe"
    MSI_FILE = OUTPUT_DIR / f"EnterpriseMonitoring_{VERSION}.msi"


class BuildLogger:
    """Simple build logger"""
    
    @staticmethod
    def info(message):
        print(f"[INFO] {message}")
    
    @staticmethod
    def success(message):
        print(f"[SUCCESS] ✓ {message}")
    
    @staticmethod
    def error(message):
        print(f"[ERROR] ✗ {message}")
    
    @staticmethod
    def warning(message):
        print(f"[WARNING] ! {message}")
    
    @staticmethod
    def section(message):
        print(f"\n{'='*70}")
        print(f"  {message}")
        print(f"{'='*70}\n")


class EnterpriseBuilder:
    """Main build orchestrator"""
    
    def __init__(self, config: BuildConfig):
        self.config = config
        self.logger = BuildLogger()
    
    def clean_build_artifacts(self):
        """Clean all build artifacts"""
        self.logger.section("Cleaning Build Artifacts")
        
        dirs_to_clean = [
            self.config.BUILD_DIR,
            self.config.DIST_DIR,
            self.config.OUTPUT_DIR,
        ]
        
        for directory in dirs_to_clean:
            if directory.exists():
                self.logger.info(f"Removing {directory}")
                shutil.rmtree(directory)
                self.logger.success(f"Cleaned {directory}")
        
        self.logger.success("Build artifacts cleaned")
    
    def build_executables(self):
        """Build all executables using PyInstaller"""
        self.logger.section("Building Executables")
        
        # Verify source files exist
        service_py = self.config.ENTERPRISE_DIR / "service_core.py"
        admin_py = self.config.ENTERPRISE_DIR / "admin_console.py"
        
        if not service_py.exists():
            self.logger.error(f"Service source not found: {service_py}")
            return False
        
        if not admin_py.exists():
            self.logger.error(f"Admin console source not found: {admin_py}")
            return False
        
        self.logger.info(f"Service source: {service_py}")
        self.logger.info(f"Admin source: {admin_py}")
        
        # Create PyInstaller spec file dynamically
        spec_content = self._generate_pyinstaller_spec()
        spec_file = self.config.BUILD_DIR / "enterprise.spec"
        
        self.config.BUILD_DIR.mkdir(parents=True, exist_ok=True)
        spec_file.write_text(spec_content, encoding='utf-8')
        
        self.logger.info(f"Generated spec file: {spec_file}")
        
        # Run PyInstaller
        try:
            self.logger.info("Running PyInstaller...")
            
            cmd = [
                sys.executable, "-m", "PyInstaller", 
                "--clean", 
                "--noconfirm", 
                str(spec_file)
            ]
            
            self.logger.info(f"Command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                cwd=str(self.config.ROOT_DIR)
            )
            
            self.logger.success("Executables built successfully")
            print(result.stdout)
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error("PyInstaller failed!")
            print(f"STDOUT:\n{e.stdout}")
            print(f"STDERR:\n{e.stderr}")
            return False
    
    def _generate_pyinstaller_spec(self):
        """Generate PyInstaller spec file with absolute paths"""
        
        # Get absolute paths
        service_script = str(self.config.ENTERPRISE_DIR / "service_core.py")
        admin_script = str(self.config.ENTERPRISE_DIR / "admin_console.py")
        src_dir = str(self.config.SRC_DIR)
        enterprise_dir = str(self.config.ENTERPRISE_DIR)
        resources_dir = str(self.config.RESOURCES_DIR)
        
        return f'''# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

block_cipher = None

# Absolute paths
ROOT_DIR = Path(r'{self.config.ROOT_DIR}')
SRC_DIR = ROOT_DIR / 'src'
ENTERPRISE_DIR = SRC_DIR / 'enterprise'
RESOURCES_DIR = ROOT_DIR / 'resources'

# Service executable
service_a = Analysis(
    [r'{service_script}'],
    pathex=[r'{src_dir}', r'{enterprise_dir}'],
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
    hooksconfig={{}},
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
    [r'{admin_script}'],
    pathex=[r'{src_dir}', r'{enterprise_dir}'],
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
    hooksconfig={{}},
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
'''
    
    def create_deployment_package(self):
        """Create final deployment package"""
        self.logger.section("Creating Deployment Package")
        
        # Create package directory
        self.config.PACKAGE_DIR.mkdir(parents=True, exist_ok=True)
        
        # Copy executables
        dist_source = self.config.DIST_DIR / "EnterpriseMonitoringAgent"
        if dist_source.exists():
            shutil.copytree(
                dist_source,
                self.config.PACKAGE_DIR / "bin",
                dirs_exist_ok=True
            )
            self.logger.success("Copied executables to package")
        else:
            self.logger.warning(f"Distribution directory not found: {dist_source}")
        
        # Create version info
        version_info = {
            "version": self.config.VERSION,
            "build_date": datetime.now().isoformat(),
            "product": self.config.PRODUCT_NAME,
            "company": self.config.COMPANY,
        }
        
        version_file = self.config.PACKAGE_DIR / "version.json"
        version_file.write_text(json.dumps(version_info, indent=2))
        
        self.logger.success(f"Deployment package created: {self.config.PACKAGE_DIR}")


def main():
    """Main build orchestration"""
    
    parser = argparse.ArgumentParser(
        description="Build Enterprise Monitoring Agent"
    )
    
    parser.add_argument(
        '--clean',
        action='store_true',
        help='Clean build artifacts before building'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Build everything'
    )
    
    args = parser.parse_args()
    
    # Initialize builder
    config = BuildConfig()
    builder = EnterpriseBuilder(config)
    
    logger = BuildLogger()
    logger.section(f"Building {config.PRODUCT_NAME} v{config.VERSION}")
    
    # Show paths
    logger.info(f"Root: {config.ROOT_DIR}")
    logger.info(f"Source: {config.SRC_DIR}")
    logger.info(f"Enterprise: {config.ENTERPRISE_DIR}")
    
    # Clean if requested
    if args.clean or args.all:
        builder.clean_build_artifacts()
    
    # Build executables
    if not builder.build_executables():
        logger.error("Build failed!")
        return 1
    
    # Create deployment package
    builder.create_deployment_package()
    
    logger.section("Build Complete!")
    logger.success(f"Output directory: {config.OUTPUT_DIR}")
    logger.success(f"Deployment package: {config.PACKAGE_DIR}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())