@echo off
title AstroMind • Enable LAN Wi-Fi Connection
:: Elevate to Administrator automatically
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [AstroMind] Requesting Administrator privileges to configure Windows Firewall...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ===================================================================
echo 🔓 ASTROMIND: ENABLING LAN WI-FI & FIREWALL FOR PC-TO-PC LINK
echo ===================================================================
echo.
echo [1/3] Opening Inbound TCP Port 5000 in Windows Firewall...
netsh advfirewall firewall delete rule name="AstroMind Space Station 5000" >nul 2>&1
netsh advfirewall firewall add rule name="AstroMind Space Station 5000" dir=in action=allow protocol=TCP localport=5000 profile=any >nul 2>&1

echo [2/3] Allowing ICMP Ping Echo across LAN...
netsh advfirewall firewall delete rule name="AstroMind ICMP Ping" >nul 2>&1
netsh advfirewall firewall add rule name="AstroMind ICMP Ping" dir=in action=allow protocol=icmpv4 profile=any >nul 2>&1

echo [3/3] Setting Network Profile to 'Private' (Enables Local Device Discovery)...
powershell -Command "Get-NetConnectionProfile | Set-NetConnectionProfile -NetworkCategory Private -ErrorAction SilentlyContinue"

echo.
echo ===================================================================
echo ✅ SUCCESS! Port 5000 and Ping are OPEN on Windows Firewall!
echo.
echo 🛰️ THIS PC's WI-FI IP ADDRESS IS:
powershell -Command "$ip = (Get-NetIPAddress -InterfaceAlias 'Wi-Fi' -AddressFamily IPv4 -ErrorAction SilentlyContinue).IPAddress; if (!$ip) { $ip = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -like '192.168.*' -and $_.InterfaceAlias -notlike '*VMware*' } | Select-Object -First 1).IPAddress }; Write-Host ('   >>> ' + $ip + ':5000 <<<') -ForegroundColor Green"
echo.
echo 👉 ON PC #2 (EARTH STATION PC):
echo    1. Open Earth Station
echo    2. In the 'Space PC IP' box, enter the IP shown above (e.g. 192.168.0.125:5000)
echo    3. Click [SYNC] or hit Enter!
echo ===================================================================
echo.
pause
