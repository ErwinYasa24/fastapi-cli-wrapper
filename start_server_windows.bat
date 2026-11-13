@echo off
title AGY FastAPI Server
cd /d "%~dp0"

echo ========================================================
echo   Menjalankan Server AGY FastAPI Wrapper (Windows)
echo ========================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python belum terinstall atau belum masuk ke PATH!
    echo Silakan install Python dari python.org dan centang "Add Python to PATH".
    pause
    exit /b 1
)

if not exist "venv" (
    echo Membuat virtual environment Python...
    python -m venv venv
)

call venv\Scripts\activate

echo Memeriksa dan menginstall dependensi...
pip install -r requirements.txt --quiet

echo.
echo ========================================================
echo   Server aktif di http://localhost:8000
echo   Tekan Ctrl+C untuk menghentikan server
echo ========================================================
echo.

python main.py
pause
