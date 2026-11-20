@echo off
title Climawell - Riavvio Server Magazzino Plus2000
color 0A
cls
echo =====================================================================
echo    CLIMAWELL - RIAVVIO SERVER MAGAZZINO PLUS2000 (PORTA 5000)
echo =====================================================================
echo.
echo 1. Chiusura istanze precedenti sulla porta 5000...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000') do taskkill /f /pid %%a >nul 2>&1
timeout /t 1 >nul
echo.
echo 2. Avvio nuovo server magazzino con filtri giacenza rigorosi...
echo    Accessibile su: http://localhost:5000 oppure http://192.168.1.47:5000
echo =====================================================================
echo.
cd /d "%~dp0"
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRORE]: Impossibile avviare il server Python.
    pause
)

