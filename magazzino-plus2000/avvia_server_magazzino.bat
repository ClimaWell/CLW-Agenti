@echo off
title Climawell - Server Magazzino e Inventario Plus2000
color 0B
cls
echo =====================================================================
echo    CLIMAWELL - GESTIONE MAGAZZINO E INVENTARIO PLUS2000
echo =====================================================================
echo.
echo Avvio del server locale per dispositivi magazzinieri (porta 5000)...
echo.
cd /d "%~dp0"
python app.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRORE]: Impossibile avviare il server Python.
    pause
)
