[Setup]
AppName=NC Invoice Manager
AppVersion=1.4
AppPublisher=NC
DefaultDirName={autopf}\NC Invoice Manager
DefaultGroupName=NC Invoice Manager
OutputDir=dist
OutputBaseFilename=NC_Invoice_Manager_Setup
SetupIconFile=app_icon.ico
UninstallDisplayIcon={app}\InvoiceManager.exe
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=admin
DisableWelcomePage=no
DisableDirPage=no
CloseApplications=force
RestartApplications=no

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "dist\InvoiceManager\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\NC Invoice Manager"; Filename: "{app}\InvoiceManager.exe"; IconFilename: "{app}\InvoiceManager.exe"
Name: "{group}\{cm:UninstallProgram,NC Invoice Manager}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\NC Invoice Manager"; Filename: "{app}\InvoiceManager.exe"; Tasks: desktopicon; IconFilename: "{app}\InvoiceManager.exe"

[Run]
Filename: "{app}\InvoiceManager.exe"; Description: "{cm:LaunchProgram,NC Invoice Manager}"; Flags: nowait postinstall skipifsilent
