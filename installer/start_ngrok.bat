@echo off
REM Starts the persistent ngrok tunnel. Requires ngrok installed and authenticated
REM once with:  ngrok config add-authtoken <TOKEN>
REM Set NGROK_DOMAIN to the reserved domain, e.g. api.vaultelectronics.co.ke
REM (a custom domain needs a paid ngrok plan; a free static *.ngrok-free.app domain also works).
setlocal
if "%NGROK_DOMAIN%"=="" set NGROK_DOMAIN=api.vaultelectronics.co.ke
if "%PORT%"=="" set PORT=8000
:loop
ngrok http --url=%NGROK_DOMAIN% %PORT%
echo ngrok exited, restarting in 10 seconds...
timeout /t 10 /nobreak >nul
goto loop
