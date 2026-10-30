; CSpace installer. Per-user (no admin): the app writes Data\ inside @Resources, so it must live somewhere the user can write.
; The app finds contract\, Skins\ and SpaceshipApp\SpaceshipUI\dist by walking up from the exe, so that tree is recreated under {app}.
; Heavy JARVIS models (vosk, kokoro, voices, wake) and personal runtime files (Data, Backups, caches) are NOT shipped;
; run Jarvis\Setup-Jarvis.ps1 after install to fetch the models.
#define Root ".."
#define Res Root + "\Skins\Spaceship\@Resources"

[Setup]
AppId={{7B1E5D0A-3C52-4F0B-9A55-C5BACE0D1A01}
AppName=CSpace
AppVersion=0.1.0
AppPublisher=Senai
DefaultDirName={localappdata}\Programs\CSpace
DefaultGroupName=CSpace
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=Output
OutputBaseFilename=CSpace-Setup-0.1.0
SetupIconFile={#Root}\SpaceshipApp\ShipCore.App\Assets\cspace.ico
UninstallDisplayIcon={app}\CSpace.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
CloseApplications=yes

[Dirs]
Name: "{app}\Skins\Spaceship\@Resources\Data"

[Files]
Source: "stage\CSpace\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "{#Root}\SpaceshipApp\SpaceshipUI\dist\*"; DestDir: "{app}\SpaceshipApp\SpaceshipUI\dist"; Flags: ignoreversion recursesubdirs
Source: "{#Root}\contract\config-keys.json"; DestDir: "{app}\contract"; Flags: ignoreversion
Source: "{#Root}\contract\exam-browsers.json"; DestDir: "{app}\contract"; Flags: ignoreversion
Source: "{#Res}\*"; DestDir: "{app}\Skins\Spaceship\@Resources"; Flags: ignoreversion recursesubdirs; Excludes: "Data,Backups,__pycache__,Jarvis\vosk,Jarvis\kokoro,Jarvis\voices,Jarvis\wake,Jarvis\Data,Jarvis\__pycache__,*.pyc,*.log"

[Icons]
Name: "{autoprograms}\CSpace"; Filename: "{app}\CSpace.exe"
Name: "{autodesktop}\CSpace"; Filename: "{app}\CSpace.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked

[Run]
Filename: "{app}\CSpace.exe"; Description: "Start CSpace"; Flags: nowait postinstall skipifsilent unchecked

[Code]
// Framework-dependent publish: warn (do not block) when no .NET 10 desktop runtime is found.
function InitializeSetup(): Boolean;
var R: TFindRec;
begin
  Result := True;
  if FindFirst(ExpandConstant('{commonpf64}\dotnet\shared\Microsoft.WindowsDesktop.App\10.*'), R) then FindClose(R)
  else if MsgBox('The .NET 10 Desktop Runtime was not found. CSpace needs it to start. Install anyway?', mbConfirmation, MB_YESNO) = IDNO then Result := False;
end;
