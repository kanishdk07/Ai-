@echo off
REM Quick Start Script for Highway Accident Detection Backend (Windows)
REM This script helps set up and run the application

echo.
echo 🚨 Highway Accident Detection System - Backend Setup
echo ====================================================
echo.

REM Check Python version
echo Checking Python version...
python --version
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.11+
    exit /b 1
)
echo ✓ Python found
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo ✓ Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet
echo ✓ Dependencies installed
echo.

REM Check if .env exists
if not exist ".env" (
    echo ⚠️  .env file not found
    echo Creating .env from .env.example...
    copy .env.example .env
    echo ✓ .env file created
    echo.
    echo ⚠️  IMPORTANT: Edit .env file with your configuration:
    echo    - DATABASE_URL (PostgreSQL connection^)
    echo    - SECRET_KEY (random 32+ character string^)
    echo.
    pause
) else (
    echo ✓ .env file exists
)
echo.

REM Create logs directory
if not exist "logs" mkdir logs
echo ✓ Logs directory ready
echo.

echo ====================================================
echo Setup complete! 🎉
echo.
echo Next steps:
echo.
echo 1. Setup PostgreSQL database:
echo    createdb highway_accident_detection
echo    psql -d highway_accident_detection -c "CREATE EXTENSION postgis;"
echo.
echo 2. Create admin user:
echo    python -m app.scripts.create_admin
echo.
echo 3. Run the application:
echo    uvicorn app.main:app --reload
echo.
echo 4. Access the API:
echo    - API: http://localhost:8000
echo    - Docs: http://localhost:8000/docs
echo    - Health: http://localhost:8000/api/v1/admin/health
echo.
echo ====================================================
echo.
pause
