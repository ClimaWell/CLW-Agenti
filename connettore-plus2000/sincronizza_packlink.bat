@echo off
chcp 65001 > nul
title CLIMAWELL - SINCRONIZZAZIONE PACKLINK PRO
echo =====================================================================
echo  CLIMAWELL COMMERCIAL HUB - GESTIONE SPEDIZIONI PACKLINK PRO
echo =====================================================================
echo.
echo  1. Creazione bozze per ordini pronti e cantieri
echo  2. Sincronizzazione tracking e lettere di vettura per ordini spediti
echo.
echo =====================================================================
python packlink_manager.py --auto
echo.
echo =====================================================================
echo  OPERAZIONE COMPLETATA!
echo  Accedi su https://pro.packlink.it per confermare le bozze e stampare.
echo =====================================================================
pause

