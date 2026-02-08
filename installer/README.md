# Installer Directory

This directory contains files needed for building the installer.

## Required Files

### NSSM (Non-Sucking Service Manager)

**Download:** https://nssm.cc/download

**Version:** 2.24 or later (64-bit)

**Steps:**
1. Download `nssm-2.24.zip` from https://nssm.cc/release/nssm-2.24.zip
2. Extract the ZIP file
3. Copy `win64/nssm.exe` to this directory
4. Result: `installer/nssm.exe`

**File size:** Approximately 350 KB

**Purpose:** NSSM wraps the Python executable as a Windows service, providing:
- Auto-start at boot
- Auto-restart on failure
- Log file redirection
- Service control via services.msc

### Why NSSM?

NSSM is:
- ✅ Stable and battle-tested (used by thousands of applications)
- ✅ Small footprint (~350 KB)
- ✅ No installation required (single .exe)
- ✅ Open source (public domain)
- ✅ Works with any executable
- ✅ Configurable via command-line or GUI

### License

NSSM is released to the public domain. You can freely bundle it with your application.

See: https://nssm.cc/licence

---

## Directory Structure

```
installer/
├── README.md          ← This file
├── nssm.exe           ← Place NSSM here (NOT INCLUDED, download separately)
└── output/            ← Generated installers go here (created by Inno Setup)
```

---

## After Downloading NSSM

Once you've placed `nssm.exe` in this directory, you're ready to build the installer:

```bash
# Build the executable first
python build_production.py

# Then build the installer
iscc EnterpriseAgent.iss
```

The installer will be created at:
```
installer/output/EnterpriseAgent-Setup-1.0.0.exe
```

---

## Alternative: Using Pre-Installed NSSM

If NSSM is already installed on the target system, you don't need to bundle it. However, for a professional installer experience, it's recommended to include it so users don't need to install anything separately.

---

## Troubleshooting

**Q: Where is nssm.exe?**
A: You need to download it separately from https://nssm.cc/download

**Q: Which version should I use?**
A: Use the 64-bit version from the `win64` folder in the ZIP file

**Q: Can I use a different service manager?**
A: Yes, but NSSM is recommended for its reliability and ease of use. The Inno Setup script is specifically designed for NSSM.

**Q: Is it legal to bundle NSSM?**
A: Yes, NSSM is public domain software. You can freely bundle it.

---

## More Information

See the complete deployment guide: `PRODUCTION_DEPLOYMENT.md`
