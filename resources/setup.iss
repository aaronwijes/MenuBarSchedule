#define MyAppName "Menu Bar Schedule"
#define MyAppExeName "MenuBarSchedule.exe"
#define MyAppVersion "4.0.0"

[Setup]
AppId={{6D1C5A91-2B47-4C83-9E20-7A8F5D3B61E2}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
UninstallDisplayName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
SetupIconFile=AppIcon.ico

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}

PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64os

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