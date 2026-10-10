"""
AstroMind: SQLite Medical Database & Longitudinal Trend Analyzer
Stores daily astronaut health records, mission group rosters,
real-time Space-Earth telemetry sync, and computes comparative health trends.
"""

import os
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "medical_records.db")


class MedicalDatabase:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()
        self._seed_initial_roster_and_history()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. Mission Groups Table (Expeditions / Deployments)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS mission_groups (
                    group_id TEXT PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    status TEXT DEFAULT 'ACTIVE_IN_SPACE',
                    launch_date TEXT,
                    return_date TEXT,
                    created_at TEXT
                )
            """)

            # 2. Astronaut Master Roster Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS astronaut_roster (
                    id TEXT PRIMARY KEY,
                    group_id TEXT NOT NULL,
                    serial TEXT NOT NULL,
                    name TEXT NOT NULL,
                    callsign TEXT,
                    role TEXT NOT NULL,
                    avatar TEXT DEFAULT 'static/assets/astronaut_sarah.jpg',
                    baseline_hr INTEGER DEFAULT 72,
                    baseline_spo2 REAL DEFAULT 98.4,
                    baseline_hrv REAL DEFAULT 58.0,
                    fatigue INTEGER DEFAULT 18,
                    is_deployed INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'IN_SPACE',
                    notes TEXT,
                    FOREIGN KEY(group_id) REFERENCES mission_groups(group_id)
                )
            """)

            # 3. Live Telemetry Bridge Table (Synchronizes Space Station with Earth Mission Control)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS telemetry_live (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    active_astronaut_id TEXT,
                    heart_rate INTEGER,
                    spo2 REAL,
                    hrv REAL,
                    fatigue_level INTEGER,
                    readiness_score INTEGER,
                    co2 REAL,
                    temp REAL,
                    radiation REAL,
                    is_emergency INTEGER,
                    emergency_reason TEXT,
                    last_sync_timestamp REAL
                )
            """)

            # 4. Longitudinal Health Logs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS astronaut_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    astronaut_id TEXT NOT NULL,
                    group_id TEXT DEFAULT 'expedition_72',
                    timestamp TEXT NOT NULL,
                    date_str TEXT NOT NULL,
                    time_str TEXT NOT NULL,
                    heart_rate INTEGER NOT NULL,
                    spo2 REAL NOT NULL,
                    hrv REAL NOT NULL,
                    fatigue INTEGER NOT NULL,
                    readiness_score INTEGER NOT NULL,
                    status_eval TEXT NOT NULL,
                    trend_diff TEXT,
                    clinical_notes TEXT,
                    snapshot_path TEXT,
                    trigger_type TEXT DEFAULT 'AUTO_30MIN'
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_astro_date ON astronaut_logs(astronaut_id, date_str);")
            
            # Migration check: ensure group_id column exists
            cursor.execute("PRAGMA table_info(astronaut_logs)")
            cols = [c["name"] for c in cursor.fetchall()]
            if "group_id" not in cols:
                cursor.execute("ALTER TABLE astronaut_logs ADD COLUMN group_id TEXT DEFAULT 'expedition_72'")
            
            # 5. Clinical Dossiers & Historical Case Reports Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clinical_dossiers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    astronaut_id TEXT NOT NULL,
                    astronaut_name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    report_title TEXT NOT NULL,
                    vitals_summary TEXT NOT NULL,
                    cabin_summary TEXT NOT NULL,
                    status_eval TEXT NOT NULL,
                    historical_match_text TEXT NOT NULL,
                    recovery_protocol_text TEXT NOT NULL,
                    ai_suggestions_text TEXT NOT NULL,
                    full_report_text TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dossier_astro ON clinical_dossiers(astronaut_id, created_at);")

            conn.commit()

    # =========================================================================
    # MISSION GROUPS CRUD (Administered from Earth Mission Control)
    # =========================================================================
    def get_all_groups(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mission_groups ORDER BY created_at DESC")
            return [dict(r) for r in cursor.fetchall()]

    def get_active_space_group(self) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM mission_groups WHERE status = 'ACTIVE_IN_SPACE' LIMIT 1")
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_group(self, group_id: str, group_name: str, status: str = "SCHEDULED_TRAINING", launch_date: str = "", return_date: str = "") -> bool:
        clean_id = group_id.strip().lower().replace(" ", "_")
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO mission_groups (group_id, group_name, status, launch_date, return_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (clean_id, group_name, status, launch_date, return_date, now_str))
            conn.commit()
            return True

    def set_active_space_group(self, target_group_id: str) -> bool:
        """
        Earth command: Sets the specific group as currently deployed in Deep Space.
        All other groups are marked non-active.
        Astronauts of this group become deployed; others marked not in space.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE mission_groups SET status = 'HISTORICAL_RETURNED' WHERE status = 'ACTIVE_IN_SPACE'")
            cursor.execute("UPDATE mission_groups SET status = 'ACTIVE_IN_SPACE' WHERE group_id = ?", (target_group_id,))
            
            # Update astronaut deployment status
            cursor.execute("UPDATE astronaut_roster SET is_deployed = 0, status = 'ON_EARTH' WHERE group_id != ?", (target_group_id,))
            cursor.execute("UPDATE astronaut_roster SET is_deployed = 1, status = 'IN_SPACE' WHERE group_id = ?", (target_group_id,))
            conn.commit()
            return True

    def delete_group(self, group_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM astronaut_roster WHERE group_id = ?", (group_id,))
            cursor.execute("DELETE FROM mission_groups WHERE group_id = ?", (group_id,))
            conn.commit()
            return True

    # =========================================================================
    # ASTRONAUT ROSTER CRUD (Administered from Earth Mission Control)
    # =========================================================================
    def get_active_space_crew(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns only the astronauts currently deployed in space for the active mission group.
        Used by Space Station software to display ONLY the deployed crew!
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.* FROM astronaut_roster r
                JOIN mission_groups g ON r.group_id = g.group_id
                WHERE g.status = 'ACTIVE_IN_SPACE' AND r.is_deployed = 1
                ORDER BY r.serial ASC
            """)
            rows = cursor.fetchall()
            crew_dict = {}
            for r in rows:
                item = dict(r)
                crew_dict[item["id"]] = item
            return crew_dict

    def get_astronauts_by_group(self, group_id: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM astronaut_roster WHERE group_id = ? ORDER BY serial ASC", (group_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_all_astronauts(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT r.*, g.group_name FROM astronaut_roster r
                LEFT JOIN mission_groups g ON r.group_id = g.group_id
                ORDER BY r.group_id, r.serial ASC
            """)
            return [dict(r) for r in cursor.fetchall()]

    def get_astronaut_by_id(self, astro_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM astronaut_roster WHERE id = ?", (astro_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def add_astronaut(self, data: Dict[str, Any]) -> bool:
        """
        Adds a new astronaut to a mission group from Earth Mission Control.
        """
        cid = data["id"].strip().lower().replace(" ", "_")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO astronaut_roster 
                (id, group_id, serial, name, callsign, role, avatar, baseline_hr, baseline_spo2, baseline_hrv, fatigue, is_deployed, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                cid,
                data.get("group_id", "expedition_72"),
                data.get("serial", "05"),
                data.get("name", "New Astronaut"),
                data.get("callsign", "CREW-SPEC"),
                data.get("role", "Mission Specialist"),
                data.get("avatar", "static/assets/astronaut_sarah.jpg"),
                int(data.get("baseline_hr", 72)),
                float(data.get("baseline_spo2", 98.4)),
                float(data.get("baseline_hrv", 58.0)),
                int(data.get("fatigue", 18)),
                int(data.get("is_deployed", 1)),
                data.get("status", "IN_SPACE"),
                data.get("notes", "")
            ))
            conn.commit()
            return True

    def update_astronaut(self, astro_id: str, updates: Dict[str, Any]) -> bool:
        """
        Updates details for an astronaut from Earth Mission Control.
        """
        allowed_keys = ["name", "callsign", "role", "serial", "avatar", "baseline_hr", "baseline_spo2", "baseline_hrv", "fatigue", "is_deployed", "status", "notes", "group_id"]
        set_clauses = []
        vals = []
        for k, v in updates.items():
            if k in allowed_keys:
                set_clauses.append(f"{k} = ?")
                vals.append(v)
        if not set_clauses:
            return False
        vals.append(astro_id)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE astronaut_roster SET {', '.join(set_clauses)} WHERE id = ?", tuple(vals))
            conn.commit()
            return True

    def remove_astronaut(self, astro_id: str) -> bool:
        """
        Deletes or removes an astronaut from the roster.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM astronaut_roster WHERE id = ?", (astro_id,))
            conn.commit()
            return True

    def archive_astronaut_returned(self, astro_id: str) -> bool:
        """
        Marks an astronaut as returned to Earth. Their historical health logs
        remain fully preserved for mission analysis!
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE astronaut_roster 
                SET is_deployed = 0, status = 'RETURNED_TO_EARTH', notes = 'Mission completed. Returned safely to Earth.'
                WHERE id = ?
            """, (astro_id,))
            conn.commit()
            return True

    # =========================================================================
    # REAL-TIME SPACE-EARTH TELEMETRY BRIDGE
    # =========================================================================
    def sync_telemetry_to_db(
        self,
        active_astro_id: str,
        vitals: Dict[str, Any],
        cabin: Dict[str, Any],
        is_emergency: bool,
        emergency_reason: str = "",
        readiness_score: int = 85
    ) -> bool:
        """
        Called by Space Station to sync live vitals into SQLite for Earth Mission Control.
        """
        now_ts = time.time()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO telemetry_live 
                (id, active_astronaut_id, heart_rate, spo2, hrv, fatigue_level, readiness_score, co2, temp, radiation, is_emergency, emergency_reason, last_sync_timestamp)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                active_astro_id,
                int(vitals.get("heart_rate", 72)),
                float(vitals.get("spo2", 98.4)),
                float(vitals.get("hrv", 58.0)),
                int(vitals.get("fatigue_level", 18)),
                int(readiness_score),
                float(cabin.get("co2_percent", 0.31)),
                float(cabin.get("temp_c", 21.6)),
                float(cabin.get("radiation_msv", 0.18)),
                1 if is_emergency else 0,
                emergency_reason,
                now_ts
            ))
            conn.commit()
            return True

    def get_live_telemetry(self) -> Optional[Dict[str, Any]]:
        """
        Called by Earth Mission Control to fetch real-time Space Station vitals.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM telemetry_live WHERE id = 1")
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d["is_emergency"] = bool(d["is_emergency"])
                return d
            return None

    # =========================================================================
    # HEALTH LOGGING & LONGITUDINAL TRENDS
    # =========================================================================
    def log_record(
        self,
        astronaut_id: str,
        vitals: Dict[str, Any],
        analysis: Dict[str, Any],
        clinical_note: str,
        snapshot_path: str = "",
        trigger_type: str = "AUTO_30MIN",
        group_id: str = "expedition_72"
    ) -> Dict[str, Any]:
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        iso_str = now.isoformat()

        hr = vitals.get("heart_rate", 72)
        spo2 = vitals.get("spo2", 98.4)
        hrv = vitals.get("hrv", 58.0)
        fatigue = vitals.get("fatigue_level", 20)
        readiness = analysis.get("readiness_score", 85)

        comparative = self.calculate_comparative_trend(astronaut_id, hr, spo2, hrv, fatigue, readiness)
        status_eval = comparative["status_eval"]
        trend_diff = comparative["trend_diff_text"]

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO astronaut_logs 
                (astronaut_id, group_id, timestamp, date_str, time_str, heart_rate, spo2, hrv, fatigue, readiness_score, status_eval, trend_diff, clinical_notes, snapshot_path, trigger_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                astronaut_id, group_id, iso_str, date_str, time_str,
                hr, spo2, hrv, fatigue, readiness,
                status_eval, trend_diff, clinical_note,
                snapshot_path, trigger_type
            ))
            conn.commit()

        return {
            "date_str": date_str,
            "time_str": time_str,
            "status_eval": status_eval,
            "trend_diff": trend_diff,
            "comparative": comparative,
            "snapshot_path": snapshot_path
        }

    def calculate_comparative_trend(
        self,
        astronaut_id: str,
        current_hr: int,
        current_spo2: float,
        current_hrv: float,
        current_fatigue: int,
        current_readiness: int
    ) -> Dict[str, Any]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT heart_rate, spo2, hrv, fatigue, readiness_score, timestamp, date_str, time_str
                FROM astronaut_logs
                WHERE astronaut_id = ?
                ORDER BY id DESC LIMIT 1
            """, (astronaut_id,))
            row = cursor.fetchone()

        if not row:
            return {
                "status_eval": "🟢 HEALTHY & STABLE (NOMINAL BASELINE)",
                "trend_diff_text": "Initial baseline established. All physiological parameters nominal.",
                "delta_hr": 0, "delta_spo2": 0.0, "delta_fatigue": 0,
                "is_deteriorating": False
            }

        prev_hr = row["heart_rate"]
        prev_spo2 = row["spo2"]
        prev_fatigue = row["fatigue"]
        prev_date = row["date_str"]

        d_hr = current_hr - prev_hr
        d_spo2 = current_spo2 - prev_spo2
        d_fatigue = current_fatigue - prev_fatigue

        is_deteriorating = False
        is_improving = False

        if current_spo2 < 93.0 or current_hr < 50 or current_hr > 115 or current_fatigue >= 65:
            is_deteriorating = True
        elif d_fatigue >= 15 or d_spo2 <= -2.5 or abs(d_hr) >= 20:
            is_deteriorating = True
        elif d_fatigue <= -10 and d_spo2 >= 1.0:
            is_improving = True

        if is_deteriorating:
            status_eval = "🚨 HEALTH DETERIORATING / ACUTE ANOMALY"
            trend_text = (
                f"Negative delta vs {prev_date}: Fatigue +{d_fatigue}%, SpO2 {d_spo2:+.1f}%, Pulse {d_hr:+d} BPM. "
                f"Immediate clinical countermeasure mandated."
            )
        elif is_improving:
            status_eval = "✨ HEALTH IMPROVING / RECOVERING"
            trend_text = (
                f"Positive physiological recovery vs {prev_date}: Fatigue {d_fatigue}% lower, SpO2 {d_spo2:+.1f}%. "
                f"Equilibrium restoring to baseline."
            )
        else:
            status_eval = "🟢 HEALTHY & STABLE (NOMINAL)"
            trend_text = (
                f"Consistent with baseline vs {prev_date}: Pulse {d_hr:+d} BPM, SpO2 {d_spo2:+.1f}%, Fatigue {d_fatigue:+d}%. "
                f"Optimal microgravity homeostasis maintained."
            )

        return {
            "status_eval": status_eval,
            "trend_diff_text": trend_text,
            "delta_hr": d_hr,
            "delta_spo2": d_spo2,
            "delta_fatigue": d_fatigue,
            "is_deteriorating": is_deteriorating
        }

    def get_records_by_date(self, astronaut_id: str, date_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if date_filter and date_filter not in ("ALL", "ALL DATES", ""):
                cursor.execute("""
                    SELECT * FROM astronaut_logs
                    WHERE astronaut_id = ? AND date_str = ?
                    ORDER BY id DESC LIMIT ?
                """, (astronaut_id, date_filter, limit))
            else:
                cursor.execute("""
                    SELECT * FROM astronaut_logs
                    WHERE astronaut_id = ?
                    ORDER BY id DESC LIMIT ?
                """, (astronaut_id, limit))
            return [dict(r) for r in cursor.fetchall()]

    def get_records_by_astronaut(self, astronaut_id: str, date_filter: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Alias for get_records_by_date used by history viewers."""
        return self.get_records_by_date(astronaut_id, date_filter=date_filter, limit=limit)

    def get_distinct_dates(self, astronaut_id: str) -> List[str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT DISTINCT date_str FROM astronaut_logs
                WHERE astronaut_id = ?
                ORDER BY date_str DESC
            """, (astronaut_id,))
            return [r["date_str"] for r in cursor.fetchall()]

    # =========================================================================
    # CLINICAL DOSSIERS & HISTORICAL CASE REPORTS
    # =========================================================================
    def save_clinical_dossier(
        self,
        astronaut_id: str,
        astronaut_name: str,
        report_title: str,
        vitals_summary: str,
        cabin_summary: str,
        status_eval: str,
        historical_match_text: str,
        recovery_protocol_text: str,
        ai_suggestions_text: str,
        full_report_text: str
    ) -> int:
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO clinical_dossiers
                (astronaut_id, astronaut_name, created_at, report_title, vitals_summary, cabin_summary, status_eval, historical_match_text, recovery_protocol_text, ai_suggestions_text, full_report_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                astronaut_id, astronaut_name, now_iso, report_title,
                vitals_summary, cabin_summary, status_eval,
                historical_match_text, recovery_protocol_text, ai_suggestions_text,
                full_report_text
            ))
            conn.commit()
            return cursor.lastrowid

    def get_clinical_dossiers(self, astronaut_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if astronaut_id and astronaut_id != "ALL":
                cursor.execute("""
                    SELECT * FROM clinical_dossiers
                    WHERE astronaut_id = ?
                    ORDER BY id DESC LIMIT ?
                """, (astronaut_id, limit))
            else:
                cursor.execute("""
                    SELECT * FROM clinical_dossiers
                    ORDER BY id DESC LIMIT ?
                """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    def get_dossier_by_id(self, dossier_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clinical_dossiers WHERE id = ?", (dossier_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def _seed_initial_roster_and_history(self):
        """
        Seeds initial mission groups (Expedition 72 Active in Space, Expedition 71 Historical on Earth)
        and astronauts into the master database.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if groups already exist
            cursor.execute("SELECT COUNT(*) as count FROM mission_groups")
            if cursor.fetchone()["count"] == 0:
                now_str = datetime.now().isoformat()
                groups = [
                    ("expedition_72", "Expedition 72 (Lunar Deep Space Gateway)", "ACTIVE_IN_SPACE", "2026-05-12", "2026-11-20", now_str),
                    ("expedition_71", "Expedition 71 (ISS Alpha Orbit - Historical)", "HISTORICAL_RETURNED", "2025-09-01", "2026-03-15", now_str),
                    ("artemis_3", "Artemis III (Lunar South Pole - Scheduled)", "SCHEDULED_TRAINING", "2027-02-10", "2027-08-30", now_str)
                ]
                cursor.executemany("""
                    INSERT INTO mission_groups (group_id, group_name, status, launch_date, return_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, groups)

            # Check if astronauts already exist
            cursor.execute("SELECT COUNT(*) as count FROM astronaut_roster")
            if cursor.fetchone()["count"] == 0:
                astronauts = [
                    # Expedition 72 (Active in Space)
                    ("sarah", "expedition_72", "01", "Capt. Sarah Connor", "ARES-LEAD", "Mission Commander / EVA Specialist", "static/assets/astronaut_sarah.jpg", 72, 98.4, 58.0, 18, 1, "IN_SPACE", "Prime Commander"),
                    ("alex", "expedition_72", "02", "Dr. Alex Vance", "BIO-SURGEON", "Flight Surgeon / Astrobiologist", "static/assets/astronaut_alex.jpg", 66, 99.1, 64.0, 30, 1, "IN_SPACE", "Chief Medical Officer"),
                    ("john", "expedition_72", "03", "Eng. John Miller", "SYSTEMS-CHIEF", "Life Support & Propulsion Engineer", "static/assets/astronaut_john.jpg", 74, 97.8, 52.0, 25, 1, "IN_SPACE", "Life support chief"),
                    ("elena", "expedition_72", "04", "Elena Rostova", "ROBOTICS-SPEC", "Payload Specialist & Robotics Operator", "static/assets/astronaut_elena.jpg", 68, 98.5, 60.0, 38, 1, "IN_SPACE", "EVA Robotics Lead"),

                    # Expedition 71 (Historical - Returned safely to Earth)
                    ("marcus", "expedition_71", "01", "Cmdr. Marcus Wright", "ALPHA-COMMAND", "Station Commander (Returned)", "static/assets/astronaut_sarah.jpg", 70, 98.6, 62.0, 20, 0, "RETURNED_TO_EARTH", "Landed safely via Orion Capsule."),
                    ("kyle", "expedition_71", "02", "Lt. Kyle Reese", "ORBIT-OPS", "Payload Operations (Returned)", "static/assets/astronaut_alex.jpg", 72, 98.0, 56.0, 24, 0, "RETURNED_TO_EARTH", "Completed 180 days on ISS."),

                    # Artemis III (Scheduled / Pre-Flight Training)
                    ("clara", "artemis_3", "01", "Dr. Clara Oswald", "LUNAR-GEO", "Lunar Geologist & Astrobiologist", "static/assets/astronaut_elena.jpg", 65, 99.0, 68.0, 15, 0, "TRAINING", "Scheduled for Artemis III lunar landing.")
                ]
                cursor.executemany("""
                    INSERT INTO astronaut_roster 
                    (id, group_id, serial, name, callsign, role, avatar, baseline_hr, baseline_spo2, baseline_hrv, fatigue, is_deployed, status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, astronauts)

            # Check if historical logs exist
            cursor.execute("SELECT COUNT(*) as count FROM astronaut_logs")
            if cursor.fetchone()["count"] == 0:
                now = datetime.now()
                yesterday_str = (now - timedelta(days=1)).strftime("%Y-%m-%d")
                prev2_str = (now - timedelta(days=2)).strftime("%Y-%m-%d")
                prev30_str = (now - timedelta(days=30)).strftime("%Y-%m-%d")

                sample_seeds = [
                    # Expedition 72 Logs
                    ("sarah", "expedition_72", prev2_str, "08:30:00", 68, 98.8, 62.0, 15, 92, "🟢 HEALTHY & STABLE", "Nominal biometric rhythm. All cardiovascular parameters within target range.", "EVA simulation training completed."),
                    ("sarah", "expedition_72", yesterday_str, "09:00:00", 71, 98.5, 60.0, 18, 91, "🟢 HEALTHY & STABLE", "Consistent with prior baseline, healthy and mission-cleared.", "Morning routine flight surgeon check."),
                    ("alex", "expedition_72", yesterday_str, "10:15:00", 66, 99.1, 65.0, 20, 93, "🟢 HEALTHY & STABLE", "Biometric equilibrium optimal. Sinus rhythm robust.", "Medical research lab shift completed."),
                    ("john", "expedition_72", yesterday_str, "11:00:00", 74, 98.0, 52.0, 26, 88, "🟢 HEALTHY & STABLE", "Life support system maintenance fitness certified.", "Routine shift fitness verified."),
                    ("elena", "expedition_72", yesterday_str, "12:00:00", 68, 98.5, 60.0, 32, 89, "🟢 HEALTHY & STABLE", "Robotics arm telemetry check. Normal physiological load.", "Shift completed."),

                    # Expedition 71 Historical Logs (Returned Astronauts)
                    ("marcus", "expedition_71", prev30_str, "14:00:00", 70, 98.6, 62.0, 20, 90, "🟢 HEALTHY & STABLE", "Final ISS debrief health status nominal.", "Completed full 180-day orbital mission profile."),
                    ("kyle", "expedition_71", prev30_str, "15:30:00", 72, 98.0, 56.0, 24, 88, "🟢 HEALTHY & STABLE", "Pre-reentry medical evaluation passed.", "Nominal microgravity fitness certified.")
                ]

                for s in sample_seeds:
                    cid, gid, d_str, t_str, hr, spo2, hrv, fat, read, stat, trend, note = s
                    cursor.execute("""
                        INSERT INTO astronaut_logs
                        (astronaut_id, group_id, timestamp, date_str, time_str, heart_rate, spo2, hrv, fatigue, readiness_score, status_eval, trend_diff, clinical_notes, snapshot_path, trigger_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cid, gid, f"{d_str}T{t_str}", d_str, t_str,
                        hr, spo2, hrv, fat, read,
                        stat, trend, note, "", "HISTORICAL_LOG"
                    ))

            conn.commit()


# Global medical database singleton
medical_db = MedicalDatabase()
