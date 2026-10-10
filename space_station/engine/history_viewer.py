"""
AstroMind: Medical History & Longitudinal Records Viewer
Allows astronauts and mission flight surgeons to inspect past medical reports
filtered by date, view comparative health trend deltas, and inspect saved snapshots.
"""

import os
import customtkinter as ctk
from PIL import Image
from typing import Optional
from .medical_db import medical_db
from .shared_state import state

class MedicalHistoryViewer(ctk.CTkToplevel):
    def __init__(self, parent, default_astronaut_id: str = "sarah"):
        super().__init__(parent)

        self.title("AstroMind: Longitudinal Medical Archive & Daily Trend Reports")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(fg_color="#070b14")
        self.attributes("-topmost", True)

        self.parent = parent
        self.astronaut_id = default_astronaut_id
        self.selected_date = "ALL"
        self.img_cache = {}

        self.build_ui()
        self.load_records()

    def build_ui(self):
        # 1. Header Frame
        hdr = ctk.CTkFrame(self, height=60, fg_color="#0b1222", corner_radius=0, border_width=1, border_color="#163b4d")
        hdr.pack(fill="x", side="top", padx=0, pady=0)

        f_left = ctk.CTkFrame(hdr, fg_color="transparent")
        f_left.pack(side="left", padx=16, pady=8)

        ctk.CTkLabel(f_left, text="📋 ASTRONAUT MEDICAL RECORDS & TREND ARCHIVE", font=ctk.CTkFont(family="Orbitron", size=14, weight="bold"), text_color="#00f0ff").pack(anchor="w")
        ctk.CTkLabel(f_left, text="Longitudinal Health Monitoring • Daily Comparison & Snapshot Inspection", font=ctk.CTkFont(family="Consolas", size=9), text_color="#94a3b8").pack(anchor="w")

        # 2. Controls Bar (Astronaut Selector & Date Filter)
        filter_bar = ctk.CTkFrame(self, fg_color="#0d1628", corner_radius=8, border_width=1, border_color="#1e293b")
        filter_bar.pack(fill="x", padx=16, pady=10)

        # Astronaut Selector
        ctk.CTkLabel(filter_bar, text="👨‍🚀 CREW:", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#38bdf8").pack(side="left", padx=(12, 4), pady=8)
        crew_options = [
            ("01 • Capt. Sarah Connor", "sarah"),
            ("02 • Dr. Alex Vance", "alex"),
            ("03 • Eng. John Miller", "john"),
            ("04 • Elena Rostova", "elena")
        ]
        self.crew_map = {opt[0]: opt[1] for opt in crew_options}
        self.crew_map_rev = {opt[1]: opt[0] for opt in crew_options}

        self.sel_crew = ctk.CTkOptionMenu(
            filter_bar,
            values=[opt[0] for opt in crew_options],
            command=self.on_crew_changed,
            fg_color="#1e293b",
            button_color="#0284c7",
            font=ctk.CTkFont(family="Inter", size=11)
        )
        self.sel_crew.set(self.crew_map_rev.get(self.astronaut_id, crew_options[0][0]))
        self.sel_crew.pack(side="left", padx=6, pady=8)

        # Date Filter Dropdown
        ctk.CTkLabel(filter_bar, text="📅 DATE FILTER:", font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#38bdf8").pack(side="left", padx=(16, 4), pady=8)
        self.sel_date = ctk.CTkOptionMenu(
            filter_bar,
            values=["ALL DATES"],
            command=self.on_date_changed,
            fg_color="#1e293b",
            button_color="#0284c7",
            font=ctk.CTkFont(family="Inter", size=11)
        )
        self.sel_date.pack(side="left", padx=6, pady=8)

        # Refresh Button
        ctk.CTkButton(
            filter_bar,
            text="🔄 REFRESH RECORDS",
            width=130,
            fg_color="#0ea5e9",
            hover_color="#0284c7",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            command=self.load_records
        ).pack(side="right", padx=12, pady=8)

        # 3. Main Scrollable List of Medical Records
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def on_crew_changed(self, choice):
        self.astronaut_id = self.crew_map.get(choice, "sarah")
        self.update_date_options()
        self.load_records()

    def on_date_changed(self, choice):
        self.selected_date = None if choice == "ALL DATES" else choice
        self.load_records()

    def update_date_options(self):
        dates = medical_db.get_distinct_dates(self.astronaut_id)
        opts = ["ALL DATES"] + dates
        self.sel_date.configure(values=opts)
        self.sel_date.set("ALL DATES")
        self.selected_date = None

    def load_records(self):
        # Clear existing cards
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        # Update available dates
        dates = medical_db.get_distinct_dates(self.astronaut_id)
        opts = ["ALL DATES"] + dates
        self.sel_date.configure(values=opts)

        records = medical_db.get_records_by_astronaut(self.astronaut_id, date_filter=self.selected_date)

        if not records:
            empty_card = ctk.CTkFrame(self.scroll_frame, fg_color="#0d1628", corner_radius=8)
            empty_card.pack(fill="x", pady=20, padx=10)
            ctk.CTkLabel(
                empty_card,
                text="No medical records found for this astronaut / date selection.\nPerform an on-demand scan or wait for 30-minute auto-snapshots.",
                font=ctk.CTkFont(family="Inter", size=12),
                text_color="#94a3b8"
            ).pack(pady=30)
            return

        for rec in records:
            self._render_record_card(rec)

    def _render_record_card(self, rec):
        card = ctk.CTkFrame(self.scroll_frame, fg_color="#0d1628", corner_radius=8, border_width=1, border_color="#1e293b")
        card.pack(fill="x", pady=6, padx=4)

        # Top row: Date/Time + Status Badge + Trigger Type
        f_top = ctk.CTkFrame(card, fg_color="transparent")
        f_top.pack(fill="x", padx=14, pady=(10, 4))

        # Time & Date
        ts_text = f"📅 {rec['date_str']} • ⏰ {rec['time_str']} UTC"
        ctk.CTkLabel(f_top, text=ts_text, font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00f0ff").pack(side="left")

        # Trigger tag
        trig_type = rec.get("trigger_type", "AUTO_30MIN")
        trig_color = "#38bdf8" if trig_type == "MANUAL_SCAN" else "#94a3b8"
        ctk.CTkLabel(f_top, text=f"[{trig_type}]", font=ctk.CTkFont(family="Consolas", size=9), text_color=trig_color).pack(side="left", padx=10)

        # Status badge
        status_eval = rec.get("status_eval", "🟢 HEALTHY & STABLE")
        badge_bg = "#103628" if "HEALTHY" in status_eval else ("#3b111e" if "CRITICAL" in status_eval else "#3b2911")
        badge_text_col = "#10b981" if "HEALTHY" in status_eval else ("#ff1e53" if "CRITICAL" in status_eval else "#f59e0b")

        ctk.CTkLabel(
            f_top,
            text=f" {status_eval} ",
            font=ctk.CTkFont(family="Inter", size=10, weight="bold"),
            fg_color=badge_bg,
            text_color=badge_text_col,
            corner_radius=4
        ).pack(side="right")

        # Middle row: Vitals Chips
        f_vitals = ctk.CTkFrame(card, fg_color="#060b14", corner_radius=6)
        f_vitals.pack(fill="x", padx=14, pady=6)

        vitals_list = [
            ("PULSE", f"{rec['heart_rate']} BPM", "#f87171"),
            ("BLOOD OXYGEN", f"{rec['spo2']:.1f}%", "#00f0ff"),
            ("HRV", f"{rec['hrv']:.0f} ms", "#c084fc"),
            ("FATIGUE", f"{rec['fatigue']}%", "#34d399"),
            ("READINESS SCORE", f"{rec['readiness_score']}%", "#10b981")
        ]

        for label, val, col in vitals_list:
            chip = ctk.CTkFrame(f_vitals, fg_color="transparent")
            chip.pack(side="left", padx=12, pady=6)
            ctk.CTkLabel(chip, text=label, font=ctk.CTkFont(family="Consolas", size=8), text_color="#64748b").pack(anchor="w")
            ctk.CTkLabel(chip, text=val, font=ctk.CTkFont(family="Rajdhani", size=14, weight="bold"), text_color=col).pack(anchor="w")

        # Bottom row: Comparative Trend Analysis + Snapshot thumbnail if present
        f_bottom = ctk.CTkFrame(card, fg_color="transparent")
        f_bottom.pack(fill="x", padx=14, pady=(2, 10))

        # Comparative difference text
        trend_text = rec.get("trend_diff", "Stable and nominal relative to prior baseline.")
        f_notes = ctk.CTkFrame(f_bottom, fg_color="transparent")
        f_notes.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(f_notes, text="📊 Longitudinal Trend Comparison:", font=ctk.CTkFont(family="Inter", size=10, weight="bold"), text_color="#38bdf8", anchor="w").pack(fill="x")
        ctk.CTkLabel(f_notes, text=trend_text, font=ctk.CTkFont(family="Inter", size=10), text_color="#cbd5e1", anchor="w", wraplength=700).pack(fill="x", pady=(1, 4))

        if rec.get("clinical_notes"):
            ctk.CTkLabel(f_notes, text=f"🩺 AI Flight Surgeon Evaluation: {rec['clinical_notes']}", font=ctk.CTkFont(family="Inter", size=9), text_color="#94a3b8", anchor="w", wraplength=700).pack(fill="x")

        # Snapshot Thumbnail Preview
        snap_path = rec.get("snapshot_path", "")
        if snap_path and os.path.exists(snap_path):
            try:
                pil_thumb = Image.open(snap_path).resize((110, 80), Image.Resampling.LANCZOS)
                ctk_thumb = ctk.CTkImage(light_image=pil_thumb, dark_image=pil_thumb, size=(110, 80))
                self.img_cache[rec["id"]] = ctk_thumb

                f_snap = ctk.CTkFrame(f_bottom, fg_color="#060b14", corner_radius=4, border_width=1, border_color="#163b4d")
                f_snap.pack(side="right", padx=(8, 0))

                lbl_snap = ctk.CTkLabel(f_snap, text="", image=ctk_thumb, cursor="hand2")
                lbl_snap.pack(padx=2, pady=2)

                def open_full_img(p=snap_path):
                    import webbrowser
                    webbrowser.open(os.path.abspath(p))

                lbl_snap.bind("<Button-1>", lambda e, p=snap_path: open_full_img(p))
            except Exception as e:
                pass
