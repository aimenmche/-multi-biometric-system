@echo off
title Multi-Biometric Identity Verification System
echo ============================================================
echo   Multi-Biometric Identity Verification System
echo ============================================================
echo.

cd /d "%~dp0"

echo [1/3] Installing dependencies...
cd backend
call python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Seeding database...
python seed.py
if %errorlevel% neq 0 (
    echo WARNING: Database seeding had issues
)

echo.
echo [3/3] Starting server...
echo.
echo   Server: http://localhost:8000
echo   Frontend: http://localhost:8000/static/index.html
echo.
echo   Default credentials:
echo     Admin:   admin / admin123
echo     Student: student1 / student123
echo.
echo   Press Ctrl+C to stop the server.
echo.

start http://localhost:8000/static/index.html

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
