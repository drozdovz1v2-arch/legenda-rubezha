; Установщик «Легенда Рубежа» — собирается через build_installer.bat



#define MyAppName "Легенда Рубежа"

#define MyAppVersion "0.0.0.4"

#define MyAppVersionName "beta 0.0.0.4"

#define MyAppPublisher "Legenda Rubezha"

#define MyAppExeName "LegendaRubezha.exe"

#define MyLauncherExeName "LegendaRubezhaLauncher.exe"



[Setup]

AppId={{A7B3C9D1-4E2F-5A6B-8C9D-0E1F2A3B4C5D}

AppName={#MyAppName}

AppVersion={#MyAppVersion}

AppVerName={#MyAppVersionName}

AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\Legenda Rubezha

DefaultGroupName={#MyAppName}

DisableDirPage=no

AlwaysShowDirOnReadyPage=yes

DisableProgramGroupPage=yes

OutputDir=installer

OutputBaseFilename=LegendaRubezha_Setup_beta_0.0.0.4

SetupIconFile=compiler:SetupClassicIcon.ico

Compression=lzma2/ultra64

SolidCompression=yes

WizardStyle=modern

PrivilegesRequired=lowest

ArchitecturesInstallIn64BitMode=x64compatible

UninstallDisplayIcon={app}\{#MyAppExeName}

UninstallDisplayName={#MyAppName}

VersionInfoVersion={#MyAppVersion}

VersionInfoProductVersion={#MyAppVersion}

VersionInfoProductName={#MyAppName}



[Languages]

Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"



[Tasks]

Name: "desktopicon"; Description: "Создать ярлык лаунчера на рабочем столе"; GroupDescription: "Дополнительно:"; Flags: checkedonce



[Files]

Source: "dist\LegendaRubezha\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion

Source: "dist\LegendaRubezha\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

Source: "dist\LegendaRubezhaLauncher\{#MyLauncherExeName}"; DestDir: "{app}\Launcher"; Flags: ignoreversion
Source: "dist\LegendaRubezhaLauncher\_internal\*"; DestDir: "{app}\Launcher\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

Source: "updates\version.json"; DestDir: "{app}"; Flags: ignoreversion

Source: "updates\launcher_config.json"; DestDir: "{app}"; Flags: ignoreversion

Source: "updates\manifest.json"; DestDir: "{app}\updates"; Flags: ignoreversion
Source: "updates\github_repo.json"; DestDir: "{app}\updates"; Flags: ignoreversion



[Icons]

Name: "{group}\{#MyAppName} (лаунчер)"; Filename: "{app}\Launcher\{#MyLauncherExeName}"

Name: "{group}\{#MyAppName} (игра)"; Filename: "{app}\{#MyAppExeName}"

Name: "{group}\Удалить {#MyAppName}"; Filename: "{uninstallexe}"

Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\Launcher\{#MyLauncherExeName}"; Tasks: desktopicon



[Run]

Filename: "{app}\Launcher\{#MyLauncherExeName}"; Description: "Открыть лаунчер"; Flags: nowait postinstall skipifsilent



[UninstallDelete]

Type: files; Name: "{app}\save.json"

Type: files; Name: "{app}\crash_log.txt"



[Code]

function InitializeSetup(): Boolean;

begin

  Result := True;

end;


