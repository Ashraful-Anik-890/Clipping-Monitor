"""
Build Script for Enterprise Monitoring Agent
Creates single-file executable using PyInstaller

Usage:
    python build_production.py

Output:
    dist/EnterpriseAgent.exe - Ready for NSSM deployment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    print("="*80)
    print("Building Enterprise Monitoring Agent")
    print("="*80)
    
    # Check if PyInstaller is installed
    try:
        import PyInstaller
        print(f"✓ PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("✗ PyInstaller not found!")
        print("  Install it with: pip install pyinstaller")
        return 1
    
    # Get project root
    project_root = Path(__file__).parent.absolute()
    spec_file = project_root / "EnterpriseAgent.spec"
    
    if not spec_file.exists():
        print(f"✗ Spec file not found: {spec_file}")
        return 1
    
    print(f"✓ Using spec file: {spec_file}")
    
    # Clean previous builds
    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    
    if build_dir.exists():
        print(f"  Cleaning {build_dir}")
        shutil.rmtree(build_dir)
    
    if dist_dir.exists():
        exe_path = dist_dir / "EnterpriseAgent.exe"
        if exe_path.exists():
            print(f"  Removing old {exe_path}")
            exe_path.unlink()
    
    # Build the executable
    print("\nBuilding executable...")
    print("-"*80)
    
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        str(spec_file),
        "--clean",
        "--noconfirm"
    ]
    
    print(f"Command: {' '.join(cmd)}")
    print("-"*80)
    
    result = subprocess.run(cmd, cwd=project_root)
    
    if result.returncode != 0:
        print("\n✗ Build failed!")
        return 1
    
    # Check if executable was created
    exe_path = dist_dir / "EnterpriseAgent.exe"
    if not exe_path.exists():
        print(f"\n✗ Executable not found: {exe_path}")
        return 1
    
    # Get file size
    size_mb = exe_path.stat().st_size / (1024 * 1024)
    
    print("\n" + "="*80)
    print("✓ Build successful!")
    print("="*80)
    print(f"  Executable: {exe_path}")
    print(f"  Size: {size_mb:.2f} MB")
    print("\nNext steps:")
    print("  1. Test the executable: dist\\EnterpriseAgent.exe")
    print("  2. Build installer: Run Inno Setup with EnterpriseAgent.iss")
    print("  3. Distribute: Share the installer with users")
    print("="*80)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
