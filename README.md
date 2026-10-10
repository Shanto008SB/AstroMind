# 🚀 AstroMind: Autonomous Deep Space & Earth Mission Control Suite

**Challenge Topic:** Create Health Monitoring Software for Astronauts on Space Missions  
**Event:** NASA Space Apps Challenge  
**Architecture:** Dual-Station Mission Suite (Deep Space Station Edge Client + NASA Houston Earth Mission Control)  
**Core Technologies:** 100% Pure Python Desktop GUI (CustomTkinter) • GroqCloud LPU Flight Surgeon AI • OpenCV 3D Biometric Facial Mesh Scanner • Hardware Audio Danger Alarm Siren • Multi-Expedition SQLite Medical Archive • Mobile Phone Wireless IoT Sensor Bridge

---

## 🌟 Executive Summary

**AstroMind** is a comprehensive dual-station health monitoring and medical management architecture designed for deep-space human exploration (ISS, Artemis Lunar Gateway, and Mars Transit missions):

1. **🚀 Deep Space Station Client (`space_station_app.py` / `desktop_app.py`):**
   - Autonomous, offline-first edge AI running aboard the spacecraft.
   - Operates independent of Earth communication delays (5–20 minutes light-time lag).
   - Features 3D Holographic Neural AI Brain, 24/7 background biometric rPPG computer vision, 3D Biometric Facial Mesh Scanner, continuous spacecraft danger alarm siren, and two-way voice Groq AI Flight Surgeon.
   - **Flight Safety Protection:** Displays **ONLY the currently deployed mission crew**. Space crew cannot tamper with or modify the mission roster from orbit.

2. **🌍 NASA Houston Earth Mission Control (`earth_control_app.py`):**
   - Ground station monitoring console for NASA flight directors and ground flight surgeons on Earth.
   - **Real-Time Deep Space Telemetry Link:** Live mirror of deployed crew heart rate, SpO2, HRV, fatigue, cabin CO2, temperature, and radiation.
   - **Ground Hazard Alarm:** Live warning indicators, flight surgeon chimes, and critical telemetry alerts.
   - **Exclusive Multi-Expedition Crew Roster Administration:**
     - Add new astronauts to mission groups.
     - Edit astronaut profiles, baselines, and flight credentials.
     - Create new expeditions (e.g., *Expedition 72*, *Expedition 71 Historical*, *Artemis III*, *Artemis IV*).
     - **Deploy Group to Space:** Earth commands which mission group is deployed in Deep Space — immediately synchronizing the Space Station software!
     - **Mark Returned to Earth / Archive:** Archive returned astronauts while permanently preserving all historical medical telemetry for longitudinal research.
   - **Clinical AI & Expedition Reports:** Text-based consultation with Groq LPU Flight Surgeon and formal clinical evaluation report generator.
   - **Telemetry Focused:** Zero camera or face recognition overhead on Earth ground workstations.

---

## 🛰️ Architecture & Synchronization Bridge

```
 ┌────────────────────────────────────────────────────────┐
 │        🚀 DEEP SPACE STATION CLIENT (Spacecraft)       │
 │  • Displays Deployed Crew Group (Read-Only Roster)    │
 │  • 3D Neural AI Brain & 3D Biometric Face Mesh Scanner │
 │  • Continuous NASA Emergency Danger Siren              │
 │  • Groq Voice AI Doctor (Mic & Audio Guidance)         │
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
 │  • Live Spacecraft Telemetry & Vital Warning Banner    │
 │  • Multi-Expedition Crew Roster Administration (Admin) │
 │  • Create Groups, Add/Edit/Return/Deploy Astronauts    │
 │  • Text Groq AI Flight Surgeon & Expedition Reports    │
 │  • Multi-Expedition Historical Database Analytics      │
 └────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start & Launchers

### Option 1: Dual Mission Suite Menu (Recommended)
Double-click:
```cmd
run_all.bat
```
Choose whether to launch the Space Station Client, Earth Mission Control, or **both side-by-side**!

### Option 2: Individual Launchers
- **Deep Space Station Client:**
  ```cmd
  run_space_station.bat
  ```
  *(or `python space_station_app.py`)*

- **NASA Houston Earth Mission Control:**
  ```cmd
  run_earth_control.bat
  ```
  *(or `python earth_control_app.py`)*

### Option 3: Wireless Mobile Phone IoT Remote
Open any mobile browser on the same local Wi-Fi:
```
http://<YOUR_LOCAL_IP>:5000/remote
```
Controls heart rate, SpO2, fatigue, cabin CO2, and one-touch emergency drills from your smartphone!

---

## 👨‍🚀 How to Pitch to NASA Space Apps Judges

1. **Launch Both Stations Side-by-Side (`run_all.bat` -> Option 3):**
   - Point out the **Deep Space Station** on one side and **NASA Houston Mission Control** on the other side.
2. **Demonstrate Autonomous Space Edge AI:**
   - Click **`🔍 INSTANT BIOMETRIC SCAN`** on the Space Station: show the 3D Biometric Facial Mesh Mask contouring the face with vertical topology lines, ocular tracking reticles, and sweeping laser beam.
   - Click **`🎙️ VOICE CONVERSATION (MIC)`** to talk to the Groq AI Flight Surgeon.
3. **Simulate a Deep Space Emergency from Phone or Space Station:**
   - Click **`🚨 SIMULATE DRILL`** or drop SpO2 to 88% on your phone.
   - The continuous multi-harmonic spacecraft danger alarm siren sounds in space, the compromised astronaut's photo replaces the 3D brain, and the AI Doctor speaks the oxygen protocol.
   - **Look at the Earth Mission Control screen:** Earth immediately turns glowing red, sounds the ground flight director alert chime, and displays the astronaut's emergency telemetry!
4. **Demonstrate Earth-Side Multi-Expedition Crew Administration:**
   - In Earth Mission Control, switch from *Expedition 72* to *Expedition 71 (Historical)* to show how past returned astronauts' health logs remain archived.
   - Click **`➕ ADD ASTRONAUT`** or **`🚀 DEPLOY GROUP TO SPACE`**: show how the Space Station software immediately reflects the new crew roster without restarting!
