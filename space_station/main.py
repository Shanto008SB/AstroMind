import sys
import os

# Ensure folder is in sys.path and cwd regardless of where launcher is run
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
os.chdir(_SCRIPT_DIR)

import time
import math
import socket
import threading
from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw
import cv2
import numpy as np
import customtkinter as ctk

from engine.shared_state import state
from engine.anomaly_detector import AnomalyDetector
from engine.groq_doctor import GroqAIDoctor
from engine.space_api_server import run_space_api_server_background
from engine.rppg_estimator import RPPGEstimator
from engine.background_analyzer import background_analyzer
from engine.history_viewer import MedicalHistoryViewer
from engine.medical_db import medical_db
from engine.alarm_sound import alarm_sound
from engine.face_mesh_scanner import face_mesh_scanner
from engine.nasa_standards_viewer import NASAStandardsViewer
from engine.clinical_report_viewer import ClinicalReportViewer
from engine.historical_case_matcher import HistoricalCaseMatcher

# Configuration
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Get host local IP for Phone Remote display
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

LOCAL_IP = get_local_ip()
IOT_REMOTE_URL = f"http://{LOCAL_IP}:5000/remote"


class AstroMindDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AstroMind: Autonomous Edge AI Health Monitoring System • NASA Space Apps")
        self.geometry("1480x920")
        self.minsize(1280, 800)
        self.configure(fg_color="#060913")

        # Core Engines
        self.groq_doctor = GroqAIDoctor()
        self.rppg_estimator = RPPGEstimator()

        # Start Silent 24/7 Background Camera Engine
        self.rppg_estimator.start_background_camera(0)

        # Start 24/7 Background Biometric Analyzer & 30-Min Snapshot Engine
        background_analyzer.groq_doctor = self.groq_doctor
        background_analyzer.frame_provider = self.rppg_estimator.get_latest_frame
        background_analyzer.start_background_monitoring()

        # Start IoT Remote Server in Background Thread
        self.space_api_server_thread = run_space_api_server_background(host="0.0.0.0", port=5000)

        # App Variables - 3D Neural AI Brain is the main UI animation!
        # Background Camera runs silently 24/7 in background.
        self.camera_mode = "neural_brain" # 'neural_brain' | 'live_camera'
        self.scan_preview_frame = None
        self.scan_preview_until = 0.0

        self.ecg_points = [0] * 120
        self.ecg_counter = 0
        self.last_emergency_state = False
        self.last_warning_state = False
        self.last_spoken_warning_time = 0.0
        self.photo_cache = {}
        self.last_frame_bgr = None
        self.history_window = None
        self.nasa_standards_window = None
        self.clinical_dossier_window = None
        self.mission_start_epoch = time.time() - (4 * 86400 + 18 * 3600 + 22 * 60) # MET ~ +04d 18h

        # Setup GUI Components
        self.build_header()
        self.build_top_vitals_cards() # Tip 3
        self.build_workspace_grid()   # 3-column layout matching user sketch
        self.build_emergency_banner() # Tip 2

        # Start Real-Time Event Loops
        self.update_video_feed_loop()
        self.update_vitals_loop()
        self.update_clock_loop()

    # =========================================================================
    # 1. TOP STATUS HEADER
    # =========================================================================
    def build_header(self):
        header_frame = ctk.CTkFrame(self, fg_color="#0b1222", corner_radius=0, border_width=1, border_color="#163b4d")
        header_frame.pack(fill="x", side="top", padx=0, pady=0)

        # ── Row 1: Brand left ── Clock + Timer right ───────────────────────
        row1 = ctk.CTkFrame(header_frame, fg_color="transparent")
        row1.pack(fill="x", padx=14, pady=(8, 2))

        # Brand / Logo (left)
        brand_frame = ctk.CTkFrame(row1, fg_color="transparent")
        brand_frame.pack(side="left")

        lbl_logo = ctk.CTkLabel(
            brand_frame,
            text="🚀 ASTROMIND",
            font=ctk.CTkFont(family="Orbitron", size=17, weight="bold"),
            text_color="#00f0ff"
        )
        lbl_logo.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            brand_frame,
            text="AUTONOMOUS EDGE AI HEALTH BRAIN • NASA SPACE APPS",
            font=ctk.CTkFont(family="Consolas", size=8),
            text_color="#64748b"
        )
        lbl_sub.pack(anchor="w")

        # Clock + Timer boxes (right side of row 1)
        clocks_frame = ctk.CTkFrame(row1, fg_color="transparent")
        clocks_frame.pack(side="right")

        # Mission UTC Clock
        clock_box = ctk.CTkFrame(clocks_frame, fg_color="#060b14", corner_radius=6, border_width=1, border_color="#163b4d")
        clock_box.pack(side="left", padx=(0, 6))
        self.lbl_mission_clock = ctk.CTkLabel(
            clock_box,
            text="📅 2026-10-09  ⏰ 13:50:00 UTC",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#38bdf8"
        )
        self.lbl_mission_clock.pack(padx=8, pady=4)

        # Mission Elapsed Time
        met_box = ctk.CTkFrame(clocks_frame, fg_color="#060b14", corner_radius=6, border_width=1, border_color="#164e63")
        met_box.pack(side="left", padx=(0, 6))
        self.lbl_met = ctk.CTkLabel(
            met_box,
            text="MET: +04d 18h 22m",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#10b981"
        )
        self.lbl_met.pack(padx=8, pady=4)

        # Auto-Scan timer
        timer_box = ctk.CTkFrame(clocks_frame, fg_color="#060b14", corner_radius=6, border_width=1, border_color="#1a3a2a")
        timer_box.pack(side="left")
        self.lbl_auto_snapshot_timer = ctk.CTkLabel(
            timer_box,
            text="📸 Auto-Scan: 30m 00s",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#10b981"
        )
        self.lbl_auto_snapshot_timer.pack(padx=8, pady=4)

        # ── Row 2: All action buttons evenly spaced ─────────────────────────
        row2 = ctk.CTkFrame(header_frame, fg_color="transparent")
        row2.pack(fill="x", padx=14, pady=(2, 6))

        btn_cfg = dict(
            font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"),
            height=28,
            corner_radius=6,
        )

        # Medical Archive
        self.btn_history = ctk.CTkButton(
            row2,
            text="📂 MEDICAL ARCHIVE",
            fg_color="#0369a1", hover_color="#0284c7",
            border_width=1, border_color="#38bdf8",
            text_color="#ffffff",
            command=self.open_history_viewer,
            **btn_cfg
        )
        self.btn_history.pack(side="left", padx=(0, 5))

        # NASA Open Data
        self.btn_nasa_standards = ctk.CTkButton(
            row2,
            text="🏛 NASA OPEN DATA",
            fg_color="#082f49", hover_color="#0284c7",
            border_width=1, border_color="#38bdf8",
            text_color="#38bdf8",
            command=self.open_nasa_standards_viewer,
            **btn_cfg
        )
        self.btn_nasa_standards.pack(side="left", padx=(0, 5))

        # Phone IoT URL (trimmed to fit — just the IP)
        self.btn_phone_link = ctk.CTkButton(
            row2,
            text=f"📱 Phone IoT: http://{LOCAL_IP}:5000/remote",
            fg_color="#0f2942", hover_color="#0284c7",
            border_width=1, border_color="#00f0ff",
            text_color="#00f0ff",
            command=self.open_phone_remote_in_browser,
            **btn_cfg
        )
        self.btn_phone_link.pack(side="left", padx=(0, 5))

        # Voice wake hint label
        lbl_voice = ctk.CTkLabel(
            row2,
            text="🎤 'Hey AstroMind'",
            font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
            text_color="#38bdf8"
        )
        lbl_voice.pack(side="left", padx=(0, 5))

        # ── SIMULATE DRILL — always on far RIGHT, never clipped ─────────────
        self.btn_header_drill = ctk.CTkButton(
            row2,
            text="🚨 SIMULATE DRILL",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#3b111e",
            hover_color="#ff1e53",
            border_width=1,
            border_color="#ff1e53",
            text_color="#ff4d6d",
            height=28,
            corner_radius=6,
            command=self.toggle_emergency_drill
        )
        self.btn_header_drill.pack(side="right", padx=(5, 0))


    def open_phone_remote_in_browser(self):
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:5000/remote")

    def open_history_viewer(self):
        if self.history_window is None or not self.history_window.winfo_exists():
            self.history_window = MedicalHistoryViewer(self, default_astronaut_id=state.active_id)
        else:
            self.history_window.focus()
            self.history_window.astronaut_id = state.active_id
            self.history_window.load_records()

    def open_nasa_standards_viewer(self):
        if self.nasa_standards_window is None or not self.nasa_standards_window.winfo_exists():
            self.nasa_standards_window = NASAStandardsViewer(self)
        else:
            self.nasa_standards_window.focus()

    def open_full_clinical_dossier(self):
        s = state.get_full_state()
        astronaut = s.get("astronaut", {})
        vitals = s.get("vitals", {})
        cabin = s.get("cabin", {})
        ai_note = state.ai_doctor_note or "Autonomous Edge AI continuous monitoring active."

        if self.clinical_dossier_window is None or not self.clinical_dossier_window.winfo_exists():
            self.clinical_dossier_window = ClinicalReportViewer(
                self,
                astronaut=astronaut,
                vitals=vitals,
                cabin=cabin,
                is_emergency=s.get("is_emergency", False)
            )
        else:
            self.clinical_dossier_window.lift()
            self.clinical_dossier_window.focus_force()

    def clear_doctor_note(self):
        state.ai_doctor_note = "Awaiting consultation or autonomous biometric anomaly..."
        self.txt_doctor_note.configure(state="normal")
        self.txt_doctor_note.delete("1.0", "end")
        self.txt_doctor_note.insert("1.0", state.ai_doctor_note)
        self.txt_doctor_note.configure(state="disabled")

    # =========================================================================
    # 2. TOP VITALS BAR: 4 CARDS (Enhancement Tip 3)
    # =========================================================================
    def build_top_vitals_cards(self):
        cards_container = ctk.CTkFrame(self, fg_color="transparent")
        cards_container.pack(fill="x", padx=16, pady=(12, 6))

        for i in range(4):
            cards_container.grid_columnconfigure(i, weight=1)

        # Card 1: Pulse / Heart Rate
        self.card_hr = ctk.CTkFrame(cards_container, fg_color="#0d1628", corner_radius=10, border_width=1, border_color="#381d24")
        self.card_hr.grid(row=0, column=0, padx=6, pady=0, sticky="nsew")

        f_hr_top = ctk.CTkFrame(self.card_hr, fg_color="transparent")
        f_hr_top.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(f_hr_top, text="❤️ PULSE / HEART RATE", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), text_color="#f87171").pack(side="left")
        self.badge_hr = ctk.CTkLabel(f_hr_top, text="NORMAL", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#10b981", fg_color="#103628", corner_radius=4)
        self.badge_hr.pack(side="right", padx=4)

        f_hr_val = ctk.CTkFrame(self.card_hr, fg_color="transparent")
        f_hr_val.pack(fill="x", padx=12, pady=2)
        self.lbl_hr_val = ctk.CTkLabel(f_hr_val, text="72", font=ctk.CTkFont(family="Rajdhani", size=36, weight="bold"), text_color="#ffffff")
        self.lbl_hr_val.pack(side="left")
        ctk.CTkLabel(f_hr_val, text=" BPM", font=ctk.CTkFont(family="Consolas", size=12), text_color="#94a3b8").pack(side="left", pady=(12, 0))

        # Realtime Animated Canvas ECG Waveform!
        self.canvas_ecg = tk.Canvas(self.card_hr, height=36, bg="#060b14", highlightthickness=0)
        self.canvas_ecg.pack(fill="x", padx=12, pady=(4, 6))

        ctk.CTkLabel(self.card_hr, text="Sinus Rhythm • Optical rPPG Extracted", font=ctk.CTkFont(family="Consolas", size=9), text_color="#64748b").pack(padx=12, pady=(0, 8), anchor="w")

        # Card 2: Blood Oxygen (SpO2)
        self.card_spo2 = ctk.CTkFrame(cards_container, fg_color="#0d1628", corner_radius=10, border_width=1, border_color="#163b4d")
        self.card_spo2.grid(row=0, column=1, padx=6, pady=0, sticky="nsew")

        f_spo2_top = ctk.CTkFrame(self.card_spo2, fg_color="transparent")
        f_spo2_top.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(f_spo2_top, text="🫁 BLOOD OXYGEN (SpO₂)", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), text_color="#00f0ff").pack(side="left")
        self.badge_spo2 = ctk.CTkLabel(f_spo2_top, text="OPTIMAL", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#10b981", fg_color="#103628", corner_radius=4)
        self.badge_spo2.pack(side="right", padx=4)

        f_spo2_val = ctk.CTkFrame(self.card_spo2, fg_color="transparent")
        f_spo2_val.pack(fill="x", padx=12, pady=2)
        self.lbl_spo2_val = ctk.CTkLabel(f_spo2_val, text="98.4", font=ctk.CTkFont(family="Rajdhani", size=36, weight="bold"), text_color="#ffffff")
        self.lbl_spo2_val.pack(side="left")
        ctk.CTkLabel(f_spo2_val, text=" %", font=ctk.CTkFont(family="Consolas", size=12), text_color="#94a3b8").pack(side="left", pady=(12, 0))

        self.prog_spo2 = ctk.CTkProgressBar(self.card_spo2, height=6, progress_color="#00f0ff", fg_color="#1e293b")
        self.prog_spo2.pack(fill="x", padx=12, pady=(10, 8))
        self.prog_spo2.set(0.984)

        ctk.CTkLabel(self.card_spo2, text="Target: > 94.0% • Microgravity Arterial", font=ctk.CTkFont(family="Consolas", size=9), text_color="#64748b").pack(padx=12, pady=(0, 8), anchor="w")

        # Card 3: Heart Rate Variability (HRV)
        self.card_hrv = ctk.CTkFrame(cards_container, fg_color="#0d1628", corner_radius=10, border_width=1, border_color="#2d1a45")
        self.card_hrv.grid(row=0, column=2, padx=6, pady=0, sticky="nsew")

        f_hrv_top = ctk.CTkFrame(self.card_hrv, fg_color="transparent")
        f_hrv_top.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(f_hrv_top, text="⚡ HRV VARIABILITY", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), text_color="#c084fc").pack(side="left")
        self.badge_hrv = ctk.CTkLabel(f_hrv_top, text="BALANCED", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#10b981", fg_color="#103628", corner_radius=4)
        self.badge_hrv.pack(side="right", padx=4)

        f_hrv_val = ctk.CTkFrame(self.card_hrv, fg_color="transparent")
        f_hrv_val.pack(fill="x", padx=12, pady=2)
        self.lbl_hrv_val = ctk.CTkLabel(f_hrv_val, text="58", font=ctk.CTkFont(family="Rajdhani", size=36, weight="bold"), text_color="#ffffff")
        self.lbl_hrv_val.pack(side="left")
        ctk.CTkLabel(f_hrv_val, text=" ms", font=ctk.CTkFont(family="Consolas", size=12), text_color="#94a3b8").pack(side="left", pady=(12, 0))

        self.prog_hrv = ctk.CTkProgressBar(self.card_hrv, height=6, progress_color="#a855f7", fg_color="#1e293b")
        self.prog_hrv.pack(fill="x", padx=12, pady=(10, 8))
        self.prog_hrv.set(0.65)

        ctk.CTkLabel(self.card_hrv, text="Autonomic Tone • Zero IoT Hardware", font=ctk.CTkFont(family="Consolas", size=9), text_color="#64748b").pack(padx=12, pady=(0, 8), anchor="w")

        # Card 4: Fatigue Level & Stress
        self.card_fatigue = ctk.CTkFrame(cards_container, fg_color="#0d1628", corner_radius=10, border_width=1, border_color="#14382c")
        self.card_fatigue.grid(row=0, column=3, padx=6, pady=0, sticky="nsew")

        f_fatigue_top = ctk.CTkFrame(self.card_fatigue, fg_color="transparent")
        f_fatigue_top.pack(fill="x", padx=12, pady=(10, 2))
        ctk.CTkLabel(f_fatigue_top, text="🧠 FATIGUE LEVEL", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), text_color="#34d399").pack(side="left")
        self.badge_fatigue = ctk.CTkLabel(f_fatigue_top, text="LOW", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#10b981", fg_color="#103628", corner_radius=4)
        self.badge_fatigue.pack(side="right", padx=4)

        f_fatigue_val = ctk.CTkFrame(self.card_fatigue, fg_color="transparent")
        f_fatigue_val.pack(fill="x", padx=12, pady=2)
        self.lbl_fatigue_val = ctk.CTkLabel(f_fatigue_val, text="18", font=ctk.CTkFont(family="Rajdhani", size=36, weight="bold"), text_color="#ffffff")
        self.lbl_fatigue_val.pack(side="left")
        ctk.CTkLabel(f_fatigue_val, text=" %", font=ctk.CTkFont(family="Consolas", size=12), text_color="#94a3b8").pack(side="left", pady=(12, 0))

        self.prog_fatigue = ctk.CTkProgressBar(self.card_fatigue, height=6, progress_color="#10b981", fg_color="#1e293b")
        self.prog_fatigue.pack(fill="x", padx=12, pady=(10, 8))
        self.prog_fatigue.set(0.18)

        ctk.CTkLabel(self.card_fatigue, text="Eye Blink Tracking • 14 blinks/min", font=ctk.CTkFont(family="Consolas", size=9), text_color="#64748b").pack(padx=12, pady=(0, 8), anchor="w")

    # =========================================================================
    # 3. WORKSPACE 3-COLUMN GRID (Matching User's Sketch)
    # =========================================================================
    def build_workspace_grid(self):
        work_frame = ctk.CTkFrame(self, fg_color="transparent")
        work_frame.pack(fill="both", expand=True, padx=16, pady=6)

        work_frame.grid_columnconfigure(0, weight=2) # Left Sidebar (Astronaut Profiles)
        work_frame.grid_columnconfigure(1, weight=5) # Center AI Face / Camera Box
        work_frame.grid_columnconfigure(2, weight=3) # Right Panel (Health Report)
        work_frame.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # 3A. LEFT SIDEBAR: Astronaut Profiles Serially
        # -------------------------------------------------------------
        sidebar = ctk.CTkFrame(work_frame, fg_color="#0b1222", corner_radius=10, border_width=1, border_color="#163b4d")
        sidebar.grid(row=0, column=0, padx=(0, 8), pady=0, sticky="nsew")

        f_side_top = ctk.CTkFrame(sidebar, fg_color="transparent")
        f_side_top.pack(fill="x", padx=10, pady=(10, 4))

        lbl_side_title = ctk.CTkLabel(f_side_top, text="👨‍🚀 CREW PROFILES", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), text_color="#00f0ff")
        lbl_side_title.pack(side="left")

        btn_add_space_crew = ctk.CTkButton(
            f_side_top,
            text="➕ ADD CREW",
            width=80,
            height=24,
            font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.open_add_crew_modal
        )
        btn_add_space_crew.pack(side="right")

        # Astronaut Profile Buttons Container (Dynamic sync with Earth Mission Control)
        self.sidebar_crew_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        self.sidebar_crew_container.pack(fill="both", expand=True, padx=0, pady=0)
        self.render_crew_sidebar()

        # Telemetry DSN Delay Info
        dsn_box = ctk.CTkFrame(sidebar, fg_color="#060b14", corner_radius=6, border_width=1, border_color="#1e293b")
        dsn_box.pack(fill="x", side="bottom", padx=10, pady=12)
        ctk.CTkLabel(dsn_box, text="🛰️ STORE-AND-FORWARD PROTOCOL", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#00f0ff").pack(padx=8, pady=(6, 2), anchor="w")
        ctk.CTkLabel(dsn_box, text="Simulated Comm Delay: 2.6s (Artemis Lunar)\nLocal Storage: Encrypted SQLite Cache", font=ctk.CTkFont(family="Consolas", size=9), text_color="#64748b", justify="left").pack(padx=8, pady=(0, 6), anchor="w")

        # -------------------------------------------------------------
        # 3B. CENTER PANEL: AI Face Recognition & rPPG Camera Box
        # -------------------------------------------------------------
        center_panel = ctk.CTkFrame(work_frame, fg_color="#0b1222", corner_radius=10, border_width=1, border_color="#163b4d")
        center_panel.grid(row=0, column=1, padx=4, pady=0, sticky="nsew")

        # Header of center box
        center_top = ctk.CTkFrame(center_panel, fg_color="transparent")
        center_top.pack(fill="x", padx=12, pady=(10, 6))

        ctk.CTkLabel(center_top, text="🧠 3D HOLOGRAPHIC NEURAL AI BRAIN", font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"), text_color="#00f0ff").pack(side="left")

        # Background status indicator
        lbl_bg_scan = ctk.CTkLabel(
            center_top,
            text="🔒 24/7 BACKGROUND BIO-SCANNER: ACTIVE",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#10b981",
            fg_color="#103628",
            corner_radius=4
        )
        lbl_bg_scan.pack(side="left", padx=10)

        # Optional View Switcher Button (Neural Brain vs Live View)
        self.btn_cam_toggle = ctk.CTkButton(
            center_top,
            text="👁️ PEEK LIVE CAMERA",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            fg_color="#0f2942",
            hover_color="#0284c7",
            border_width=1,
            border_color="#00f0ff",
            text_color="#00f0ff",
            height=26,
            command=self.toggle_camera_source
        )
        self.btn_cam_toggle.pack(side="right")

        # Camera Viewport Canvas (Shows 640x480 frame scaled to fit)
        self.canvas_video = tk.Canvas(center_panel, bg="#04070d", highlightthickness=1, highlightbackground="#163b4d")
        self.canvas_video.pack(fill="both", expand=True, padx=12, pady=4)

        # AI Doctor Box (Inside lower part of center panel, exactly as drawn in sketch!)
        doctor_interact_frame = ctk.CTkFrame(center_panel, fg_color="#080e1c", corner_radius=8, border_width=1, border_color="#163b4d")
        doctor_interact_frame.pack(fill="x", padx=12, pady=(6, 10))

        # Row 1: Action buttons: Instant Scan, Voice Conversation (Mic), Clinical Summary
        doc_btn_row = ctk.CTkFrame(doctor_interact_frame, fg_color="transparent")
        doc_btn_row.pack(fill="x", padx=10, pady=(8, 4))

        # Manual Biometric Scan Button (100% English)
        self.btn_manual_scan = ctk.CTkButton(
            doc_btn_row,
            text="🔍 INSTANT BIOMETRIC SCAN",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#041209",
            height=32,
            command=self.on_manual_instant_scan
        )
        self.btn_manual_scan.pack(side="left", padx=(0, 6), fill="x", expand=True)

        # Voice Conversation Button (Microphone recording & Whisper transcription)
        self.btn_voice_talk = ctk.CTkButton(
            doc_btn_row,
            text="🎙️ VOICE CONVERSATION (MIC)",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0ea5e9",
            text_color="#ffffff",
            height=32,
            command=self.on_voice_talk_button
        )
        self.btn_voice_talk.pack(side="left", padx=(0, 6), fill="x", expand=True)

        # Talk to AI Doctor Summary Button
        self.btn_talk_doctor = ctk.CTkButton(
            doc_btn_row,
            text="🩺 CLINICAL SUMMARY",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#0f2942",
            hover_color="#0369a1",
            text_color="#38bdf8",
            border_width=1,
            border_color="#38bdf8",
            height=32,
            command=self.on_click_talk_doctor
        )
        self.btn_talk_doctor.pack(side="left", fill="x", expand=True)

        # Row 2: Query Entry & Ask Button
        doc_row = ctk.CTkFrame(doctor_interact_frame, fg_color="transparent")
        doc_row.pack(fill="x", padx=10, pady=4)

        # Query Entry & Ask Button
        self.entry_doctor_query = ctk.CTkEntry(
            doc_row,
            placeholder_text="Ask flight surgeon or speak symptoms (or click Voice Conversation)...",
            font=ctk.CTkFont(family="Inter", size=11),
            height=32,
            fg_color="#0f172a",
            border_color="#334155"
        )
        self.entry_doctor_query.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.entry_doctor_query.bind("<Return>", lambda e: self.submit_doctor_query())

        self.btn_send_query = ctk.CTkButton(
            doc_row,
            text="SEND",
            font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"),
            width=70,
            height=32,
            fg_color="#0ea5e9",
            command=self.submit_doctor_query
        )
        self.btn_send_query.pack(side="left", padx=(0, 6))

        # 🔇 Stop Voice Button — stops pyttsx3 TTS mid-sentence
        self.btn_stop_voice = ctk.CTkButton(
            doc_row,
            text="🔇 STOP",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            width=72,
            height=32,
            fg_color="#1e293b",
            hover_color="#ff1e53",
            border_width=1,
            border_color="#ff4d6d",
            text_color="#ff4d6d",
            command=self.stop_ai_voice
        )
        self.btn_stop_voice.pack(side="left")


        # Quick Voice Query Chips
        chips_frame = ctk.CTkFrame(doctor_interact_frame, fg_color="transparent")
        chips_frame.pack(fill="x", padx=10, pady=(0, 8))

        quick_queries = [
            ("Heart Rate", "What is my heart rate and sinus rhythm?"),
            ("EVA Readiness", "Am I fit for the spacewalk EVA?"),
            ("Cabin Air", "Check cabin carbon dioxide and atmosphere"),
            ("Fatigue Level", "Evaluate my fatigue and sleep readiness")
        ]
        for label, q_text in quick_queries:
            btn_chip = ctk.CTkButton(
                chips_frame,
                text=label,
                font=ctk.CTkFont(family="Consolas", size=9),
                fg_color="#1e293b",
                hover_color="#334155",
                height=22,
                command=lambda qt=q_text: self.submit_doctor_query(qt)
            )
            btn_chip.pack(side="left", padx=3)

        # -------------------------------------------------------------
        # 3C. RIGHT PANEL: Astronaut Health Report & Suggestion
        # -------------------------------------------------------------
        right_panel = ctk.CTkFrame(work_frame, fg_color="#0b1222", corner_radius=10, border_width=1, border_color="#163b4d")
        right_panel.grid(row=0, column=2, padx=(8, 0), pady=0, sticky="nsew")

        f_r_hdr = ctk.CTkFrame(right_panel, fg_color="transparent")
        f_r_hdr.pack(fill="x", padx=12, pady=(12, 6))

        ctk.CTkLabel(f_r_hdr, text="📋 ASTRONAUT HEALTH REPORT", font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"), text_color="#00f0ff").pack(side="left")

        self.btn_full_dossier = ctk.CTkButton(
            f_r_hdr,
            text="📄 FULL DOSSIER & NASA MATCH",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            text_color="#041209",
            height=26,
            width=175,
            command=self.open_full_clinical_dossier
        )
        self.btn_full_dossier.pack(side="right", padx=(4, 0))
        
        self.btn_view_history = ctk.CTkButton(
            f_r_hdr,
            text="📂 PAST REPORTS",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0ea5e9",
            height=26,
            width=100,
            command=self.open_history_viewer
        )
        self.btn_view_history.pack(side="right")

        # Crew Readiness Score Card
        self.readiness_card = ctk.CTkFrame(right_panel, fg_color="#0d1628", corner_radius=8, border_width=1, border_color="#14382c")
        self.readiness_card.pack(fill="x", padx=12, pady=6)

        ctk.CTkLabel(self.readiness_card, text="CREW READINESS SCORE", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), text_color="#94a3b8").pack(padx=10, pady=(8, 2), anchor="w")

        f_readiness_val = ctk.CTkFrame(self.readiness_card, fg_color="transparent")
        f_readiness_val.pack(fill="x", padx=10, pady=2)
        self.lbl_readiness_pct = ctk.CTkLabel(f_readiness_val, text="88%", font=ctk.CTkFont(family="Rajdhani", size=32, weight="bold"), text_color="#10b981")
        self.lbl_readiness_pct.pack(side="left")

        self.lbl_readiness_tag = ctk.CTkLabel(f_readiness_val, text="FIT FOR EVA / SPACEWALK", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#10b981")
        self.lbl_readiness_tag.pack(side="right", padx=6)

        self.prog_readiness = ctk.CTkProgressBar(self.readiness_card, height=8, progress_color="#10b981", fg_color="#1e293b")
        self.prog_readiness.pack(fill="x", padx=10, pady=(4, 10))
        self.prog_readiness.set(0.88)

        # AI Doctor Analysis (Live Groq LLM Output Box)
        doc_analysis_card = ctk.CTkFrame(right_panel, fg_color="#0d1628", corner_radius=8, border_width=1, border_color="#163b4d")
        doc_analysis_card.pack(fill="x", padx=12, pady=6)

        f_doc_title = ctk.CTkFrame(doc_analysis_card, fg_color="transparent")
        f_doc_title.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(f_doc_title, text="🩺 AI DOCTOR CLINICAL ANALYSIS", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), text_color="#00f0ff").pack(side="left")
        
        self.lbl_doc_active_astro = ctk.CTkLabel(
            f_doc_title,
            text=f"CREW: {state.active_astronaut.get('name', 'ASTRONAUT').upper()}",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            text_color="#38bdf8"
        )
        self.lbl_doc_active_astro.pack(side="left", padx=8)

        ctk.CTkLabel(f_doc_title, text="GROQ LPU", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#a855f7", fg_color="#2d1a45", corner_radius=4).pack(side="right")
        
        self.btn_clear_doc_note = ctk.CTkButton(
            f_doc_title,
            text="🧹 CLEAR",
            font=ctk.CTkFont(family="Consolas", size=9, weight="bold"),
            width=58,
            height=20,
            fg_color="#334155",
            hover_color="#475569",
            command=self.clear_doctor_note
        )
        self.btn_clear_doc_note.pack(side="right", padx=(0, 6))

        self.txt_doctor_note = ctk.CTkTextbox(doc_analysis_card, height=140, font=ctk.CTkFont(family="Inter", size=11), fg_color="#060b14", text_color="#e2e8f0", wrap="word")
        self.txt_doctor_note.pack(fill="x", padx=10, pady=(2, 10))
        self.txt_doctor_note.insert("1.0", state.ai_doctor_note)
        self.txt_doctor_note.configure(state="disabled")

        # Clinical Suggestions
        sug_card = ctk.CTkFrame(right_panel, fg_color="#0d1628", corner_radius=8)
        sug_card.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(sug_card, text="💡 CLINICAL RECOMMENDATIONS", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), text_color="#fbbf24").pack(padx=10, pady=(8, 4), anchor="w")

        self.lbl_sug1 = ctk.CTkLabel(sug_card, text="• 💧 Hydration: Drink 350ml electrolyte pouch", font=ctk.CTkFont(family="Inter", size=10), text_color="#94a3b8", anchor="w")
        self.lbl_sug1.pack(fill="x", padx=10, pady=2)
        self.lbl_sug2 = ctk.CTkLabel(sug_card, text="• 🏃 Exercise: 45 min cycle ergometer protocol", font=ctk.CTkFont(family="Inter", size=10), text_color="#94a3b8", anchor="w")
        self.lbl_sug2.pack(fill="x", padx=10, pady=2)
        self.lbl_sug3 = ctk.CTkLabel(sug_card, text="• 💤 Rest: Synchronize circadian light cycle to GMT", font=ctk.CTkFont(family="Inter", size=10), text_color="#94a3b8", anchor="w")
        self.lbl_sug3.pack(fill="x", padx=10, pady=(2, 8))

        # Cabin Telemetry Grid
        cabin_card = ctk.CTkFrame(right_panel, fg_color="#060b14", corner_radius=8, border_width=1, border_color="#1e293b")
        cabin_card.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(cabin_card, text="🛰️ CABIN TELEMETRY", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#00f0ff").pack(padx=8, pady=(6, 4), anchor="w")

        f_cab_grid = ctk.CTkFrame(cabin_card, fg_color="transparent")
        f_cab_grid.pack(fill="x", padx=8, pady=(0, 6))
        self.lbl_co2 = ctk.CTkLabel(f_cab_grid, text="CO₂: 0.31%", font=ctk.CTkFont(family="Consolas", size=10), text_color="#38bdf8")
        self.lbl_co2.pack(side="left", padx=4)
        self.lbl_temp = ctk.CTkLabel(f_cab_grid, text="Temp: 21.6°C", font=ctk.CTkFont(family="Consolas", size=10), text_color="#38bdf8")
        self.lbl_temp.pack(side="left", padx=4)
        self.lbl_rad = ctk.CTkLabel(f_cab_grid, text="Rad: 0.18 mSv/h", font=ctk.CTkFont(family="Consolas", size=10), text_color="#38bdf8")
        self.lbl_rad.pack(side="left", padx=4)

    # =========================================================================
    # 4. EMERGENCY / RED ALERT ZONE BANNER (Enhancement Tip 2)
    # =========================================================================
    def build_emergency_banner(self):
        self.emergency_banner = ctk.CTkFrame(
            self,
            height=54,
            fg_color="#081820",
            corner_radius=8,
            border_width=2,
            border_color="#10b981"
        )
        self.emergency_banner.pack(fill="x", side="bottom", padx=16, pady=(4, 12))

        inner = ctk.CTkFrame(self.emergency_banner, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=8)

        self.lbl_alert_symbol = ctk.CTkLabel(inner, text="🟢", font=ctk.CTkFont(size=20))
        self.lbl_alert_symbol.pack(side="left", padx=(0, 10))

        content_f = ctk.CTkFrame(inner, fg_color="transparent")
        content_f.pack(side="left", fill="both", expand=True)

        self.lbl_alert_title = ctk.CTkLabel(
            content_f,
            text="SYSTEM NOMINAL: NO CRITICAL ANOMALIES DETECTED",
            font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"),
            text_color="#10b981",
            anchor="w"
        )
        self.lbl_alert_title.pack(fill="x")

        self.lbl_alert_desc = ctk.CTkLabel(
            content_f,
            text="All physiological and cabin parameters within mission safety tolerances. Live IoT Remote listening on local network.",
            font=ctk.CTkFont(family="Inter", size=10),
            text_color="#94a3b8",
            anchor="w"
        )
        self.lbl_alert_desc.pack(fill="x")

        self.btn_banner_action = ctk.CTkButton(
            inner,
            text="🚨 SIMULATE EMERGENCY",
            font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"),
            fg_color="#3b111e",
            hover_color="#ff1e53",
            text_color="#ff4d6d",
            border_width=1,
            border_color="#ff1e53",
            command=self.toggle_emergency_drill
        )
        self.btn_banner_action.pack(side="right")

        self.btn_banner_mute = ctk.CTkButton(
            inner,
            text="🔕 MUTE SIREN",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            text_color="#94a3b8",
            border_width=1,
            border_color="#475569",
            command=self.toggle_siren_mute,
            width=120
        )
        self.btn_banner_mute.pack(side="right", padx=(0, 10))

    # =========================================================================
    # EVENT HANDLERS & LOGIC
    # =========================================================================
    def render_crew_sidebar(self):
        if not hasattr(self, "sidebar_crew_container"):
            return
        for widget in self.sidebar_crew_container.winfo_children():
            widget.destroy()

        self.crew_btn_cards = {}
        for cid, member in state.crew_members.items():
            card = ctk.CTkFrame(self.sidebar_crew_container, fg_color="#131e36", corner_radius=8, border_width=1, border_color="#1e293b", cursor="hand2")
            card.pack(fill="x", padx=10, pady=5)

            avatar_path = member.get("avatar", "")
            img_tk = None
            if os.path.exists(avatar_path):
                try:
                    pil_img = Image.open(avatar_path).resize((44, 44), Image.Resampling.LANCZOS)
                    img_tk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(44, 44))
                    self.photo_cache[cid] = img_tk
                except Exception:
                    pass

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=8)

            if img_tk:
                lbl_img = ctk.CTkLabel(row, text="", image=img_tk)
                lbl_img.pack(side="left", padx=(0, 8))

            info_f = ctk.CTkFrame(row, fg_color="transparent")
            info_f.pack(side="left", fill="both", expand=True)

            lbl_name = ctk.CTkLabel(info_f, text=f"{member.get('serial', '00')} • {member.get('name', 'Astronaut')}", font=ctk.CTkFont(family="Inter", size=12, weight="bold"), text_color="#ffffff", anchor="w")
            lbl_name.pack(fill="x")

            lbl_role = ctk.CTkLabel(info_f, text=member.get('role', 'Specialist'), font=ctk.CTkFont(family="Inter", size=9), text_color="#94a3b8", anchor="w")
            lbl_role.pack(fill="x")

            def make_selector(chosen_id):
                return lambda event=None: self.select_crew_member(chosen_id)

            card.bind("<Button-1>", make_selector(cid))
            for child in [row, info_f, lbl_name, lbl_role]:
                child.bind("<Button-1>", make_selector(cid))

            self.crew_btn_cards[cid] = card

        if state.active_id in self.crew_btn_cards:
            self.crew_btn_cards[state.active_id].configure(border_color="#00f0ff", fg_color="#162c4e")
        elif self.crew_btn_cards:
            first_id = list(self.crew_btn_cards.keys())[0]
            self.crew_btn_cards[first_id].configure(border_color="#00f0ff", fg_color="#162c4e")

    def select_crew_member(self, cid):
        state.set_active_astronaut(cid)
        for k, card in self.crew_btn_cards.items():
            if k == cid:
                card.configure(border_color="#00f0ff", fg_color="#162c4e")
            else:
                card.configure(border_color="#1e293b", fg_color="#131e36")
        if hasattr(self, "lbl_doc_active_astro"):
            name = state.active_astronaut.get("name", "Astronaut")
            self.lbl_doc_active_astro.configure(text=f"CREW: {name.upper()}")

    def open_add_crew_modal(self):
        """Allows space crew or test engineers to register an astronaut on the Space Station directly!"""
        modal = ctk.CTkToplevel(self)
        modal.title("Register Astronaut to Space Station")
        modal.geometry("460x520")
        modal.grab_set()

        ctk.CTkLabel(modal, text="➕ REGISTER NEW SPACE CREW MEMBER", font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"), text_color="#00f0ff").pack(pady=12)

        f = ctk.CTkFrame(modal, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=4)

        def make_row(lbl, default_val=""):
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=lbl, font=ctk.CTkFont(family="Inter", size=10, weight="bold"), width=120, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, font=ctk.CTkFont(family="Inter", size=11))
            entry.insert(0, default_val)
            entry.pack(side="left", fill="x", expand=True)
            return entry

        e_id = make_row("Subject ID (slug):", "pilot_mark")
        e_name = make_row("Full Name:", "Lt. Mark Watney")
        e_callsign = make_row("Callsign:", "BOTANIST")
        e_serial = make_row("Serial Number:", "ARES-05")
        e_role = make_row("Mission Role:", "Mission Specialist / Botanist")
        e_hr = make_row("Baseline Heart Rate:", "68")
        e_spo2 = make_row("Baseline SpO2 (%):", "98.5")

        def _save():
            aid = e_id.get().strip().lower().replace(" ", "_")
            aname = e_name.get().strip()
            if not aid or not aname:
                messagebox.showerror("Error", "ID and Name are required fields!")
                return
            
            active_grp = medical_db.get_active_space_group() or {"group_id": "expedition_72"}
            new_astro = {
                "id": aid,
                "name": aname,
                "callsign": e_callsign.get().strip(),
                "serial": e_serial.get().strip(),
                "role": e_role.get().strip(),
                "avatar": "static/assets/astronaut_sarah.jpg",
                "group_id": active_grp["group_id"],
                "baseline_hr": int(e_hr.get().strip() or "70"),
                "baseline_spo2": float(e_spo2.get().strip() or "98.5"),
                "baseline_hrv": 60.0,
                "fatigue": 15,
                "is_deployed": 1,
                "status": "IN_SPACE"
            }
            medical_db.add_astronaut(new_astro)
            state.reload_crew_from_db()
            state.set_active_astronaut(aid)
            self.render_crew_sidebar()
            modal.destroy()
            messagebox.showinfo("Success", f"Astronaut '{aname}' registered and deployed to Deep Space!")

        ctk.CTkButton(modal, text="REGISTER TO CREW ROSTER", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), fg_color="#059669", hover_color="#10b981", command=_save).pack(fill="x", padx=20, pady=16)

    def toggle_siren_mute(self):
        """Silences or resumes the audible medical siren."""
        is_muted = alarm_sound.toggle_mute()
        if is_muted:
            self.btn_banner_mute.configure(
                text="🔔 UNMUTE SIREN",
                fg_color="#3b2911",
                text_color="#fbbf24",
                border_color="#f59e0b"
            )
        else:
            self.btn_banner_mute.configure(
                text="🔕 MUTE SIREN",
                fg_color="#1e293b",
                text_color="#94a3b8",
                border_color="#475569"
            )
            # If an anomaly is active, restart alarm
            s = state.get_full_state()
            v = s["vitals"]
            an = s["analysis"]
            is_warn = (
                s["is_emergency"]
                or v.get("spo2", 98.4) < 94.0
                or v.get("heart_rate", 72) < 50
                or v.get("heart_rate", 72) > 115
                or v.get("fatigue_level", 20) >= 65
                or an.get("readiness_score", 90) < 65
            )
            if is_warn:
                alarm_sound.start_alarm()

    def toggle_emergency_drill(self):
        s = state.get_full_state()
        v = s["vitals"]
        # If currently in emergency OR vitals are abnormal, resolve back to nominal!
        is_warn = (
            s["is_emergency"]
            or v.get("spo2", 98.4) < 94.0
            or v.get("heart_rate", 72) < 50
            or v.get("heart_rate", 72) > 115
            or v.get("fatigue_level", 20) >= 65
        )
        if is_warn:
            # Return patient to normal ("rugi shavabik hocce") & turn off alarm
            state.update_from_phone(hr=72, spo2=98.4, hrv=58.0, fatigue=18, co2=0.31, is_emergency=False)
            alarm_sound.stop_alarm(reset_mute=True)
            self.btn_banner_mute.configure(
                text="🔕 MUTE SIREN",
                fg_color="#1e293b",
                text_color="#94a3b8",
                border_color="#475569"
            )
            self.groq_doctor.speak_async(
                f"Emergency status resolved. Astronaut {s['astronaut']['name']} physiological parameters returned to nominal baseline."
            )
        else:
            # Trigger emergency drill & start continuous siren alarm
            alarm_sound.unmute()
            state.update_from_phone(hr=42, spo2=88.5, hrv=18.0, fatigue=85, co2=0.75, is_emergency=True)
            alarm_sound.start_alarm()

    def toggle_camera_source(self):
        if self.camera_mode == "neural_brain":
            self.camera_mode = "live_camera"
            self.btn_cam_toggle.configure(text="🧠 SHOW NEURAL BRAIN", fg_color="#163b4d", text_color="#38bdf8")
        else:
            self.camera_mode = "neural_brain"
            self.scan_preview_until = 0.0
            self.btn_cam_toggle.configure(text="👁️ PEEK LIVE CAMERA", fg_color="#0f2942", text_color="#00f0ff")

    def on_click_talk_doctor(self):
        query = "Flight Surgeon, report on my flight clearance, cardiovascular tone, and EVA spacewalk readiness."
        self.submit_doctor_query(query)

    def on_voice_talk_button(self):
        """
        Interactive Voice Conversation: Records voice from astronaut microphone,
        converts speech to text via Groq Whisper-large-v3, and queries AI flight surgeon!
        """
        self.btn_voice_talk.configure(text="🔴 LISTENING... (SPEAK NOW)", fg_color="#ff1e53")
        self.txt_doctor_note.configure(state="normal")
        self.txt_doctor_note.delete("1.0", "end")
        self.txt_doctor_note.insert("1.0", "🎙️ [VOICE MODE ACTIVE] Listening to microphone for 3.5 seconds... Speak your question clearly into the mic!")
        self.txt_doctor_note.configure(state="disabled")

        def _record_worker():
            transcribed = self.groq_doctor.transcribe_audio_from_mic(duration=3.5)
            
            def _on_transcription_ready():
                self.btn_voice_talk.configure(text="🎙️ VOICE CONVERSATION (MIC)", fg_color="#0284c7")
                clean = transcribed.strip()
                if clean and clean not in [".", "..", "...", "!", "?"] and len(clean) > 2:
                    self.entry_doctor_query.delete(0, "end")
                    self.entry_doctor_query.insert(0, clean)
                    self.submit_doctor_query(clean)
                else:
                    self.txt_doctor_note.configure(state="normal")
                    self.txt_doctor_note.delete("1.0", "end")
                    self.txt_doctor_note.insert("1.0", "⚠️ No speech detected from microphone. Please click 'VOICE CONVERSATION' and speak clearly, or type in the query box below.")
                    self.txt_doctor_note.configure(state="disabled")

            self.after(0, _on_transcription_ready)

        threading.Thread(target=_record_worker, daemon=True).start()

    def stop_ai_voice(self):
        """Immediately stops the AI voice (pyttsx3 TTS) mid-sentence."""
        try:
            self.groq_doctor.stop_speaking()
            # Flash the stop button to confirm
            self.btn_stop_voice.configure(fg_color="#ff1e53", text="🔇 STOPPED")
            self.after(800, lambda: self.btn_stop_voice.configure(
                fg_color="#1e293b", text="🔇 STOP"
            ))
        except Exception as e:
            print(f"[AstroMind] Stop voice error: {e}")

    def submit_doctor_query(self, query=None):

        if query is None:
            query = self.entry_doctor_query.get().strip()
            self.entry_doctor_query.delete(0, "end")

        if not query:
            return

        astro_name = state.active_astronaut.get("name", "Astronaut")

        # Show thinking in UI
        self.txt_doctor_note.configure(state="normal")
        self.txt_doctor_note.delete("1.0", "end")
        self.txt_doctor_note.insert("1.0", f"💬 [{astro_name}] Query: \"{query}\"\n\n🩺 AstroMind Groq AI Flight Surgeon analyzing telemetry...")
        self.txt_doctor_note.configure(state="disabled")

        # Run in thread so GUI remains responsive
        def _call_groq():
            s = state.get_full_state()
            try:
                answer = self.groq_doctor.ask_doctor(
                    query=query,
                    astronaut=s["astronaut"],
                    vitals=s["vitals"],
                    cabin=s["cabin"],
                    is_emergency=s["is_emergency"]
                )
            except Exception as e:
                answer = f"Clinical Assessment: Vitals for {s['astronaut']['name']} are stable. SpO2 at {s['vitals']['spo2']:.1f}%. Hydrate and maintain mission protocols."

            # NASA Historical Case Matching
            try:
                matched = HistoricalCaseMatcher.match_case(s["vitals"], s["cabin"], query=query)
                if matched.get("matched_case"):
                    rec_text = (
                        f"\n\n===================================================\n"
                        f"🏛️ NASA HISTORICAL FLIGHT CASE MATCH: {matched['matched_mission']}\n"
                        f"Incident: {matched['matched_case']}\n"
                        f"Similarity: {matched['similarity_score']}%\n"
                        f"---------------------------------------------------\n"
                        f"💊 HOW HISTORICAL ASTRONAUT RECOVERED (FLIGHT PROTOCOL):\n"
                        f"{matched['how_astronaut_recovered']}\n"
                        f"---------------------------------------------------\n"
                        f"🤖 ASTROMIND AI RECOMMENDATION & COUNTERMEASURE:\n"
                        f"{matched['ai_autonomous_suggestion']}\n"
                        f"==================================================="
                    )
                    answer += rec_text

                    # Automatically persist to Clinical Dossier database
                    try:
                        vitals_sum = f"HR: {s['vitals'].get('heart_rate')} BPM | SpO2: {s['vitals'].get('spo2')}% | Fatigue: {s['vitals'].get('fatigue_level')}%"
                        cabin_sum = f"CO2: {s['cabin'].get('co2_percent')}% | Temp: {s['cabin'].get('temp_c')}C | Rad: {s['cabin'].get('radiation_msv')} mSv/h"
                        medical_db.save_clinical_dossier(
                            astronaut_id=s["astronaut"].get("id", state.active_id),
                            astronaut_name=s["astronaut"].get("name", "Astronaut"),
                            report_title=f"Consultation Dossier - {astro_name} - {matched['matched_mission'][:40]}",
                            vitals_summary=vitals_sum,
                            cabin_summary=cabin_sum,
                            status_eval="CRITICAL ANOMALY" if s.get("is_emergency") else "NOMINAL",
                            historical_match_text=matched.get("matched_mission", ""),
                            recovery_protocol_text=matched.get("how_astronaut_recovered", ""),
                            ai_suggestions_text=matched.get("ai_autonomous_suggestion", ""),
                            full_report_text=answer
                        )
                    except Exception as db_ex:
                        print(f"[AstroMind DB Save Error] {db_ex}")

            except Exception as match_ex:
                print(f"[AstroMind Historical Matcher Error] {match_ex}")

            state.ai_doctor_note = answer
            # Speak aloud via pyttsx3 in thread!
            self.groq_doctor.speak_async(answer)

            # Update GUI text
            def _update_ui():
                self.txt_doctor_note.configure(state="normal")
                self.txt_doctor_note.delete("1.0", "end")
                self.txt_doctor_note.insert("1.0", f"💬 [{astro_name}] Query: \"{query}\"\n\n🩺 AI Flight Surgeon (Groq LPU):\n{answer}")
                self.txt_doctor_note.configure(state="disabled")

            self.after(0, _update_ui)

        threading.Thread(target=_call_groq, daemon=True).start()

    def on_manual_instant_scan(self):
        """
        On-demand manual biometric face scan requested by astronaut or judge.
        Captures the live camera frame from the background worker, temporarily
        displays the scanned face with HUD overlay on the center screen,
        computes comparative difference, logs to DB, and delivers spoken diagnosis in English.
        """
        self.btn_manual_scan.configure(text="⏳ SCANNING FACE...", state="disabled")

        # Grab live frame from silent background camera worker
        live_cam_frame = self.rppg_estimator.get_latest_frame()
        if live_cam_frame is None:
            s_now = state.get_full_state()
            av_p = s_now["astronaut"].get("avatar", "")
            if os.path.exists(av_p):
                av_img = cv2.imread(av_p)
                if av_img is not None:
                    live_cam_frame = cv2.resize(av_img, (640, 480))

        if live_cam_frame is not None:
            self.scan_preview_frame = live_cam_frame
            self.scan_preview_until = time.time() + 8.0 # Preview scanned face with 3D mesh for 8 seconds!
        
        self.txt_doctor_note.configure(state="normal")
        self.txt_doctor_note.delete("1.0", "end")
        self.txt_doctor_note.insert("1.0", "🔬 Scanning facial biometrics, calculating comparative delta vs historical baseline...")
        self.txt_doctor_note.configure(state="disabled")

        def _run_scan():
            res = background_analyzer.perform_manual_instant_scan(current_frame_bgr=live_cam_frame)
            
            def _update_ui():
                self.btn_manual_scan.configure(text="🔍 INSTANT BIOMETRIC SCAN", state="normal")
                
                doc_text = (
                    f"【 ON-DEMAND BIOMETRIC SCAN RESULTS 】\n"
                    f"👤 Subject: {res['astronaut']['name']} ({res['astronaut']['role']})\n"
                    f"🩺 Physiological Status: {res['status_eval']}\n"
                    f"📊 Longitudinal Baseline Comparison: {res['trend_diff']}\n\n"
                    f"💡 Flight Surgeon Countermeasures: {res['ai_advice']}\n"
                    f"📸 Snapshot Archived: {res['snapshot_filename']}"
                )
                self.txt_doctor_note.configure(state="normal")
                self.txt_doctor_note.delete("1.0", "end")
                self.txt_doctor_note.insert("1.0", doc_text)
                self.txt_doctor_note.configure(state="disabled")

                # Refresh history modal if currently opened
                if self.history_window and self.history_window.winfo_exists():
                    self.history_window.load_records()

            self.after(0, _update_ui)

        threading.Thread(target=_run_scan, daemon=True).start()

    def render_astronaut_warning_frame(self, member, vitals, reason: str, t: float) -> np.ndarray:
        """
        Renders emergency warning HUD showing the astronaut's profile picture,
        name, critical vitals, and alert overlay in place of the 3D neural brain!
        """
        h, w = 480, 640
        frame = np.zeros((h, w, 3), dtype=np.uint8)
        frame[:] = (10, 12, 22) # Dark space medical background

        # Red pulsing alarm borders
        pulse = 0.5 + 0.5 * math.sin(t * 7)
        red_intensity = int(180 + 75 * pulse)
        border_col = (30, 30, red_intensity)

        # Draw outer HUD border
        cv2.rectangle(frame, (8, 8), (w - 8, h - 8), border_col, 2)

        # Top Red Hazard Banner
        cv2.rectangle(frame, (8, 8), (w - 8, 48), (20, 15, red_intensity), -1)
        cv2.putText(frame, "🚨 CRITICAL MEDICAL ALERT • NASA FLIGHT SURGEON INTERVENTION", (18, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 2)
        cv2.putText(frame, "EMERGENCY ACTIVE", (w - 180, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 255, 255), 1)

        # Load and paste astronaut avatar
        avatar_path = member.get("avatar", "")
        if not hasattr(self, "avatar_bgr_cache"):
            self.avatar_bgr_cache = {}

        if avatar_path not in self.avatar_bgr_cache:
            if os.path.exists(avatar_path):
                img = cv2.imread(avatar_path)
                if img is not None:
                    img = cv2.resize(img, (200, 200))
                    self.avatar_bgr_cache[avatar_path] = img
                else:
                    self.avatar_bgr_cache[avatar_path] = None
            else:
                self.avatar_bgr_cache[avatar_path] = None

        avatar_img = self.avatar_bgr_cache.get(avatar_path)
        ax, ay, aw, ah = 30, 68, 200, 200
        if avatar_img is not None:
            frame[ay:ay+ah, ax:ax+aw] = avatar_img
        else:
            cv2.rectangle(frame, (ax, ay), (ax+aw, ay+ah), (40, 40, 60), -1)
            cv2.putText(frame, "PHOTO UNAVAILABLE", (ax + 20, ay + 100), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Draw glowing red photo frame and corner brackets
        cv2.rectangle(frame, (ax, ay), (ax+aw, ay+ah), border_col, 2)
        c_len = 22
        cv2.line(frame, (ax, ay), (ax + c_len, ay), (0, 240, 255), 3)
        cv2.line(frame, (ax, ay), (ax, ay + c_len), (0, 240, 255), 3)
        cv2.line(frame, (ax+aw, ay), (ax+aw - c_len, ay), (0, 240, 255), 3)
        cv2.line(frame, (ax+aw, ay), (ax+aw, ay + c_len), (0, 240, 255), 3)
        cv2.line(frame, (ax, ay+ah), (ax + c_len, ay+ah), (0, 240, 255), 3)
        cv2.line(frame, (ax, ay+ah), (ax, ay+ah - c_len), (0, 240, 255), 3)
        cv2.line(frame, (ax+aw, ay+ah), (ax+aw - c_len, ay+ah), (0, 240, 255), 3)
        cv2.line(frame, (ax+aw, ay+ah), (ax+aw, ay+ah - c_len), (0, 240, 255), 3)

        # Astronaut Name & Credentials (Right side of photo)
        tx = 250
        name_str = member.get("name", "ASTRONAUT").upper()
        role_str = member.get("role", "CREW MEMBER").upper()
        serial_str = member.get("serial", "CREW-01")

        cv2.putText(frame, "COMPROMISED SUBJECT:", (tx, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (148, 163, 184), 1)
        cv2.putText(frame, name_str, (tx, 116), cv2.FONT_HERSHEY_SIMPLEX, 0.70, (255, 255, 255), 2)
        cv2.putText(frame, f"{serial_str} • {role_str}", (tx, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 240, 255), 1)

        # Warning Diagnosis Box
        cv2.rectangle(frame, (tx, 155), (w - 20, 225), (25, 20, 45), -1)
        cv2.rectangle(frame, (tx, 155), (w - 20, 225), border_col, 1)
        cv2.putText(frame, "DIAGNOSTIC ANOMALY:", (tx + 10, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 100, 120), 1)
        cv2.putText(frame, reason, (tx + 10, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (50, 50, 255), 2)

        # Telemetry Card Bar (Middle)
        cv2.rectangle(frame, (30, 280), (w - 20, 360), (14, 20, 35), -1)
        cv2.rectangle(frame, (30, 280), (w - 20, 360), (50, 70, 100), 1)

        hr = vitals.get("heart_rate", 72)
        spo2 = vitals.get("spo2", 98.4)
        fat = vitals.get("fatigue_level", 20)
        hrv = vitals.get("hrv", 58.0)

        col_hr = (50, 50, 255) if (hr < 50 or hr > 115) else (0, 255, 120)
        col_spo2 = (50, 50, 255) if spo2 < 93.0 else (0, 240, 255)
        col_fat = (50, 50, 255) if fat >= 65 else (0, 255, 120)

        cv2.putText(frame, "PULSE / HR", (50, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (148, 163, 184), 1)
        cv2.putText(frame, f"{hr} BPM", (50, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col_hr, 2)

        cv2.putText(frame, "BLOOD OXYGEN", (200, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (148, 163, 184), 1)
        cv2.putText(frame, f"{spo2:.1f}%", (200, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col_spo2, 2)

        cv2.putText(frame, "COGNITIVE FATIGUE", (360, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (148, 163, 184), 1)
        cv2.putText(frame, f"{fat}%", (360, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.65, col_fat, 2)

        cv2.putText(frame, "HRV TONE", (520, 305), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (148, 163, 184), 1)
        cv2.putText(frame, f"{hrv:.0f} ms", (520, 340), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (200, 150, 255), 2)

        # Mandatory Emergency Action Banner
        cv2.rectangle(frame, (30, 375), (w - 20, 458), (35, 15, 25), -1)
        cv2.rectangle(frame, (30, 375), (w - 20, 458), (50, 50, 255), 1)

        cv2.putText(frame, "MANDATORY COUNTERMEASURES PROTOCOL:", (45, 400), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (0, 255, 255), 1)
        cv2.putText(frame, "1. Engage pressurized supplemental O2 mask loop immediately.", (45, 423), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)
        cv2.putText(frame, "2. Cease all EVA spacewalk duties and notify Ground Flight Surgeon.", (45, 443), cv2.FONT_HERSHEY_SIMPLEX, 0.40, (255, 255, 255), 1)

        return frame

    # =========================================================================
    # REAL-TIME ANIMATION & TELEMETRY LOOPS
    # =========================================================================
    def update_video_feed_loop(self):
        """
        Renders real-time 3D Holographic Neural AI Brain animation continuously on the main viewport.
        When any health warning or emergency occurs, displays that astronaut's photo & warning HUD!
        When manual scan is triggered, displays the scanned face with HUD telemetry for 8 seconds,
        then automatically resumes the 3D Neural AI Brain!
        """
        try:
            t = time.time()
            s = state.get_full_state()
            vitals = s["vitals"]
            analysis = s["analysis"]
            is_emergency = s["is_emergency"]

            # Check if astronaut has an active health warning or emergency
            is_warning = False
            warning_reason = ""
            if is_emergency:
                is_warning = True
                warning_reason = "ACUTE HYPOXIA & CARDIAC COLLAPSE DRILL"
            elif vitals.get("spo2", 98.4) < 94.0:
                is_warning = True
                warning_reason = f"CRITICAL HYPOXIA ALERT (SpO2: {vitals['spo2']:.1f}%)"
            elif vitals.get("heart_rate", 72) < 50:
                is_warning = True
                warning_reason = f"SEVERE BRADYCARDIA ALERT (HR: {vitals['heart_rate']} BPM)"
            elif vitals.get("heart_rate", 72) > 115:
                is_warning = True
                warning_reason = f"ACUTE TACHYCARDIA ALERT (HR: {vitals['heart_rate']} BPM)"
            elif vitals.get("fatigue_level", 20) >= 65:
                is_warning = True
                warning_reason = f"CRITICAL COGNITIVE EXHAUSTION ({vitals['fatigue_level']}%)"
            elif analysis.get("readiness_score", 90) < 65:
                is_warning = True
                warning_reason = f"RESTRICTED DUTY CLEARANCE ({analysis['readiness_score']}%)"

            # 1. HEALTH WARNING MODE: Show Astronaut Profile Picture & Warning HUD instead of 3D brain!
            if is_warning:
                frame = self.render_astronaut_warning_frame(s["astronaut"], vitals, warning_reason, t)

            # 2. Peek Live Camera mode (if manually toggled):
            elif self.camera_mode == "live_camera":
                cam_f = self.rppg_estimator.get_latest_frame()
                if cam_f is not None:
                    frame = cam_f
                else:
                    frame = self.rppg_estimator.generate_synthetic_astronaut_frame(t, vitals=vitals, is_emergency=is_emergency)

            # 3. Instant Scan Preview mode (active for 8 seconds after clicking Manual Scan):
            elif time.time() < self.scan_preview_until:
                raw_preview = None
                if self.scan_preview_frame is not None:
                    raw_preview = self.scan_preview_frame.copy()
                else:
                    avatar_p = s["astronaut"].get("avatar", "")
                    if os.path.exists(avatar_p):
                        av_bgr = cv2.imread(avatar_p)
                        if av_bgr is not None:
                            raw_preview = cv2.resize(av_bgr, (640, 480))
                if raw_preview is None:
                    raw_preview = np.zeros((480, 640, 3), dtype=np.uint8)
                    raw_preview[:] = (18, 22, 34)

                # Dynamically apply the 3D Biometric Facial Mesh Mask with vertical contour lines,
                # eye tracking, anatomical landmarks, and sweeping animated laser beam!
                frame, _ = face_mesh_scanner.apply_face_mesh_mask(
                    raw_preview,
                    t=t,
                    is_active_scan=True,
                    vitals=vitals
                )

                rem = max(1, int(self.scan_preview_until - time.time()))
                h, w, _ = frame.shape
                cv2.rectangle(frame, (10, h - 68), (w - 10, h - 38), (16, 50, 24), -1)
                cv2.rectangle(frame, (10, h - 68), (w - 10, h - 38), (0, 255, 120), 1)
                cv2.putText(
                    frame,
                    f"3D BIOMETRIC MESH SCAN • ANALYZING TOPOLOGY • NEURAL BRAIN IN {rem}s",
                    (20, h - 48),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.38,
                    (0, 255, 180),
                    1
                )

            # 4. Default Nominal State: 3D Holographic Animated Neural AI Brain!
            else:
                frame = self.rppg_estimator.generate_synthetic_astronaut_frame(t, vitals=vitals, is_emergency=is_emergency)

            # Store latest frame for snapshots
            self.last_frame_bgr = frame

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Scale to fit canvas
            can_w = self.canvas_video.winfo_width()
            can_h = self.canvas_video.winfo_height()
            if can_w > 50 and can_h > 50:
                frame_resized = cv2.resize(frame_rgb, (can_w, can_h))
                img_pil = Image.fromarray(frame_resized)
                self.img_tk_video = ImageTk.PhotoImage(image=img_pil)
                self.canvas_video.delete("all")
                self.canvas_video.create_image(0, 0, anchor="nw", image=self.img_tk_video)

        except Exception as e:
            pass

        self.after(33, self.update_video_feed_loop)

    def update_vitals_loop(self):
        """
        Refreshes vitals from shared state (reflecting phone or local changes),
        animates ECG canvas line, and updates emergency red alert status.
        """
        s = state.get_full_state()
        v = s["vitals"]
        c = s["cabin"]
        analysis = s["analysis"]
        is_em = s["is_emergency"]

        # 1. Update Card 1: Pulse
        hr = v["heart_rate"]
        self.lbl_hr_val.configure(text=str(hr))
        if hr < 50 or hr > 115:
            self.badge_hr.configure(text="BRADYCARDIA" if hr < 50 else "TACHYCARDIA", text_color="#ff1e53", fg_color="#3b111e")
            self.card_hr.configure(border_color="#ff1e53")
        else:
            self.badge_hr.configure(text="NORMAL", text_color="#10b981", fg_color="#103628")
            self.card_hr.configure(border_color="#381d24")

        # Animate ECG Canvas
        self.render_ecg_pulse(hr, is_em)

        # 2. Update Card 2: SpO2
        spo2 = v["spo2"]
        self.lbl_spo2_val.configure(text=f"{spo2:.1f}")
        self.prog_spo2.set(max(0.0, min(1.0, spo2 / 100.0)))
        if spo2 < 90.0:
            self.badge_spo2.configure(text="HYPOXIA", text_color="#ff1e53", fg_color="#3b111e")
            self.prog_spo2.configure(progress_color="#ff1e53")
            self.card_spo2.configure(border_color="#ff1e53")
        elif spo2 < 94.0:
            self.badge_spo2.configure(text="CAUTION", text_color="#f59e0b", fg_color="#3b2911")
            self.prog_spo2.configure(progress_color="#f59e0b")
        else:
            self.badge_spo2.configure(text="OPTIMAL", text_color="#10b981", fg_color="#103628")
            self.prog_spo2.configure(progress_color="#00f0ff")
            self.card_spo2.configure(border_color="#163b4d")

        # 3. Update Card 3: HRV
        hrv = v["hrv"]
        self.lbl_hrv_val.configure(text=f"{hrv:.0f}")
        self.prog_hrv.set(max(0.0, min(1.0, hrv / 100.0)))

        # 4. Update Card 4: Fatigue
        fatigue = v["fatigue_level"]
        self.lbl_fatigue_val.configure(text=str(fatigue))
        self.prog_fatigue.set(max(0.0, min(1.0, fatigue / 100.0)))

        # 5. Readiness Score
        readiness = analysis["readiness_score"]
        self.lbl_readiness_pct.configure(text=f"{readiness}%")
        self.lbl_readiness_tag.configure(text=analysis["readiness_status"])
        self.prog_readiness.set(max(0.0, min(1.0, readiness / 100.0)))

        # 6. Cabin Environment
        self.lbl_co2.configure(text=f"CO₂: {c['co2_percent']:.2f}%")
        self.lbl_temp.configure(text=f"Temp: {c['temp_c']:.1f}°C")
        self.lbl_rad.configure(text=f"Rad: {c['radiation_msv']:.2f} mSv/h")

        # 7. Suggestions
        suggs = analysis.get("suggestions", [])
        if len(suggs) > 0: self.lbl_sug1.configure(text=f"• {suggs[0]}")
        if len(suggs) > 1: self.lbl_sug2.configure(text=f"• {suggs[1]}")
        if len(suggs) > 2: self.lbl_sug3.configure(text=f"• {suggs[2]}")

        # 8. EMERGENCY RED ALERT BANNER & CONTINUOUS AUDIBLE WARNING SIREN
        is_warning = False
        warning_reason = ""
        if is_em:
            is_warning = True
            warning_reason = "CRITICAL HYPOXIA & CARDIAC COLLAPSE DRILL"
        elif spo2 < 94.0:
            is_warning = True
            warning_reason = f"CRITICAL HYPOXIA ALERT (SpO2: {spo2:.1f}%)"
        elif hr < 50:
            is_warning = True
            warning_reason = f"SEVERE BRADYCARDIA ALERT (HR: {hr} BPM)"
        elif hr > 115:
            is_warning = True
            warning_reason = f"ACUTE TACHYCARDIA ALERT (HR: {hr} BPM)"
        elif fatigue >= 65:
            is_warning = True
            warning_reason = f"CRITICAL COGNITIVE EXHAUSTION ({fatigue}%)"
        elif readiness < 65:
            is_warning = True
            warning_reason = f"RESTRICTED DUTY CLEARANCE ({readiness}%)"

        if is_warning:
            # 1. Continuous audible medical siren plays until turned off or patient returns to normal!
            alarm_sound.start_alarm()

            # 2. Update Emergency Red Alert Banner
            self.emergency_banner.configure(fg_color="#3b0914", border_color="#ff1e53")
            self.lbl_alert_symbol.configure(text="🚨")
            self.lbl_alert_title.configure(text=f"CRITICAL MEDICAL ALERT: {s['astronaut']['name'].upper()}", text_color="#ff1e53")
            self.lbl_alert_desc.configure(
                text=f"{warning_reason}. Continuous audible warning siren active until resolved or telemetry stabilizes.",
                text_color="#fca5a5"
            )
            self.btn_banner_action.configure(text="RESOLVE EMERGENCY", fg_color="#ff1e53", text_color="#ffffff")
            self.btn_header_drill.configure(text="RESOLVE DRILL", fg_color="#ff1e53", text_color="#ffffff")

            # 3. Voice announcement (triggers when warning starts or repeats every 25s if unresolved)
            now_t = time.time()
            if not self.last_warning_state or (now_t - self.last_spoken_warning_time > 25.0):
                self.last_spoken_warning_time = now_t
                alert_speech = f"Attention crew! Critical health alert detected for {s['astronaut']['name']}. {warning_reason}. Continuous warning alarm sounding!"
                self.groq_doctor.speak_async(alert_speech)

            self.last_warning_state = True

        else:
            # When patient returns to normal ("rugi shavabik hocce") or warning is turned off:
            if self.last_warning_state:
                # Turn off alarm siren immediately!
                alarm_sound.stop_alarm(reset_mute=True)
                self.btn_banner_mute.configure(
                    text="🔕 MUTE SIREN",
                    fg_color="#1e293b",
                    text_color="#94a3b8",
                    border_color="#475569"
                )
                self.groq_doctor.speak_async(f"Health alert cleared. Astronaut {s['astronaut']['name']} physiological parameters returned to normal.")
                self.last_warning_state = False

            # Restore Nominal Green State
            self.emergency_banner.configure(fg_color="#081820", border_color="#10b981")
            self.lbl_alert_symbol.configure(text="🟢")
            self.lbl_alert_title.configure(text="SYSTEM NOMINAL: NO CRITICAL ANOMALIES DETECTED", text_color="#10b981")
            self.lbl_alert_desc.configure(
                text="All physiological and cabin parameters within mission safety tolerances. Live IoT Remote listening on local network.",
                text_color="#94a3b8"
            )
            self.btn_banner_action.configure(text="🚨 SIMULATE EMERGENCY", fg_color="#3b111e", text_color="#ff4d6d")
            self.btn_header_drill.configure(text="🚨 SIMULATE DRILL", fg_color="#3b111e", text_color="#ff4d6d")

        # Check if Earth Mission Control updated the active space crew or deployment group
        gui_crew_ids = set(self.crew_btn_cards.keys()) if hasattr(self, "crew_btn_cards") else set()
        current_crew_ids = set(state.crew_members.keys())
        current_rev = getattr(state, "crew_revision", 0)

        if gui_crew_ids != current_crew_ids or getattr(self, "last_rendered_crew_rev", -1) != current_rev:
            self.last_rendered_crew_rev = current_rev
            self.render_crew_sidebar()

        self.after(500, self.update_vitals_loop)

    def render_ecg_pulse(self, hr, is_emergency):
        """
        Draws dynamic P-Q-R-S-T ECG pulse line across Tkinter canvas.
        """
        self.ecg_counter += 1
        pqrst = [0, 1, 2, 0, -3, 16, -6, 0, 1, 2, 1, 0]
        period = 18 if is_emergency else 10

        val = 0
        idx = self.ecg_counter % period
        if idx < len(pqrst):
            val = pqrst[idx]

        self.ecg_points.append(val)
        if len(self.ecg_points) > 120:
            self.ecg_points.pop(0)

        self.canvas_ecg.delete("all")
        w = self.canvas_ecg.winfo_width()
        h = self.canvas_ecg.winfo_height()
        if w < 10 or h < 10:
            return

        mid_y = h / 2
        line_color = "#ff1e53" if is_emergency else "#10b981"

        coords = []
        step = w / len(self.ecg_points)
        for i, pt in enumerate(self.ecg_points):
            x = i * step
            y = mid_y - (pt * 0.9)
            coords.extend([x, y])

        if len(coords) >= 4:
            self.canvas_ecg.create_line(coords, fill=line_color, width=1.5, smooth=True)

    def update_clock_loop(self):
        """
        Live Mission Date & Time feature + 30-min auto-scan countdown ticker.
        """
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        utc_str = now.strftime("%H:%M:%S UTC")

        # Mission Elapsed Time (MET)
        elapsed = max(0, int(time.time() - self.mission_start_epoch))
        days = elapsed // 86400
        hours = (elapsed % 86400) // 3600
        mins = (elapsed % 3600) // 60
        secs = elapsed % 60
        met_str = f"+{days:02d}d {hours:02d}h {mins:02d}m {secs:02d}s"

        self.lbl_mission_clock.configure(text=f"📅 {date_str}  ⏰ {utc_str}")

        # Mission Elapsed Time — separate badge
        if hasattr(self, 'lbl_met'):
            self.lbl_met.configure(text=f"MET: {met_str}")

        # 30-Minute Auto Snapshot Countdown
        rem_sec = background_analyzer.get_seconds_until_next_snapshot()
        rem_m = rem_sec // 60
        rem_s = rem_sec % 60
        self.lbl_auto_snapshot_timer.configure(text=f"📸 Auto-Scan: {rem_m:02d}m {rem_s:02d}s")

        self.after(1000, self.update_clock_loop)



if __name__ == "__main__":
    app = AstroMindDesktopApp()
    app.mainloop()
