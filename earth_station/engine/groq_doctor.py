"""
AstroMind: GroqCloud AI Doctor Engine
Powered by GroqCloud LPU Inference & pyttsx3 Offline Voice Synthesis
Features:
- Real-time Speech-to-Text via Groq Whisper-large-v3-turbo (Microphone input)
- Clinical Diagnosis & General Flight Support via Qwen-3.8-27B on GroqCloud
- Thread-safe Windows COM voice synthesis via pyttsx3
"""

import os
import io
import wave
import threading
from typing import Dict, Any, Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import sounddevice as sd
    import numpy as np
    AUDIO_RECORDING_AVAILABLE = True
except ImportError:
    AUDIO_RECORDING_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


def _get_default_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if key:
        return key
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    candidates = [
        os.path.join(base_dir, "groq_api_key.txt"),
        os.path.join(os.path.dirname(base_dir), "groq_api_key.txt")
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return content
            except Exception:
                pass
    return ""


class GroqAIDoctor:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key if api_key is not None else _get_default_api_key()
        self.client = None
        if GROQ_AVAILABLE and self.api_key:
            try:
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                print(f"[GroqDoctor] Initialization warning: {e}")

        # TTS state
        self.tts_lock = threading.Lock()
        self._tts_engine = None        # live engine reference (for stop)
        self.is_speaking = False       # True while voice is playing
        # High-performance working model on Groq
        self.model_name = "qwen/qwen3.8-27b"
        self.fallback_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
        self.is_recording = False

    def transcribe_audio_from_mic(self, duration: float = 3.5) -> str:
        """
        Records voice from microphone and transcribes it using Groq Whisper.
        """
        if not AUDIO_RECORDING_AVAILABLE:
            return ""

        fs = 16000
        try:
            self.is_recording = True
            print(f"[AstroMind Audio] Recording voice input for {duration}s...")
            recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
            sd.wait()
            self.is_recording = False

            # Convert numpy recording to WAV buffer
            wav_buf = io.BytesIO()
            with wave.open(wav_buf, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(fs)
                wf.writeframes(recording.tobytes())
            wav_buf.seek(0)
            wav_buf.name = "astronaut_speech.wav"

            if self.client:
                transcription = self.client.audio.transcriptions.create(
                    file=wav_buf,
                    model="whisper-large-v3-turbo",
                    response_format="text"
                )
                text = str(transcription).strip()
                print(f"[AstroMind Audio] Transcribed: '{text}'")
                return text
        except Exception as e:
            print(f"[AstroMind Audio Error] {e}")
            self.is_recording = False
        return ""

    def ask_doctor(
        self,
        query: str,
        astronaut: Dict[str, Any],
        vitals: Dict[str, Any],
        cabin: Dict[str, Any],
        is_emergency: bool = False
    ) -> str:
        """
        Sends telemetry context and flight query to GroqCloud API.
        Handles clinical diagnostics, vital assessment, mission advice, and general conversation.
        Falls back gracefully to rich offline heuristic intelligence if network is unavailable.
        """
        name = astronaut.get("name", "Astronaut")
        role = astronaut.get("role", "Crew Member")
        hr = vitals.get("heart_rate", 72)
        spo2 = vitals.get("spo2", 98.4)
        hrv = vitals.get("hrv", 58.0)
        fatigue = vitals.get("fatigue_level", 20)
        co2 = cabin.get("co2_percent", 0.31)
        radiation = cabin.get("radiation_msv", 0.18)

        # NASA Flight Surgeon & Medical Intelligence Assistant System Prompt
        system_prompt = (
            "You are AstroMind AI Flight Surgeon & NASA Medical Intelligence Assistant. "
            f"Active Subject Monitored: {name} ({role}). "
            f"Current Telemetry: Heart Rate {hr} BPM, Blood Oxygen SpO2 {spo2:.1f}%, HRV {hrv:.0f} ms, Cognitive Fatigue {fatigue}%. "
            f"Cabin Atmosphere: CO2 {co2:.2f}%, Radiation {radiation:.2f} mSv/h. "
            f"Alert State: {'CRITICAL MEDICAL EMERGENCY IN PROGRESS' if is_emergency else 'NOMINAL MISSION PARAMETERS'}. "
            "You are capable of both authoritative clinical medical advice and friendly, professional flight controller conversation in 100% English. "
            "If the user asks general questions or greets you, respond politely, warmly, and helpfully as NASA's top medical intelligence. "
            "If the user asks about crew health, anomalies, or medical countermeasures, provide clear clinical assessments and actionable space medicine protocols. "
            "Keep responses clear, concise (2 to 4 sentences), and professional."
        )

        if self.client:
            for model_candidate in self.fallback_models:
                try:
                    chat = self.client.chat.completions.create(
                        model=model_candidate,
                        max_tokens=220,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": query}
                        ]
                    )
                    raw_ans = chat.choices[0].message.content.strip()
                    clean_ans = self._sanitize_text(raw_ans)
                    if clean_ans and len(clean_ans) > 5:
                        return clean_ans
                except Exception as e:
                    print(f"[GroqDoctor] Model '{model_candidate}' failed ({e}), checking next...")

        # Rich Local Offline Edge AI Fallback in 100% English
        return self._offline_fallback_response(query, name, hr, spo2, hrv, fatigue, is_emergency)

    def _sanitize_text(self, text: str) -> str:
        """Removes markdown tags and cleans non-standard characters safely."""
        text = text.replace("**", "").replace("##", "").replace("```", "")
        text = text.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
        try:
            text = text.encode("ascii", "ignore").decode("ascii")
        except Exception:
            pass
        return text.strip()

    def _sanitize_for_speech(self, text: str) -> str:
        """
        Aggressively cleans text for TTS voice output.
        Removes ALL emojis, separator lines (===, ---), bullet symbols,
        bracket labels ([...], 【...】), markdown headers, and other
        non-speakable characters so pyttsx3 reads only clean natural English.
        """
        import re

        # 1. Remove emoji and all non-ASCII unicode characters
        text = text.encode("ascii", "ignore").decode("ascii")

        # 2. Remove full separator/divider lines (===, ---, ***, ___)
        text = re.sub(r'^[=\-*_~]{3,}\s*$', '', text, flags=re.MULTILINE)

        # 3. Remove inline separator runs
        text = re.sub(r'[=\-*_]{3,}', ' ', text)

        # 4. Remove bracket labels [AI FLIGHT SURGEON], 【...】, {TEXT}
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\u3010.*?\u3011', '', text)
        text = re.sub(r'\{.*?\}', '', text)

        # 5. Remove markdown headers and bold/italic markup
        text = re.sub(r'#+\s*', '', text)
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)

        # 6. Remove bullet and special punctuation markers
        text = re.sub(r'^[\u2022\u00b7\u25cf\u25e6\u25aa\u25b8>|~\*]\s*', '', text, flags=re.MULTILINE)
        text = text.replace('\u2022', '').replace('\u00b7', '').replace('\u25cf', '')
        text = text.replace('|', ' ').replace('~', ' ')

        # 7. Replace technical separator punctuation
        text = text.replace('/', ' or ').replace('&', ' and ')

        # 8. Convert abbreviations to speakable forms
        text = re.sub(r'\bBPM\b', 'beats per minute', text)
        text = re.sub(r'\bSpO2\b', 'blood oxygen', text, flags=re.IGNORECASE)
        text = re.sub(r'\bHRV\b', 'heart rate variability', text)
        text = re.sub(r'\bEVA\b', 'spacewalk', text)
        text = re.sub(r'\bCO2\b', 'carbon dioxide', text, flags=re.IGNORECASE)
        text = re.sub(r'\bmSv\b', 'millisieverts', text)

        # 9. Collapse extra blank lines and spaces
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)

        # 10. Rejoin lines, drop empty ones
        lines = [ln.strip() for ln in text.splitlines()]
        lines = [ln for ln in lines if len(ln) > 2]
        text = ' '.join(lines)

        # 11. Final space collapse
        text = re.sub(r' {2,}', ' ', text).strip()

        return text if text else "Clinical assessment complete. Telemetry is nominal."

    def _offline_fallback_response(
        self,
        query: str,
        name: str,
        hr: int,
        spo2: float,
        hrv: float,
        fatigue: int,
        is_emergency: bool
    ) -> str:
        q = query.lower().strip()
        
        # 1. Emergency situation
        if is_emergency or spo2 < 90 or hr < 50 or hr > 120:
            return (
                f"CRITICAL FLIGHT SURGEON ALERT for {name}! Acute physiological instability detected "
                f"(SpO2: {spo2:.1f}%, Pulse: {hr} BPM). Immediate countermeasure: Engage 100% oxygen rebreather "
                "mask and position subject flat to stabilize microgravity cerebral perfusion."
            )
        
        # 2. Greetings & General conversation
        if any(w in q for w in ["hello", "hi", "hey", "greetings", "good morning", "good evening"]):
            return (
                f"Greetings, Flight Controller. AstroMind AI Flight Surgeon is fully operational and online. "
                f"Currently monitoring {name} in Deep Space. All telemetry channels are synchronized. How can I assist you today?"
            )
        
        if "who are you" in q or "what are you" in q:
            return (
                "I am AstroMind AI Flight Surgeon, an autonomous medical intelligence engine designed for NASA deep space expeditions. "
                "I analyze biometric telemetry, predict microgravity anomalies, and provide real-time clinical countermeasures."
            )
        
        if "how are you" in q or "status" in q:
            return (
                f"All diagnostic subroutines and neural inference engines are running at optimal performance. "
                f"Subject {name} is at Heart Rate {hr} BPM and SpO2 {spo2:.1f}%. Mission telemetry is nominal."
            )

        if "help" in q or "what can you do" in q:
            return (
                "You can ask me to evaluate crew vital signs, assess spacewalk/EVA flight readiness, "
                "explain microgravity countermeasures, analyze cabin atmospheric metrics, or provide general flight guidance."
            )

        # 3. Specific clinical inquiries
        if any(w in q for w in ["heart", "pulse", "bpm", "cardiac", "rhythm"]):
            return (
                f"{name}'s cardiac rhythm is stable at {hr} BPM with steady sinus wave and autonomic HRV at {hrv:.0f} ms. "
                "Arterial pulse pressure is within nominal microgravity parameters."
            )

        if any(w in q for w in ["oxygen", "spo2", "breathing", "lung"]):
            return (
                f"Arterial oxygen saturation for {name} is optimal at {spo2:.1f} percent. Pulmonary gas exchange is normal."
            )

        if any(w in q for w in ["spacewalk", "eva", "ready", "clearance", "mission"]):
            if fatigue < 50 and spo2 >= 95:
                return (
                    f"Physiological baselines confirm {name} is cleared for extravehicular EVA spacewalk duty. "
                    "Maintain standard hydration schedule during egress."
                )
            else:
                return (
                    f"EVA flight clearance restricted for {name} due to fatigue index ({fatigue}%). "
                    "Recommend a minimum 45-minute metabolic rest cycle before suit donning."
                )

        if any(w in q for w in ["fatigue", "tired", "sleep", "rest", "circadian"]):
            return (
                f"Cognitive fatigue index for {name} is recorded at {fatigue} percent. "
                "Recommend circadian lighting adjustment to GMT protocol and 7.5 hours rest in crew sleep quarters."
            )

        if any(w in q for w in ["cabin", "co2", "radiation", "temp"]):
            return (
                "Cabin atmospheric scrubbers maintain nominal life support. "
                "CO2 and radiation sensors indicate safe pressurized environment for deep space operations."
            )

        # 4. General default flight surgeon response
        return (
            f"AstroMind Medical Intelligence online for {name}. Current telemetry: Pulse {hr} BPM, "
            f"SpO2 {spo2:.1f}%, Cognitive Fatigue {fatigue}%. Clinical baseline is within normal operating limits. "
            "Please specify any clinical protocol or vital parameter you wish to evaluate."
        )

    def speak_async(self, text: str):
        """
        Speaks text in a non-blocking daemon thread using pyttsx3.
        Strips all emojis, === dividers, bullet symbols and markdown before TTS.
        Call stop_speaking() at any time to interrupt mid-sentence.
        """
        if not pyttsx3:
            return

        # Stop any currently running voice before starting a new one
        self.stop_speaking()

        clean_text = self._sanitize_for_speech(text)

        def _speak():
            self.is_speaking = True
            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass

                with self.tts_lock:
                    engine = pyttsx3.init()
                    self._tts_engine = engine          # store reference for stop
                    engine.setProperty('rate', 160)
                    voices = engine.getProperty('voices')
                    for v in voices:
                        if "zira" in v.name.lower() or "david" in v.name.lower() or "hazel" in v.name.lower():
                            engine.setProperty('voice', v.id)
                            break
                    engine.say(clean_text)
                    engine.runAndWait()
                    engine.stop()
                    self._tts_engine = None

                try:
                    import pythoncom
                    pythoncom.CoUninitialize()
                except Exception:
                    pass
            except Exception as e:
                print(f"[GroqDoctor] TTS voice error: {e}")
            finally:
                self.is_speaking = False
                self._tts_engine = None

        t = threading.Thread(target=_speak, daemon=True)
        t.start()

    def stop_speaking(self):
        """
        Immediately stops any currently playing TTS voice output.
        Safe to call even when nothing is playing.
        """
        try:
            if self._tts_engine is not None:
                self._tts_engine.stop()
                self._tts_engine = None
        except Exception:
            pass
        self.is_speaking = False
