@echo off
REM Daily backup of the database and knowledge base. Schedule with Windows Task Scheduler.
setlocal
set APP=%~dp0..
if not exist "%APP%\backups" mkdir "%APP%\backups"
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd"') do set D=%%i
copy /Y "%APP%\data\chatbot.db" "%APP%\backups\chatbot_%D%.db" >nul
copy /Y "%APP%\data\knowledge_base.json" "%APP%\backups\knowledge_base_%D%.json" >nul
REM keep the last 30 days
forfiles /P "%APP%\backups" /D -30 /C "cmd /c del @path" 2>nul
