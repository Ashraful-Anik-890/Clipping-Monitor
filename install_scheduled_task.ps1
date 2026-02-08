# Install Enterprise Monitoring Agent using Windows Task Scheduler
# This provides an alternative to Windows Services
#
# Advantages:
#   - Easier to configure than Windows services
#   - Can run without user login
#   - Built-in retry and error recovery
#   - No DLL dependency issues
#
# Run as Administrator

param(
    [string]$TaskName = "EnterpriseMonitoringAgent",
    [string]$PythonPath = "",
    [string]$ScriptPath = "",
    [switch]$Hidden = $false
)

Write-Host "="*80 -ForegroundColor Cyan
Write-Host "Enterprise Monitoring Agent - Task Scheduler Installer" -ForegroundColor Cyan
Write-Host "="*80 -ForegroundColor Cyan

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
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

# Use pythonw.exe for hidden execution (no console window)
if ($Hidden) {
    $PythonPath = $PythonPath -replace "python\.exe$", "pythonw.exe"
    if (-not (Test-Path $PythonPath)) {
        Write-Host "WARNING: pythonw.exe not found, using python.exe instead" -ForegroundColor Yellow
        $PythonPath = $PythonPath -replace "pythonw\.exe$", "python.exe"
    } else {
        Write-Host "Using pythonw.exe for hidden execution" -ForegroundColor Green
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
Write-Host "  Task Name:  $TaskName" -ForegroundColor White
Write-Host "  Python:     $PythonPath" -ForegroundColor White
Write-Host "  Script:     $ScriptPath" -ForegroundColor White
Write-Host "  Hidden:     $Hidden" -ForegroundColor White
Write-Host ""

# Check if task already exists
$existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Write-Host "Task '$TaskName' already exists!" -ForegroundColor Yellow
    $response = Read-Host "Do you want to remove and reinstall? (y/n)"
    if ($response -eq 'y') {
        Write-Host "Removing existing task..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Start-Sleep -Seconds 1
    } else {
        Write-Host "Installation cancelled" -ForegroundColor Yellow
        exit 0
    }
}

# Create action
Write-Host "Creating scheduled task..." -ForegroundColor Green
$action = New-ScheduledTaskAction `
    -Execute $PythonPath `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory (Split-Path $ScriptPath -Parent)

# Create trigger (at system startup)
$trigger = New-ScheduledTaskTrigger -AtStartup

# Add additional trigger for recovery (every 5 minutes if not running)
$trigger2 = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5) -RepetitionDuration ([TimeSpan]::MaxValue)

# Create settings
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit ([TimeSpan]::MaxValue) `
    -RunOnlyIfNetworkAvailable:$false

# Create principal (run with highest privileges, even when user not logged in)
$principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest

# Register task
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger,$trigger2 `
        -Settings $settings `
        -Principal $principal `
        -Description "Enterprise Activity Monitoring Agent - Monitors clipboard, applications, browser activity, and keystrokes" `
        -ErrorAction Stop | Out-Null
    
    Write-Host "Task registered successfully!" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to register task: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Task installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Task Details:" -ForegroundColor Cyan
Write-Host "  - Starts at system boot" -ForegroundColor White
Write-Host "  - Runs as SYSTEM account (works without user login)" -ForegroundColor White
Write-Host "  - Automatically restarts if it stops" -ForegroundColor White
Write-Host "  - Checks every 5 minutes to ensure it's running" -ForegroundColor White
Write-Host ""
Write-Host "Management Commands:" -ForegroundColor Cyan
Write-Host "  Start now:     " -NoNewline; Write-Host "Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
Write-Host "  Stop:          " -NoNewline; Write-Host "Stop-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Yellow
Write-Host "  View status:   " -NoNewline; Write-Host "Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo" -ForegroundColor Yellow
Write-Host "  Remove:        " -NoNewline; Write-Host "Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor Yellow
Write-Host "  View logs:     " -NoNewline; Write-Host "type `$env:PROGRAMDATA\EnterpriseMonitoring\logs\standalone_*.log" -ForegroundColor Yellow
Write-Host ""

# Ask if user wants to start now
$startNow = Read-Host "Start task now? (y/n)"
if ($startNow -eq 'y') {
    Write-Host "Starting task..." -ForegroundColor Green
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    
    $taskInfo = Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo
    Write-Host "Task status: $($taskInfo.LastTaskResult)" -ForegroundColor $(if ($taskInfo.LastTaskResult -eq 0) { "Green" } else { "Yellow" })
    
    if ($taskInfo.LastTaskResult -ne 0) {
        Write-Host "Check logs for details:" -ForegroundColor Yellow
        Write-Host "  $env:PROGRAMDATA\EnterpriseMonitoring\logs\" -ForegroundColor Yellow
    } else {
        Write-Host "Task started successfully!" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "TIP: To verify it's running after reboot:" -ForegroundColor Cyan
Write-Host "  Get-ScheduledTask -TaskName '$TaskName' | Get-ScheduledTaskInfo" -ForegroundColor Yellow
