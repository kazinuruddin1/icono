; Inno Setup Script — Icono (Image Crop OCR & Icon Maker)
; Before compiling, run build.bat to generate dist\ImageCropOCR.exe

#define MyAppName "Icono"
#define MyAppVersion "1.5"
#define MyAppPublisher "Rupsha IT Park"
#define MyAppURL "https://www.rupshaitpark.com/"
#define MyAppExeName "ImageCropOCR.exe"

[Setup]
AppId={{43D908D0-78C7-43E2-BDF6-16BD6AAF53CA}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=Icono_Setup_v1.5
SetupIconFile=icon.ico
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "dist\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.png"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent

[Code]
function IsTesseractInstalled: Boolean;
begin
  Result := FileExists('C:\Program Files\Tesseract-OCR\tesseract.exe') or
            FileExists('C:\Program Files (x86)\Tesseract-OCR\tesseract.exe');
end;

procedure CurPageChanged(CurPageID: Integer);
var
  ResultCode: Integer;
begin
  if (CurPageID = wpFinished) and not IsTesseractInstalled then
  begin
    if SuppressibleMsgBox(
      'Tesseract OCR engine is not installed on this system.' + #13#10 + #13#10 +
      'Icono requires Tesseract to extract text from images.' + #13#10 + #13#10 +
      'Open the download page now?',
      mbConfirmation, MB_YESNO, IDYES) = IDYES then
    begin
      ShellExec('open',
        'https://github.com/UB-Mannheim/tesseract/wiki',
        '', '', SW_SHOW, ewNoWait, ResultCode);
    end;
  end;
end;

