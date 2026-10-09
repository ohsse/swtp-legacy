@echo off
setlocal

cd /d "%~dp0"
set "APP_CONFIG=%~dp0config.json"
set "APP_CONNECTIONS=%~dp0libs\connections.json"

echo Starting GSSource API...
echo URL: http://0.0.0.0:30093
echo Config: %APP_CONFIG%
echo Connections: %APP_CONNECTIONS%

python api_server.py

echo.
echo GSSource API stopped. Exit code: %ERRORLEVEL%
echo If this window closed immediately before, check the error message above.
pause
