@echo off
REM Build the Windows installer. Run on a Windows 10/11 machine with Python 3.10+ and Inno Setup 6.
REM Output: installer\Output\VaultChatbotSetup.exe
setlocal
cd /d "%~dp0\.."

python -m venv .buildvenv || goto :fail
call .buildvenv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt pyinstaller || goto :fail

python scripts\generate_training_data.py || goto :fail
python scripts\train_model.py || goto :fail

pyinstaller --noconfirm --clean --name VaultChatbot --onedir --console ^
  --hidden-import uvicorn.logging --hidden-import uvicorn.loops.auto --hidden-import uvicorn.protocols.http.auto ^
  --hidden-import uvicorn.protocols.websockets.auto --hidden-import uvicorn.lifespan.on ^
  --collect-submodules sklearn --collect-submodules app ^
  run_server.py || goto :fail

REM Data, model and widget live next to the exe so staff can edit the knowledge base
xcopy /E /I /Y data   dist\VaultChatbot\data   >nul
del /Q dist\VaultChatbot\data\chatbot.db 2>nul
xcopy /E /I /Y models dist\VaultChatbot\models >nul
xcopy /E /I /Y widget dist\VaultChatbot\widget >nul
copy /Y config.json dist\VaultChatbot\config.json >nul
copy /Y installer\start_ngrok.bat dist\VaultChatbot\start_ngrok.bat >nul

"%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" installer\vault_chatbot.iss || goto :fail
echo.
echo SUCCESS: installer\Output\VaultChatbotSetup.exe
exit /b 0

:fail
echo BUILD FAILED
exit /b 1
