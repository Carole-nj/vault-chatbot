; Inno Setup 6 script for the Vault Electronics chatbot.
; Supports silent install:  VaultChatbotSetup.exe /VERYSILENT /SUPPRESSMSGBOXES /TASKS="autostart"

[Setup]
AppId={{B6F1D7A2-4C1E-4E1B-9A55-5C0E7A3F1D10}
AppName=Vault Electronics Chatbot
AppVersion=1.0.0
AppPublisher=Vault Electronics
DefaultDirName={autopf}\VaultChatbot
DefaultGroupName=Vault Chatbot
OutputDir=Output
OutputBaseFilename=VaultChatbotSetup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=Vault Electronics Chatbot

[Tasks]
Name: "autostart"; Description: "Start the chatbot and ngrok tunnel automatically when Windows boots"; Flags: checkedonce

[Files]
; program files are always replaced on upgrade
Source: "..\dist\VaultChatbot\*"; DestDir: "{app}"; Excludes: "data\*,config.json"; Flags: recursesubdirs ignoreversion
; knowledge base and config are only written on first install so upgrades never overwrite staff edits
Source: "..\dist\VaultChatbot\data\*"; DestDir: "{app}\data"; Flags: recursesubdirs onlyifdoesntexist uninsneveruninstall
Source: "..\dist\VaultChatbot\config.json"; DestDir: "{app}"; Flags: onlyifdoesntexist uninsneveruninstall

[Dirs]
Name: "{app}\logs"
Name: "{app}\backups"

[Icons]
Name: "{group}\Start Vault Chatbot"; Filename: "{app}\VaultChatbot.exe"; WorkingDir: "{app}"
Name: "{group}\Start ngrok tunnel"; Filename: "{app}\start_ngrok.bat"; WorkingDir: "{app}"
Name: "{group}\Edit configuration"; Filename: "notepad.exe"; Parameters: """{app}\config.json"""
Name: "{group}\Edit knowledge base"; Filename: "notepad.exe"; Parameters: """{app}\data\knowledge_base.json"""
Name: "{group}\View logs"; Filename: "{app}\logs"

[Run]
; auto-start at boot (runs as SYSTEM, restarts are handled by the scheduled task)
Filename: "schtasks.exe"; Parameters: "/Create /TN ""VaultChatbot"" /TR ""\""{app}\VaultChatbot.exe\"""" /SC ONSTART /RU SYSTEM /RL HIGHEST /F"; Flags: runhidden; Tasks: autostart
Filename: "schtasks.exe"; Parameters: "/Create /TN ""VaultChatbotNgrok"" /TR ""\""{app}\start_ngrok.bat\"""" /SC ONSTART /RU SYSTEM /RL HIGHEST /F"; Flags: runhidden; Tasks: autostart
; open config so the operator can set admin_token / ngrok domain
Filename: "notepad.exe"; Parameters: """{app}\config.json"""; Description: "Open configuration (set admin_token and ngrok domain)"; Flags: postinstall nowait skipifsilent
Filename: "{app}\VaultChatbot.exe"; Description: "Start the chatbot now"; WorkingDir: "{app}"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "schtasks.exe"; Parameters: "/Delete /TN ""VaultChatbot"" /F"; Flags: runhidden; RunOnceId: "DelTask1"
Filename: "schtasks.exe"; Parameters: "/Delete /TN ""VaultChatbotNgrok"" /F"; Flags: runhidden; RunOnceId: "DelTask2"
Filename: "taskkill.exe"; Parameters: "/F /IM VaultChatbot.exe"; Flags: runhidden; RunOnceId: "KillExe"
