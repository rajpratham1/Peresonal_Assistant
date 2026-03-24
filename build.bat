@echo off
echo ======================================================
echo   VIRU: Ultimate Assistant - EXE BUILDER
echo ======================================================
echo.

:: Ensure venv is active
if not exist .venv (
    echo [ERROR] Virtual environment not found! Please run setup.bat first.
    pause
    exit /b
)

echo [1/3] Cleaning up previous builds...
if exist build rd /s /q build
if exist dist rd /s /q dist
if exist main_loader.spec del /f /q main_loader.spec

echo [2/3] Compiling Assistant into Standalone EXE...
echo This will take a few minutes (Compressing dependencies)...

.\.venv\Scripts\pyinstaller --noconfirm --onedir --windowed ^
    --name "Viru_Assistant" ^
    --add-data "backend;backend" ^
    --add-data "frontend;frontend" ^
    --hidden-import "customtkinter" ^
    --hidden-import "pystray" ^
    --hidden-import "easyocr" ^
    --hidden-import "faster_whisper" ^
    --hidden-import "duckduckgo_search" ^
    --icon "NONE" ^
    main_loader.py

echo.
echo [3/3] BUILD COMPLETE!
echo Your shareable app is in the "dist/Viru_Assistant" folder.
echo.
echo NOTE: First time users will auto-download the AI Brain upon launch.
pause
