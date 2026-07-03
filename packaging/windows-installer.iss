; Inno Setup script — run after `pyinstaller packaging/speechtyper.spec`
; Produces SpeechTyperSetup.exe with Start Menu entry + optional run-at-login.
[Setup]
AppName=SpeechTyper
AppVersion=2.0.0
AppPublisher=SpeechTyper
DefaultDirName={autopf}\SpeechTyper
DefaultGroupName=SpeechTyper
OutputBaseFilename=SpeechTyperSetup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest

[Files]
Source: "..\dist\SpeechTyper\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\SpeechTyper"; Filename: "{app}\SpeechTyper.exe"
Name: "{userstartup}\SpeechTyper"; Filename: "{app}\SpeechTyper.exe"; Tasks: autostart

[Tasks]
Name: "autostart"; Description: "Start SpeechTyper when I log in"; Flags: unchecked

[Run]
Filename: "{app}\SpeechTyper.exe"; Description: "Launch SpeechTyper"; Flags: postinstall nowait skipifsilent
