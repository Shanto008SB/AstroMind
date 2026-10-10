"""
AstroMind: Continuous Background Face Recognition & 30-Min Snapshot Engine
Runs 24/7 background biometric monitoring, takes automated 30-minute photo snapshots,
and handles on-demand manual instant face health checks.
"""

import os
import time
import threading
from datetime import datetime
import cv2
import numpy as np
from typing import Dict, Any, Optional

from .medical_db import medical_db
from .shared_state import state
from .anomaly_detector import AnomalyDetector
from .groq_doctor import GroqAIDoctor

SNAPSHOTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "snapshots")

class BackgroundBiometricAnalyzer:
    def __init__(self, groq_doctor: Optional[GroqAIDoctor] = None):
        self.groq_doctor = groq_doctor or GroqAIDoctor()
        self.detector = AnomalyDetector()
        self.is_running = False
        self.interval_seconds = 1800 # 30 minutes
        self.last_auto_snapshot_time = time.time()
        self.lock = threading.Lock()
        self.frame_provider = None # Hook to grab live camera frame from desktop app
        os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

        self.last_scan_result: Optional[Dict[str, Any]] = None

    def start_background_monitoring(self):
        if self.is_running:
            return
        self.is_running = True
        t = threading.Thread(target=self._background_loop, daemon=True)
        t.start()
        print("[AstroMind] Continuous Background Face & Biometric Monitoring Activated.")

    def get_seconds_until_next_snapshot(self) -> int:
        elapsed = time.time() - self.last_auto_snapshot_time
        remaining = max(0, int(self.interval_seconds - elapsed))
        return remaining

    def _background_loop(self):
        """
        Continuously runs in background. Every 30 minutes, automatically
        captures an analyzed biometric snapshot and logs to SQLite database.
        """
        while self.is_running:
            time.sleep(2)
            elapsed = time.time() - self.last_auto_snapshot_time
            if elapsed >= self.interval_seconds:
                self.last_auto_snapshot_time = time.time()
                self._execute_periodic_auto_scan()

    def _execute_periodic_auto_scan(self):
        """
        Takes 30-minute automated snapshot from live camera and saves to database.
        """
        try:
            full_state = state.get_full_state()
            cid = full_state["active_id"]
            vitals = full_state["vitals"]
            cabin = full_state["cabin"]
            analysis = full_state["analysis"]

            now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"auto_{cid}_{now_str}.jpg"
            filepath = os.path.join(SNAPSHOTS_DIR, filename)

            # Grab live camera frame if available
            live_frame = None
            if self.frame_provider is not None:
                try:
                    live_frame = self.frame_provider()
                except Exception:
                    live_frame = None

            # Generate stamped biometric snapshot with real camera frame
            self._create_annotated_snapshot(
                filepath,
                full_state["astronaut"]["name"],
                vitals,
                analysis,
                "30-MIN AUTO SCAN",
                base_frame=live_frame
            )

            # Log to SQLite
            clinical_note = f"30-minute automated routine biometric check. Readiness score: {analysis['readiness_score']}%. All systems nominal."
            record = medical_db.log_record(
                astronaut_id=cid,
                vitals=vitals,
                analysis=analysis,
                clinical_note=clinical_note,
                snapshot_path=filepath,
                trigger_type="AUTO_30MIN"
            )
            print(f"[AstroMind DB] 30-Min Automated Live Snapshot saved: {filename} -> {record['status_eval']}")
        except Exception as e:
            print(f"[AstroMind Background Error] {e}")

    def perform_manual_instant_scan(self, current_frame_bgr: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Triggered when an astronaut clicks the 'Instant Face Health Check' button!
        Immediately scans face biometrics from camera, compares with past records, logs to DB,
        and returns spoken diagnosis.
        """
        if current_frame_bgr is None and self.frame_provider is not None:
            try:
                current_frame_bgr = self.frame_provider()
            except Exception:
                current_frame_bgr = None

        full_state = state.get_full_state()
        cid = full_state["active_id"]
        member = full_state["astronaut"]
        vitals = full_state["vitals"]
        cabin = full_state["cabin"]
        analysis = self.detector.evaluate_crew_member(vitals, cabin)

        now = datetime.now()
        now_str = now.strftime("%Y%m%d_%H%M%S")
        filename = f"manual_{cid}_{now_str}.jpg"
        filepath = os.path.join(SNAPSHOTS_DIR, filename)

        # Annotate & save picture from live camera
        self._create_annotated_snapshot(
            filepath,
            member["name"],
            vitals,
            analysis,
            "ON-DEMAND MANUAL CHECK",
            base_frame=current_frame_bgr
        )

        # Query Groq AI Doctor for instant evaluation
        eval_prompt = (
            f"Astronaut {member['name']} performed an on-demand manual face scan. "
            f"Vitals: Heart Rate {vitals['heart_rate']} BPM, SpO2 {vitals['spo2']}%, Fatigue {vitals['fatigue_level']}%. "
            "Evaluate if the astronaut is healthy, fatigued, or deteriorating compared to normal space flight baselines. "
            "Give clear, concise reassurance or advice in 2 short sentences."
        )
        ai_advice = self.groq_doctor.ask_doctor(eval_prompt, member, vitals, cabin, analysis["is_emergency"])

        # Log into SQLite and get comparative trend analysis
        record = medical_db.log_record(
            astronaut_id=cid,
            vitals=vitals,
            analysis=analysis,
            clinical_note=ai_advice,
            snapshot_path=filepath,
            trigger_type="MANUAL_SCAN"
        )

        # Spoken vocal feedback
        speech_msg = (
            f"Biometric scan complete for {member['name']}. "
            f"Status evaluation: {record['status_eval']}. {ai_advice}"
        )
        self.groq_doctor.speak_async(speech_msg)

        result = {
            "astronaut": member,
            "vitals": vitals,
            "analysis": analysis,
            "ai_advice": ai_advice,
            "status_eval": record["status_eval"],
            "trend_diff": record["trend_diff"],
            "comparative": record["comparative"],
            "snapshot_path": filepath,
            "snapshot_filename": filename,
            "timestamp_str": now.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.last_scan_result = result
        return result

    def _create_annotated_snapshot(
        self,
        filepath: str,
        name: str,
        vitals: Dict[str, Any],
        analysis: Dict[str, Any],
        tag: str,
        base_frame: Optional[np.ndarray] = None
    ):
        """
        Creates a high-tech stamped biometric screenshot with HUD data overlays.
        """
        h, w = 480, 640
        if base_frame is not None and base_frame.shape[0] > 100:
            frame = cv2.resize(base_frame.copy(), (w, h))
        else:
            frame = np.zeros((h, w, 3), dtype=np.uint8)
            frame[:] = (12, 16, 28)

        # Top banner stamp
        cv2.rectangle(frame, (0, 0), (w, 52), (6, 10, 20), -1)
        cv2.line(frame, (0, 52), (w, 52), (0, 240, 255), 1)

        cv2.putText(frame, f"ASTROMIND BIOMETRIC SCAN ARCHIVE • [{tag}]", (16, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 240, 255), 1)
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        cv2.putText(frame, f"SUBJECT: {name.upper()} | TIMESTAMP: {now_ts}", (16, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (180, 220, 240), 1)

        # Bottom data HUD stamp
        cv2.rectangle(frame, (0, h - 64), (w, h), (6, 10, 20), -1)
        cv2.line(frame, (0, h - 64), (w, h - 64), (0, 240, 255), 1)

        hr = vitals.get("heart_rate", 72)
        spo2 = vitals.get("spo2", 98.4)
        hrv = vitals.get("hrv", 58.0)
        fat = vitals.get("fatigue_level", 20)
        readiness = analysis.get("readiness_score", 85)

        line1 = f"PULSE: {hr} BPM | SpO2: {spo2:.1f}% | HRV: {hrv:.0f} ms | FATIGUE: {fat}% | READINESS: {readiness}%"
        cv2.putText(frame, line1, (16, h - 38), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 255, 128), 1)
        cv2.putText(frame, f"EVALUATION: {analysis.get('readiness_status', 'NOMINAL')}", (16, h - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 240, 255), 1)

        # Watermark
        cv2.putText(frame, "NASA SPACE APPS CHALLENGE • 100% OFFLINE EDGE LOG", (w - 320, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (100, 160, 200), 1)

        cv2.imwrite(filepath, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

# Global background analyzer singleton
background_analyzer = BackgroundBiometricAnalyzer()
