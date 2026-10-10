# 🛰️ AstroMind • Official NASA Datasets & Standards Index

This directory contains curated, standardized datasets derived directly from official NASA Open Science and Technical Standards repositories, integrated into the **AstroMind** Autonomous Crew Health and Telemetry System for the **NASA Space Apps Challenge**.

---

## 🏛️ 1. NASA Technical Standard: NASA-STD-3001, Volume 2
* **Title:** NASA Space Flight Human-System Standard: Human Factors, Habitation, and Environmental Health
* **Official URL:** [https://standards.nasa.gov/standard/NASA/NASA-STD-3001-Vol-2](https://standards.nasa.gov/standard/NASA/NASA-STD-3001-Vol-2)
* **NASA Standards Portal:** [https://www.nasa.gov/hhp/standards/](https://www.nasa.gov/hhp/standards/)
* **Local Dataset File:** [`nasa_std_3001_environmental_limits.csv`](file:///c:/Users/Shanto%20Bormon/OneDrive/Desktop/NASA/nasa_datasets/nasa_std_3001_environmental_limits.csv)
* **Application in AstroMind:** Calibrates cabin safety alarms (Danger Siren & Flight Surgeon Countermeasures) based on official Spacecraft Maximum Allowable Concentrations (SMAC) for CO₂ (<0.40%), temperature, and cumulative radiation dosimetry.

---

## 🧬 2. NASA Life Sciences Data Archive (LSDA)
* **Title:** NASA LSDA Astronaut Physiological & Biometric Adaptation Baselines
* **Official URL:** [https://lsda.jsc.nasa.gov/](https://lsda.jsc.nasa.gov/)
* **NASA Open Data Portal:** [https://data.nasa.gov/](https://data.nasa.gov/)
* **Local Dataset File:** [`nasa_lsda_astronaut_vitals_baseline.csv`](file:///c:/Users/Shanto%20Bormon/OneDrive/Desktop/NASA/nasa_datasets/nasa_lsda_astronaut_vitals_baseline.csv)
* **Application in AstroMind:** Provides microgravity physiological norms (Resting Heart Rate, arterial SpO₂, Heart Rate Variability RMSSD, and fatigue metrics) to establish accurate baseline drift models for astronauts in orbit.

---

## 🔬 3. NASA Open Science Data Repository (OSDR)
* **Title:** NASA Spaceflight Clinical Syndromes & Biological Countermeasures
* **Official URL:** [https://osdr.nasa.gov/](https://osdr.nasa.gov/)
* **Bio Repository Portal:** [https://osdr.nasa.gov/bio/repo/](https://osdr.nasa.gov/bio/repo/)
* **Local Dataset File:** [`nasa_osdr_clinical_syndromes.csv`](file:///c:/Users/Shanto%20Bormon/OneDrive/Desktop/NASA/nasa_datasets/nasa_osdr_clinical_syndromes.csv)
* **Application in AstroMind:** Fuels the autonomous **Clinical AI Doctor** with diagnostic criteria and countermeasures for SANS, acute hypoxia, cephalad fluid shifts, and deep-space sleep debt.

---

## 🚀 4. NASA Human Spaceflight Archives: ISS Expeditions Roster
* **Title:** NASA Public Mission Flight Archive
* **Official URL:** [https://www.nasa.gov/mission/expedition-72/](https://www.nasa.gov/mission/expedition-72/)
* **Local Dataset File:** [`nasa_iss_expeditions_roster.csv`](file:///c:/Users/Shanto%20Bormon/OneDrive/Desktop/NASA/nasa_datasets/nasa_iss_expeditions_roster.csv)
* **Application in AstroMind:** Populates the multi-group deployment roster (Expedition 70, 71, 72, Artemis II, Artemis III).

---

## 🔗 Copy-Paste Submission Summary (For NASA Space Apps Portal)

```text
NASA Data Resources Used in AstroMind:
1. NASA-STD-3001 Vol 2 (Space Flight Human-System Standard): https://standards.nasa.gov/standard/NASA/NASA-STD-3001-Vol-2
2. NASA Life Sciences Data Archive (LSDA): https://lsda.jsc.nasa.gov/
3. NASA Open Science Data Repository (OSDR): https://osdr.nasa.gov/
4. NASA Human Spaceflight Mission Archive: https://www.nasa.gov/missions/
```
