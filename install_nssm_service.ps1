# Install Enterprise Monitoring Agent using NSSM
# NSSM = Non-Sucking Service Manager - Much more reliable than pywin32 services
#
# Prerequisites:
#   1. Download NSSM from https://nssm.cc/download
#   2. Extract nssm.exe to a folder (e.g., C:\Tools\nssm\)
#   3. Run this script as Administrator

param(
    [string]$NssmPath = "C:\Tools\nssm\nssm.exe",
    [string]$ServiceName = "EnterpriseMonitoringAgent",
    [string]$PythonPath = "",
    [string]$ScriptPath = ""
)

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "Enterprise Monitoring Agent - NSSM Service Installer" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Find NSSM
if (-not (Test-Path $NssmPath)) {
    Write-Host "NSSM not found at: $NssmPath" -ForegroundColor Yellow
    Write-Host "Searching for nssm.exe..." -ForegroundColor Yellow
    
    $nssmLocations = @(
        "C:\Tools\nssm\nssm.exe",
        "C:\Program Files\nssm\nssm.exe",
        "C:\nssm\nssm.exe",
        "$PSScriptRoot\nssm.exe"
    )
    
    foreach ($loc in $nssmLocations) {
        if (Test-Path $loc) {
            $NssmPath = $loc
            Write-Host "Found NSSM at: $NssmPath" -ForegroundColor Green
            break
        }
    }
    
    if (-not (Test-Path $NssmPath)) {
        Write-Host ""
        Write-Host "NSSM not found! Please download it:" -ForegroundColor Red
        Write-Host "  1. Go to https://nssm.cc/download" -ForegroundColor Yellow
        Write-Host "  2. Download nssm-2.24.zip (or latest)" -ForegroundColor Yellow
        Write-Host "  3. Extract to C:\Tools\nssm\" -ForegroundColor Yellow
        Write-Host "  4. Run this script again" -ForegroundColor Yellow
        exit 1
    }
}

# Find Python
if ($PythonPath -eq "") {
    Write-Host "Detecting Python installation..." -ForegroundColor Yellow
    
    $pythonCommands = @("python", "python3", "py")
    foreach ($cmd in $pythonCommands) {
        try {
            $pythonExe = (Get-Command $cmd -ErrorAction SilentlyContinue).Source
            if ($pythonExe) {
                $PythonPath = $pythonExe
                Write-Host "Found Python at: $PythonPath" -ForegroundColor Green
                break
            }
        } catch {}
    }
    
    if ($PythonPath -eq "") {
        Write-Host "ERROR: Python not found in PATH!" -ForegroundColor Red
        Write-Host "Please specify Python path using -PythonPath parameter" -ForegroundColor Yellow
        exit 1
    }
}

# Find script
if ($ScriptPath -eq "") {
    $ScriptPath = Join-Path $PSScriptRoot "standalone_runner.py"
}

if (-not (Test-Path $ScriptPath)) {
    Write-Host "ERROR: Script not found at: $ScriptPath" -ForegroundColor Red
    Write-Host "Please specify script path using -ScriptPath parameter" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  NSSM Path:     $NssmPath" -ForegroundColor White
Write-Host "  Service Name:  $ServiceName" -ForegroundColor White
Write-Host "  Python:        $PythonPath" -ForegroundColor White
Write-Host "  Script:        $ScriptPath" -ForegroundColor White
Write-Host ""

# Check if service already exists
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "Service '$ServiceName' already exists!" -ForegroundColor Yellow
    $response = Read-Host "Do you want to remove and reinstall? (y/n)"
    if ($response -eq 'y') {
        Write-Host "Stopping service..." -ForegroundColor Yellow
        & $NssmPath stop $ServiceName 2>&1 | Out-Null
        Start-Sleep -Seconds 2
        
        Write-Host "Removing service..." -ForegroundColor Yellow
        & $NssmPath remove $ServiceName confirm
        Start-Sleep -Seconds 2
    } else {
        Write-Host "Installation cancelled" -ForegroundColor Yellow
        exit 0
    }
}

# Install service
Write-Host "Installing service..." -ForegroundColor Green
& $NssmPath install $ServiceName $PythonPath $ScriptPath

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Service installation failed!" -ForegroundColor Red
    exit 1
}

# Configure service
Write-Host "Configuring service..." -ForegroundColor Green

# Set display name and description
& $NssmPath set $ServiceName DisplayName "Enterprise Activity Monitoring Service"
& $NssmPath set $ServiceName Description "Monitors clipboard, applications, browser activity, and keystrokes for enterprise compliance"

# Set working directory to script location
$workingDir = Split-Path $ScriptPath -Parent
& $NssmPath set $ServiceName AppDirectory $workingDir

# Configure startup
& $NssmPath set $ServiceName Start SERVICE_AUTO_START

# Configure restart behavior
& $NssmPath set $ServiceName AppExit Default Restart
& $NssmPath set $ServiceName AppRestartDelay 5000  # 5 seconds

# Configure output redirection (for debugging)
$logDir = "$env:PROGRAMDATA\EnterpriseMonitoring\logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

& $NssmPath set $ServiceName AppStdout "$logDir\nssm_stdout.log"
& $NssmPath set $ServiceName AppStderr "$logDir\nssm_stderr.log"
& $NssmPath set $ServiceName AppStdoutCreationDisposition 4  # Append
& $NssmPath set $ServiceName AppStderrCreationDisposition 4  # Append

# Set process priority (optional - normal priority)
& $NssmPath set $ServiceName AppPriority NORMAL_PRIORITY_CLASS

Write-Host ""
Write-Host "Service installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start service:  " -NoNewline; Write-Host "net start $ServiceName" -ForegroundColor Yellow
Write-Host "  2. Check status:   " -NoNewline; Write-Host "sc query $ServiceName" -ForegroundColor Yellow
Write-Host "  3. View logs:      " -NoNewline; Write-Host "type $logDir\standalone_*.log" -ForegroundColor Yellow
Write-Host "  4. Stop service:   " -NoNewline; Write-Host "net stop $ServiceName" -ForegroundColor Yellow
Write-Host "  5. Remove service: " -NoNewline; Write-Host "nssm remove $ServiceName confirm" -ForegroundColor Yellow
Write-Host ""

# Ask if user wants to start now
$startNow = Read-Host "Start service now? (y/n)"
if ($startNow -eq 'y') {
    Write-Host "Starting service..." -ForegroundColor Green
    & $NssmPath start $ServiceName
    Start-Sleep -Seconds 3
    
    $status = & $NssmPath status $ServiceName
    if ($status -eq "SERVICE_RUNNING") {
        Write-Host "Service started successfully!" -ForegroundColor Green
    } else {
        Write-Host "Service status: $status" -ForegroundColor Yellow
        Write-Host "Check logs at: $logDir" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
