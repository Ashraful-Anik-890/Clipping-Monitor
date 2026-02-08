; Inno Setup Script for Enterprise Monitoring Agent
; This script installs the Enterprise Monitoring Agent as a Windows Service using NSSM
; Requires: nssm.exe and EnterpriseAgent.exe in the dist folder

#define MyAppName "Enterprise Monitoring Agent"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Skillers Zone LTD"
#define MyAppURL "https://www.skillerszone.com"
#define MyServiceName "EnterpriseMonitoringAgent"
#define MyServiceDisplayName "Enterprise Monitoring Agent"
#define MyServiceDescription "Enterprise-grade monitoring and tracking service"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{E7A4B9C3-2D5F-4A1E-9B8C-3F2E1D4A5B6C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={commonpf}\Enterprise Monitoring Agent
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=installer_output
OutputBaseFilename=EnterpriseMonitoringAgent_Setup_{#MyAppVersion}
Compression=lzma
SolidCompression=yes
; Require administrator privileges
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
UninstallDisplayIcon={app}\EnterpriseAgent.exe
; SetupIconFile=resources\icon.ico
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
; Main executable
Source: "dist\EnterpriseAgent.exe"; DestDir: "{app}"; Flags: ignoreversion
; NSSM service manager
Source: "dist\nssm.exe"; DestDir: "{app}"; Flags: ignoreversion
; Additional files if needed
; Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
; Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Create ProgramData directories
Name: "C:\ProgramData\EnterpriseMonitoring"; Permissions: users-modify
Name: "C:\ProgramData\EnterpriseMonitoring\logs"; Permissions: users-modify
Name: "C:\ProgramData\EnterpriseMonitoring\data"; Permissions: users-modify
Name: "C:\ProgramData\EnterpriseMonitoring\config"; Permissions: users-modify

[Icons]
; Create shortcuts (optional)
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"

[Run]
; Install the service using NSSM
Filename: "{app}\nssm.exe"; Parameters: "install ""{#MyServiceName}"" ""{app}\EnterpriseAgent.exe"""; Flags: runhidden; StatusMsg: "Installing Windows Service..."

; Configure service stdout log
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyServiceName}"" AppStdout ""C:\ProgramData\EnterpriseMonitoring\logs\service.log"""; Flags: runhidden; StatusMsg: "Configuring service logging..."

; Configure service stderr log
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyServiceName}"" AppStderr ""C:\ProgramData\EnterpriseMonitoring\logs\service_error.log"""; Flags: runhidden; StatusMsg: "Configuring service error logging..."

; Set service display name
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyServiceName}"" DisplayName ""{#MyServiceDisplayName}"""; Flags: runhidden

; Set service description
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyServiceName}"" Description ""{#MyServiceDescription}"""; Flags: runhidden

; Set service to start automatically
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyServiceName}"" Start SERVICE_AUTO_START"; Flags: runhidden

; Configure service restart on failure
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyServiceName}"" AppExit Default Restart"; Flags: runhidden

; Set restart delay (30 seconds)
Filename: "{app}\nssm.exe"; Parameters: "set ""{#MyServiceName}"" AppRestartDelay 30000"; Flags: runhidden

; Start the service
Filename: "{app}\nssm.exe"; Parameters: "start ""{#MyServiceName}"""; Flags: runhidden; StatusMsg: "Starting service..."; 

[UninstallRun]
; Stop the service before uninstall
Filename: "{app}\nssm.exe"; Parameters: "stop ""{#MyServiceName}"""; Flags: runhidden; RunOnceId: "StopService"

; Remove the service
Filename: "{app}\nssm.exe"; Parameters: "remove ""{#MyServiceName}"" confirm"; Flags: runhidden; RunOnceId: "RemoveService"

[Code]
// Check for admin privileges
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  
  // Check if running as administrator
  if not IsAdminLoggedOn() then
  begin
    MsgBox('This installer requires administrator privileges to install a Windows service.' + #13#10 + 
           'Please run the installer as administrator.', mbError, MB_OK);
    Result := False;
    Exit;
  end;
  
  // Additional check for elevated privileges
  if not IsAdminInstallMode() then
  begin
    MsgBox('This installer must be run with elevated privileges.' + #13#10 +
           'Please right-click the installer and select "Run as administrator".', mbError, MB_OK);
    Result := False;
    Exit;
  end;
end;

// Check if service already exists before installation
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ResultCode: Integer;
begin
  Result := '';
  
  // Check if service already exists and stop it
  if Exec(ExpandConstant('{app}\nssm.exe'), 'status "{#MyServiceName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode = 0 then
    begin
      // Service exists, stop it first
      Exec(ExpandConstant('{app}\nssm.exe'), 'stop "{#MyServiceName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Sleep(2000); // Wait for service to stop
      
      // Remove the existing service
      Exec(ExpandConstant('{app}\nssm.exe'), 'remove "{#MyServiceName}" confirm', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
      Sleep(1000); // Wait for service removal
    end;
  end;
end;

// Post-installation message
procedure CurStepChanged(CurStep: TSetupStep);
var
  ResultCode: Integer;
begin
  if CurStep = ssPostInstall then
  begin
    // Verify service installation
    if Exec(ExpandConstant('{app}\nssm.exe'), 'status "{#MyServiceName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    begin
      if ResultCode = 0 then
      begin
        Log('Service installed and started successfully');
      end
      else
      begin
        MsgBox('Warning: Service installation may have encountered issues. Please check the logs at C:\ProgramData\EnterpriseMonitoring\logs\', mbInformation, MB_OK);
      end;
    end;
  end;
end;

// Clean up on uninstall
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  ResultCode: Integer;
begin
  if CurUninstallStep = usUninstall then
  begin
    // Stop and remove service
    Exec(ExpandConstant('{app}\nssm.exe'), 'stop "{#MyServiceName}"', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(2000);
    Exec(ExpandConstant('{app}\nssm.exe'), 'remove "{#MyServiceName}" confirm', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Sleep(1000);
  end;
  
  if CurUninstallStep = usPostUninstall then
  begin
    // Optional: Ask user if they want to keep the data
    if MsgBox('Do you want to remove all monitoring data and logs from C:\ProgramData\EnterpriseMonitoring?', mbConfirmation, MB_YESNO) = IDYES then
    begin
      DelTree('C:\ProgramData\EnterpriseMonitoring', True, True, True);
    end;
  end;
end;
