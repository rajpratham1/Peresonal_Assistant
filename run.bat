@echo off
title Viru AI Assistant
cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo  =========================================
echo   Viru AI Assistant - Starting...
echo  =========================================
echo.

python main_loader.py
pause
