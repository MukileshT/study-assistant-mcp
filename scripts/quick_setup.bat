@echo off
REM Study Assistant MCP - Quick Setup Script for Windows

echo ======================================
echo Study Assistant MCP - Quick Setup
echo ======================================
echo.

REM Check Python installation
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11+ from python.org
    pause
    exit /b 1
)

python --version
echo Python found!
echo.

REM Create virtual environment
echo Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip >nul 2>&1
echo pip upgraded
echo.

REM Install dependencies
echo Installing dependencies...
echo This may take a few minutes...
pip install -r requirements.txt
echo Dependencies installed!
echo.

REM Create .env file
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo .env file created
    echo.
    echo IMPORTANT: Edit .env file with your API keys before proceeding
) else (
    echo .env file already exists
)
echo.

REM Create data directories
echo Creating data directories...
if not exist "data" mkdir data
if not exist "data\cache" mkdir data\cache
if not exist "data\uploads" mkdir data\uploads
if not exist "data\processed" mkdir data\processed
echo Data directories created
echo.

REM Summary
echo ======================================
echo Setup Complete!
echo ======================================
echo.
echo Next steps:
echo 1. Edit .env file with your API keys:
echo    - GOOGLE_API_KEY (from ai.google.dev)
echo    - GROQ_API_KEY (from console.groq.com)
echo    - NOTION_API_KEY (from notion.so/my-integrations)
echo.
echo 2. Test API connections:
echo    python scripts\test_apis.py
echo.
echo 3. Set up Notion workspace:
echo    python scripts\setup_notion.py
echo.
echo 4. Start processing notes!
echo.
echo Happy studying! 📚
echo.

pause