@echo off
title Viru Web Client
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo  =========================================
echo   Viru AI Assistant - Web Client
echo   Opening http://localhost:5000 ...
echo  =========================================
echo.

:: Install flask if missing
python -c "import flask" 2>nul || pip install flask --quiet

python web_server.py
pause
