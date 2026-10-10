"""
AstroMind: Multi-Modal Anomaly Detection Engine
Evaluates vital statistics + cabin telemetry to predict:
- Hypoxia
- Bradycardia / Tachycardia / Cardiac Arrhythmia
- Cognitive Fatigue & Severe Sleep Deprivation
- Heat/Dehydration Stress & Radiation Exposure
Calculates Daily Crew Readiness Score (0 - 100%)
"""

from typing import Dict, Any, List

class AnomalyDetector:
    def __init__(self):
        # Clinical Thresholds for Astronauts in Microgravity
        self.THRESHOLDS = {
            "hr_min": 50,       # Below 50 BPM = Bradycardia risk
            "hr_max": 115,      # Above 115 BPM resting = Tachycardia / High Stress
            "spo2_min": 94.0,   # Below 94% = Mild Hypoxia, Below 90% = Severe Hypoxia
            "spo2_crit": 90.0,
            "hrv_min": 25.0,    # Below 25 ms = High Sympathetic Stress / Autonomic Exhaustion
            "fatigue_max": 65,  # Above 65% = High Cognitive Fatigue
            "co2_max": 0.65,    # Cabin CO2 > 0.65% triggers astronaut headaches / cognitive slowdown
            "radiation_max": 0.40 # mSv/h Solar particle event warning
        }

    def evaluate_crew_member(self, vitals: Dict[str, Any], cabin: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes astronaut vitals and cabin environment to output:
        - alert_level: 'NOMINAL' | 'CAUTION' | 'CRITICAL'
        - readiness_score: 0 to 100%
        - is_emergency: bool
        - detected_anomalies: list of string descriptions
        - emergency_message: clinical directive
        - suggestions: list of actionable recommendations
        """
        hr = vitals.get("heart_rate", 72)
        spo2 = vitals.get("spo2", 98.0)
        hrv = vitals.get("hrv", 55.0)
        fatigue = vitals.get("fatigue_level", 20)
        blink_rate = vitals.get("blink_rate", 14)
        
        co2 = cabin.get("co2_percent", 0.32)
        temp = cabin.get("temp_c", 21.5)
        radiation = cabin.get("radiation_msv", 0.18)

        anomalies: List[str] = []
        suggestions: List[str] = []
        is_emergency = False
        emergency_message = ""

        # 1. Hypoxia Detection
        if spo2 < self.THRESHOLDS["spo2_crit"]:
            is_emergency = True
            anomalies.append(f"CRITICAL HYPOXIA DETECTED: Blood oxygen dropped to {spo2:.1f}%")
            emergency_message = f"Immediate Oxygen Anomaly! Crew SpO2 is {spo2:.1f}%. Engage emergency O2 mask immediately and check suit pressure seal!"
            suggestions.append("Switch to Secondary Oxygen Reserve loop immediately.")
        elif spo2 < self.THRESHOLDS["spo2_min"]:
            anomalies.append(f"Mild Oxygen Depletion: SpO2 at {spo2:.1f}%")
            suggestions.append("Verify cabin air circulation scrubbers and reduce physical exertion.")

        # 2. Cardiac Anomalies
        if hr < self.THRESHOLDS["hr_min"]:
            is_emergency = True
            anomalies.append(f"ACUTE BRADYCARDIA DETECTED: Heart rate dropped to {hr} BPM")
            if not emergency_message:
                emergency_message = f"Cardiac Warning! Abnormal bradycardia detected ({hr} BPM). Immediate vital telemetry stabilization required."
            suggestions.append("Administer intravenous saline or electrolyte fluids. Recline to combat cephalad fluid shift.")
        elif hr > self.THRESHOLDS["hr_max"]:
            anomalies.append(f"Tachycardia / Elevated Cardiovascular Strain: {hr} BPM")
            suggestions.append("Immediate 15-minute rest protocol. Hydrate with 400ml electrolyte pouch.")

        # 3. Autonomic Tone / HRV Analysis
        if hrv < self.THRESHOLDS["hrv_min"]:
            anomalies.append(f"Autonomic Exhaustion: HRV reduced to {hrv:.1f} ms (Sympathetic Overdrive)")
            suggestions.append("Perform 5 minutes of guided 4-7-8 resonance breathing.")

        # 4. Cognitive Burnout & Fatigue
        if fatigue > 70 or blink_rate < 7:
            anomalies.append(f"Severe Sleep Deprivation / Cognitive Burnout ({fatigue}% fatigue index)")
            suggestions.append("Restrict critical robotic and manual docking tasks. Prescribe 90-minute circadian restorative nap.")
        elif fatigue > 50:
            suggestions.append("Schedule 30-minute cognitive decompression break before upcoming mission shift.")

        # 5. Environmental Cabin Correlation
        if co2 > self.THRESHOLDS["co2_max"]:
            anomalies.append(f"Cabin CO2 Spike: {co2:.2f}% (High risk of hypercapnia and headache)")
            suggestions.append("Inspect Life Support CDRA (Carbon Dioxide Removal Assembly) beds.")

        if radiation > self.THRESHOLDS["radiation_max"]:
            anomalies.append(f"Elevated Radiation Flux: {radiation:.2f} mSv/h (Solar Event)")
            suggestions.append("Crew muster to storm shelter (radiation-shielded crew quarters).")

        # Calculate Crew Readiness Score (0-100)
        # Base 100 with deductions
        score = 100.0

        # HR penalties
        if hr < 50: score -= 35
        elif hr > 115: score -= 25
        elif hr > 95: score -= 10

        # SpO2 penalties
        if spo2 < 90: score -= 45
        elif spo2 < 94: score -= 20
        elif spo2 < 96: score -= 8

        # HRV penalties
        if hrv < 25: score -= 20
        elif hrv < 40: score -= 10

        # Fatigue penalties
        score -= (fatigue * 0.35)

        # Environmental penalties
        if co2 > 0.65: score -= 15
        if radiation > 0.40: score -= 15

        readiness_score = max(5, min(100, int(score)))

        # Determine Alert Level
        if is_emergency:
            alert_level = "CRITICAL"
        elif len(anomalies) > 0 or readiness_score < 65:
            alert_level = "CAUTION"
        else:
            alert_level = "NOMINAL"
            suggestions.append("Maintain baseline hydration: Drink 300ml electrolyte pouch.")
            suggestions.append("Scheduled EVA fitness: 45 min cycle ergometer workout.")
            suggestions.append("Circadian lighting synchronized to Earth GMT.")

        # Readiness classification
        if readiness_score >= 80:
            readiness_status = "FIT FOR EVA / SPACEWALK"
            readiness_class = "optimal"
        elif readiness_score >= 60:
            readiness_status = "QUALIFIED FOR LIGHT CABIN DUTY"
            readiness_class = "moderate"
        else:
            readiness_status = "UNFIT FOR DUTY - MEDICAL REST ADVISED"
            readiness_class = "critical"

        return {
            "alert_level": alert_level,
            "is_emergency": is_emergency,
            "readiness_score": readiness_score,
            "readiness_status": readiness_status,
            "readiness_class": readiness_class,
            "anomalies": anomalies,
            "emergency_message": emergency_message,
            "suggestions": suggestions[:4]  # Top 4 suggestions
        }
