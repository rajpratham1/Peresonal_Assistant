@echo off
echo ===================================================
echo Ultimate Personal Assistant - Master Setup
echo ===================================================

echo Checking Python installation...
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not attached to PATH!
    pause
    exit /b 1
)

echo Creating Virtual Environment...
python -m venv .venv
call .venv\Scripts\activate.bat

echo Installing Core Requirements...
pip install -r requirements.txt

echo Installing Advanced Phase Modules (This may take a while)...
pip install pystray pillow easyocr chromadb langchain langchain-community sentence-transformers pymupdf playwright google-api-python-client google-auth-httplib2 google-auth-oauthlib openwakeword
python -m playwright install chromium

echo ===================================================
echo Setup Complete! 
echo You can now double-click run.bat to start.
echo ===================================================
pause
