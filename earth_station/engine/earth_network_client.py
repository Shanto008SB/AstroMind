"""
AstroMind Earth Station: Deep Space S-Band Network Client
Communicates over Wi-Fi/LAN with the Space Station on PC #1 (or localhost).
Fetches live telemetry asynchronously in background, dispatches ground commands,
and synchronizes crew deployment.
"""

import urllib.request
import urllib.parse
import json
import socket
import threading
import time
import os
from typing import Dict, Any, Optional
from .medical_db import medical_db


CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "space_link_config.json")


class EarthNetworkClient:
    def __init__(self, space_host: str = "127.0.0.1", space_port: int = 5000):
        self.space_host = space_host.strip()
        self.space_port = space_port
        self.is_connected = False
        self.last_error = ""
        self.latest_telemetry: Optional[Dict[str, Any]] = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

        # Load persisted Space Station IP if previously saved
        self._load_config()

        # Start non-blocking background polling thread
        self._worker_thread = threading.Thread(target=self._background_poll_worker, daemon=True)
        self._worker_thread.start()

    def _load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_host = data.get("space_host")
                    saved_port = data.get("space_port", 5000)
                    if saved_host:
                        self.space_host = saved_host
                        self.space_port = saved_port
        except Exception:
            pass

    def _save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"space_host": self.space_host, "space_port": self.space_port}, f, indent=2)
        except Exception:
            pass

    @property
    def base_url(self) -> str:
        host = self.space_host.replace("http://", "").replace("https://", "").strip().rstrip("/")
        return f"http://{host}:{self.space_port}"

    def set_space_address(self, address_str: str):
        """Allows user to change Space Station IP (e.g. '192.168.0.125', '192.168.0.125:5000', or URL)."""
        clean = address_str.strip()
        if clean.startswith("http://"):
            clean = clean[7:]
        elif clean.startswith("https://"):
            clean = clean[8:]
        clean = clean.split("/")[0].strip()
        
        if ":" in clean:
            parts = clean.split(":")
            self.space_host = parts[0].strip()
            try:
                self.space_port = int(parts[1].strip())
            except Exception:
                self.space_port = 5000
        else:
            self.space_host = clean
            self.space_port = 5000

        self._save_config()
        # Trigger immediate poll in thread
        threading.Thread(target=self._poll_once, daemon=True).start()

    def _poll_once(self):
        url = f"{self.base_url}/api/telemetry/live"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AstroMind-Earth-Client/2.0"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    telem = data.get("telemetry", {})
                    with self._lock:
                        self.latest_telemetry = telem
                        self.is_connected = True
                        self.last_error = ""

                    # Cache to local SQLite
                    if telem:
                        v = telem.get("vitals", {})
                        c = telem.get("cabin", {})
                        medical_db.sync_telemetry_to_db(
                            active_astro_id=telem.get("active_id", "sarah"),
                            vitals=v,
                            cabin=c,
                            is_emergency=telem.get("is_emergency", False),
                            emergency_reason=telem.get("emergency_reason", ""),
                            readiness_score=telem.get("analysis", {}).get("readiness_score", 85)
                        )
                    return True
        except Exception as e:
            with self._lock:
                self.is_connected = False
                self.last_error = str(e)
            return False

    def _background_poll_worker(self):
        """Background daemon polling worker: keeps UI silky smooth with 0ms freezing."""
        while not self._stop_event.is_set():
            self._poll_once()
            time.sleep(0.7)

    def fetch_live_telemetry(self) -> Optional[Dict[str, Any]]:
        """
        Instant, non-blocking telemetry getter.
        Returns the background thread's latest received telemetry, or falls back to local DB cache.
        """
        with self._lock:
            if self.is_connected and self.latest_telemetry:
                return self.latest_telemetry

        # Fallback to local SQLite cache if offline
        cached = medical_db.get_live_telemetry()
        if cached:
            return {
                "active_id": cached.get("active_astronaut_id", "sarah"),
                "vitals": {
                    "heart_rate": cached.get("heart_rate", 72),
                    "spo2": cached.get("spo2", 98.4),
                    "hrv": cached.get("hrv", 58.0),
                    "fatigue_level": cached.get("fatigue_level", 18)
                },
                "cabin": {
                    "co2_percent": cached.get("co2", 0.31),
                    "temp_c": cached.get("temp", 21.6),
                    "radiation_msv": cached.get("radiation", 0.18)
                },
                "is_emergency": cached.get("is_emergency", False),
                "emergency_reason": cached.get("emergency_reason", "")
            }
        return None

    def fetch_telemetry_for_astronaut(
        self, astro_id: str, astro_data: dict
    ) -> Dict[str, Any]:
        """
        Returns live or best-available telemetry for a SPECIFIC astronaut.
        
        - If astronaut IS the currently active one in Space Station → returns real live telemetry.
        - If astronaut is a DIFFERENT crew member → builds personalized vitals from their
          DB medical records + baseline, so Earth can still analyse any crew member.
        - Always returns a well-formed dict (never None) so callers don't need to guard.
        """
        live = self.fetch_live_telemetry()

        # Case 1: Astronaut is the active monitored one in Space
        if live and live.get("active_id") == astro_id:
            return {
                "vitals": live.get("vitals", {}),
                "cabin": live.get("cabin", {}),
                "is_emergency": live.get("is_emergency", False),
                "emergency_reason": live.get("emergency_reason", ""),
                "source": "LIVE_TELEMETRY"
            }

        # Case 2: Different crew member — build from DB records + baseline
        records = medical_db.get_records_by_date(astro_id, limit=1)
        baseline_hr  = int(astro_data.get("baseline_hr", 72))
        baseline_spo2 = float(astro_data.get("baseline_spo2", 98.4))
        baseline_hrv  = float(astro_data.get("baseline_hrv", 58.0))
        baseline_fat  = int(astro_data.get("fatigue", 18))

        if records:
            rec = records[0]
            vitals = {
                "heart_rate":   int(rec.get("heart_rate", baseline_hr)),
                "spo2":         float(rec.get("spo2", baseline_spo2)),
                "hrv":          float(rec.get("hrv", baseline_hrv)),
                "fatigue_level": int(rec.get("fatigue_level", baseline_fat)),
            }
        else:
            vitals = {
                "heart_rate":   baseline_hr,
                "spo2":         baseline_spo2,
                "hrv":          baseline_hrv,
                "fatigue_level": baseline_fat,
            }

        # Cabin — use live cabin if connected (same pressurized habitat), else defaults
        if live and live.get("cabin"):
            cabin = live["cabin"]
        else:
            cabin = {"co2_percent": 0.31, "temp_c": 21.6, "radiation_msv": 0.18}

        return {
            "vitals": vitals,
            "cabin": cabin,
            "is_emergency": False,
            "emergency_reason": "",
            "source": "DB_BASELINE" if not records else "DB_RECORDS"
        }


    def send_command(self, cmd_dict: Dict[str, Any]) -> bool:
        url = f"{self.base_url}/api/telemetry/command"
        try:
            payload = json.dumps(cmd_dict).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def deploy_group_to_space(self, group_id: str) -> bool:
        """Transmits deployment command over Wi-Fi to Space Station!"""
        # 1. Update local database
        medical_db.set_active_space_group(group_id)
        
        # 2. Transmit to remote Space Station if reachable
        url = f"{self.base_url}/api/roster/deploy_group"
        try:
            payload = json.dumps({"group_id": group_id}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status == 200
        except Exception:
            return True # Local updated

    def add_astronaut_to_space(self, astro_data: Dict[str, Any]) -> bool:
        medical_db.add_astronaut(astro_data)
        url = f"{self.base_url}/api/roster/add_astronaut"
        try:
            payload = json.dumps(astro_data).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status == 200
        except Exception:
            return True

    def update_astronaut_on_space(self, astro_id: str, updates: Dict[str, Any]) -> bool:
        medical_db.update_astronaut(astro_id, updates)
        url = f"{self.base_url}/api/roster/update_astronaut"
        try:
            payload = json.dumps({"id": astro_id, "updates": updates}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return resp.status == 200
        except Exception:
            return True


# Global client instance
network_client = EarthNetworkClient()
