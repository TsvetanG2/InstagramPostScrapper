; Inno Setup Script - Instagram Post Scrapper
; Build first with PyInstaller:
;   python -m PyInstaller --onedir --windowed --name "InstagramPostScrapper" --icon "icon.ico" ^
;     --version-file "version_info.txt" ^
;     --add-data "icon.ico;." ^
;     --collect-all selenium ^
;     scraper_selenium.py

#define MyAppName "Instagram Post Scrapper"
#define MyAppVersion "0.0.1"
#define MyAppPublisher "Tsvetan Gerginov"
#define MyAppURL "https://www.tsvetangerginov.com/"
#define MyAppExeName "InstagramScrapper.exe"

[Setup]
AppId={{3301F994-AD99-47B9-836A-67E045C218CD}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
LicenseFile=LICENSE.md

DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes

; Per-user install (без admin prompt)
PrivilegesRequired=lowest

ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

; Output
OutputDir=dist_installer
OutputBaseFilename=InstagramPostScrapperSetup_{#MyAppVersion}
SetupIconFile=icon.ico

Compression=lzma2
SolidCompression=yes

WizardStyle=modern
DisableProgramGroupPage=yes

UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; PyInstaller output (onedir) - ПРОВЕРИ дали папката съвпада с твоето --name
Source: "dist\InstagramScrapper\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Optional files (ако ги имаш)
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "README.md"
Source: "LICENSE.md"; DestDir: "{app}"; Flags: ignoreversion; DestName: "LICENSE.md"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon; WorkingDir: "{app}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
