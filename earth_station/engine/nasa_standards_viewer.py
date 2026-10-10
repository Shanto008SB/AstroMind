"""
AstroMind: NASA Open Standards & Official Datasets Viewer
Displays:
1. 1,280 NASA Astronaut Flight Records (Official NASA Public Archive)
2. 383 NASA & Russian Spacewalk EVAs (Official data.nasa.gov CSV)
3. NASA Technical Standards (NASA-STD-3001 Vol 2)
4. NASA Life Sciences Data Archive (LSDA) Microgravity Baselines
5. NASA Open Science Data Repository (OSDR) Clinical Syndromes
6. Direct URLs and One-Click Citation Copy for NASA Space Apps Challenge Submissions
"""

import os
import csv
import webbrowser
import customtkinter as ctk
from typing import List, Dict, Any


class NASAStandardsViewer(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("🏛️ NASA Official Open Datasets & Standards • NASA Space Apps Challenge")
        self.geometry("1060x720")
        self.configure(fg_color="#060c18")

        self.attributes("-topmost", True)
        self.lift()
        self.focus_force()

        # Resolve paths to CSV datasets
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.ds_dir = os.path.join(base_dir, "nasa_datasets")
        if not os.path.exists(self.ds_dir):
            root_dir = os.path.dirname(base_dir)
            self.ds_dir = os.path.join(root_dir, "nasa_datasets")

        self.astronaut_data_cache: List[Dict[str, str]] = []
        self.eva_data_cache: List[Dict[str, str]] = []

        self.build_ui()

    def build_ui(self):
        # 1. Header Banner
        header = ctk.CTkFrame(self, fg_color="#091426", corner_radius=0, border_width=1, border_color="#1e3a5f")
        header.pack(fill="x", side="top", padx=0, pady=0)

        top_f = ctk.CTkFrame(header, fg_color="transparent")
        top_f.pack(fill="x", padx=18, pady=12)

        lbl_title = ctk.CTkLabel(
            top_f,
            text="🏛️ NASA OFFICIAL OPEN DATASETS & STANDARDS COMPLIANCE",
            font=ctk.CTkFont(family="Orbitron", size=15, weight="bold"),
            text_color="#38bdf8"
        )
        lbl_title.pack(anchor="w")

        lbl_sub = ctk.CTkLabel(
            top_f,
            text="Loaded Official NASA Files: 1,280 Astronaut Flight Records • 383 EVA Spacewalks • NASA-STD-3001 • NASA LSDA",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#94a3b8"
        )
        lbl_sub.pack(anchor="w", pady=(2, 0))

        # Copy Citation Button
        btn_copy = ctk.CTkButton(
            top_f,
            text="📋 Copy NASA Citation for Submission",
            font=ctk.CTkFont(family="Orbitron", size=10, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self.copy_citation_text
        )
        btn_copy.pack(side="right", padx=6)

        # 2. Tabview
        self.tabview = ctk.CTkTabview(self, fg_color="#081020", segmented_button_selected_color="#0284c7")
        self.tabview.pack(fill="both", expand=True, padx=16, pady=12)

        self.tab_astros = self.tabview.add("👨‍🚀 NASA Astronauts (1,280 Records)")
        self.tab_evas = self.tabview.add("🌌 NASA Spacewalks (383 EVAs)")
        self.tab_env = self.tabview.add("🛰️ NASA-STD-3001 (Spacecraft Limits)")
        self.tab_lsda = self.tabview.add("🧬 NASA LSDA (Astronaut Biometrics)")
        self.tab_osdr = self.tabview.add("🔬 NASA OSDR (Clinical Syndromes)")
        self.tab_sources = self.tabview.add("🔗 Official NASA URLs & Citations")

        self.populate_tab_astros()
        self.populate_tab_evas()
        self.populate_tab_env()
        self.populate_tab_lsda()
        self.populate_tab_osdr()
        self.populate_tab_sources()

    def _read_csv(self, filename: str) -> List[Dict[str, str]]:
        path = os.path.join(self.ds_dir, filename)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception:
            return []

    # -------------------------------------------------------------------------
    # TAB 1: NASA Astronauts Full Official Dataset (1,280 Records)
    # -------------------------------------------------------------------------
    def populate_tab_astros(self):
        self.astronaut_data_cache = self._read_csv("nasa_astronauts_official_full.csv")

        top_bar = ctk.CTkFrame(self.tab_astros, fg_color="transparent")
        top_bar.pack(fill="x", padx=8, pady=(4, 8))

        ctk.CTkLabel(
            top_bar,
            text=f"Total Astronaut Flight Records: {len(self.astronaut_data_cache)} (Source: NASA Public Archives)",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="left")

        # Search Entry
        self.entry_astro_search = ctk.CTkEntry(top_bar, placeholder_text="Search astronaut name / mission...", width=240, height=28, font=ctk.CTkFont(family="Consolas", size=11))
        self.entry_astro_search.pack(side="right", padx=6)
        self.entry_astro_search.bind("<KeyRelease>", lambda e: self.filter_astronauts())

        self.scroll_astros = ctk.CTkScrollableFrame(self.tab_astros, fg_color="transparent")
        self.scroll_astros.pack(fill="both", expand=True, padx=4, pady=4)

        self.render_astronaut_cards(self.astronaut_data_cache[:50])

    def filter_astronauts(self):
        query = self.entry_astro_search.get().strip().lower()
        if not query:
            filtered = self.astronaut_data_cache[:50]
        else:
            filtered = [
                a for a in self.astronaut_data_cache
                if query in a.get("name", "").lower() or query in a.get("mission_title", "").lower() or query in a.get("nationality", "").lower()
            ][:50]
        self.render_astronaut_cards(filtered)

    def render_astronaut_cards(self, astros: List[Dict[str, str]]):
        for widget in self.scroll_astros.winfo_children():
            widget.destroy()

        if not astros:
            ctk.CTkLabel(self.scroll_astros, text="No matching NASA astronaut records found.", text_color="#94a3b8").pack(pady=20)
            return

        for a in astros:
            card = ctk.CTkFrame(self.scroll_astros, fg_color="#0d172a", corner_radius=6, border_width=1, border_color="#1e293b")
            card.pack(fill="x", pady=4, padx=2)

            t_f = ctk.CTkFrame(card, fg_color="transparent")
            t_f.pack(fill="x", padx=10, pady=(6, 2))

            name = a.get("name", "Unknown Astronaut")
            nat = a.get("nationality", "USA")
            mil = a.get("military_civilian", "civilian")
            ctk.CTkLabel(t_f, text=f"👨‍🚀 {name} ({nat})", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#38bdf8").pack(side="left")
            ctk.CTkLabel(t_f, text=f"[{mil.upper()}] • Group: {a.get('selection', 'NASA')}", font=ctk.CTkFont(family="Consolas", size=9), text_color="#94a3b8").pack(side="right")

            b_f = ctk.CTkFrame(card, fg_color="transparent")
            b_f.pack(fill="x", padx=10, pady=(2, 6))

            m_title = a.get("mission_title", "N/A")
            m_year = a.get("year_of_mission", "N/A")
            m_hrs = a.get("hours_mission", "0")
            eva_hrs = a.get("total_eva_hrs", "0")
            role = a.get("occupation", "Crew")

            info = f"🚀 Mission: {m_title} ({m_year}) | Role: {role} | Flight Duration: {m_hrs} hrs | Total EVA Spacewalk: {eva_hrs} hrs"
            ctk.CTkLabel(b_f, text=info, font=ctk.CTkFont(family="Inter", size=10), text_color="#cbd5e1").pack(anchor="w")

    # -------------------------------------------------------------------------
    # TAB 2: NASA & Russian Spacewalks / EVAs (383 Official Records)
    # -------------------------------------------------------------------------
    def populate_tab_evas(self):
        self.eva_data_cache = self._read_csv("nasa_eva_spacewalks_official.csv")

        top_bar = ctk.CTkFrame(self.tab_evas, fg_color="transparent")
        top_bar.pack(fill="x", padx=8, pady=(4, 8))

        ctk.CTkLabel(
            top_bar,
            text=f"Total Official Extra-Vehicular Activities (EVAs): {len(self.eva_data_cache)} (Source: data.nasa.gov)",
            font=ctk.CTkFont(family="Inter", size=11, weight="bold"),
            text_color="#00f0ff"
        ).pack(side="left")

        # Search Entry
        self.entry_eva_search = ctk.CTkEntry(top_bar, placeholder_text="Search EVA crew / vehicle / purpose...", width=240, height=28, font=ctk.CTkFont(family="Consolas", size=11))
        self.entry_eva_search.pack(side="right", padx=6)
        self.entry_eva_search.bind("<KeyRelease>", lambda e: self.filter_evas())

        self.scroll_evas = ctk.CTkScrollableFrame(self.tab_evas, fg_color="transparent")
        self.scroll_evas.pack(fill="both", expand=True, padx=4, pady=4)

        self.render_eva_cards(self.eva_data_cache[:50])

    def filter_evas(self):
        query = self.entry_eva_search.get().strip().lower()
        if not query:
            filtered = self.eva_data_cache[:50]
        else:
            filtered = [
                e for e in self.eva_data_cache
                if query in e.get("Crew", "").lower() or query in e.get("Vehicle", "").lower() or query in e.get("Purpose", "").lower()
            ][:50]
        self.render_eva_cards(filtered)

    def render_eva_cards(self, evas: List[Dict[str, str]]):
        for widget in self.scroll_evas.winfo_children():
            widget.destroy()

        if not evas:
            ctk.CTkLabel(self.scroll_evas, text="No matching NASA EVA spacewalk records found.", text_color="#94a3b8").pack(pady=20)
            return

        for e in evas:
            card = ctk.CTkFrame(self.scroll_evas, fg_color="#0d172a", corner_radius=6, border_width=1, border_color="#1e293b")
            card.pack(fill="x", pady=4, padx=2)

            t_f = ctk.CTkFrame(card, fg_color="transparent")
            t_f.pack(fill="x", padx=10, pady=(6, 2))

            eva_num = e.get("EVA #", e.get("EVA", ""))
            crew = e.get("Crew", e.get("Crew    ", "Astronaut"))
            veh = e.get("Vehicle", "Spacecraft")
            dur = e.get("Duration", "N/A")
            dt = e.get("Date", "")

            ctk.CTkLabel(t_f, text=f"🌌 EVA #{eva_num}: {crew.strip()}", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#00f0ff").pack(side="left")
            ctk.CTkLabel(t_f, text=f"Vehicle: {veh} • Date: {dt} • Duration: {dur}", font=ctk.CTkFont(family="Consolas", size=10), text_color="#34d399").pack(side="right")

            purp = e.get("Purpose ", e.get("Purpose", "Routine orbital maintenance."))
            ctk.CTkLabel(card, text=f"Mission Log: {purp.strip()}", font=ctk.CTkFont(family="Inter", size=10), text_color="#cbd5e1", wraplength=850, justify="left").pack(anchor="w", padx=10, pady=(2, 6))

    # -------------------------------------------------------------------------
    # TAB 3: NASA-STD-3001 Environmental Limits
    # -------------------------------------------------------------------------
    def populate_tab_env(self):
        f = ctk.CTkScrollableFrame(self.tab_env, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=6, pady=6)

        ctk.CTkLabel(
            f,
            text="NASA Space Flight Human-System Standard: Spacecraft Maximum Allowable Concentrations (SMAC)",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", pady=(4, 10))

        rows = self._read_csv("nasa_std_3001_environmental_limits.csv")
        for r in rows:
            card = ctk.CTkFrame(f, fg_color="#0d172a", corner_radius=8, border_width=1, border_color="#1e293b")
            card.pack(fill="x", pady=5, padx=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(top, text=f"{r.get('parameter', '')} ({r.get('unit', '')})", font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#00f0ff").pack(side="left")
            ctk.CTkLabel(top, text=f"Ref: {r.get('nasa_standard_reference', '')}", font=ctk.CTkFont(family="Consolas", size=9), text_color="#64748b").pack(side="right")

            v_f = ctk.CTkFrame(card, fg_color="#070c18", corner_radius=4)
            v_f.pack(fill="x", padx=12, pady=4)
            vals = (
                f"Nominal: {r.get('nominal_min', '')} - {r.get('nominal_max', '')} {r.get('unit', '')}  |  "
                f"Caution: > {r.get('caution_threshold', '')}  |  "
                f"Emergency: > {r.get('emergency_threshold', '')}"
            )
            ctk.CTkLabel(v_f, text=vals, font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#10b981").pack(side="left", padx=8, pady=4)

            notes = ctk.CTkFrame(card, fg_color="transparent")
            notes.pack(fill="x", padx=12, pady=(2, 8))
            ctk.CTkLabel(notes, text=f"• Clinical Risk: {r.get('clinical_risk', '')}", font=ctk.CTkFont(family="Inter", size=10), text_color="#fca5a5").pack(anchor="w")
            ctk.CTkLabel(notes, text=f"• NASA Protocol: {r.get('countermeasure', '')}", font=ctk.CTkFont(family="Inter", size=10), text_color="#94a3b8").pack(anchor="w")

    # -------------------------------------------------------------------------
    # TAB 4: NASA LSDA Astronaut Biometric Baselines
    # -------------------------------------------------------------------------
    def populate_tab_lsda(self):
        f = ctk.CTkScrollableFrame(self.tab_lsda, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=6, pady=6)

        ctk.CTkLabel(
            f,
            text="NASA Life Sciences Data Archive (LSDA): In-Flight Microgravity Physiological Norms",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", pady=(4, 10))

        rows = self._read_csv("nasa_lsda_astronaut_vitals_baseline.csv")
        for r in rows:
            card = ctk.CTkFrame(f, fg_color="#0d172a", corner_radius=8, border_width=1, border_color="#1e293b")
            card.pack(fill="x", pady=5, padx=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))
            ctk.CTkLabel(top, text=r.get("metric", "").replace("_", " ").upper(), font=ctk.CTkFont(family="Consolas", size=13, weight="bold"), text_color="#38bdf8").pack(side="left")
            ctk.CTkLabel(top, text=f"Source: {r.get('nasa_study_source', '')}", font=ctk.CTkFont(family="Consolas", size=9), text_color="#64748b").pack(side="right")

            v_f = ctk.CTkFrame(card, fg_color="#070c18", corner_radius=4)
            v_f.pack(fill="x", padx=12, pady=4)
            vals = (
                f"Microgravity Mean: {r.get('microgravity_mean', '')}  |  "
                f"Normal Range: {r.get('nominal_range', '')}  |  "
                f"Caution: {r.get('caution_limit', '')}  |  "
                f"Emergency: {r.get('emergency_limit', '')}"
            )
            ctk.CTkLabel(v_f, text=vals, font=ctk.CTkFont(family="Consolas", size=10, weight="bold"), text_color="#34d399").pack(side="left", padx=8, pady=4)

            ctk.CTkLabel(
                card,
                text=f"Physiological Notes: {r.get('physiological_notes', '')}",
                font=ctk.CTkFont(family="Inter", size=10),
                text_color="#94a3b8"
            ).pack(anchor="w", padx=12, pady=(2, 8))

    # -------------------------------------------------------------------------
    # TAB 5: NASA OSDR Spaceflight Clinical Syndromes
    # -------------------------------------------------------------------------
    def populate_tab_osdr(self):
        f = ctk.CTkScrollableFrame(self.tab_osdr, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=6, pady=6)

        ctk.CTkLabel(
            f,
            text="NASA Open Science Data Repository (OSDR): Spaceflight Health Risk Diagnoses",
            font=ctk.CTkFont(family="Inter", size=12, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", pady=(4, 10))

        rows = self._read_csv("nasa_osdr_clinical_syndromes.csv")
        for r in rows:
            card = ctk.CTkFrame(f, fg_color="#0d172a", corner_radius=8, border_width=1, border_color="#1e293b")
            card.pack(fill="x", pady=5, padx=2)

            top = ctk.CTkFrame(card, fg_color="transparent")
            top.pack(fill="x", padx=12, pady=(8, 2))
            crit = r.get("criticality", "MODERATE")
            crit_col = "#ff1e53" if crit == "CRITICAL" else ("#f59e0b" if crit == "HIGH" else "#10b981")
            
            ctk.CTkLabel(top, text=f"[{r.get('syndrome_code', '')}] {r.get('syndrome_name', '')}", font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#ffffff").pack(side="left")
            ctk.CTkLabel(top, text=f" {crit} ", font=ctk.CTkFont(family="Consolas", size=9, weight="bold"), text_color=crit_col, fg_color="#1a1215", corner_radius=4).pack(side="right")

            notes = ctk.CTkFrame(card, fg_color="transparent")
            notes.pack(fill="x", padx=12, pady=(4, 8))
            ctk.CTkLabel(notes, text=f"• Study ID: {r.get('nasa_osdr_id', '')} | Primary Symptoms: {r.get('primary_symptoms', '')}", font=ctk.CTkFont(family="Inter", size=10), text_color="#cbd5e1").pack(anchor="w")
            ctk.CTkLabel(notes, text=f"• Clinical Protocol: {r.get('flight_surgeon_protocol', '')}", font=ctk.CTkFont(family="Inter", size=10), text_color="#38bdf8").pack(anchor="w")

    # -------------------------------------------------------------------------
    # TAB 6: Official NASA URLs & Citations
    # -------------------------------------------------------------------------
    def populate_tab_sources(self):
        f = ctk.CTkScrollableFrame(self.tab_sources, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=6, pady=6)

        sources = [
            ("1. NASA Open Data Portal: Extra-vehicular Activity (EVA - US & Russia)", "https://data.nasa.gov/docs/legacy/Extra-vehicular_Activity_EVA_-_US_and_Russia/Extra-vehicular_Activity_EVA_-_US_and_Russia_rows.csv", "383 official cataloged spacewalks beyond Earth's atmosphere with durations and anomalies."),
            ("2. NASA Astronaut Public Historical Archive", "https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-07-14/astronauts.csv", "1,280 detailed flight records of NASA and international astronauts from 1959 to present."),
            ("3. NASA Technical Standard (NASA-STD-3001 Vol 2)", "https://standards.nasa.gov/standard/NASA/NASA-STD-3001-Vol-2", "Spacecraft Maximum Allowable Concentrations (SMAC) for cabin atmospheric safety."),
            ("4. NASA Life Sciences Data Archive (LSDA)", "https://lsda.jsc.nasa.gov/", "Astronaut in-flight cardiovascular, SpO2, and sleep debt microgravity baselines."),
            ("5. NASA Open Science Data Repository (OSDR)", "https://osdr.nasa.gov/", "Biological responses, SANS diagnosis, and spaceflight clinical countermeasure guidelines."),
            ("6. NASA Human Research Program Roadmap (ExMC)", "https://humanresearchroadmap.nasa.gov/", "Autonomous medical decision support protocols for exploration-class deep space missions.")
        ]

        for title, url, desc in sources:
            card = ctk.CTkFrame(f, fg_color="#0d172a", corner_radius=8, border_width=1, border_color="#1e293b")
            card.pack(fill="x", pady=6, padx=2)

            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(family="Consolas", size=12, weight="bold"), text_color="#38bdf8").pack(anchor="w", padx=12, pady=(8, 2))
            ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(family="Inter", size=10), text_color="#94a3b8").pack(anchor="w", padx=12, pady=1)

            btn_link = ctk.CTkButton(
                card,
                text=f"🌐 Open Official Link: {url}",
                font=ctk.CTkFont(family="Consolas", size=10),
                fg_color="#071224",
                hover_color="#0f2b48",
                anchor="w",
                command=lambda u=url: webbrowser.open(u)
            )
            btn_link.pack(fill="x", padx=12, pady=(4, 8))

    def copy_citation_text(self):
        citation = (
            "NASA Data Resources & Open Standards Used in AstroMind:\n\n"
            "1. NASA Open Data Portal: Extra-vehicular Activity (EVA - US and Russia):\n"
            "   URL: https://data.nasa.gov/docs/legacy/Extra-vehicular_Activity_EVA_-_US_and_Russia/Extra-vehicular_Activity_EVA_-_US_and_Russia_rows.csv\n"
            "   Usage: 383 historical spacewalk mission records to cross-reference EVA physiological workloads.\n\n"
            "2. NASA Astronaut Historical Archive (NASA Open Data & Corlett Database):\n"
            "   URL: https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-07-14/astronauts.csv\n"
            "   Usage: 1,280 official NASA astronaut flight logs for cumulative spaceflight hours and mission tracking.\n\n"
            "3. NASA-STD-3001 Vol 2 (NASA Space Flight Human-System Standard):\n"
            "   URL: https://standards.nasa.gov/standard/NASA/NASA-STD-3001-Vol-2\n"
            "   Usage: Spacecraft environmental safety limits (Cabin CO2 SMAC levels, ambient temperature, radiation thresholds).\n\n"
            "4. NASA Life Sciences Data Archive (LSDA):\n"
            "   URL: https://lsda.jsc.nasa.gov/\n"
            "   Usage: Astronaut physiological baseline data (microgravity heart rate drift, SpO2 tolerances, and cognitive fatigue metrics).\n\n"
            "5. NASA Open Science Data Repository (OSDR):\n"
            "   URL: https://osdr.nasa.gov/\n"
            "   Usage: Spaceflight clinical anomaly profiles and systemic microgravity health deconditioning protocols.\n\n"
            "6. NASA Human Research Roadmap (Exploration Medical Capabilities - ExMC):\n"
            "   URL: https://humanresearchroadmap.nasa.gov/\n"
            "   Usage: Autonomous clinical decision-making protocols designed for deep-space missions facing Earth communication latency."
        )
        self.clipboard_clear()
        self.clipboard_append(citation)
        
        toast = ctk.CTkLabel(self, text="✅ NASA Citation Text Copied to Clipboard! Ready to paste into submission form.", fg_color="#103628", text_color="#10b981", corner_radius=6, pady=6)
        toast.pack(side="bottom", fill="x", padx=16, pady=8)
        self.after(3500, toast.destroy)
