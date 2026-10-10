"""
AstroMind: Shared Telemetry State & IoT Bridge
Maintains real-time astronaut vitals, allows external mobile phone control,
synchronizes deployed space crew with medical database, and bridges to Earth Mission Control.
"""

import threading
import time
from typing import Dict, Any
from .anomaly_detector import AnomalyDetector
from .medical_db import medical_db


class SharedTelemetryState:
    def __init__(self):
        self.lock = threading.Lock()
        self.detector = AnomalyDetector()

        # Load deployed space crew dynamically from database
        self.crew_members = {}
        self.active_id = "sarah"
        self.crew_revision = 0
        self.reload_crew_from_db()
        self.is_emergency = False
        self.emergency_reason = ""
        self.last_update_source = "System Auto"
        self.last_update_time = time.time()

        # Dynamic Vitals
        self.vitals = {
            "heart_rate": 72,
            "spo2": 98.4,
            "hrv": 58.0,
            "fatigue_level": 18,
            "blink_rate": 14,
            "eye_aspect_ratio": 0.32
        }

        # Cabin Telemetry
        self.cabin = {
            "co2_percent": 0.31,
            "cabin_pressure_kpa": 101.3,
            "temp_c": 21.6,
            "radiation_msv": 0.18
        }

        # AI Doctor text
        self.ai_doctor_note = (
            "AstroMind AI Doctor online. Optimal physiological equilibrium established for mission crew. "
            "Cardiovascular sinus rhythm, SpO2, and autonomic tone are within mission safety baselines."
        )

        # Initial live sync to database for Earth Mission Control
        self._sync_live()

    def reload_crew_from_db(self):
        """
        Reloads the currently deployed space mission crew from SQLite database.
        Space Station ONLY displays astronauts deployed for the active mission!
        """
        with self.lock:
            db_crew = medical_db.get_active_space_crew()
            if db_crew:
                self.crew_members = db_crew
                if self.active_id not in self.crew_members:
                    self.active_id = list(self.crew_members.keys())[0]
            elif not self.crew_members:
                # Default safety fallback
                self.crew_members = {
                    "sarah": {
                        "id": "sarah", "serial": "01", "name": "Capt. Sarah Connor",
                        "callsign": "ARES-LEAD", "role": "Mission Commander / EVA Specialist",
                        "avatar": "static/assets/astronaut_sarah.jpg", "baseline_hr": 72,
                        "baseline_spo2": 98.4, "baseline_hrv": 58.0, "fatigue": 18
                    }
                }
            self.crew_revision += 1

    @property
    def active_astronaut(self) -> Dict[str, Any]:
        with self.lock:
            return self.crew_members.get(self.active_id, {
                "id": self.active_id, "name": "Astronaut", "role": "Crew Member",
                "avatar": "static/assets/astronaut_sarah.jpg", "serial": "01"
            })

    def set_active_astronaut(self, astronaut_id: str):
        with self.lock:
            if astronaut_id in self.crew_members:
                self.active_id = astronaut_id
                m = self.crew_members[astronaut_id]
                self.vitals["heart_rate"] = m.get("baseline_hr", 72)
                self.vitals["spo2"] = m.get("baseline_spo2", 98.4)
                self.vitals["hrv"] = m.get("baseline_hrv", 58.0)
                self.vitals["fatigue_level"] = m.get("fatigue", 18)
                self.is_emergency = False
                self.last_update_source = "Desktop Profile Switch"
                self.last_update_time = time.time()
                self._sync_live()

    def update_from_phone(self, hr=None, spo2=None, hrv=None, fatigue=None, co2=None, temp=None, radiation=None, is_emergency=None):
        """
        Called when user adjusts controls on their mobile phone or simulated telemetry!
        """
        with self.lock:
            if hr is not None: self.vitals["heart_rate"] = int(hr)
            if spo2 is not None: self.vitals["spo2"] = round(float(spo2), 1)
            if hrv is not None: self.vitals["hrv"] = round(float(hrv), 1)
            if fatigue is not None: self.vitals["fatigue_level"] = int(fatigue)
            if co2 is not None: self.cabin["co2_percent"] = round(float(co2), 2)
            if temp is not None: self.cabin["temp_c"] = round(float(temp), 1)
            if radiation is not None: self.cabin["radiation_msv"] = round(float(radiation), 2)
            if is_emergency is not None: self.is_emergency = bool(is_emergency)

            # Auto trigger emergency if parameters are dangerous
            if self.vitals["spo2"] < 90.0 or self.vitals["heart_rate"] < 50:
                self.is_emergency = True
                self.emergency_reason = f"CRITICAL HYPOXIA / BRADYCARDIA (SpO2: {self.vitals['spo2']}%, HR: {self.vitals['heart_rate']} BPM)"
            elif is_emergency is False:
                self.is_emergency = False

            self.last_update_source = "Mobile Phone IoT Controller"
            self.last_update_time = time.time()
            self._sync_live()

    def _sync_live(self):
        """Internal helper to write real-time telemetry to SQLite for Earth Mission Control."""
        try:
            readiness = 85
            if self.vitals["spo2"] < 90.0 or self.vitals["heart_rate"] < 50:
                readiness = 20
            elif self.vitals["fatigue_level"] >= 65:
                readiness = 50
            medical_db.sync_telemetry_to_db(
                active_astro_id=self.active_id,
                vitals=self.vitals,
                cabin=self.cabin,
                is_emergency=self.is_emergency,
                emergency_reason=self.emergency_reason,
                readiness_score=readiness
            )
        except Exception:
            pass

    def get_full_state(self) -> Dict[str, Any]:
        with self.lock:
            if self.active_id not in self.crew_members and self.crew_members:
                self.active_id = list(self.crew_members.keys())[0]

            active_m = self.crew_members.get(self.active_id, {
                "id": self.active_id, "name": "Astronaut", "role": "Crew Member",
                "avatar": "static/assets/astronaut_sarah.jpg", "serial": "01"
            })
            analysis = self.detector.evaluate_crew_member(self.vitals, self.cabin)
            if self.is_emergency:
                analysis["is_emergency"] = True
                analysis["alert_level"] = "CRITICAL"
                analysis["readiness_score"] = min(20, analysis["readiness_score"])
                analysis["readiness_status"] = "CRITICAL MEDICAL EMERGENCY"

            # Sync live periodically
            self._sync_live()

            return {
                "active_id": self.active_id,
                "astronaut": active_m,
                "vitals": dict(self.vitals),
                "cabin": dict(self.cabin),
                "analysis": analysis,
                "is_emergency": self.is_emergency,
                "emergency_reason": self.emergency_reason,
                "ai_doctor_note": self.ai_doctor_note,
                "last_update_source": self.last_update_source,
                "crew_list": self.crew_members,
                "active_group": medical_db.get_active_space_group(),
                "crew_revision": self.crew_revision
            }


# Global singleton
state = SharedTelemetryState()
