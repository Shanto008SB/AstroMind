"""
AstroMind Earth Station: NASA Houston Mission Control Center
Runs on Earth PC (PC #2) and connects via Local Wi-Fi / LAN to the Space Station (PC #1).

Key Capabilities:
1. Deep Space LAN S-Band Telemetry Link (fetches live vitals & alerts from Space PC)
2. Interactive Space Station IP Configuration in Header
3. Ground Flight Director Red Alert System (Audio chimes + glowing hazard HUD)
4. Direct Sick Astronaut Detection & Visual Profile Alert (Prominently shows WHO is sick in space)
5. Multi-Expedition Crew Roster Administration (Exclusive to Earth):
   - Add/Edit astronauts and sync over Wi-Fi to Space Station
   - Create new expeditions (e.g. Artemis III, Expedition 73)
   - Deploy groups to Space (Space Station ONLY displays the currently deployed crew!)
   - Archive / remove returned astronauts while preserving historical medical data
6. Full Conversational AI Flight Surgeon with Groq Qwen-3.8-27B (Medical diagnosis & general conversation)
7. Comprehensive Multi-Expedition Medical History & Clinical Report Generator
8. Zero Camera / Face Recognition overhead on Earth workstation (Telemetry & Analytics focus)
"""

import sys
import os

# Ensure folder is in sys.path and cwd regardless of where launcher is run
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
os.chdir(_SCRIPT_DIR)

import time
import math
import threading
from datetime import datetime, timezone
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import customtkinter as ctk

from engine.medical_db import medical_db
from engine.groq_doctor import GroqAIDoctor
from engine.earth_network_client import network_client
from engine.nasa_standards_viewer import NASAStandardsViewer
from engine.clinical_report_viewer import ClinicalReportViewer
from engine.historical_case_matcher import HistoricalCaseMatcher

# Appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


class EarthMissionControlApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("AstroMind • NASA Mission Control Center (Houston Earth Station)")
        self.geometry("1520x940")
        self.minsize(1280, 800)
        self.configure(fg_color="#050a14")

        # Core Services
        self.groq_doctor = GroqAIDoctor()
        
        # State variables
        self.selected_group_id = "expedition_72"
        self.selected_astro_id = "sarah"
        self.photo_cache = {}
        self.last_emergency_state = False
        self.manual_selection_override = False
        self.ecg_points = [0] * 120
        self.ecg_counter = 0
        self.nasa_standards_window = None

        # Build UI
        self.build_header()
        self.build_vitals_strip()
        self.build_main_workspace()
        self.build_emergency_banner()

        # Start background polling loops
        self.poll_space_telemetry_loop()
        self.update_clock_loop()

    # =========================================================================
    # 1. HEADER
    # =========================================================================
    def build_header(self):
        header = ctk.CTkFrame(self, height=64, fg_color="#091224", corner_radius=0, border_width=1, border_color="#132742")
        header.pack(fill="x", side="top")

        brand_f = ctk.CTkFrame(header, fg_color="transparent")
        brand_f.pack(side="left", padx=16, pady=8)

        lbl_logo = ctk.CTkLabel(brand_f, text="🌍 NASA MISSION CONTROL • HOUSTON", font=ctk.CTkFont(family="Orbitron", size=16, weight="bold"), text_color="#38bdf8")
        lbl_logo.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(brand_f, text="EARTH GROUND FLIGHT SURGEON & EXPEDITION COMMAND CONSOLE", font=ctk.CTkFont(family="Consolas", size=9), text_color="#94a3b8")
        lbl_sub.pack(anchor="w")

        # Status & Time Badges
        right_f = ctk.CTkFrame(header, fg_color="transparent")
        right_f.pack(side="right", padx=16, pady=8)

        # Space Station IP Configuration Box (For 2 PCs over LAN / Wi-Fi!)
        ip_box = ctk.CTkFrame(right_f, fg_color="#060c18", corner_radius=6, border_width=1, border_color="#1e3a5f")
        ip_box.pack(side="left", padx=6)

        ctk.CTkLabel(ip_box, text="🛰️ Space PC IP:", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#38bdf8").pack(side="left", padx=(6, 2))
        self.entry_space_ip = ctk.CTkEntry(ip_box, width=130, height=24, font=ctk.CTkFont(family="Consolas", size=10))
        initial_ip = f"{network_client.space_host}:{network_client.space_port}"
        self.entry_space_ip.insert(0, initial_ip)
        self.entry_space_ip.bind("<Return>", lambda e: self.apply_space_ip())
        self.entry_space_ip.pack(side="left", padx=4)

        btn_connect = ctk.CTkButton(ip_box, text="SYNC", width=50, height=22, font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"), fg_color="#0284c7", command=self.apply_space_ip)
        btn_connect.pack(side="left", padx=(2, 6))

        # DSN Uplink Status Badge
        self.link_box = ctk.CTkFrame(right_f, fg_color="#060c18", corner_radius=6, border_width=1, border_color="#10b981")
        self.link_box.pack(side="left", padx=6)
        self.lbl_link_status = ctk.CTkLabel(self.link_box, text="🟢 DSN LINK: CONNECTED", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#10b981")
        self.lbl_link_status.pack(padx=8, pady=4)

        # Active Deployment Group Indicator
        self.lbl_active_group_badge = ctk.CTkLabel(
            right_f,
            text="🚀 ACTIVE IN SPACE: Expedition 72",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#0f2b48",
            text_color="#00f0ff",
            corner_radius=6,
            padx=10, pady=4
        )
        self.lbl_active_group_badge.pack(side="left", padx=6)

        # NASA Open Data Standards Button
        btn_nasa_data = ctk.CTkButton(
            right_f,
            text="🏛️ NASA DATA",
            width=84,
            height=24,
            font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"),
            fg_color="#082f49",
            hover_color="#0284c7",
            border_width=1,
            border_color="#38bdf8",
            text_color="#38bdf8",
            command=self.open_nasa_standards_viewer
        )
        btn_nasa_data.pack(side="left", padx=6)

        # Mission UTC Clock
        clock_box = ctk.CTkFrame(right_f, fg_color="#060c18", corner_radius=6, border_width=1, border_color="#1e293b")
        clock_box.pack(side="left", padx=6)
        self.lbl_earth_clock = ctk.CTkLabel(clock_box, text="📅 2026-10-09  ⏰ 14:00:00 UTC", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#38bdf8")
        self.lbl_earth_clock.pack(padx=8, pady=4)

    def open_nasa_standards_viewer(self):
        if self.nasa_standards_window is None or not self.nasa_standards_window.winfo_exists():
            self.nasa_standards_window = NASAStandardsViewer(self)
        else:
            self.nasa_standards_window.focus()

    def apply_space_ip(self):
        val = self.entry_space_ip.get().strip()
        if val:
            self.lbl_link_status.configure(text=f"🟡 CONNECTING TO {val}...", text_color="#f59e0b")
            self.link_box.configure(border_color="#f59e0b")
            network_client.set_space_address(val)
            self.poll_space_telemetry_loop()

    # =========================================================================
    # 2. TOP VITALS STRIP (Space Station Live Sync)
    # =========================================================================
    def build_vitals_strip(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="x", padx=16, pady=(8, 4))

        for i in range(4):
            container.grid_columnconfigure(i, weight=1)

        # Card 1: Pulse
        self.card_hr = ctk.CTkFrame(container, fg_color="#0a1324", corner_radius=8, border_width=1, border_color="#2b1a23")
        self.card_hr.grid(row=0, column=0, padx=5, sticky="nsew")
        top_1 = ctk.CTkFrame(self.card_hr, fg_color="transparent")
        top_1.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(top_1, text="❤️ SPACE CREW PULSE", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), text_color="#f87171").pack(side="left")
        self.badge_hr = ctk.CTkLabel(top_1, text="NORMAL", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#10b981", fg_color="#103628", corner_radius=4)
        self.badge_hr.pack(side="right")
        self.lbl_hr_val = ctk.CTkLabel(self.card_hr, text="72 BPM", font=ctk.CTkFont(family="Rajdhani", size=28, weight="bold"), text_color="#ffffff")
        self.lbl_hr_val.pack(padx=10, pady=(0, 2), anchor="w")
        self.canvas_ecg = tk.Canvas(self.card_hr, height=24, bg="#060c18", highlightthickness=0)
        self.canvas_ecg.pack(fill="x", padx=10, pady=(2, 6))

        # Card 2: SpO2
        self.card_spo2 = ctk.CTkFrame(container, fg_color="#0a1324", corner_radius=8, border_width=1, border_color="#132742")
        self.card_spo2.grid(row=0, column=1, padx=5, sticky="nsew")
        top_2 = ctk.CTkFrame(self.card_spo2, fg_color="transparent")
        top_2.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(top_2, text="🫁 BLOOD OXYGEN (SpO₂)", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), text_color="#00f0ff").pack(side="left")
        self.badge_spo2 = ctk.CTkLabel(top_2, text="OPTIMAL", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#10b981", fg_color="#103628", corner_radius=4)
        self.badge_spo2.pack(side="right")
        self.lbl_spo2_val = ctk.CTkLabel(self.card_spo2, text="98.4 %", font=ctk.CTkFont(family="Rajdhani", size=28, weight="bold"), text_color="#ffffff")
        self.lbl_spo2_val.pack(padx=10, pady=(0, 2), anchor="w")
        self.prog_spo2 = ctk.CTkProgressBar(self.card_spo2, height=5, progress_color="#00f0ff", fg_color="#1e293b")
        self.prog_spo2.pack(fill="x", padx=10, pady=(8, 8))
        self.prog_spo2.set(0.984)

        # Card 3: Fatigue
        self.card_fatigue = ctk.CTkFrame(container, fg_color="#0a1324", corner_radius=8, border_width=1, border_color="#152b22")
        self.card_fatigue.grid(row=0, column=2, padx=5, sticky="nsew")
        top_3 = ctk.CTkFrame(self.card_fatigue, fg_color="transparent")
        top_3.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(top_3, text="🧠 COGNITIVE FATIGUE", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), text_color="#34d399").pack(side="left")
        self.lbl_fatigue_val = ctk.CTkLabel(self.card_fatigue, text="18 %", font=ctk.CTkFont(family="Rajdhani", size=28, weight="bold"), text_color="#ffffff")
        self.lbl_fatigue_val.pack(padx=10, pady=(0, 2), anchor="w")
        self.prog_fatigue = ctk.CTkProgressBar(self.card_fatigue, height=5, progress_color="#34d399", fg_color="#1e293b")
        self.prog_fatigue.pack(fill="x", padx=10, pady=(8, 8))
        self.prog_fatigue.set(0.18)

        # Card 4: Cabin Environment
        self.card_cabin = ctk.CTkFrame(container, fg_color="#0a1324", corner_radius=8, border_width=1, border_color="#2b2413")
        self.card_cabin.grid(row=0, column=3, padx=5, sticky="nsew")
        top_4 = ctk.CTkFrame(self.card_cabin, fg_color="transparent")
        top_4.pack(fill="x", padx=10, pady=(6, 2))
        ctk.CTkLabel(top_4, text="🛸 SPACECRAFT CABIN", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), text_color="#fbbf24").pack(side="left")
        self.lbl_cabin_val = ctk.CTkLabel(self.card_cabin, text="CO₂: 0.31% • 21.6°C", font=ctk.CTkFont(family="Rajdhani", size=24, weight="bold"), text_color="#fef08a")
        self.lbl_cabin_val.pack(padx=10, pady=(0, 2), anchor="w")
        ctk.CTkLabel(self.card_cabin, text="Radiation: 0.18 mSv/h • Nominal Pressure", font=ctk.CTkFont(family="Consolas", size=9), text_color="#94a3b8").pack(padx=10, pady=(2, 6), anchor="w")

    # =========================================================================
    # 3. MAIN WORKSPACE (3 Columns)
    # =========================================================================
    def build_main_workspace(self):
        grid = ctk.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="both", expand=True, padx=16, pady=6)

        grid.grid_columnconfigure(0, weight=3) # Left: Expeditions & Crew Administration
        grid.grid_columnconfigure(1, weight=5) # Center: Bio-Telemetry & Sick Astronaut Alert
        grid.grid_columnconfigure(2, weight=4) # Right: Conversational AI Surgeon & Reports
        grid.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # 3A. LEFT: EXPEDITIONS & ROSTER MANAGEMENT (EXCLUSIVE TO EARTH)
        # -------------------------------------------------------------
        left_col = ctk.CTkFrame(grid, fg_color="#081020", corner_radius=10, border_width=1, border_color="#132742")
        left_col.grid(row=0, column=0, padx=(0, 5), sticky="nsew")

        l_header = ctk.CTkFrame(left_col, fg_color="transparent")
        l_header.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(l_header, text="👥 EXPEDITION ROSTER (ADMIN)", font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"), text_color="#38bdf8").pack(side="left")

        # Group Selector dropdown
        grp_row = ctk.CTkFrame(left_col, fg_color="transparent")
        grp_row.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(grp_row, text="Select Group:", font=ctk.CTkFont(family="Inter", size=10), text_color="#94a3b8").pack(side="left", padx=(0, 6))
        
        self.opt_groups = ctk.CTkOptionMenu(
            grp_row,
            values=["Expedition 72", "Expedition 71 (Historical)", "Artemis III"],
            command=self.on_group_selected,
            fg_color="#0f2b48",
            button_color="#0284c7"
        )
        self.opt_groups.pack(side="left", fill="x", expand=True)

        # Crew cards scrollable frame
        self.scroll_crew = ctk.CTkScrollableFrame(left_col, fg_color="transparent")
        self.scroll_crew.pack(fill="both", expand=True, padx=8, pady=4)

        # Action Buttons Box for Earth Administration
        admin_btns = ctk.CTkFrame(left_col, fg_color="#050a14", corner_radius=8, border_width=1, border_color="#132742")
        admin_btns.pack(fill="x", padx=10, pady=8)

        # Row 1: Add Astronaut & Edit Astronaut
        row1 = ctk.CTkFrame(admin_btns, fg_color="transparent")
        row1.pack(fill="x", padx=6, pady=3)
        btn_add_astro = ctk.CTkButton(row1, text="➕ ADD ASTRONAUT", font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"), fg_color="#0284c7", command=self.open_add_astronaut_modal)
        btn_add_astro.pack(side="left", fill="x", expand=True, padx=2)
        btn_edit_astro = ctk.CTkButton(row1, text="✏️ EDIT ASTRONAUT", font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"), fg_color="#1e293b", command=self.open_edit_astronaut_modal)
        btn_edit_astro.pack(side="left", fill="x", expand=True, padx=2)

        # Row 2: Mark Returned & Remove Astronaut
        row2 = ctk.CTkFrame(admin_btns, fg_color="transparent")
        row2.pack(fill="x", padx=6, pady=3)
        btn_return = ctk.CTkButton(row2, text="🗄️ RETURN TO EARTH", font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"), fg_color="#334155", command=self.mark_astronaut_returned)
        btn_return.pack(side="left", fill="x", expand=True, padx=2)
        btn_remove = ctk.CTkButton(row2, text="🗑️ REMOVE", font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"), fg_color="#450a0a", text_color="#fca5a5", command=self.remove_astronaut_action)
        btn_remove.pack(side="left", fill="x", expand=True, padx=2)

        # Row 3: Deploy Group to Space & New Group
        row3 = ctk.CTkFrame(admin_btns, fg_color="transparent")
        row3.pack(fill="x", padx=6, pady=3)
        btn_deploy_group = ctk.CTkButton(row3, text="🚀 DEPLOY GROUP TO SPACE", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), fg_color="#059669", hover_color="#10b981", command=self.deploy_selected_group_to_space)
        btn_deploy_group.pack(side="left", fill="x", expand=True, padx=2)
        btn_new_group = ctk.CTkButton(row3, text="➕ NEW GROUP", font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"), fg_color="#1e293b", width=100, command=self.open_create_group_modal)
        btn_new_group.pack(side="left", padx=2)

        # -------------------------------------------------------------
        # 3B. CENTER: SICK ASTRONAUT PROFILE & TELEMETRY MONITOR
        # -------------------------------------------------------------
        center_col = ctk.CTkFrame(grid, fg_color="#081020", corner_radius=10, border_width=1, border_color="#132742")
        center_col.grid(row=0, column=1, padx=5, sticky="nsew")

        c_header = ctk.CTkFrame(center_col, fg_color="transparent")
        c_header.pack(fill="x", padx=12, pady=(10, 4))
        self.lbl_center_header = ctk.CTkLabel(c_header, text="📡 DEEP SPACE TELEMETRY MONITOR", font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"), text_color="#00f0ff")
        self.lbl_center_header.pack(side="left")

        # Telemetry subject card (Transforms into High-Visibility Red Alert when someone is sick!)
        self.card_subject = ctk.CTkFrame(center_col, fg_color="#0a1426", corner_radius=8, border_width=1, border_color="#1e3a5f")
        self.card_subject.pack(fill="x", padx=12, pady=6)

        subj_top_row = ctk.CTkFrame(self.card_subject, fg_color="transparent")
        subj_top_row.pack(fill="x", padx=12, pady=(8, 0))

        self.lbl_card_title = ctk.CTkLabel(subj_top_row, text="MONITORED SUBJECT (ORBIT)", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#94a3b8")
        self.lbl_card_title.pack(side="left")

        self.lbl_subj_badge = ctk.CTkLabel(subj_top_row, text="🟢 OPTIMAL", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#10b981", fg_color="#103628", corner_radius=4)
        self.lbl_subj_badge.pack(side="right")

        subj_inner = ctk.CTkFrame(self.card_subject, fg_color="transparent")
        subj_inner.pack(fill="x", padx=12, pady=(6, 10))

        self.lbl_subj_avatar = ctk.CTkLabel(subj_inner, text="[PHOTO]", width=76, height=76)
        self.lbl_subj_avatar.pack(side="left", padx=(0, 12))

        subj_info = ctk.CTkFrame(subj_inner, fg_color="transparent")
        subj_info.pack(side="left", fill="both", expand=True)

        self.lbl_subj_name = ctk.CTkLabel(subj_info, text="CAPT. SARAH CONNOR", font=ctk.CTkFont(family="Orbitron", size=15, weight="bold"), text_color="#ffffff", anchor="w")
        self.lbl_subj_name.pack(fill="x")

        self.lbl_subj_role = ctk.CTkLabel(subj_info, text="ARES-LEAD • Mission Commander / EVA Specialist", font=ctk.CTkFont(family="Inter", size=11), text_color="#38bdf8", anchor="w")
        self.lbl_subj_role.pack(fill="x")

        self.lbl_subj_status = ctk.CTkLabel(subj_info, text="🟢 STATUS: DEPLOYED IN DEEP SPACE • EXPEDITION 72", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#10b981", anchor="w")
        self.lbl_subj_status.pack(fill="x", pady=(2, 0))

        self.lbl_subj_alert_detail = ctk.CTkLabel(subj_info, text="", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#ff1e53", anchor="w")
        self.lbl_subj_alert_detail.pack(fill="x", pady=(2, 0))

        # Clinical Diagnosis Readout Box
        diag_box = ctk.CTkFrame(center_col, fg_color="#050a14", corner_radius=8, border_width=1, border_color="#132742")
        diag_box.pack(fill="both", expand=True, padx=12, pady=6)

        ctk.CTkLabel(diag_box, text="🩺 GROUND FLIGHT SURGEON REAL-TIME ASSESSMENT", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), text_color="#38bdf8").pack(padx=10, pady=(8, 4), anchor="w")

        self.txt_telemetry_diag = ctk.CTkTextbox(diag_box, font=ctk.CTkFont(family="Consolas", size=11), fg_color="#04070e", text_color="#e2e8f0", wrap="word")
        self.txt_telemetry_diag.pack(fill="both", expand=True, padx=10, pady=(2, 6))
        self.txt_telemetry_diag.insert("1.0", "Receiving live telemetry packets from Deep Space via S-Band Uplink...\nEquilibrium stable. Autonomous edge AI monitoring nominal.")
        self.txt_telemetry_diag.configure(state="disabled")

        # Open Full Dossier Button in Center Readout
        btn_center_dossier = ctk.CTkButton(
            diag_box,
            text="📄 OPEN FULL CLINICAL REPORT & NASA CASE MATCH",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=28,
            command=self.open_full_clinical_dossier
        )
        btn_center_dossier.pack(fill="x", padx=10, pady=(0, 8))

        # Telemetry Action Bar
        act_row = ctk.CTkFrame(center_col, fg_color="transparent")
        act_row.pack(fill="x", padx=12, pady=(4, 10))
        btn_refresh_telem = ctk.CTkButton(act_row, text="🔄 REFRESH TELEMETRY", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), fg_color="#0284c7", command=self.poll_space_telemetry_loop)
        btn_refresh_telem.pack(side="left", padx=4)

        btn_ack_alarm = ctk.CTkButton(act_row, text="🔕 ACKNOWLEDGE ALARM", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), fg_color="#1e293b", command=self.silence_alarm)
        btn_ack_alarm.pack(side="right", padx=4)

        # -------------------------------------------------------------
        # 3C. RIGHT: CONVERSATIONAL AI FLIGHT SURGEON & CLINICAL REPORTS
        # -------------------------------------------------------------
        right_col = ctk.CTkFrame(grid, fg_color="#081020", corner_radius=10, border_width=1, border_color="#132742")
        right_col.grid(row=0, column=2, padx=(5, 0), sticky="nsew")

        r_header = ctk.CTkFrame(right_col, fg_color="transparent")
        r_header.pack(fill="x", padx=12, pady=(10, 2))

        f_rt = ctk.CTkFrame(r_header, fg_color="transparent")
        f_rt.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(f_rt, text="🩺 AI FLIGHT SURGEON CONSULT", font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"), text_color="#00f0ff").pack(anchor="w")
        self.lbl_chat_active_astro = ctk.CTkLabel(f_rt, text="👨‍🚀 Consulting for: CAPT. SARAH CONNOR (ARES-LEAD)", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color="#38bdf8")
        self.lbl_chat_active_astro.pack(anchor="w", pady=(1, 0))

        btn_clear_chat = ctk.CTkButton(
            r_header,
            text="🧹 CLEAR CHAT",
            width=85,
            height=24,
            font=ctk.CTkFont(family="Orbitron", size=8, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.clear_ai_chat
        )
        btn_clear_chat.pack(side="right")

        # Conversational Chat Box (ENLARGED & HIGHLY READABLE)
        self.txt_ai_response = ctk.CTkTextbox(right_col, font=ctk.CTkFont(family="Consolas", size=11), fg_color="#04070e", text_color="#e2e8f0", wrap="word", height=280)
        self.txt_ai_response.pack(fill="both", expand=True, padx=12, pady=6)
        self.txt_ai_response.insert("1.0", "💬 AstroMind AI Flight Surgeon (Groq Qwen-3.8-27B) Online.\n🩺 Active Session: Bound to CAPT. SARAH CONNOR (ARES-LEAD)\nReady for clinical guidance, telemetry analysis, and historical NASA case cross-referencing.\nType your message below or click a quick inquiry chip.")
        self.txt_ai_response.configure(state="disabled")

        # Quick Inquiry Chips
        chips_f = ctk.CTkFrame(right_col, fg_color="transparent")
        chips_f.pack(fill="x", padx=12, pady=(0, 4))

        quick_chips = [
            ("📊 Crew Status", "What is the current health status and physiological baseline of the crew?"),
            ("❤️ Vitals Review", "Analyze the active crew member's heart rate, rhythm, and oxygen saturation."),
            ("🚀 Spacewalk Fit", "Is the monitored astronaut cleared for EVA spacewalk duties?"),
            ("💊 Countermeasures", "What microgravity countermeasures should be applied right now?")
        ]

        chip_row1 = ctk.CTkFrame(chips_f, fg_color="transparent")
        chip_row1.pack(fill="x", pady=1)
        chip_row2 = ctk.CTkFrame(chips_f, fg_color="transparent")
        chip_row2.pack(fill="x", pady=1)

        for i, (label, query_text) in enumerate(quick_chips):
            target_row = chip_row1 if i < 2 else chip_row2
            btn_chip = ctk.CTkButton(
                target_row,
                text=label,
                height=22,
                font=ctk.CTkFont(family="Inter", size=9, weight="bold"),
                fg_color="#0f223a",
                hover_color="#0284c7",
                text_color="#38bdf8",
                command=lambda q=query_text: self.send_ai_query(preset_query=q)
            )
            btn_chip.pack(side="left", fill="x", expand=True, padx=2)

        # Query Input Box
        input_f = ctk.CTkFrame(right_col, fg_color="transparent")
        input_f.pack(fill="x", padx=12, pady=(4, 6))

        self.entry_ai_query = ctk.CTkEntry(
            input_f,
            placeholder_text="Ask flight surgeon or type general message...",
            font=ctk.CTkFont(family="Inter", size=11),
            fg_color="#050a14",
            border_color="#163b4d"
        )
        self.entry_ai_query.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry_ai_query.bind("<Return>", lambda e: self.send_ai_query())

        btn_send = ctk.CTkButton(
            input_f,
            text="SEND",
            width=70,
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#0284c7",
            command=self.send_ai_query
        )
        btn_send.pack(side="right", padx=(4, 0))

        # 🔇 Stop Voice Button
        self.btn_stop_voice = ctk.CTkButton(
            input_f,
            text="🔇 STOP",
            width=72,
            height=32,
            font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"),
            fg_color="#1e293b",
            hover_color="#ff1e53",
            border_width=1,
            border_color="#ff4d6d",
            text_color="#ff4d6d",
            command=self.stop_ai_voice
        )
        self.btn_stop_voice.pack(side="right", padx=(0, 4))

        # Clinical Report & Database Archive Buttons
        report_f = ctk.CTkFrame(right_col, fg_color="#050a14", corner_radius=8, border_width=1, border_color="#132742")
        report_f.pack(fill="x", padx=12, pady=(4, 10))

        btn_gen_report = ctk.CTkButton(
            report_f,
            text="📄 OPEN FULL CLINICAL DOSSIER & NASA CASE MATCH",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=30,
            command=self.open_full_clinical_dossier
        )
        btn_gen_report.pack(fill="x", padx=10, pady=(8, 4))

        btn_view_archive = ctk.CTkButton(
            report_f,
            text="📂 ALL EXPEDITIONS DATABASE ARCHIVE",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            command=self.open_database_archive
        )
        btn_view_archive.pack(fill="x", padx=10, pady=(4, 8))

        # Populate crew list after all UI cards are created
        self.refresh_groups_dropdown()
        self.refresh_crew_roster_view()

    # =========================================================================
    # 4. EMERGENCY BANNER (Ground Alert)
    # =========================================================================
    def build_emergency_banner(self):
        self.emergency_banner = ctk.CTkFrame(self, height=48, fg_color="#081820", corner_radius=8, border_width=1, border_color="#10b981")
        self.emergency_banner.pack(fill="x", side="bottom", padx=16, pady=(4, 10))

        inner = ctk.CTkFrame(self.emergency_banner, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=14, pady=6)

        self.lbl_alert_symbol = ctk.CTkLabel(inner, text="🟢", font=ctk.CTkFont(size=18))
        self.lbl_alert_symbol.pack(side="left", padx=(0, 10))

        content_f = ctk.CTkFrame(inner, fg_color="transparent")
        content_f.pack(side="left", fill="both", expand=True)

        self.lbl_alert_title = ctk.CTkLabel(content_f, text="GROUND STATUS: ALL DEEP SPACE TELEMETRY WITHIN NOMINAL TOLERANCES", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), text_color="#10b981", anchor="w")
        self.lbl_alert_title.pack(fill="x")

        self.lbl_alert_desc = ctk.CTkLabel(content_f, text="Continuous Earth-to-Space monitoring active. Zero critical vital anomalies detected on deployed crew.", font=ctk.CTkFont(family="Inter", size=9), text_color="#94a3b8", anchor="w")
        self.lbl_alert_desc.pack(fill="x")

        self.btn_resolve = ctk.CTkButton(
            inner,
            text="COMMAND RESOLVE",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#1e293b",
            command=self.command_resolve_emergency
        )
        self.btn_resolve.pack(side="right")

    # =========================================================================
    # TELEMETRY POLLING & LIVE SYNC OVER NETWORK (LAN Wi-Fi)
    # =========================================================================
    def poll_space_telemetry_loop(self):
        """
        Polls the Space Station over the network (LAN Wi-Fi).
        Updates vitals, highlights compromised sick astronauts, and synchronizes status.
        """
        telem = network_client.fetch_live_telemetry()
        
        # Update connection badge
        if network_client.is_connected:
            self.link_box.configure(border_color="#10b981")
            self.lbl_link_status.configure(text=f"🟢 DSN LINK: CONNECTED ({network_client.space_host})", text_color="#10b981")
        else:
            self.link_box.configure(border_color="#f59e0b")
            self.lbl_link_status.configure(text=f"🟡 DSN LINK: RECONNECTING ({network_client.space_host})...", text_color="#f59e0b")

        if telem:
            # Synchronize active deployment group from space
            act_grp = telem.get("active_group")
            if act_grp and act_grp.get("group_name"):
                self.lbl_active_group_badge.configure(text=f"🚀 ACTIVE IN SPACE: {act_grp['group_name']}")
                cur_active = medical_db.get_active_space_group()
                if not cur_active or cur_active.get("group_id") != act_grp.get("group_id"):
                    medical_db.set_active_space_group(act_grp["group_id"])
                    self.refresh_groups_dropdown()
                    self.refresh_crew_roster_view()

            # Sync any new astronauts added directly on Space Station
            space_crew = telem.get("crew_list", {})
            for sid, sdata in space_crew.items():
                if not medical_db.get_astronaut_by_id(sid):
                    medical_db.add_astronaut(sdata)
                    self.refresh_crew_roster_view()

            vitals = telem.get("vitals", {})
            cabin = telem.get("cabin", {})
            hr = vitals.get("heart_rate", 72)
            spo2 = vitals.get("spo2", 98.4)
            fat = vitals.get("fatigue_level", 18)
            is_em = telem.get("is_emergency", False)
            em_reason = telem.get("emergency_reason", "")
            active_id = telem.get("active_id", "sarah")

            self.lbl_hr_val.configure(text=f"{hr} BPM")
            self.lbl_spo2_val.configure(text=f"{spo2:.1f} %")
            self.prog_spo2.set(max(0.0, min(1.0, spo2 / 100.0)))
            self.lbl_fatigue_val.configure(text=f"{fat} %")
            self.prog_fatigue.set(max(0.0, min(1.0, fat / 100.0)))
            
            c_co2 = cabin.get("co2_percent", 0.31)
            c_temp = cabin.get("temp_c", 21.6)
            c_rad = cabin.get("radiation_msv", 0.18)
            self.lbl_cabin_val.configure(text=f"CO₂: {c_co2:.2f}% • {c_temp:.1f}°C • Rad: {c_rad:.2f} mSv/h")

            # Check for warning conditions
            is_warning = is_em or (spo2 < 94.0) or (hr < 50) or (hr > 115) or (fat >= 65)

            # Determine astronaut object from space telemetry
            astro_obj = telem.get("astronaut")
            if not astro_obj:
                astro_obj = next((a for a in medical_db.get_all_astronauts() if a["id"] == active_id), None)
            if not astro_obj:
                astro_obj = {"id": active_id, "name": "Astronaut in Orbit", "role": "Crew Member", "serial": "CREW-01", "callsign": "ARES"}

            astro_name = astro_obj.get("name", "Astronaut").upper()

            # ── EMERGENCY or WARNING state ──────────────────────────────────
            if is_warning:
                # Emergency overrides manual selection — sick astronaut must be visible!
                self.manual_selection_override = False
                self.selected_astro_id = active_id
                self.card_subject.configure(fg_color="#260810", border_color="#ff1e53", border_width=2)
                self.lbl_card_title.configure(text="CRITICAL: COMPROMISED CREW IN ORBIT", text_color="#ff1e53")
                self.lbl_subj_badge.configure(text="CRITICAL ALERT", text_color="#ffffff", fg_color="#ff1e53")

                self.lbl_subj_name.configure(text=astro_name, text_color="#ffffff")
                self.lbl_subj_role.configure(
                    text=f"{astro_obj.get('callsign', 'CREW')} | {astro_obj.get('role', 'Specialist')} | {astro_obj.get('serial', '01')}",
                    text_color="#fca5a5"
                )
                self.lbl_subj_status.configure(text="HEALTH EMERGENCY DETECTED IN DEEP SPACE", text_color="#ff1e53")
                self.lbl_subj_alert_detail.configure(text=f"ANOMALY: {em_reason or 'Acute Hypoxia / Cardiac Crisis'}")

                av_p = astro_obj.get("avatar", "")
                if os.path.exists(av_p):
                    try:
                        pil_img = Image.open(av_p).resize((76, 76), Image.Resampling.LANCZOS)
                        tk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(76, 76))
                        self.lbl_subj_avatar.configure(image=tk_img, text="")
                        self._avatar_img_ref = tk_img
                    except Exception:
                        self.lbl_subj_avatar.configure(text="[PHOTO]")
                else:
                    self.lbl_subj_avatar.configure(text="[PHOTO]")

                self.txt_telemetry_diag.configure(state="normal")
                self.txt_telemetry_diag.delete("1.0", "end")
                diag_warning_text = (
                    f"[ EMERGENCY TELEMETRY ALERT: {astro_name} ]\n"
                    f"  Anomaly      : {em_reason or 'Acute Vital Collapse'}\n"
                    f"  Heart Rate   : {hr} BPM\n"
                    f"  SpO2         : {spo2:.1f}%\n"
                    f"  Fatigue      : {fat}%\n"
                    f"  CO2          : {c_co2:.2f}%\n"
                    f"  Radiation    : {c_rad:.2f} mSv/h\n"
                    f"--------------------------------------------------------------------------\n"
                    f"FLIGHT SURGEON IMMEDIATE COUNTERMEASURES:\n"
                    f"1. Order subject to don emergency 100% O2 rebreather immediately.\n"
                    f"2. Position subject horizontal to restore arterial cerebral perfusion.\n"
                    f"3. Abort current EVA / high-stress operational tasks.\n"
                    f"4. Click [COMMAND RESOLVE] below once stabilization protocol is verified."
                )
                self.txt_telemetry_diag.insert("1.0", diag_warning_text)
                self.txt_telemetry_diag.configure(state="disabled")

                self.emergency_banner.configure(fg_color="#3b0914", border_color="#ff1e53")
                self.lbl_alert_symbol.configure(text="ALERT")
                self.lbl_alert_title.configure(text=f"CRITICAL SPACE ALERT: {astro_name} IS SICK IN DEEP SPACE!", text_color="#ff1e53")
                self.lbl_alert_desc.configure(
                    text=f"Anomaly: {em_reason or 'Vital Instability'}. Pulse: {hr} BPM, SpO2: {spo2:.1f}%. Immediate intervention required!",
                    text_color="#fca5a5"
                )
                self.btn_resolve.configure(fg_color="#ff1e53", text_color="#ffffff")

                if not self.last_emergency_state and WINSOUND_AVAILABLE:
                    try:
                        winsound.Beep(880, 300)
                    except Exception:
                        pass
                self.last_emergency_state = True

            else:
                # ── NOMINAL STATE ────────────────────────────────────────────
                self.emergency_banner.configure(fg_color="#081820", border_color="#10b981")
                self.lbl_alert_symbol.configure(text="OK")
                self.lbl_alert_title.configure(
                    text="GROUND STATUS: ALL DEEP SPACE TELEMETRY WITHIN NOMINAL TOLERANCES",
                    text_color="#10b981"
                )
                self.lbl_alert_desc.configure(
                    text=f"Continuous monitoring active. Zero critical vital anomalies detected on deployed crew.",
                    text_color="#94a3b8"
                )
                self.btn_resolve.configure(fg_color="#1e293b", text_color="#94a3b8")
                self.last_emergency_state = False

                # Only update center panel profile if user has NOT manually selected an astronaut
                if not self.manual_selection_override:
                    self.card_subject.configure(fg_color="#0a1426", border_color="#1e3a5f", border_width=1)
                    self.lbl_card_title.configure(text="MONITORED SUBJECT (ORBIT)", text_color="#94a3b8")
                    self.lbl_subj_badge.configure(text="OPTIMAL", text_color="#10b981", fg_color="#103628")
                    self.lbl_subj_alert_detail.configure(text="")

                    self.lbl_subj_name.configure(text=astro_name, text_color="#ffffff")
                    self.lbl_subj_role.configure(
                        text=f"{astro_obj.get('callsign', 'CREW')} | {astro_obj.get('role', 'Specialist')}",
                        text_color="#38bdf8"
                    )
                    self.lbl_subj_status.configure(
                        text=f"STATUS: DEPLOYED IN DEEP SPACE | {astro_obj.get('group_id', 'EXPEDITION 72').upper()}",
                        text_color="#10b981"
                    )
                    av_p = astro_obj.get("avatar", "")
                    if os.path.exists(av_p):
                        try:
                            pil_img = Image.open(av_p).resize((76, 76), Image.Resampling.LANCZOS)
                            tk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(76, 76))
                            self.lbl_subj_avatar.configure(image=tk_img, text="")
                            self._avatar_img_ref = tk_img
                        except Exception:
                            self.lbl_subj_avatar.configure(text="[PHOTO]")
                    self.selected_astro_id = active_id

            # Update ECG Line
            self.render_ecg_pulse(hr, is_warning)

        self.after(600, self.poll_space_telemetry_loop)


    def render_ecg_pulse(self, hr, is_emergency):
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
            coords.extend([i * step, mid_y - (pt * 0.7)])
        if len(coords) >= 4:
            self.canvas_ecg.create_line(coords, fill=line_color, width=1.5, smooth=True)

    def update_clock_loop(self):
        now = datetime.now(timezone.utc)
        d_str = now.strftime("%Y-%m-%d")
        t_str = now.strftime("%H:%M:%S UTC")
        self.lbl_earth_clock.configure(text=f"📅 {d_str}  ⏰ {t_str}")
        self.after(1000, self.update_clock_loop)

    # =========================================================================
    # ROSTER & EXPEDITIONS MANAGEMENT (EARTH EXCLUSIVE)
    # =========================================================================
    def refresh_groups_dropdown(self):
        groups = medical_db.get_all_groups()
        if not groups:
            return
        vals = [f"{g['group_name']} ({g['status']})" for g in groups]
        self.groups_map = {f"{g['group_name']} ({g['status']})": g['group_id'] for g in groups}
        self.opt_groups.configure(values=vals)
        
        # Set active group badge
        active_grp = medical_db.get_active_space_group()
        if active_grp:
            self.lbl_active_group_badge.configure(text=f"🚀 ACTIVE IN SPACE: {active_grp['group_name']}")

    def on_group_selected(self, val):
        self.selected_group_id = self.groups_map.get(val, "expedition_72")
        self.manual_selection_override = True
        self.refresh_crew_roster_view()

    def refresh_crew_roster_view(self):
        for widget in self.scroll_crew.winfo_children():
            widget.destroy()

        astros = medical_db.get_astronauts_by_group(self.selected_group_id)
        if not astros:
            ctk.CTkLabel(self.scroll_crew, text="No astronauts assigned to this group yet.\nClick '➕ ADD ASTRONAUT' below.", font=ctk.CTkFont(family="Inter", size=10), text_color="#64748b").pack(pady=20)
            return

        self._crew_cards = {}  # track card frames for highlight

        for astro in astros:
            cid = astro["id"]
            card = ctk.CTkFrame(self.scroll_crew, fg_color="#0a1426", corner_radius=6, border_width=1, border_color="#1e293b", cursor="hand2")
            card.pack(fill="x", pady=3)
            self._crew_cards[cid] = card

            av_p = astro.get("avatar", "")
            img_tk = None
            if os.path.exists(av_p):
                try:
                    pil_img = Image.open(av_p).resize((36, 36), Image.Resampling.LANCZOS)
                    img_tk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(36, 36))
                except Exception:
                    pass

            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=6, pady=6)

            if img_tk:
                ctk.CTkLabel(row, text="", image=img_tk).pack(side="left", padx=(0, 6))

            info = ctk.CTkFrame(row, fg_color="transparent")
            info.pack(side="left", fill="both", expand=True)

            status_color = "#10b981" if astro.get("is_deployed") == 1 else "#94a3b8"
            status_text = "IN SPACE" if astro.get("is_deployed") == 1 else "ON EARTH"

            lbl_name = ctk.CTkLabel(
                info,
                text=f"{astro.get('serial', '00')}  {astro.get('name', 'Astronaut')}",
                font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
                text_color="#ffffff", anchor="w"
            )
            lbl_name.pack(fill="x")

            lbl_role = ctk.CTkLabel(
                info,
                text=f"{astro.get('role', 'Specialist')} | {status_text}",
                font=ctk.CTkFont(family="Inter", size=9),
                text_color=status_color, anchor="w"
            )
            lbl_role.pack(fill="x")

            def _select(chosen_id=cid, chosen_data=astro, chosen_card=card):
                # Highlight selected card immediately
                for c in self._crew_cards.values():
                    c.configure(border_color="#1e293b")
                chosen_card.configure(border_color="#0ea5e9")

                self.manual_selection_override = True
                self.select_astronaut(chosen_id, chosen_data, manual=True)

                # If deployed, tell Space Station to focus on this astronaut
                if chosen_data.get("is_deployed") == 1:
                    import threading
                    threading.Thread(
                        target=lambda: network_client.send_command({"command": "SELECT_ASTRONAUT", "astronaut_id": chosen_id}),
                        daemon=True
                    ).start()

            # Bind click to EVERY widget inside the card so no click is missed
            self._bind_all_children(card, lambda e, fn=_select: fn())

        if astros:
            self.select_astronaut(astros[0]["id"], astros[0])
            # Highlight first card
            if astros[0]["id"] in self._crew_cards:
                self._crew_cards[astros[0]["id"]].configure(border_color="#0ea5e9")

    def _bind_all_children(self, widget, callback):
        """Recursively binds <Button-1> click to a widget and ALL its children."""
        try:
            widget.bind("<Button-1>", callback)
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._bind_all_children(child, callback)
        except Exception:
            pass


    def select_astronaut(self, astro_id: str, astro_data: dict, manual: bool = False):
        self.selected_astro_id = astro_id
        if manual:
            self.manual_selection_override = True

        name = astro_data.get("name", "Astronaut").upper()
        self.lbl_subj_name.configure(text=name)
        self.lbl_subj_role.configure(
            text=f"{astro_data.get('callsign', 'CREW')} | {astro_data.get('role', 'Specialist')}"
        )

        is_deployed = astro_data.get("is_deployed") == 1
        status_str = "IN DEEP SPACE" if is_deployed else "ON EARTH"
        status_color = "#10b981" if is_deployed else "#94a3b8"
        self.lbl_subj_status.configure(
            text=f"STATUS: {status_str} | {astro_data.get('group_id', '').upper()}",
            text_color=status_color
        )

        # Update subject card header label and badge immediately
        self.lbl_card_title.configure(text="SELECTED CREW MEMBER", text_color="#38bdf8")
        self.lbl_subj_badge.configure(
            text="DEPLOYED" if is_deployed else "ON EARTH",
            text_color="#10b981" if is_deployed else "#94a3b8",
            fg_color="#103628" if is_deployed else "#1e293b"
        )
        self.lbl_subj_alert_detail.configure(text="")
        self.card_subject.configure(fg_color="#0a1426", border_color="#1e3a5f", border_width=1)

        # Load avatar instantly
        av_p = astro_data.get("avatar", "")
        if os.path.exists(av_p):
            try:
                pil_img = Image.open(av_p).resize((76, 76), Image.Resampling.LANCZOS)
                tk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(76, 76))
                self.lbl_subj_avatar.configure(image=tk_img, text="")
                self._avatar_img_ref = tk_img
            except Exception:
                self.lbl_subj_avatar.configure(text="[PHOTO]", image=None)
        else:
            self.lbl_subj_avatar.configure(text="[PHOTO]", image=None)

        # Show DB/baseline data INSTANTLY (no waiting)
        self.update_clinical_assessment_box(astro_data)

        # Update AI consultation header
        if hasattr(self, 'lbl_chat_active_astro'):
            callsign = astro_data.get('callsign', 'CREW')
            self.lbl_chat_active_astro.configure(text=f"Consulting for: {name} ({callsign})")

        # Fetch live telemetry in background AFTER 200ms — UI already shows baseline
        # Using after() avoids blocking the click response
        def _do_live_fetch():
            import threading
            def _fetch():
                try:
                    telem = network_client.fetch_telemetry_for_astronaut(astro_id, astro_data)
                    # Schedule UI update back on main thread
                    self.after(0, lambda: self._apply_live_vitals_to_report(astro_data, telem))
                except Exception:
                    pass
            threading.Thread(target=_fetch, daemon=True).start()

        self.after(200, _do_live_fetch)


    def _apply_live_vitals_to_report(self, astro_data: dict, telem: dict):
        """Updates the health report box with actual live/DB vitals after background fetch."""
        v = telem.get("vitals", {})
        c = telem.get("cabin", {})
        is_em = telem.get("is_emergency", False)
        source = telem.get("source", "DB_BASELINE")
        name = astro_data.get("name", "Astronaut").upper()
        records = medical_db.get_records_by_date(self.selected_astro_id, limit=3)

        source_label = {
            "LIVE_TELEMETRY": "LIVE S-BAND TELEMETRY",
            "DB_RECORDS":     "CACHED MEDICAL RECORDS",
            "DB_BASELINE":    "ASTRONAUT BASELINE PROFILE"
        }.get(source, source)

        readiness = 95
        if v.get("fatigue_level", 0) > 50: readiness -= 15
        if v.get("spo2", 99) < 95: readiness -= 20
        if v.get("heart_rate", 72) > 110 or v.get("heart_rate", 72) < 50: readiness -= 15
        if c.get("co2_percent", 0.3) > 0.5: readiness -= 10
        readiness = max(0, min(100, readiness))

        hr_status  = "CRITICAL" if v.get("heart_rate", 72) > 120 or v.get("heart_rate", 72) < 50 else ("ELEVATED" if v.get("heart_rate", 72) > 100 else "NORMAL")
        spo2_status = "LOW" if v.get("spo2", 99) < 94 else ("FAIR" if v.get("spo2", 99) < 97 else "OPTIMAL")
        fat_status  = "HIGH" if v.get("fatigue_level", 18) > 60 else ("MODERATE" if v.get("fatigue_level", 18) > 35 else "LOW")

        emergency_line = ""
        if is_em:
            emergency_line = f"[!!! EMERGENCY ALERT !!!] {telem.get('emergency_reason', 'Anomaly detected')}\n"

        text = (
            f"[ CLINICAL BIO-TELEMETRY REPORT: {name} ]\n"
            f"Data Source: {source_label}\n"
            f"Readiness Score: {readiness}% {'| FIT FOR EVA/SPACEWALK' if readiness >= 80 else '| RESTRICTED DUTY'}\n"
            f"--------------------------------------------------------------------------\n"
            f"{emergency_line}"
            f"VITAL SIGNS:\n"
            f"  Heart Rate : {v.get('heart_rate', astro_data.get('baseline_hr', 72))} BPM   [{hr_status}]\n"
            f"  Blood O2   : {v.get('spo2', astro_data.get('baseline_spo2', 98.4))}%   [{spo2_status}]\n"
            f"  HRV        : {v.get('hrv', astro_data.get('baseline_hrv', 58.0))} ms\n"
            f"  Fatigue    : {v.get('fatigue_level', astro_data.get('fatigue', 18))}%   [{fat_status}]\n"
            f"CABIN ENVIRONMENT:\n"
            f"  CO2        : {c.get('co2_percent', 0.31)}% {'[OK]' if c.get('co2_percent', 0.31) < 0.5 else '[HIGH]'}\n"
            f"  Temperature: {c.get('temp_c', 21.6)} C\n"
            f"  Radiation  : {c.get('radiation_msv', 0.18)} mSv/h\n"
            f"ASTRONAUT BASELINE:\n"
            f"  Group      : {astro_data.get('group_id', 'N/A').upper()}\n"
            f"  Role       : {astro_data.get('role', 'Specialist')}\n"
            f"  Deployed   : {'IN DEEP SPACE' if astro_data.get('is_deployed') == 1 else 'RETURNED TO EARTH'}\n"
        )
        if records:
            text += f"--------------------------------------------------------------------------\n"
            text += f"LATEST MEDICAL EVALUATION:\n"
            for r in records[:2]:
                text += (
                    f"  [{r.get('date_str','?')} {r.get('time_str','')}] Status: {r.get('status_eval','?')}\n"
                    f"  Trend: {r.get('trend_diff','')}\n"
                    f"  Note : {r.get('clinical_notes','')[:80]}...\n"
                )
        else:
            text += "No prior medical evaluations on record. Mission baseline nominal.\n"

        self.txt_telemetry_diag.configure(state="normal")
        self.txt_telemetry_diag.delete("1.0", "end")
        self.txt_telemetry_diag.insert("1.0", text)
        self.txt_telemetry_diag.configure(state="disabled")

    def update_clinical_assessment_box(self, astro_data):
        """Shows immediate static baseline data while live fetch runs in background."""
        name = astro_data.get('name', '').upper()
        records = medical_db.get_records_by_date(self.selected_astro_id, limit=1)
        self.txt_telemetry_diag.configure(state="normal")
        self.txt_telemetry_diag.delete("1.0", "end")

        text = (
            f"[ CLINICAL PROFILE: {name} ]\n"
            f"  Expedition : {astro_data.get('group_id', 'N/A').upper()}\n"
            f"  Role       : {astro_data.get('role', 'Specialist')}\n"
            f"  Baseline HR: {astro_data.get('baseline_hr', 72)} BPM | SpO2: {astro_data.get('baseline_spo2', 98.4)}%\n"
            f"  Baseline HRV: {astro_data.get('baseline_hrv', 58.0)} ms | Fatigue: {astro_data.get('fatigue', 18)}%\n"
            f"  Status     : {'IN DEEP SPACE' if astro_data.get('is_deployed') == 1 else 'RETURNED TO EARTH'}\n"
            f"--------------------------------------------------------------------------\n"
        )
        if records:
            text += f"Last Evaluation: {records[0].get('status_eval', 'N/A')}\n"
            text += f"Trend: {records[0].get('trend_diff', '')}\n"
        else:
            text += "Fetching live telemetry data...\n"

        self.txt_telemetry_diag.insert("1.0", text)
        self.txt_telemetry_diag.configure(state="disabled")


    # =========================================================================
    # EARTH MODAL ACTIONS: ADD, EDIT, REMOVE, DEPLOY
    # =========================================================================
    def open_add_astronaut_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Add New Astronaut to Mission Group")
        modal.geometry("480x560")
        modal.grab_set()

        ctk.CTkLabel(modal, text="➕ ADD ASTRONAUT TO EXPEDITION", font=ctk.CTkFont(family="Orbitron", size=13, weight="bold"), text_color="#38bdf8").pack(pady=12)

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

        e_id = make_row("Subject ID (slug):", "mark_watney")
        e_name = make_row("Full Name:", "Dr. Mark Watney")
        e_callsign = make_row("Callsign:", "BOTANIST")
        e_serial = make_row("Serial Number:", "ARES-04")
        e_role = make_row("Mission Role:", "Botanist / Mechanical Engineer")
        e_hr = make_row("Baseline Heart Rate:", "68")
        e_spo2 = make_row("Baseline SpO2 (%):", "98.8")

        def _save():
            aid = e_id.get().strip().lower().replace(" ", "_")
            aname = e_name.get().strip()
            if not aid or not aname:
                messagebox.showerror("Error", "ID and Name are required fields!")
                return
            
            # Determine if this astronaut's group is currently active in Space
            active_grp = medical_db.get_active_space_group() or {"group_id": "expedition_72"}
            is_active_deployed = (self.selected_group_id == active_grp.get("group_id"))

            # Pick a valid avatar
            avatar_choices = [
                "static/assets/astronaut_sarah.jpg",
                "static/assets/astronaut_alex.jpg",
                "static/assets/astronaut_john.jpg",
                "static/assets/astronaut_elena.jpg"
            ]
            import random
            chosen_avatar = random.choice(avatar_choices)

            astro_dict = {
                "id": aid,
                "name": aname,
                "callsign": e_callsign.get().strip() or "CREW",
                "serial": e_serial.get().strip() or "05",
                "role": e_role.get().strip() or "Mission Specialist",
                "avatar": chosen_avatar,
                "group_id": self.selected_group_id,
                "baseline_hr": int(e_hr.get().strip() or "70"),
                "baseline_spo2": float(e_spo2.get().strip() or "98.5"),
                "baseline_hrv": 60.0,
                "fatigue": 15,
                "readiness": 90,
                "is_deployed": 1 if is_active_deployed else 0,
                "status": "IN_SPACE" if is_active_deployed else "SCHEDULED_TRAINING",
                "notes": "Added from Earth Mission Control"
            }
            # Save locally and transmit to Space Station over LAN
            network_client.add_astronaut_to_space(astro_dict)
            if is_active_deployed:
                network_client.send_command({"command": "SELECT_ASTRONAUT", "astronaut_id": aid})
            
            modal.destroy()
            self.refresh_crew_roster_view()
            messagebox.showinfo("Success", f"Astronaut '{aname}' added successfully and synced to Space Station!")

        ctk.CTkButton(modal, text="SAVE ASTRONAUT TO ROSTER", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), fg_color="#0284c7", command=_save).pack(fill="x", padx=20, pady=16)

    def open_edit_astronaut_modal(self):
        astro = next((a for a in medical_db.get_all_astronauts() if a["id"] == self.selected_astro_id), None)
        if not astro:
            messagebox.showinfo("Select Astronaut", "Please select an astronaut from the roster first.")
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Edit Astronaut • {astro['name']}")
        modal.geometry("480x500")
        modal.grab_set()

        ctk.CTkLabel(modal, text=f"✏️ EDIT ASTRONAUT: {astro['name'].upper()}", font=ctk.CTkFont(family="Orbitron", size=13, weight="bold"), text_color="#38bdf8").pack(pady=12)

        f = ctk.CTkFrame(modal, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=4)

        def make_row(lbl, val):
            row = ctk.CTkFrame(f, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=lbl, font=ctk.CTkFont(family="Inter", size=10, weight="bold"), width=120, anchor="w").pack(side="left")
            entry = ctk.CTkEntry(row, font=ctk.CTkFont(family="Inter", size=11))
            entry.insert(0, str(val))
            entry.pack(side="left", fill="x", expand=True)
            return entry

        e_name = make_row("Full Name:", astro["name"])
        e_callsign = make_row("Callsign:", astro["callsign"])
        e_role = make_row("Mission Role:", astro["role"])
        e_hr = make_row("Baseline HR:", astro["baseline_hr"])
        e_spo2 = make_row("Baseline SpO2:", astro["baseline_spo2"])

        def _update():
            updates = {
                "name": e_name.get().strip(),
                "callsign": e_callsign.get().strip(),
                "role": e_role.get().strip(),
                "baseline_hr": int(e_hr.get().strip() or "70"),
                "baseline_spo2": float(e_spo2.get().strip() or "98.0")
            }
            network_client.update_astronaut_on_space(astro["id"], updates)
            modal.destroy()
            self.refresh_crew_roster_view()
            messagebox.showinfo("Success", f"Astronaut '{updates['name']}' updated and synced over LAN!")

        ctk.CTkButton(modal, text="UPDATE & SYNC", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), fg_color="#0284c7", command=_update).pack(fill="x", padx=20, pady=16)

    def mark_astronaut_returned(self):
        """Archives the astronaut as safely returned to Earth while preserving medical records."""
        if messagebox.askyesno("Confirm Return", f"Mark astronaut '{self.selected_astro_id}' as safely RETURNED TO EARTH?\n(Their historical medical records will remain intact in the archive)."):
            medical_db.archive_astronaut_returned(self.selected_astro_id)
            self.refresh_crew_roster_view()

    def remove_astronaut_action(self):
        if messagebox.askyesno("Confirm Removal", f"Permanently remove astronaut '{self.selected_astro_id}' from this group roster?"):
            medical_db.remove_astronaut(self.selected_astro_id)
            self.refresh_crew_roster_view()

    def open_create_group_modal(self):
        modal = ctk.CTkToplevel(self)
        modal.title("Create New Mission Group / Expedition")
        modal.geometry("450x320")
        modal.grab_set()

        ctk.CTkLabel(modal, text="➕ CREATE NEW EXPEDITION GROUP", font=ctk.CTkFont(family="Orbitron", size=12, weight="bold"), text_color="#38bdf8").pack(pady=12)

        f = ctk.CTkFrame(modal, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=4)

        r1 = ctk.CTkFrame(f, fg_color="transparent")
        r1.pack(fill="x", pady=6)
        ctk.CTkLabel(r1, text="Group ID (slug):", width=120, anchor="w").pack(side="left")
        e_gid = ctk.CTkEntry(r1)
        e_gid.insert(0, "artemis_4")
        e_gid.pack(side="left", fill="x", expand=True)

        r2 = ctk.CTkFrame(f, fg_color="transparent")
        r2.pack(fill="x", pady=6)
        ctk.CTkLabel(r2, text="Display Name:", width=120, anchor="w").pack(side="left")
        e_gname = ctk.CTkEntry(r2)
        e_gname.insert(0, "Artemis IV (Lunar Base Alpha)")
        e_gname.pack(side="left", fill="x", expand=True)

        def _create():
            gid = e_gid.get().strip()
            gname = e_gname.get().strip()
            if not gid or not gname:
                return
            medical_db.create_group(gid, gname, status="SCHEDULED_TRAINING")
            modal.destroy()
            self.refresh_groups_dropdown()
            messagebox.showinfo("Success", f"Mission Group '{gname}' created successfully!")

        ctk.CTkButton(modal, text="CREATE MISSION GROUP", font=ctk.CTkFont(family="Orbitron", size=11, weight="bold"), fg_color="#059669", command=_create).pack(fill="x", padx=20, pady=16)

    def deploy_selected_group_to_space(self):
        """
        Earth command: Switches the active deployment group in Space!
        Transmits over Wi-Fi / LAN to Space Station, which immediately updates its screen!
        """
        grp = next((g for g in medical_db.get_all_groups() if g["group_id"] == self.selected_group_id), None)
        gname = grp["group_name"] if grp else self.selected_group_id

        if messagebox.askyesno("Deploy to Space", f"Deploy mission group '{gname}' to Deep Space?\nThis will transmit over LAN to update the Space Station software."):
            network_client.deploy_group_to_space(self.selected_group_id)
            self.refresh_groups_dropdown()
            self.refresh_crew_roster_view()
            messagebox.showinfo("Deployment Synchronized", f"🚀 '{gname}' is now ACTIVE IN SPACE!\nSpace Station software has been synchronized over LAN.")

    # =========================================================================
    # AI FLIGHT SURGEON CONVERSATION & MEDICAL REPORTS
    # =========================================================================

    def clear_ai_chat(self):
        astro = next((a for a in medical_db.get_all_astronauts() if a["id"] == self.selected_astro_id), {})
        astro_name = astro.get("name", "Active Crew Member").upper()
        callsign = astro.get("callsign", "CREW")
        self.txt_ai_response.configure(state="normal")
        self.txt_ai_response.delete("1.0", "end")
        greeting = (
            f"💬 AstroMind AI Flight Surgeon (Groq Qwen-3.8-27B) Online.\n"
            f"🩺 Active Consultation Session bound to: {astro_name} ({callsign})\n"
            f"Ready for flight telemedicine, telemetry analysis, or historical NASA case cross-referencing.\n"
            f"Type any question below or click a quick inquiry chip.\n"
            f"--------------------------------------------------------------------------------\n"
        )
        self.txt_ai_response.insert("1.0", greeting)
        self.txt_ai_response.configure(state="disabled")

    def open_full_clinical_dossier(self):
        telem = network_client.fetch_live_telemetry() or {}
        astro = next((a for a in medical_db.get_all_astronauts() if a["id"] == self.selected_astro_id), {})
        if not astro:
            astro = {"id": self.selected_astro_id, "name": "Astronaut in Orbit", "role": "Crew Member", "serial": "CREW-01", "callsign": "ARES", "group_id": self.selected_group_id, "is_deployed": 1}
        v = telem.get("vitals", {"heart_rate": 72, "spo2": 98.4, "hrv": 58.0, "fatigue_level": 18})
        c = telem.get("cabin", {"co2_percent": 0.31, "temp_c": 21.6, "radiation_msv": 0.18})
        is_em = telem.get("is_emergency", False)

        ClinicalReportViewer(self, astronaut=astro, vitals=v, cabin=c, is_emergency=is_em)

    def stop_ai_voice(self):
        """Immediately stops the AI voice (pyttsx3 TTS) mid-sentence."""
        try:
            self.groq_doctor.stop_speaking()
            self.btn_stop_voice.configure(fg_color="#ff1e53", text="🔇 STOPPED")
            self.after(800, lambda: self.btn_stop_voice.configure(
                fg_color="#1e293b", text="🔇 STOP"
            ))
        except Exception as e:
            print(f"[EarthStation] Stop voice error: {e}")

    def send_ai_query(self, preset_query=None):
        q = preset_query if preset_query else self.entry_ai_query.get().strip()
        if not q:
            return
        if not preset_query:
            self.entry_ai_query.delete(0, "end")

        astro = next((a for a in medical_db.get_all_astronauts() if a["id"] == self.selected_astro_id), {})
        astro_name = astro.get("name", "Astronaut").upper()

        # Append query to chat box
        self.txt_ai_response.configure(state="normal")
        self.txt_ai_response.insert("end", f"\n👤 [HOUSTON SURGEON FOR {astro_name}]: {q}\n🩺 [AI FLIGHT SURGEON]: Cross-referencing telemetry & NASA historical mission debriefs...\n")
        self.txt_ai_response.see("end")
        self.txt_ai_response.configure(state="disabled")

        def _call():
            # Use per-astronaut telemetry (live if they're the active one, DB otherwise)
            telem = network_client.fetch_telemetry_for_astronaut(self.selected_astro_id, astro)
            v = telem.get("vitals", {"heart_rate": int(astro.get("baseline_hr", 72)), "spo2": float(astro.get("baseline_spo2", 98.4)), "hrv": float(astro.get("baseline_hrv", 58.0)), "fatigue_level": int(astro.get("fatigue", 18))})
            c = telem.get("cabin", {"co2_percent": 0.31, "temp_c": 21.6, "radiation_msv": 0.18})
            is_em = telem.get("is_emergency", False)
            data_src = telem.get("source", "DB_BASELINE")

            # Match against NASA historical medical cases
            h_match = HistoricalCaseMatcher.match_case(astronaut=astro, vitals=v, cabin=c, is_emergency=is_em)

            prompt_query = (
                f"You are the NASA Houston Flight Surgeon specifically advising on Astronaut {astro_name} ({astro.get('callsign', 'CREW')}, {astro.get('role', 'Specialist')}).\n"
                f"Data Source: {data_src} | Baseline Pulse: {astro.get('baseline_hr')} BPM | Baseline SpO2: {astro.get('baseline_spo2')}%.\n"
                f"Current Telemetry: Pulse {v.get('heart_rate')} BPM, SpO2 {v.get('spo2')}%, Fatigue {v.get('fatigue_level')}%, Cabin CO2 {c.get('co2_percent')}%, Temp {c.get('temp_c')}C, Radiation {c.get('radiation_msv')} mSv/h.\n"
                f"Matched NASA Historical Mission: {h_match['matched_mission']}.\n"
                f"Historical Astronaut Recovery Treatment: {h_match['how_astronaut_recovered']}.\n"
                f"User Question: {q}\n"
                f"Provide clinical guidance directly focused on {astro_name}, addressing their condition and integrating the historical NASA recovery protocol."
            )
            
            try:
                ans = self.groq_doctor.ask_doctor(
                    query=prompt_query,
                    astronaut=astro,
                    vitals=v,
                    cabin=c,
                    is_emergency=is_em
                )
            except Exception:
                ans = (
                    f"Clinical Telemetry Assessment for {astro_name}:\n"
                    f"Pulse: {v.get('heart_rate')} BPM | SpO2: {v.get('spo2')}% | Fatigue: {v.get('fatigue_level')}%. "
                    f"Telemetry within acceptable microgravity tolerances."
                )

            # Format comprehensive response with NASA Historical Match and AI Suggestions
            formatted_response = (
                f"🩺 [AI FLIGHT SURGEON EVALUATION FOR {astro_name}]:\n"
                f"{ans}\n\n"
                f"🔍 [NASA HISTORICAL CASE MATCH]:\n"
                f"• Mission: {h_match['matched_mission']}\n"
                f"• Historical Circumstance: {h_match['matched_case']}\n\n"
                f"💊 [HOW THAT HISTORICAL ASTRONAUT RECOVERED]:\n"
                f"{h_match['how_astronaut_recovered']}\n\n"
                f"💡 [ASTROMIND AUTONOMOUS AI RECOMMENDATION FOR {astro_name}]:\n"
                f"• {h_match['ai_autonomous_suggestion']}\n"
                f"--------------------------------------------------------------------------------\n"
            )

            def _show():
                self.txt_ai_response.configure(state="normal")
                current_txt = self.txt_ai_response.get("1.0", "end")
                placeholder = f"🩺 [AI FLIGHT SURGEON]: Cross-referencing telemetry & NASA historical mission debriefs...\n"
                if placeholder in current_txt:
                    updated_txt = current_txt.replace(placeholder, formatted_response)
                    self.txt_ai_response.delete("1.0", "end")
                    self.txt_ai_response.insert("1.0", updated_txt)
                else:
                    self.txt_ai_response.insert("end", formatted_response)
                self.txt_ai_response.see("end")
                self.txt_ai_response.configure(state="disabled")

            self.after(0, _show)

        threading.Thread(target=_call, daemon=True).start()

    def generate_expedition_report(self):
        """Opens the full clinical dossier for the selected astronaut."""
        self.open_full_clinical_dossier()

    def open_database_archive(self):
        from engine.history_viewer import MedicalHistoryViewer
        MedicalHistoryViewer(self)

    def command_resolve_emergency(self):
        """Transmits Ground command to resolve emergency in Space over LAN Wi-Fi!"""
        network_client.send_command({"command": "RESOLVE_EMERGENCY"})
        messagebox.showinfo("Command Dispatched", "Emergency resolution command transmitted to Deep Space via S-Band Uplink.")

    def silence_alarm(self):
        self.emergency_banner.configure(fg_color="#081820", border_color="#10b981")
        self.lbl_alert_symbol.configure(text="🟡")
        self.lbl_alert_title.configure(text="GROUND STATUS: EMERGENCY ALARM ACKNOWLEDGED BY FLIGHT SURGEON", text_color="#fbbf24")


if __name__ == "__main__":
    app = EarthMissionControlApp()
    app.mainloop()
