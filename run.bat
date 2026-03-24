@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat

:: Launch Ghost Mode handler silently in the background
start "" /B pythonw.exe -m backend.tray

:: Launch the main interactive graphical engine
python -m frontend.gui
