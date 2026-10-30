#define MyAppName "Menu Bar Schedule"
#define MyAppExeName "MenuBarSchedule.exe"
#define MyAppVersion "4.0.0"

[Setup]
AppId={{6D1C5A91-2B47-4C83-9E20-7A8F5D3B61E2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

OutputBaseFilename=MenuBarSchedule-Setup-{#MyAppVersion}

WizardStyle=modern
Compression=lzma2
SolidCompression=yes

DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; \
    Description: "Create a desktop shortcut"; \
    GroupDescription: "Additional options:"; \
    Flags: unchecked

Name: "autostarticon"; \
    Description: "Start application when Windows starts"; \
    GroupDescription: "Additional options:"; \
    Flags: unchecked

[Files]
Source: "..\dist\MenuBarSchedule\*"; \
    DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\MenuBarSchedule"; \
    Filename: "{app}\{#MyAppExeName}"

Name: "{autodesktop}\MenuBarSchedule"; \
    Filename: "{app}\{#MyAppExeName}"; \
    Tasks: desktopicon

Name: "{userstartup}\\{#MyAppName}"; \
    Filename: "{app}\\{#MyAppExeName}"; \
    Tasks: autostarticon

[Run]
Filename: "{app}\{#MyAppExeName}"; \
    Description: "Launch Menu Bar Schedule"; \
    Flags: postinstall nowait skipifsilent

[Code]
function IsAppRunning(const FileName: string): Boolean;
var
  FWMIService: Variant;
  FSWbemLocator: Variant;
  FWbemObjectSet: Variant;
begin
  Result := false;
  FSWbemLocator := CreateOleObject('WBEMScripting.SWBEMLocator');
  FWMIService := FSWbemLocator.ConnectServer('', 'root\CIMV2', '', '');
  FWbemObjectSet := FWMIService.ExecQuery(Format('SELECT Name FROM Win32_Process Where Name="%s"',[FileName]));
  Result := (FWbemObjectSet.Count > 0);
  FWbemObjectSet := Unassigned;
  FWMIService := Unassigned;
  FSWbemLocator := Unassigned;
end;

function InitializeSetup: boolean;
begin
  Result := not IsAppRunning('MenuBarSchedule.exe');
  if not Result then
  MsgBox('Menu Bar Schedule is running. Please close the application before running the installer.', mbError, MB_OK);
end;