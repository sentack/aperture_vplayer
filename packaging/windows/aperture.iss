; Windows installer for the PyInstaller build in dist\aperture.
; CI runs:  iscc /DAppVersion=<version> packaging\windows\aperture.iss
; Per-user install by default (no admin prompt); the dialog offers an all-users install.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif
#define AppName "Aperture"
#define AppExe "aperture.exe"

[Setup]
AppId={{0B6D8C92-1138-427D-BE87-1619DBB61D5C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher=sentack
AppPublisherURL=https://github.com/sentack/aperture_vplayer
AppSupportURL=https://github.com/sentack/aperture_vplayer/issues
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\..\dist
OutputBaseFilename=Aperture-{#AppVersion}-windows-x64-setup
SetupIconFile=..\icons\aperture.ico
UninstallDisplayIcon={app}\{#AppExe}
; Release compression (v0.3.0+): LZMA2 at its strongest preset, one solid block, done in a
; separate process so the large dictionary does not exhaust the compiler's memory.
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
WizardStyle=modern
ChangesAssociations=yes
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "associate"; Description: "Offer Aperture in ""Open with"" for video files"; GroupDescription: "File types:"

[Files]
Source: "..\..\dist\aperture\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Registry]
; A ProgID plus OpenWithProgids entries: Aperture shows up in "Open with" and the
; default-apps list, without taking over file types the user already assigned.
Root: HKA; Subkey: "Software\Classes\Aperture.Video"; ValueType: string; ValueData: "Video file"; Flags: uninsdeletekey; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Aperture.Video\DefaultIcon"; ValueType: string; ValueData: "{app}\{#AppExe},0"; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Aperture.Video\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}"; ValueType: string; ValueName: "FriendlyAppName"; ValueData: "{#AppName}"; Flags: uninsdeletekey; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\shell\open\command"; ValueType: string; ValueData: """{app}\{#AppExe}"" ""%1"""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".3gp"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".avi"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".flv"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".m2ts"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".m4v"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mkv"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mov"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mp4"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mpeg"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".mpg"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".ogv"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".ts"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".webm"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\Applications\{#AppExe}\SupportedTypes"; ValueType: string; ValueName: ".wmv"; ValueData: ""; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.3gp\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.avi\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.flv\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.m2ts\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.m4v\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.mkv\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.mov\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.mp4\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.mpeg\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.mpg\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.ogv\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.ts\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.webm\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\.wmv\OpenWithProgids"; ValueType: string; ValueName: "Aperture.Video"; ValueData: ""; Flags: uninsdeletevalue; Tasks: associate

; Capabilities + RegisteredApplications: lists Aperture in Settings → Default apps, which
; is the only way Windows 10+ lets a user pick a default player.
Root: HKA; Subkey: "Software\RegisteredApplications"; ValueType: string; ValueName: "Aperture"; ValueData: "Software\Aperture\Capabilities"; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Aperture"; Flags: uninsdeletekey; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities"; ValueType: string; ValueName: "ApplicationName"; ValueData: "{#AppName}"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities"; ValueType: string; ValueName: "ApplicationDescription"; ValueData: "Lightweight video player"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".3gp"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".avi"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".flv"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".m2ts"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".m4v"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mkv"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mov"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mp4"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mpeg"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".mpg"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".ogv"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".ts"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".webm"; ValueData: "Aperture.Video"; Tasks: associate
Root: HKA; Subkey: "Software\Aperture\Capabilities\FileAssociations"; ValueType: string; ValueName: ".wmv"; ValueData: "Aperture.Video"; Tasks: associate

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent
