"""
AstroMind: Quick LAN Connection Diagnostic Tool
Tests connection from this Earth PC to the Space Station PC.
"""

import sys
import os
import json
import urllib.request
import subprocess

def test_connection():
    print("=" * 65)
    print("🛰️ ASTROMIND: EARTH -> SPACE STATION LAN CONNECTION TEST")
    print("=" * 65)
    
    # 1. Load config if exists
    config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "space_link_config.json")
    default_ip = "192.168.0.125:5000"
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                d = json.load(f)
                default_ip = f"{d.get('space_host', '192.168.0.125')}:{d.get('space_port', 5000)}"
        except Exception:
            pass

    target = input(f"\nEnter Space Station IP:Port [Press Enter for {default_ip}]: ").strip()
    if not target:
        target = default_ip

    clean = target.replace("http://", "").replace("https://", "").strip().rstrip("/")
    if ":" in clean:
        host, port = clean.split(":")[:2]
    else:
        host, port = clean, "5000"

    print(f"\n[1/3] Testing Ping (ICMP) to Space PC ({host})...")
    res = subprocess.run(["ping", "-n", "2", "-w", "1000", host], capture_output=True, text=True)
    if res.returncode == 0:
        print(f"  ✅ SUCCESS: Host {host} is REACHABLE over Wi-Fi/LAN!")
    else:
        print(f"  ❌ WARNING: Ping to {host} failed or timed out.")
        print("     Possible causes:")
        print("     - PC #1 (Space PC) and this PC are not on the same Wi-Fi network.")
        print("     - Windows Firewall on PC #1 is blocking (run 'enable_lan_connection.bat' on PC #1 as Admin).")
        print("     - Router has AP/Client Isolation enabled (try connecting both to mobile hotspot).")

    print(f"\n[2/3] Testing HTTP Telemetry Link to http://{host}:{port}/api/telemetry/live...")
    url = f"http://{host}:{port}/api/telemetry/live"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AstroMind-Diagnostic/1.0"})
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"  ✅ SUCCESS! Space Station Telemetry API responded!")
                print(f"     Station Name: {data.get('station', 'AstroMind Deep Space')}")
                telem = data.get("telemetry", {})
                v = telem.get("vitals", {})
                print(f"     Live Heart Rate: {v.get('heart_rate', 'N/A')} BPM | SpO2: {v.get('spo2', 'N/A')}%")
                print("\n=================================================================")
                print("🎉 EVERYTHING IS WORKING! You can run 'run_earth_station.bat' now!")
                print("=================================================================")
                return
    except urllib.error.URLError as e:
        print(f"  ❌ Connection Failed: {e}")
        if "refused" in str(e).lower() or "10061" in str(e):
            print("     -> Space Station PC is reachable, but the Space Station software is NOT RUNNING on PC #1!")
            print("     -> Start 'run_space_station.bat' on PC #1 first!")
        elif "timed out" in str(e).lower() or "10060" in str(e):
            print("     -> Request timed out. Windows Firewall on PC #1 is likely blocking Port 5000.")
            print("     -> Right-click 'enable_lan_connection.bat' on PC #1 -> 'Run as Administrator'.")
    except Exception as e:
        print(f"  ❌ Error: {e}")

    print("\n=================================================================")
    print("💡 QUICK FIX CHECKLIST:")
    print("1. On Space PC (PC #1): Run 'enable_lan_connection.bat' as Administrator.")
    print("2. On Space PC (PC #1): Run 'run_space_station.bat' (keep it open).")
    print("3. Check that both PCs are connected to the SAME Wi-Fi or Mobile Hotspot.")
    print(f"4. On this Earth PC: In Earth Station, type '{host}:{port}' and click [SYNC].")
    print("=================================================================\n")

if __name__ == "__main__":
    test_connection()
