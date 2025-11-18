@echo off
title Trading Agent Startup

echo ======================================================
echo           Starting Trading Agent and Dashboard
echo ======================================================
echo.

REM This script automates the setup and execution of the trading agent's live mode.

REM --- 1. Setup Python Virtual Environment ---
if not exist venv (
    echo Creating Python virtual environment...
    py -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please ensure Python is installed and in your PATH.
        goto :eof
    )
)

REM --- 2. Activate Virtual Environment and Install Dependencies ---
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

if %errorlevel% neq 0 (
    echo Failed to install dependencies from requirements.txt.
    goto :eof
)

REM --- 3. Run the Main Application in Live Mode ---
echo Starting the application in live mode...
py main.py live

echo.
echo Application finished.
deactivate

echo.
echo ======================================================
echo           Script finished. Press any key to exit.
echo ======================================================
pause >nul
