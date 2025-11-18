@echo off
REM This script automates the setup and execution of the trading agent.
REM Usage:
REM   run.bat live      - Runs the agent in live trading mode.
REM   run.bat backtest  - Runs a sample backtest.

REM --- 1. Check for required argument ---
if "%1"=="" (
    echo Usage: %0 [live^|backtest]
    goto :eof
)

REM --- 2. Setup Python Virtual Environment ---
if not exist venv (
    echo Creating Python virtual environment...
    py -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please ensure Python is installed and in your PATH.
        goto :eof
    )
)

REM --- 3. Activate Virtual Environment and Install Dependencies ---
echo Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt -q

if %errorlevel% neq 0 (
    echo Failed to install dependencies from requirements.txt.
    goto :eof
)

REM --- 4. Run the Main Application ---
echo Starting the application in %1 mode...
py main.py %1

echo.
echo Application finished.
deactivate
