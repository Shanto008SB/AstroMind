@echo off
title AstroMind • Deep Space Station Client
echo ===================================================================
echo 🚀 ASTROMIND: DEEP SPACE STATION CREW HEALTH SYSTEM
echo Autonomous Edge AI • 3D Biometric Face Mesh • Danger Siren
echo Real-Time S-Band Telemetry Server listening on Port 5000
echo ===================================================================
echo.
echo 📡 LOCAL WI-FI / NETWORK IP OF THIS SPACE STATION PC:
powershell -Command "$ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like '*Wi-Fi*' -or $_.InterfaceAlias -like '*Wireless*' } | Select-Object -ExpandProperty IPAddress -ErrorAction SilentlyContinue); if (!$ip) { $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' -and $_.InterfaceAlias -notlike '*VMware*' } | Select-Object -ExpandProperty IPAddress -ErrorAction SilentlyContinue) }; if ($ip) { Write-Host ('   >>> ' + $ip + ':5000 <<<') -ForegroundColor Green } else { Write-Host '   >>> 127.0.0.1:5000 <<<' -ForegroundColor Yellow }"
echo.
echo 👉 ON PC #2 (EARTH STATION): Enter the IP above into the 'Space PC IP' box!
echo 👉 NOTE: If connecting from another PC, make sure you ran
echo    'enable_lan_connection.bat' (Run as Administrator) once!
echo ===================================================================
echo.
python main.py
pause
