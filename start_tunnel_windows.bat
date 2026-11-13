@echo off
title Cloudflare Tunnel untuk Chiko (Port 8000)
cd /d "%~dp0"

echo ========================================================
echo   Membuka URL HTTPS Publik untuk Bot Chiko
echo ========================================================

where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    if not exist "cloudflared.exe" (
        echo [INFO] Mengunduh cloudflared.exe otomatis...
        curl -L -o cloudflared.exe https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
    )
    echo Menjalankan tunnel via cloudflared.exe...
    cloudflared.exe tunnel --url http://localhost:8000
) else (
    echo Menjalankan tunnel via cloudflared sistem...
    cloudflared tunnel --url http://localhost:8000
)

pause
