@echo off
setlocal

cd /d "%~dp0"

echo Installing GSSource packages for Python 3.8 from local wheelhouse...
echo Wheelhouse: %~dp0wheelhouse_py38

python --version
python -m pip install --no-index --find-links="%~dp0wheelhouse_py38" -r "%~dp0requirements_py38.txt"

echo.
echo Verifying imports...
python -c "import flask, xgboost, pandas, numpy, pymysql, schedule, sqlalchemy, openpyxl; print('OK')"

echo.
echo Done.
pause
