"""
Automated Build and Deployment Script - FIXED VERSION
Enterprise Monitoring Agent

This script automates the entire build process from source code to
deployable installer package.

Usage:
    python build_deployment.py [options]

Options:
    --clean         Clean all build artifacts before building
    --test          Run tests before building
    --sign          Sign executables (requires certificate)
    --msi           Build MSI installer (requires WiX)
    --all           Build everything (recommended)
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
    
    # Paths - FIXED
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
    TRAY_EXE = "MonitoringTray.exe"
    
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
    
    def run_tests(self):
        """Run test suite"""
        self.logger.section("Running Tests")
        
        test_dir = self.config.ROOT_DIR / "tests"
        
        if not test_dir.exists():
            self.logger.warning("No tests directory found, skipping tests")
            return True
        
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", str(test_dir), "-v"],
                check=True,
                capture_output=True,
                text=True
            )
            
            self.logger.success("All tests passed")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error("Tests failed!")
            print(e.stdout)
            print(e.stderr)
            return False
    
    def build_executables(self):
        """Build all executables using PyInstaller"""
        self.logger.section("Building Executables")
        
        # Create PyInstaller spec file dynamically
        spec_content = self._generate_pyinstaller_spec()
        spec_file = self.config.BUILD_DIR / "enterprise.spec"
        
        self.config.BUILD_DIR.mkdir(parents=True, exist_ok=True)
        spec_file.write_text(spec_content, encoding='utf-8')
        
        self.logger.info(f"Generated spec file: {spec_file}")
        
        # Run PyInstaller
        try:
            self.logger.info("Running PyInstaller...")
            
            # FIX: Use sys.executable to run PyInstaller as a module
            cmd = [
                sys.executable, "-m", "PyInstaller", 
                "--clean", 
                "--noconfirm", 
                str(spec_file)
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                cwd=str(self.config.ROOT_DIR)
            )
            
            self.logger.success("Executables built successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error("PyInstaller failed!")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return False
    
    def _generate_pyinstaller_spec(self):
        """Generate PyInstaller spec file content - FIXED PATHS"""
        return f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Service executable
service_a = Analysis(
    ['src/enterprise/service_core.py'],
    pathex=['src', 'src/enterprise'],
    binaries=[],
    datas=[
        ('resources', 'resources') if Path('resources').exists() else ([], []),
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
    name='{self.config.SERVICE_EXE.replace(".exe", "")}',
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
    ['src/enterprise/admin_console.py'],
    pathex=['src', 'src/enterprise'],
    binaries=[],
    datas=[
        ('resources', 'resources') if Path('resources').exists() else ([], []),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
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
    name='{self.config.ADMIN_EXE.replace(".exe", "")}',
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
    icon='resources/icon.ico' if Path('resources/icon.ico').exists() else None,
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
    
    def sign_executables(self, cert_path: str = None, password: str = None):
        """Sign executables with code signing certificate"""
        self.logger.section("Signing Executables")
        
        if not cert_path:
            self.logger.warning("No certificate path provided, skipping signing")
            return True
        
        executables = [
            self.config.DIST_DIR / "EnterpriseMonitoringAgent" / self.config.SERVICE_EXE,
            self.config.DIST_DIR / "EnterpriseMonitoringAgent" / self.config.ADMIN_EXE,
        ]
        
        for exe in executables:
            if not exe.exists():
                self.logger.error(f"Executable not found: {exe}")
                continue
            
            try:
                # Use signtool.exe from Windows SDK
                cmd = [
                    "signtool.exe",
                    "sign",
                    "/f", cert_path,
                    "/p", password if password else "",
                    "/t", "http://timestamp.digicert.com",
                    "/v",
                    str(exe)
                ]
                
                subprocess.run(cmd, check=True, capture_output=True)
                self.logger.success(f"Signed: {exe.name}")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Failed to sign {exe.name}")
                return False
        
        self.logger.success("All executables signed")
        return True
    
    def build_nsis_installer(self):
        """Build NSIS installer"""
        self.logger.section("Building NSIS Installer")
        
        nsis_script = self.config.INSTALLER_DIR / "installer.nsi"
        
        if not nsis_script.exists():
            self.logger.error(f"NSIS script not found: {nsis_script}")
            return False
        
        try:
            # Run NSIS
            cmd = [
                "makensis.exe",
                f"/DVERSION={self.config.VERSION}",
                f"/DOUTFILE={self.config.SETUP_EXE}",
                str(nsis_script)
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            self.logger.success(f"Installer created: {self.config.SETUP_EXE}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error("NSIS build failed!")
            print(e.stdout)
            print(e.stderr)
            return False
        except FileNotFoundError:
            self.logger.error("NSIS not found. Install from https://nsis.sourceforge.io/")
            return False
    
    def build_msi_installer(self):
        """Build MSI installer using WiX"""
        self.logger.section("Building MSI Installer")
        
        wix_script = self.config.INSTALLER_DIR / "wix_installer.wxs"
        
        if not wix_script.exists():
            self.logger.warning(f"WiX script not found: {wix_script}, skipping MSI build")
            return True
        
        try:
            # Compile WiX
            wixobj = self.config.BUILD_DIR / "installer.wixobj"
            
            cmd_compile = [
                "candle.exe",
                "-out", str(wixobj),
                str(wix_script)
            ]
            
            subprocess.run(cmd_compile, check=True, capture_output=True)
            
            # Link to MSI
            cmd_link = [
                "light.exe",
                "-out", str(self.config.MSI_FILE),
                str(wixobj)
            ]
            
            subprocess.run(cmd_link, check=True, capture_output=True)
            
            self.logger.success(f"MSI created: {self.config.MSI_FILE}")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error("WiX build failed!")
            return False
        except FileNotFoundError:
            self.logger.warning("WiX Toolset not found, skipping MSI build")
            return True
    
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
        
        # Copy installers
        if self.config.SETUP_EXE.exists():
            shutil.copy2(
                self.config.SETUP_EXE,
                self.config.PACKAGE_DIR / self.config.SETUP_EXE.name
            )
            self.logger.success("Copied NSIS installer to package")
        
        if self.config.MSI_FILE.exists():
            shutil.copy2(
                self.config.MSI_FILE,
                self.config.PACKAGE_DIR / self.config.MSI_FILE.name
            )
            self.logger.success("Copied MSI installer to package")
        
        # Copy documentation
        docs_to_copy = [
            "README.md",
            "LICENSE",
        ]
        
        docs_dir = self.config.PACKAGE_DIR / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        for doc in docs_to_copy:
            src = self.config.ROOT_DIR / doc
            if src.exists():
                shutil.copy2(src, docs_dir / doc)
        
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
    
    def generate_checksums(self):
        """Generate SHA-256 checksums for verification"""
        self.logger.section("Generating Checksums")
        
        import hashlib
        
        files_to_hash = []
        
        if self.config.SETUP_EXE.exists():
            files_to_hash.append(self.config.SETUP_EXE)
        
        if self.config.MSI_FILE.exists():
            files_to_hash.append(self.config.MSI_FILE)
        
        checksums = {}
        
        for filepath in files_to_hash:
            sha256 = hashlib.sha256()
            
            with open(filepath, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b''):
                    sha256.update(chunk)
            
            checksums[filepath.name] = sha256.hexdigest()
            self.logger.info(f"{filepath.name}: {sha256.hexdigest()}")
        
        # Save checksums
        checksum_file = self.config.OUTPUT_DIR / "checksums.txt"
        with open(checksum_file, 'w') as f:
            for filename, checksum in checksums.items():
                f.write(f"{checksum}  {filename}\n")
        
        self.logger.success(f"Checksums saved to {checksum_file}")


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
        '--test',
        action='store_true',
        help='Run tests before building'
    )
    
    parser.add_argument(
        '--sign',
        action='store_true',
        help='Sign executables (requires certificate)'
    )
    
    parser.add_argument(
        '--cert',
        type=str,
        help='Path to code signing certificate'
    )
    
    parser.add_argument(
        '--cert-password',
        type=str,
        help='Certificate password'
    )
    
    parser.add_argument(
        '--msi',
        action='store_true',
        help='Build MSI installer (requires WiX)'
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
    
    # Clean if requested
    if args.clean or args.all:
        builder.clean_build_artifacts()
    
    # Run tests if requested
    if args.test or args.all:
        if not builder.run_tests():
            logger.error("Tests failed, aborting build")
            return 1
    
    # Build executables
    if not builder.build_executables():
        logger.error("Build failed!")
        return 1
    
    # Sign executables if requested
    if args.sign or args.all:
        if not builder.sign_executables(args.cert, args.cert_password):
            logger.warning("Signing failed, continuing anyway")
    
    # Build NSIS installer
    # Commented out until NSIS is installed
    # if not builder.build_nsis_installer():
    #     logger.error("Installer build failed!")
    #     return 1
    
    # Build MSI if requested
    if args.msi or args.all:
        builder.build_msi_installer()
    
    # Create deployment package
    builder.create_deployment_package()
    
    # Generate checksums
    # builder.generate_checksums()
    
    logger.section("Build Complete!")
    logger.success(f"Output directory: {config.OUTPUT_DIR}")
    logger.success(f"Deployment package: {config.PACKAGE_DIR}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())