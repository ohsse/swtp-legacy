@echo off
setlocal

cd /d "%~dp0"
set "APP_CONFIG=%~dp0config.prob.json"

echo Starting Roughness GA Optimizer API...
echo URL: http://0.0.0.0:30092
echo Config: %APP_CONFIG%

python -m waitress --host=0.0.0.0 --port=30092 api_server:app
