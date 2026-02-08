; Inno Setup Script for Enterprise Monitoring Agent
; Production-grade installer with NSSM service integration
; Similar to Grammarly's installer approach
;
; Prerequisites:
;   1. Build EnterpriseAgent.exe using: python build_production.py
;   2. Download nssm.exe (64-bit) from https://nssm.cc/download
;   3. Place nssm.exe in the installer/ directory
;
; Build installer:
;   iscc EnterpriseAgent.iss

#define MyAppName "Enterprise Monitoring Agent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Enterprise Solutions"
#define MyAppURL "https://github.com/YourCompany/Enterprise-Monitoring"
#define MyAppExeName "EnterpriseAgent.exe"
#define MyAppServiceName "EnterpriseMonitoringAgent"
#define MyAppServiceDisplayName "Enterprise Activity Monitoring Service"
#define MyAppServiceDescription "Monitors clipboard, applications, and browser activity for enterprise compliance"

[Setup]
; Basic app info
AppId={{A7B8C9D0-1E2F-3A4B-5C6D-7E8F9A0B1C2D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
AppVerName={#MyAppName} {#MyAppVersion}
AppCopyright=Copyright (C) 2026 {#MyAppPublisher}

; Installation directories
DefaultDirName={commonpf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Require administrator privileges
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Output
OutputDir=installer\output
OutputBaseFilename=EnterpriseAgent-Setup-{#MyAppVersion}
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/max
SolidCompression=yes

; UI
WizardStyle=modern
DisableWelcomePage=no
LicenseFile=LICENSE

; Prevent installation on unsupported OS
MinVersion=10.0.17763

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Main executable
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; NSSM service manager (64-bit)
Source: "installer\nssm.exe"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "QUICK_START.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Create ProgramData directories with proper permissions
Name: "{commonappdata}\EnterpriseMonitoring"; Permissions: everyone-full
Name: "{commonappdata}\EnterpriseMonitoring\logs"; Permissions: everyone-full
Name: "{commonappdata}\EnterpriseMonitoring\data"; Permissions: everyone-full
Name: "{commonappdata}\EnterpriseMonitoring\config"; Permissions: everyone-full
Name: "{commonappdata}\EnterpriseMonitoring\data\keystrokes"; Permissions: everyone-full

[Icons]
; Start menu shortcuts
Name: "{group}\{#MyAppName} Service Manager"; Filename: "services.msc"; Parameters: "/s"
Name: "{group}\View Logs"; Filename: "{commonappdata}\EnterpriseMonitoring\logs"
Name: "{group}\Configuration"; Filename: "{commonappdata}\EnterpriseMonitoring\config"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Install and start service using NSSM
Filename: "{app}\nssm.exe"; Parameters: "install ""{#MyAppServiceName}"" ""{app}\{#MyAppExeName}"""; \
    StatusMsg: "Installing Windows service..."; Flags: runhidden waituntilterminated

; Configure service display name
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" DisplayName ""{#MyAppServiceDisplayName}"""; \
    Flags: runhidden waituntilterminated

; Configure service description
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" Description ""{#MyAppServiceDescription}"""; \
    Flags: runhidden waituntilterminated

; Configure service to start automatically
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" Start SERVICE_AUTO_START"; \
    Flags: runhidden waituntilterminated

; Configure stdout log file
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" AppStdout ""{commonappdata}\EnterpriseMonitoring\logs\service.log"""; \
    Flags: runhidden waituntilterminated

; Configure stderr log file (same as stdout for combined logging)
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" AppStderr ""{commonappdata}\EnterpriseMonitoring\logs\service.log"""; \
    Flags: runhidden waituntilterminated

; Configure log rotation
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" AppRotateFiles 1"; \
    Flags: runhidden waituntilterminated

; Set online delay (service will appear online before fully started)
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" AppRotateOnline 0"; \
    Flags: runhidden waituntilterminated

; Configure restart on failure (after 5 seconds)
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" AppExit Default Restart"; \
    Flags: runhidden waituntilterminated

; Set restart delay to 5000ms (5 seconds)
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyAppServiceName}"" AppRestartDelay 5000"; \
    Flags: runhidden waituntilterminated

; Start the service
Filename: "{app}\nssm.exe"; Parameters: "start ""{#MyAppServiceName}"""; \
    StatusMsg: "Starting service..."; Flags: runhidden waituntilterminated

; Show completion message
Filename: "notepad.exe"; Parameters: """{app}\README.md"""; \
    Description: "View README"; Flags: postinstall shellexec skipifsilent nowait

[UninstallRun]
; Stop the service before uninstalling
Filename: "{app}\nssm.exe"; Parameters: "stop ""{#MyAppServiceName}"""; \
    RunOnceId: "StopService"; Flags: runhidden waituntilterminated

; Wait 2 seconds for service to stop
Filename: "{sys}\timeout.exe"; Parameters: "/t 2 /nobreak"; \
    RunOnceId: "WaitForStop"; Flags: runhidden waituntilterminated

; Remove the service
Filename: "{app}\nssm.exe"; Parameters: "remove ""{#MyAppServiceName}"" confirm"; \
    RunOnceId: "RemoveService"; Flags: runhidden waituntilterminated

[Code]
// Check if service is already installed
function IsServiceInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  // Check using sc query command
  Exec('sc.exe', 'query ' + ExpandConstant('{#MyAppServiceName}'), '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
  Result := (ResultCode = 0);
end;

// Stop existing service before installation
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  
  if IsServiceInstalled() then
  begin
    // Stop the service
    Exec('sc.exe', 'stop ' + ExpandConstant('{#MyAppServiceName}'), '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    
    // Wait for service to stop
    Sleep(2000);
    
    // Remove old service
    Exec(ExpandConstant('{app}\nssm.exe'), 'remove ' + ExpandConstant('{#MyAppServiceName}') + ' confirm', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    
    // Wait a bit more
    Sleep(1000);
  end;
end;

// Initialize setup
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Check if running on supported Windows version
  if not IsWindows10OrLater() then
  begin
    MsgBox('This application requires Windows 10 or later.', mbError, MB_OK);
    Result := False;
  end;
end;

// After installation completes
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Create a marker file to indicate successful installation
    SaveStringToFile(ExpandConstant('{commonappdata}\EnterpriseMonitoring\config\.installed'), 
                     'Installed on ' + GetDateTimeString('yyyy-mm-dd hh:nn:ss', #0, #0), False);
  end;
end;

// Custom uninstall confirmation
function InitializeUninstall(): Boolean;
var
  Response: Integer;
begin
  Response := MsgBox('This will stop and remove the Enterprise Monitoring Agent service. ' + #13#10 + #13#10 + 
                     'Do you want to continue?', mbConfirmation, MB_YESNO);
  Result := (Response = IDYES);
end;

// Check if Windows 10 or later
function IsWindows10OrLater(): Boolean;
begin
  Result := (GetWindowsVersion >= $0A000000); // Windows 10 is version 10.0
end;
