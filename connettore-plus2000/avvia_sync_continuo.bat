@echo off
title CLIMAWELL - SINCRONIZZATORE REALTIME (SUPABASE - PLUS 2000)
chcp 65001 >nul
cd /d "%~dp0"

echo ====================================================================
echo  CLIMAWELL - CONNETTORE AUTOMATICO PLUS 2000 ^<--^> SUPABASE
echo ====================================================================
echo  Questo servizio rimane in esecuzione in background per scaricare
echo  in tempo reale (ogni 30 secondi) le offerte e gli ordini inseriti
echo  dagli agenti direttamente su Plus 2000 (SQL Server).
echo.
echo  Premi CTRL+C per interrompere.
echo ====================================================================
echo.

python servizio_sync_continuo.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERRORE] Il servizio si e' interrotto con errore %ERRORLEVEL%.
    pause
)
