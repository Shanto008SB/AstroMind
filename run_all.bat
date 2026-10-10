@echo off
title AstroMind • NASA Space & Earth Dual Suite Launcher
echo ===================================================================
echo 🚀 ASTROMIND: NASA SPACE APPS CHALLENGE • DUAL MISSION SUITE
echo ===================================================================
echo [1] Launch Deep Space Station Software (space_station_app.py)
echo [2] Launch NASA Houston Earth Mission Control (earth_control_app.py)
echo [3] Launch BOTH Apps Side-by-Side (Space + Earth Link Demo)
echo ===================================================================
set /p choice="Enter selection (1, 2, or 3): "

if "%choice%"=="1" (
    start "AstroMind Space Station" python space_station\main.py
) else if "%choice%"=="2" (
    start "NASA Houston Earth Control" python earth_station\main.py
) else if "%choice%"=="3" (
    echo Launching Space Station Client and Earth Mission Control...
    start "AstroMind Space Station" python space_station\main.py
    timeout /t 3 >nul
    start "NASA Houston Earth Control" python earth_station\main.py
) else (
    echo Invalid selection. Launching Space Station by default...
    start "AstroMind Space Station" python space_station\main.py
)
