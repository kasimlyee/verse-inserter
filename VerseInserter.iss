; VerseInserter.iss
; Complete installation script for VerseInserter
; Author: Kasim Lyee <lyee@codewithlyee.com>
; Company: Softlite Inc.

[Setup]
AppId={{A1B2C3D4-E5F6-7890-1234-567890ABCDEF}
AppName=VerseInserter
AppVersion=1.0.0
AppVerName=VerseInserter 1.0.0
AppPublisher=Softlite Inc.
AppPublisherURL=https://codewithlyee.com
AppSupportURL=https://codewithlyee.com/support
AppUpdatesURL=https://codewithlyee.com/updates
AppCopyright=Copyright (c) 2025 Softlite Inc. All Rights Reserved.
DefaultDirName={autopf}\Softlite Inc\VerseInserter
DefaultGroupName=VerseInserter
AllowNoIcons=yes
LicenseFile=license.rtf
InfoBeforeFile=readme.rtf
Compression=lzma2/max
SolidCompression=yes
OutputDir=Installer
OutputBaseFilename=VerseInserter_Setup
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\VerseInserter.exe
UninstallDisplayName=VerseInserter
WizardStyle=modern
WizardImageFile=wizard.bmp
WizardSmallImageFile=wizard_small.bmp
DisableWelcomePage=no
DisableDirPage=no
DisableProgramGroupPage=no
PrivilegesRequired=lowest
ChangesAssociations=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[CustomMessages]
english.ProductDescription=Automated Scripture Insertion for Microsoft Word Documents

[Types]
Name: "full"; Description: "Full installation"
Name: "compact"; Description: "Compact installation"
Name: "custom"; Description: "Custom installation"; Flags: iscustom

[Components]
Name: "main"; Description: "Main Files"; Types: full compact custom; Flags: fixed
Name: "desktop"; Description: "Desktop Shortcut"; Types: full
Name: "startmenu"; Description: "Start Menu Shortcut"; Types: full compact
Name: "quicklaunch"; Description: "Quick Launch Shortcut"; Types: full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Components: desktop
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Components: quicklaunch; Flags: unchecked
Name: "associate"; Description: "&Associate .docx files with VerseInserter"; GroupDescription: "File associations:"; Flags: unchecked

[Files]
Source: "dist\VerseInserter.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: main
Source: "dist\*.*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main

[Icons]
Name: "{group}\VerseInserter"; Filename: "{app}\VerseInserter.exe"; Components: startmenu
Name: "{group}\Read Me"; Filename: "{app}\readme.pdf"; Components: startmenu
Name: "{group}\License Agreement"; Filename: "{app}\license.pdf"; Components: startmenu
Name: "{group}\Uninstall VerseInserter"; Filename: "{uninstallexe}"; Components: startmenu
Name: "{autodesktop}\VerseInserter"; Filename: "{app}\VerseInserter.exe"; Tasks: desktopicon; Components: desktop
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\VerseInserter"; Filename: "{app}\VerseInserter.exe"; Tasks: quicklaunchicon; Components: quicklaunch

[Registry]
; File association (optional)
Root: HKA; Subkey: "Software\Classes\.verseinsert"; ValueType: string; ValueName: ""; ValueData: "VerseInserter.Document"; Flags: uninsdeletevalue; Tasks: associate
Root: HKA; Subkey: "Software\Classes\VerseInserter.Document"; ValueType: string; ValueName: ""; ValueData: "VerseInserter Document"; Flags: uninsdeletekey; Tasks: associate
Root: HKA; Subkey: "Software\Classes\VerseInserter.Document\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\VerseInserter.exe,0"; Tasks: associate
Root: HKA; Subkey: "Software\Classes\VerseInserter.Document\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\VerseInserter.exe"" ""%1"""; Tasks: associate

; Application settings
Root: HKCU; Subkey: "Software\Softlite Inc\VerseInserter"; Flags: uninsdeletekey

[Run]
Filename: "{app}\VerseInserter.exe"; Description: "{cm:LaunchProgram,VerseInserter}"; Flags: nowait postinstall skipifsilent
Filename: "{app}\readme.pdf"; Description: "View Read Me"; Flags: shellexec postinstall skipifsilent unchecked
Filename: "{app}\license.pdf"; Description: "View License Agreement"; Flags: shellexec postinstall skipifsilent unchecked

[UninstallRun]
Filename: "{app}\VerseInserter.exe"; Parameters: "/uninstall"; Flags: runhidden waituntilterminated

[Code]
// Custom validation
function InitializeSetup(): Boolean;
begin
  Result := True;
  
  // Check if .NET Framework is installed (if needed)
  // if not IsDotNetInstalled then begin
  //   MsgBox('VerseInserter requires .NET Framework 4.8. Please install it first.', mbError, MB_OK);
  //   Result := False;
  // end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Log installation
    Log('VerseInserter installed successfully to: ' + ExpandConstant('{app}'));
  end;
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Clean up any additional files
    DelTree(ExpandConstant('{localappdata}\VerseInserter'), True, True, True);
  end;
end;