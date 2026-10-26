@echo off
REM ==============================================================================
REM setup_client.bat - 1-Click Client Setup for Lab PCs
REM ==============================================================================

echo ==============================================================================
echo Setting up Lab Face-Verified Access Lock Client
echo ==============================================================================

echo [1/4] Checking Python installation...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python 3.11 is required. Please install Python from https://www.python.org/
    pause
    exit /b 1
)

echo [2/4] Setting up Python virtual environment...
if not exist ".venv" (
    python -m venv .venv
    echo Virtual environment created.
) else (
    echo Existing virtual environment found.
)

echo [3/4] Installing dependencies...
call .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt

echo [4/4] Provisioning device credentials with Central Server...
python setup_device.py

echo.
echo ==============================================================================
echo Client Setup Complete!
echo Run 'python login.py' to begin face-verified workstation monitoring.
echo ==============================================================================
pause
