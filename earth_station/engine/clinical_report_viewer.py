"""
AstroMind: Comprehensive Clinical Evaluation Dossier & Historical Archive Viewer
Generates, displays, saves, and archives formal NASA Flight Medicine clinical dossiers.
Integrates:
1. Active Crew Biometric Telemetry & Baselines
2. Historical NASA Spaceflight Medical Case Matching
3. Step-by-Step Historical Astronaut Recovery Protocols
4. AstroMind Autonomous AI Clinical Guidance
5. Persistent SQLite database storage for longitudinal review
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
import customtkinter as ctk

from .medical_db import medical_db
from .historical_case_matcher import HistoricalCaseMatcher


class ClinicalReportViewer(ctk.CTkToplevel):
    def __init__(self, parent, astronaut: Dict[str, Any], vitals: Dict[str, Any], cabin: Dict[str, Any], is_emergency: bool = False):
        super().__init__(parent)
        self.astronaut = astronaut
        self.vitals = vitals
        self.cabin = cabin
        self.is_emergency = is_emergency

        self.title(f"📋 NASA Flight Medicine Dossier • {astronaut.get('name', 'Astronaut')}")
        self.geometry("1040x740")
        self.configure(fg_color="#060c18")

        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

        # Build UI layout
        self.build_ui()
        self.generate_and_display_report(auto_save=True)
        self.load_saved_dossiers_list()

    def build_ui(self):
        # 1. Header Banner
        header = ctk.CTkFrame(self, height=60, fg_color="#091426", corner_radius=0, border_width=1, border_color="#1e3a5f")
        header.pack(fill="x", side="top")

        h_inner = ctk.CTkFrame(header, fg_color="transparent")
        h_inner.pack(fill="both", expand=True, padx=16, pady=10)

        f_title = ctk.CTkFrame(h_inner, fg_color="transparent")
        f_title.pack(side="left")

        lbl_logo = ctk.CTkLabel(
            f_title,
            text="📋 NASA CLINICAL EVALUATION DOSSIER & HISTORICAL CASE ARCHIVE",
            font=ctk.CTkFont(family="Orbitron", size=14, weight="bold"),
            text_color="#38bdf8"
        )
        lbl_logo.pack(anchor="w")

        self.lbl_sub = ctk.CTkLabel(
            f_title,
            text=f"SUBJECT: {self.astronaut.get('name', '').upper()} ({self.astronaut.get('callsign', 'CREW')}) • EXPEDITION: {self.astronaut.get('group_id', 'EXPEDITION 72').upper()}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#94a3b8"
        )
        self.lbl_sub.pack(anchor="w", pady=(2, 0))

        # Action Buttons on Right
        f_actions = ctk.CTkFrame(h_inner, fg_color="transparent")
        f_actions.pack(side="right")

        btn_copy = ctk.CTkButton(
            f_actions,
            text="📋 COPY DOSSIER",
            font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"),
            fg_color="#1e293b",
            hover_color="#334155",
            width=110,
            height=28,
            command=self.copy_dossier_text
        )
        btn_copy.pack(side="left", padx=4)

        btn_save = ctk.CTkButton(
            f_actions,
            text="💾 SAVE TO DATABASE",
            font=ctk.CTkFont(family="Orbitron", size=9, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            width=135,
            height=28,
            command=self.save_current_dossier_manual
        )
        btn_save.pack(side="left", padx=4)

        # 2. Main Two-Column Body: Left Sidebar (History Archive), Right (Report Display)
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=12, pady=10)
        body.grid_columnconfigure(0, weight=1) # Archive Sidebar (width ~ 280px)
        body.grid_columnconfigure(1, weight=3) # Full Report View (width ~ 720px)
        body.grid_rowconfigure(0, weight=1)

        # -------------------------------------------------------------
        # LEFT: Saved Dossiers Archive List
        # -------------------------------------------------------------
        sidebar = ctk.CTkFrame(body, fg_color="#0b1222", corner_radius=8, border_width=1, border_color="#163b4d")
        sidebar.grid(row=0, column=0, padx=(0, 8), sticky="nsew")

        f_sb_hdr = ctk.CTkFrame(sidebar, fg_color="transparent")
        f_sb_hdr.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(f_sb_hdr, text="📂 SAVED REPORTS ARCHIVE", font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"), text_color="#00f0ff").pack(side="left")

        btn_refresh_arch = ctk.CTkButton(f_sb_hdr, text="🔄", width=26, height=22, font=ctk.CTkFont(size=11), fg_color="#1e293b", command=self.load_saved_dossiers_list)
        btn_refresh_arch.pack(side="right")

        self.scroll_archive = ctk.CTkScrollableFrame(sidebar, fg_color="transparent")
        self.scroll_archive.pack(fill="both", expand=True, padx=6, pady=6)

        # -------------------------------------------------------------
        # RIGHT: Detailed Medical Report Display
        # -------------------------------------------------------------
        right_box = ctk.CTkFrame(body, fg_color="#081020", corner_radius=8, border_width=1, border_color="#163b4d")
        right_box.grid(row=0, column=1, sticky="nsew")

        self.txt_report = ctk.CTkTextbox(
            right_box,
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#04070e",
            text_color="#e2e8f0",
            wrap="word"
        )
        self.txt_report.pack(fill="both", expand=True, padx=12, pady=12)

    def generate_and_display_report(self, auto_save: bool = True):
        # 1. Match against NASA historical spaceflight medical case
        match_info = HistoricalCaseMatcher.match_case(
            astronaut=self.astronaut,
            vitals=self.vitals,
            cabin=self.cabin,
            is_emergency=self.is_emergency
        )

        name = self.astronaut.get("name", "Astronaut").upper()
        role = self.astronaut.get("role", "Mission Specialist")
        callsign = self.astronaut.get("callsign", "CREW")
        serial = self.astronaut.get("serial", "CREW-01")
        grp = self.astronaut.get("group_id", "expedition_72").upper()

        hr = int(self.vitals.get("heart_rate", 72))
        spo2 = float(self.vitals.get("spo2", 98.4))
        hrv = float(self.vitals.get("hrv", 58.0))
        fatigue = int(self.vitals.get("fatigue_level", 18))
        readiness = 88 if not self.is_emergency else 38

        b_hr = self.astronaut.get("baseline_hr", 72)
        b_spo2 = self.astronaut.get("baseline_spo2", 98.4)
        b_hrv = self.astronaut.get("baseline_hrv", 58.0)

        c_co2 = float(self.cabin.get("co2_percent", 0.31))
        c_temp = float(self.cabin.get("temp_c", 21.6))
        c_rad = float(self.cabin.get("radiation_msv", 0.18))

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        # Determine clinical health status
        status_eval = "🚨 ACUTE VITAL ANOMALY / CRITICAL" if self.is_emergency or spo2 < 93.0 or hr > 115 else "🟢 NOMINAL HOMEOSTASIS"

        report = (
            f"========================================================================================\n"
            f"       NATIONAL AERONAUTICS AND SPACE ADMINISTRATION • FLIGHT MEDICINE CLINICAL BRIEF\n"
            f"       ASTROMIND AUTONOMOUS CREW HEALTH MONITORING SYSTEM • HOUSTON MISSION CONTROL\n"
            f"       REPORT GENERATED: {now_str}\n"
            f"========================================================================================\n\n"
            f"1. SUBJECT & MISSION IDENTIFICATION\n"
            f"   • Full Name:           {name}\n"
            f"   • Flight Callsign:     {callsign}  |  Crew Serial: {serial}\n"
            f"   • Assigned Duty:       {role}\n"
            f"   • Expedition Group:    {grp}\n"
            f"   • Operational Status:  {'🚀 DEPLOYED IN DEEP SPACE' if self.astronaut.get('is_deployed') == 1 else '🌍 SAFELY RETURNED TO EARTH'}\n"
            f"   • Medical Readiness:   {readiness}% ({'FIT FOR EVA' if readiness >= 75 else 'DUTY RESTRICTED'})\n\n"
            f"2. LIVE BIOMETRIC TELEMETRY vs NASA BASELINE (NASA-STD-3001 & LSDA)\n"
            f"   • Heart Rate:          {hr} BPM      [Baseline: {b_hr} BPM | Delta: {hr - b_hr:+d} BPM]\n"
            f"   • Arterial SpO2:       {spo2:.1f} %     [Baseline: {b_spo2:.1f} % | Delta: {spo2 - b_spo2:+.1f} %]\n"
            f"   • Autonomic HRV:       {hrv:.1f} ms    [Baseline: {b_hrv:.1f} ms | Delta: {hrv - b_hrv:+.1f} ms]\n"
            f"   • Cognitive Fatigue:   {fatigue} %\n"
            f"   • Cabin Environment:   CO2: {c_co2:.2f}% (SMAC <0.40%) | Temp: {c_temp:.1f}°C | Rad: {c_rad:.2f} mSv/h\n"
            f"   • Evaluation Verdict:  {status_eval}\n\n"
            f"3. 🔍 HISTORICAL NASA SPACEFLIGHT CASE MATCH (NASA MISSION ARCHIVE)\n"
            f"   • Matched Mission:     {match_info['matched_mission']}\n"
            f"   • Historical Context:  \n"
            f"     {match_info['matched_case']}\n\n"
            f"4. 💊 HOW THE HISTORICAL ASTRONAUT RECOVERED (OFFICIAL NASA FLIGHT SURGEON PROTOCOL)\n"
            f"   {match_info['how_astronaut_recovered']}\n\n"
            f"5. 🤖 ASTROMIND AI AUTONOMOUS CLINICAL COUNTERMEASURES\n"
            f"   • {match_info['ai_autonomous_suggestion']}\n\n"
            f"6. 🩺 FLIGHT SURGEON CERTIFICATION & SIGN-OFF\n"
            f"   • Surveillance:        Autonomous 24/7 Silent Camera Face Mesh & Edge Telemetry active.\n"
            f"   • Communication State: Ground S-Band DSN Telemetry Synchronized with Earth Mission Control.\n"
            f"========================================================================================\n"
        )

        self.current_report_text = report
        self.current_match_info = match_info
        self.txt_report.configure(state="normal")
        self.txt_report.delete("1.0", "end")
        self.txt_report.insert("1.0", report)
        self.txt_report.configure(state="disabled")

        if auto_save:
            self.save_dossier_to_db(report, match_info, silent=True)

    def save_dossier_to_db(self, report_text: str, match_info: Dict[str, str], silent: bool = False):
        aid = self.astronaut.get("id", "sarah")
        aname = self.astronaut.get("name", "Astronaut")
        v_sum = f"HR: {self.vitals.get('heart_rate')} BPM | SpO2: {self.vitals.get('spo2')}% | Fatigue: {self.vitals.get('fatigue_level')}%"
        c_sum = f"CO2: {self.cabin.get('co2_percent')}% | Temp: {self.cabin.get('temp_c')}C | Rad: {self.cabin.get('radiation_msv')} mSv/h"
        stat = "CRITICAL ANOMALY" if self.is_emergency else "NOMINAL"
        title = f"NASA Clinical Dossier • {aname} ({datetime.now().strftime('%b %d, %H:%M')})"

        dossier_id = medical_db.save_clinical_dossier(
            astronaut_id=aid,
            astronaut_name=aname,
            report_title=title,
            vitals_summary=v_sum,
            cabin_summary=c_sum,
            status_eval=stat,
            historical_match_text=match_info.get("matched_mission", ""),
            recovery_protocol_text=match_info.get("how_astronaut_recovered", ""),
            ai_suggestions_text=match_info.get("ai_autonomous_suggestion", ""),
            full_report_text=report_text
        )
        if not silent:
            toast = ctk.CTkLabel(self, text=f"✅ Clinical Report Saved Successfully to Database (Dossier #{dossier_id})!", fg_color="#103628", text_color="#10b981", corner_radius=6, pady=6)
            toast.pack(side="bottom", fill="x", padx=16, pady=8)
            self.after(3000, toast.destroy)
        self.load_saved_dossiers_list()

    def save_current_dossier_manual(self):
        if hasattr(self, "current_report_text") and hasattr(self, "current_match_info"):
            self.save_dossier_to_db(self.current_report_text, self.current_match_info, silent=False)

    def load_saved_dossiers_list(self):
        for widget in self.scroll_archive.winfo_children():
            widget.destroy()

        dossiers = medical_db.get_clinical_dossiers(limit=50)
        if not dossiers:
            ctk.CTkLabel(self.scroll_archive, text="No archived reports yet.", font=ctk.CTkFont(size=10), text_color="#64748b").pack(pady=20)
            return

        for d in dossiers:
            card = ctk.CTkFrame(self.scroll_archive, fg_color="#0d172a", corner_radius=6, border_width=1, border_color="#1e293b")
            card.pack(fill="x", pady=4, padx=2)

            t_f = ctk.CTkFrame(card, fg_color="transparent")
            t_f.pack(fill="x", padx=8, pady=(6, 2))

            ctk.CTkLabel(t_f, text=d.get("astronaut_name", "Astronaut"), font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color="#38bdf8").pack(side="left")
            
            is_crit = "CRITICAL" in d.get("status_eval", "")
            badge_col = "#ff1e53" if is_crit else "#10b981"
            ctk.CTkLabel(t_f, text="🚨" if is_crit else "🟢", font=ctk.CTkFont(size=10)).pack(side="right")

            ctk.CTkLabel(card, text=f"📅 {d.get('created_at', '')}", font=ctk.CTkFont(family="Consolas", size=8), text_color="#64748b").pack(anchor="w", padx=8)
            ctk.CTkLabel(card, text=d.get("vitals_summary", ""), font=ctk.CTkFont(family="Inter", size=9), text_color="#cbd5e1").pack(anchor="w", padx=8, pady=(1, 4))

            # View button for this archived dossier
            btn_view = ctk.CTkButton(
                card,
                text="📖 Read Full Dossier",
                height=22,
                font=ctk.CTkFont(family="Orbitron", size=8, weight="bold"),
                fg_color="#0f223a",
                hover_color="#0284c7",
                command=lambda did=d["id"]: self.view_archived_dossier(did)
            )
            btn_view.pack(fill="x", padx=8, pady=(2, 6))

    def view_archived_dossier(self, dossier_id: int):
        dossier = medical_db.get_dossier_by_id(dossier_id)
        if dossier and dossier.get("full_report_text"):
            self.txt_report.configure(state="normal")
            self.txt_report.delete("1.0", "end")
            self.txt_report.insert("1.0", dossier["full_report_text"])
            self.txt_report.configure(state="disabled")
            self.lbl_sub.configure(text=f"VIEWING ARCHIVE DOSSIER #{dossier_id} • SUBJECT: {dossier.get('astronaut_name', '').upper()} • SAVED: {dossier.get('created_at', '')}")

    def copy_dossier_text(self):
        text = self.txt_report.get("1.0", "end")
        self.clipboard_clear()
        self.clipboard_append(text)
        toast = ctk.CTkLabel(self, text="📋 Complete Clinical Dossier Copied to Clipboard!", fg_color="#103628", text_color="#10b981", corner_radius=6, pady=6)
        toast.pack(side="bottom", fill="x", padx=16, pady=8)
        self.after(3000, toast.destroy)
