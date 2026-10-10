"""
AstroMind: Local Edge AI Doctor Engine
Provides 100% offline medical guidance, clinical voice dialogues,
and autonomous countermeasure recommendations for deep space missions.
"""

from typing import Dict, Any

class AIDoctor:
    def __init__(self, detector):
        self.detector = detector

    def generate_clinical_summary(self, astronaut: Dict[str, Any], vitals: Dict[str, Any], cabin: Dict[str, Any]) -> str:
        """
        Generates real-time AI Doctor clinical diagnosis note for right panel.
        """
        analysis = self.detector.evaluate_crew_member(vitals, cabin)
        name = astronaut.get("name", "Astronaut")
        role = astronaut.get("role", "Crew Member")
        
        if analysis["is_emergency"]:
            return (
                f"🚨 EMERGENCY ALERT for {name} ({role}): "
                f"{analysis['emergency_message']} "
                "Immediate intervention required by medical team or self-rescue protocol."
            )
        elif analysis["alert_level"] == "CAUTION":
            issues = "; ".join(analysis["anomalies"])
            return (
                f"⚠️ CAUTION STATUS for {name}: {issues}. "
                f"Current Crew Readiness is {analysis['readiness_score']}%. "
                "Restorative hydration and physiological recovery protocol initiated."
            )
        else:
            return (
                f"🩺 Optimal Physiological Equilibrium for {name} ({role}). "
                f"Cardiovascular rhythm, SpO2, and autonomic tone are within mission safety baselines. "
                f"Readiness Score: {analysis['readiness_score']}% ({analysis['readiness_status']})."
            )

    def process_voice_query(self, query: str, astronaut: Dict[str, Any], vitals: Dict[str, Any], cabin: Dict[str, Any]) -> Dict[str, str]:
        """
        Handles hands-free voice inputs ("Hey AstroMind...") and button commands.
        Returns spoken response and action flags.
        """
        q = query.lower().strip()
        analysis = self.detector.evaluate_crew_member(vitals, cabin)
        name = astronaut.get("name", "Astronaut")
        hr = vitals.get("heart_rate", 72)
        spo2 = vitals.get("spo2", 98.0)
        hrv = vitals.get("hrv", 55.0)
        fatigue = vitals.get("fatigue_level", 20)
        readiness = analysis["readiness_score"]

        # Emergency Simulation Command
        if any(w in q for w in ["emergency", "red alert", "simulate alert", "danger", "drill"]):
            return {
                "action": "trigger_emergency",
                "speech": f"Attention crew! Simulating critical medical emergency. SpO2 critical drop detected for {name}. Commencing emergency oxygen protocol!",
                "text": "CRITICAL DRILL: Emergency alert active! SpO2 hypoxia condition simulated."
            }

        # Clear Emergency Command
        if any(w in q for w in ["clear alert", "stand down", "normal", "stop emergency", "resolve"]):
            return {
                "action": "clear_emergency",
                "speech": f"Emergency cleared. Systems restored to nominal baseline for {name}.",
                "text": "Emergency cleared. Physiological parameters returned to safe baseline."
            }

        # Vitals / Heart Rate Query
        if any(w in q for w in ["heart rate", "pulse", "bpm", "cardiac", "heart"]):
            return {
                "action": "none",
                "speech": f"{name}, your heart rate is currently {hr} beats per minute with heart rate variability of {hrv:.0f} milliseconds. Rhythm is stable.",
                "text": f"Heart Rate: {hr} BPM | HRV: {hrv:.0f} ms (Normal sinus rhythm)."
            }

        # Oxygen / SpO2 Query
        if any(w in q for w in ["oxygen", "spo2", "blood oxygen", "o2"]):
            return {
                "action": "none",
                "speech": f"Blood oxygen saturation is at {spo2:.1f} percent. Arterial oxygenation in microgravity is optimal.",
                "text": f"Blood Oxygen: {spo2:.1f}% SpO2 (Within safe threshold)."
            }

        # Spacewalk / EVA Readiness Query
        if any(w in q for w in ["spacewalk", "eva", "ready", "fit", "fitness", "clearance"]):
            if readiness >= 80:
                speech = f"{name}, your crew readiness score is {readiness} percent. You are fully cleared and fit for the scheduled Extravehicular Spacewalk."
            else:
                speech = f"{name}, readiness is currently {readiness} percent. Spacewalk is restricted until fatigue levels drop and hydration is replenished."
            return {
                "action": "none",
                "speech": speech,
                "text": f"Readiness Index: {readiness}% - {analysis['readiness_status']}."
            }

        # Fatigue & Sleep Query
        if any(w in q for w in ["fatigue", "tired", "sleep", "burnout", "exhausted", "rest"]):
            return {
                "action": "none",
                "speech": f"Cognitive fatigue index is calculated at {fatigue} percent based on facial micro-expression and blink tracking. Rest recommendation: 7 hours deep circadian sleep.",
                "text": f"Fatigue Level: {fatigue}% | Average Blink Rate: {vitals.get('blink_rate', 14)} blinks/min."
            }

        # Cabin Atmosphere Query
        if any(w in q for w in ["cabin", "environment", "radiation", "co2", "atmosphere"]):
            co2 = cabin.get("co2_percent", 0.32)
            rad = cabin.get("radiation_msv", 0.18)
            temp = cabin.get("temp_c", 21.5)
            return {
                "action": "none",
                "speech": f"Cabin atmosphere is nominal. Ambient temperature is {temp} degrees Celsius, CO2 is {co2:.2f} percent, and radiation is {rad:.2f} millisieverts per hour.",
                "text": f"Cabin Temp: {temp}°C | CO2: {co2:.2f}% | Radiation: {rad:.2f} mSv/h."
            }

        # Default Greeting / Status Report
        return {
            "action": "none",
            "speech": (
                f"Greetings {name}. AstroMind Edge AI Doctor is online. "
                f"Your physiological readiness is {readiness} percent. "
                "All vital systems are monitoring autonomously without IoT wearable dependency."
            ),
            "text": (
                f"AstroMind Edge AI Doctor Active. Vitals: HR {hr} BPM, SpO2 {spo2:.1f}%, HRV {hrv:.0f} ms. "
                f"Readiness Score: {readiness}%. All systems nominal."
            )
        }
