<div align="center">

# 🚀 AstroMind
### Autonomous Deep Space & Earth Mission Control Medical Suite
**NASA Space Apps Challenge • Astronaut Health & Deep Space Exploration**

[![NASA Space Apps](https://img.shields.io/badge/NASA%20Space%20Apps-2026-blue.svg?style=for-the-badge&logo=nasa)](https://www.spaceappschallenge.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GUI](https://img.shields.io/badge/GUI-CustomTkinter-007ACC.svg?style=for-the-badge)](https://github.com/TomSchimansky/CustomTkinter)
[![Computer Vision](https://img.shields.io/badge/Vision-OpenCV%20%7C%20rPPG-5C3EE8.svg?style=for-the-badge&logo=opencv&logoColor=white)](https://opencv.org/)
[![AI Engine](https://img.shields.io/badge/Edge%20AI-Groq%20LPU%20Qwen-f55036.svg?style=for-the-badge)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)

<p align="center">
  <b>An offline-first, dual-station edge medical telemetry suite designed to protect astronauts during Moon & Mars missions when Earth communication is delayed by 10 to 40 minutes.</b>
</p>

</div>

---

## 🌌 1. The Deep Space Challenge & Mission Context

During long-duration deep-space exploration (such as NASA's **Artemis Lunar Gateway** and crewed **Mars Transit**), radio signals between spacecraft and Earth face **5 to 20 minutes of one-way latency** (up to 40 minutes round-trip). 

If a crew member encounters an acute medical crisis—such as:
* Sudden hypoxia or cabin decompression,
* Microgravity cardiovascular arrhythmia,
* Cabin hypercapnia (ECLSS CO₂ scrubber failure), or
* Spaceflight-Associated Neuro-ocular Syndrome (SANS),

**Ground flight surgeons at NASA Houston cannot intervene in real time.**

**AstroMind** bridges this critical gap through a **Dual-Station Edge Computing Architecture**:
1. **🚀 Deep Space Station (Spacecraft Edge Client):** Operates 100% offline aboard the spacecraft with zero Earth latency, providing autonomous clinical diagnosis, contactless biometric vital monitoring, and continuous acoustic hazard alarms.
2. **🌍 NASA Houston Earth Mission Control:** Provides real-time mirrored telemetry over S-Band LAN links, exclusive multi-expedition astronaut roster administration, and longitudinal health analytics.

---

## 💡 2. Why AstroMind? (Impact, Mission Benefits & Uniqueness)

### 🌟 Why This Project Matters
In future long-duration human missions to Mars and deep space, an astronaut's life cannot be put on hold waiting for Earth to reply. AstroMind shifts space medicine from **reactive ground-dependent telemedicine** to **proactive, autonomous edge healthcare**. It functions as an omnipresent, non-fatiguing flight surgeon aboard the spacecraft that monitors crew health 24/7 without requiring Earth connectivity.

### 🎯 How It Helps the Mission & Crew
* **Zero-Latency Clinical Emergency Triage:** Delivers instant diagnostic countermeasures within milliseconds of an anomaly, bypassing the deadly 40-minute round-trip communication blackout.
* **Frictionless 24/7 Crew Monitoring:** Removes sensor fatigue and skin irritation caused by adhesive electrodes and bulky wires, enabling passive vital sign tracking during sleep and routine mission operations.
* **ECLSS Life-Support Protection:** Prevents catastrophic cabin asphyxiation by warning the crew of toxic CO₂ buildups (hypercapnia) and environmental breaches before cognitive impairment sets in.
* **Crew Autonomy for Small Missions:** Compensates for the absence of dedicated medical doctors on 3-to-4 member exploratory crews by offering expert-level clinical guidance.
* **Longitudinal Space Biology Research:** Empowers NASA flight surgeons on Earth with continuous biometric drift data to study long-term microgravity adaptation, cardiovascular deconditioning, and SANS.

### 🦄 What Makes AstroMind Unique?
Unlike typical hackathon projects that build simple mock web dashboards, AstroMind delivers a complete, authentic mission ecosystem:
1. **True Dual-Station Edge-to-Ground Architecture:** Emulates an authentic deep-space communication architecture—an autonomous offline Edge station on the spacecraft combined with Houston Ground Control over a synchronized S-Band LAN link.
2. **Contactless Optical rPPG & 3D Topological Facial Meshing:** Combines computer vision and remote photoplethysmography to extract pulse, SpO₂, and fatigue from micro-vascular facial perfusion without requiring wearable sensors.
3. **NASA-STD-3001 Deterministic Safety Guardrails:** Rather than relying purely on probabilistic LLM responses, AstroMind binds the AI Doctor to official NASA environmental limits (SMAC) and LSDA baseline models to eliminate clinical hallucinations.
4. **Historical Flight Case Matcher:** The only system that instantly matches live in-flight crises with documented historical NASA mission incidents (Apollo 15 arrhythmia, Gemini IX-A metabolic spikes, Mir EO-23 hypercapnia) to surface battle-tested NASA countermeasures.
5. **Interactive Wireless Mobile IoT Simulation Bridge:** Allows judges and flight directors to inject physiological anomalies and trigger multi-harmonic acoustic danger sirens directly from any smartphone in real time (`/remote`).

---

## 🛰️ 3. Dual-Station Architecture & Data Flow

```
 ┌────────────────────────────────────────────────────────┐
 │        🚀 DEEP SPACE STATION CLIENT (Spacecraft)       │
 │  • Displays Deployed Crew Group (Read-Only in Orbit)   │
 │  • 3D Holographic Neural AI Brain                      │
 │  • Contactless 3D Biometric Facial Mesh Scanner (rPPG) │
 │  • Continuous Multi-Harmonic NASA Danger Alarm Siren   │
 │  • Groq Voice AI Doctor (Hands-Free Mic Consultation)  │
 └──────────────────────────┬─────────────────────────────┘
                            │ Real-Time S-Band Telemetry
                            │ & Roster Synchronization
                            ▼
 ┌────────────────────────────────────────────────────────┐
 │        📁 SHARED MEDICAL DATABASE (SQLite Engine)      │
 │  • Live Telemetry Bridge (telemetry_live)              │
 │  • Mission Groups Master Registry (mission_groups)     │
 │  • Multi-Expedition Astronaut Roster (astronaut_roster)│
 │  • Longitudinal Clinical Logs & Snapshots              │
 └──────────────────────────▲─────────────────────────────┘
                            │ Real-Time Ground Command
                            │ & Deployment Uplink
 ┌──────────────────────────┴─────────────────────────────┐
 │       🌍 NASA HOUSTON EARTH MISSION CONTROL CENTER     │
 │  • Live Spacecraft Telemetry & Ground Warning Banner   │
 │  • Multi-Expedition Crew Roster Administration (Admin) │
 │  • Create Groups, Add/Edit/Return/Deploy Astronauts    │
 │  • Text Groq AI Flight Surgeon & Expedition Reports    │
 │  • Multi-Expedition Historical Database Analytics      │
 └────────────────────────────────────────────────────────┘
```

---

## ⚡ 4. Comprehensive Feature Breakdown

### 🚀 Deep Space Station Client (`space_station/main.py`)
* **3D Holographic Neural AI Brain:** Real-time animated 3D neural topography visualizing central nervous stress, cognitive workload, and circadian alignment.
* **Contactless 3D Biometric Facial Mesh Scanner:** Uses OpenCV computer vision to detect micro-vascular facial blood flow (rPPG) and Eye Aspect Ratio (EAR) for Heart Rate, SpO₂, and fatigue tracking without invasive sticky electrodes or cables.
* **Groq AI Flight Surgeon:** Hands-free, two-way conversational voice doctor offering instant clinical guidance directly on the spacecraft.
* **Hardware Danger Alarm Siren:** Multi-harmonic synthesized spacecraft hazard siren that triggers automatically when biometric or environmental parameters breach NASA safety thresholds.
* **Flight Safety Protection:** Displays **ONLY the currently deployed mission crew**. Astronauts cannot tamper with or modify mission assignments from orbit.

### 🌍 NASA Houston Earth Mission Control (`earth_station/main.py`)
* **Ground Flight Director Hazard HUD:** Visual hazard indicators and ground alert chimes to immediately isolate and identify sick crew members in deep space.
* **Exclusive Multi-Expedition Crew Administration:** Centralized ground authority to enroll astronauts, customize physiological baselines, create expeditions (Expedition 71/72, Artemis III/IV), and deploy groups to space.
* **NASA Historical Case Matcher:** Matches live biometric anomalies against real NASA spaceflight incidents (Apollo 15 arrhythmia, Gemini IX-A metabolic spikes, Mir EO-23 hypercapnia) to provide historical countermeasures.
* **Automated Clinical Dossier Generator:** Compiles standardized medical evaluation reports for NASA longitudinal flight archives.

### 📱 Wireless Mobile IoT Sensor Remote (`/remote`)
* Allows crew and flight directors to simulate telemetry changes, vitals drops, and one-touch emergency drills straight from any smartphone on the local network.

---

## 🔬 Official NASA Datasets & Technical Standards Integrated

AstroMind directly integrates data and regulatory thresholds from official NASA resources:

| NASA Resource | Standard / Dataset / Source | Implementation in AstroMind |
| :--- | :--- | :--- |
| **[NASA Open Data Portal](https://data.nasa.gov/docs/legacy/Extra-vehicular_Activity_EVA_-_US_and_Russia/Extra-vehicular_Activity_EVA_-_US_and_Russia_rows.csv)** | Extra-vehicular Activity (EVA - US and Russia) | 383 historical spacewalk mission records to cross-reference EVA physiological workloads. |
| **[NASA Astronaut Historical Archive](https://raw.githubusercontent.com/rfordatascience/tidytuesday/master/data/2020/2020-07-14/astronauts.csv)** | NASA Open Data & Corlett Database | 1,280 official NASA astronaut flight logs for cumulative spaceflight hours and mission tracking. |
| **[NASA-STD-3001 Vol 2](https://standards.nasa.gov/standard/NASA/NASA-STD-3001-Vol-2)** | NASA Space Flight Human-System Standard | Spacecraft environmental safety limits (Cabin CO₂ SMAC levels, ambient temperature, radiation thresholds). |
| **[NASA LSDA](https://lsda.jsc.nasa.gov/)** | Life Sciences Data Archive | Astronaut physiological baseline data (microgravity heart rate drift, SpO₂ tolerances, and cognitive fatigue metrics). |
| **[NASA OSDR](https://osdr.nasa.gov/)** | Open Science Data Repository | Spaceflight clinical anomaly profiles and systemic microgravity health deconditioning protocols. |
| **[NASA Human Research Roadmap](https://humanresearchroadmap.nasa.gov/)** | Exploration Medical Capabilities (ExMC) | Autonomous clinical decision-making protocols designed for deep-space missions facing Earth communication latency. |

---

## 🛠️ 6. Technology Stack

* **Core Language:** Python 3.10+
* **User Interface:** CustomTkinter (Futuristic NASA Dark Mode HUD)
* **Computer Vision:** OpenCV, Haar Cascades, Remote Photoplethysmography (rPPG), 3D Topological Face Meshing
* **Edge Intelligence & LLM:** GroqCloud LPU Inference Engine (Qwen-3.8-27B & Whisper Speech-to-Text)
* **Audio & Acoustics:** Native multi-harmonic acoustic synthesis, `pyttsx3`, `sounddevice`
* **Local IoT & Telemetry:** Flask REST API, S-Band LAN sync bridge, SQLite3 multi-expedition database

---

## 🚀 7. Quick Start & Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/Shanto008SB/AstroMind.git
cd AstroMind
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Dual Mission Suite
Launch both stations side-by-side using the launcher menu:
```cmd
run_all.bat
```
*(Or launch individually via `run_space_station.bat` and `run_earth_control.bat`)*

### Step 4: Open Mobile Phone Remote (Optional)
Connect your smartphone to the same local Wi-Fi and open:
```
http://<YOUR_LOCAL_IP>:5000/remote
```

---

## 👨‍🚀 8. Pitch & Demonstration Flow for Judges

1. **Launch Both Stations Side-by-Side (`run_all.bat` -> Option 3):**
   - Point out the **Deep Space Station** on one side and **NASA Houston Mission Control** on the other side.
2. **Demonstrate Autonomous Space Edge AI:**
   - Click **`🔍 INSTANT BIOMETRIC SCAN`** on the Space Station: show the 3D Biometric Facial Mesh Mask contouring the face with vertical topology lines, ocular tracking reticles, and sweeping laser beam.
   - Click **`🎙️ VOICE CONVERSATION (MIC)`** to talk hands-free to the Groq AI Flight Surgeon.
3. **Simulate a Deep Space Emergency from Phone or Space Station:**
   - Click **`🚨 SIMULATE DRILL`** or drop SpO₂ to 88% on your phone.
   - The continuous multi-harmonic spacecraft danger alarm siren sounds in space, the compromised astronaut's photo replaces the 3D brain, and the AI Doctor speaks the oxygen protocol.
   - **Look at the Earth Mission Control screen:** Earth immediately turns glowing red, sounds the ground flight director alert chime, and displays the astronaut's emergency telemetry!
4. **Demonstrate Earth-Side Multi-Expedition Crew Administration:**
   - In Earth Mission Control, switch from *Expedition 72* to *Expedition 71 (Historical)* to show how past returned astronauts' health logs remain archived.
   - Click **`➕ ADD ASTRONAUT`** or **`🚀 DEPLOY GROUP TO SPACE`**: show how the Space Station software immediately reflects the new crew roster without restarting!

---

