@echo off
setlocal

cd /d "%~dp0"

echo Installing packages for Python 3.8 from local wheelhouse...
echo Wheelhouse: %~dp0wheelhouse_py38
echo.
echo Python runtime:
python -c "import platform, sys; print(sys.version); print(platform.architecture()[0]); print(sys.executable)"
echo.

if not exist "%~dp0wheelhouse_py38\wntr-1.2.0-cp38-cp38-win_amd64.whl" (
    echo ERROR: wntr wheel not found in wheelhouse_py38.
    echo Expected: %~dp0wheelhouse_py38\wntr-1.2.0-cp38-cp38-win_amd64.whl
    pause
    exit /b 1
)

python -m pip install --no-index --find-links="%~dp0wheelhouse_py38" -r requirements.txt
if errorlevel 1 (
    pause
    exit /b 1
)

echo.
echo Verifying imports...
python -c "import pymysql, pandas, numpy, wntr, pygad, flask, waitress; print('IMPORT OK')"
if errorlevel 1 (
    pause
    exit /b 1
)
