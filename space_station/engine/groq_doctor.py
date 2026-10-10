"""
AstroMind: GroqCloud AI Doctor Engine
Powered by GroqCloud LPU Inference & pyttsx3 Offline Voice Synthesis
Features:
- Real-time Speech-to-Text via Groq Whisper-large-v3-turbo (Microphone input)
- Autonomous Flight Surgeon clinical diagnosis via Qwen-3.8-27B on GroqCloud
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
    # Try searching for groq_api_key.txt in project directories
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
        self.model_name = "qwen/qwen3.8-27b"
        self.fallback_models = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b"]
        self.is_recording = False

    def transcribe_audio_from_mic(self, duration: float = 3.5) -> str:
        """
        Records voice from astronaut microphone and transcribes it using Groq Whisper.
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
        Sends telemetry context and astronaut query to GroqCloud API.
        Falls back to local edge heuristics if network or quota issue occurs.
        """
        name = astronaut.get("name", "Astronaut")
        role = astronaut.get("role", "Crew Member")
        hr = vitals.get("heart_rate", 72)
        spo2 = vitals.get("spo2", 98.4)
        hrv = vitals.get("hrv", 58.0)
        fatigue = vitals.get("fatigue_level", 20)
        co2 = cabin.get("co2_percent", 0.31)
        radiation = cabin.get("radiation_msv", 0.18)

        # NASA Flight Surgeon Context Prompt
        system_prompt = (
            "You are AstroMind AI Flight Surgeon, an autonomous onboard space medical intelligence for NASA deep space missions. "
            f"Active Subject: {name} ({role}). "
            f"Current Physiological Telemetry: Heart Rate {hr} BPM, Blood Oxygen SpO2 {spo2:.1f}%, HRV {hrv:.0f} ms, Cognitive Fatigue {fatigue}%. "
            f"Cabin Atmosphere: CO2 {co2:.2f}%, Radiation {radiation:.2f} mSv/h. "
            f"Mission Alert Status: {'CRITICAL MEDICAL EMERGENCY ACTIVE' if is_emergency else 'NOMINAL MISSION PARAMETERS'}. "
            "Respond directly as an authoritative, calm NASA flight surgeon in 100% English. "
            "If user greets or asks general questions, answer professionally and politely. "
            "Provide immediate clinical assessment and microgravity countermeasures. "
            "Keep response concise: 2 to 3 sentences maximum so it can be spoken clearly over the spacecraft intercom."
        )

        if self.client:
            for model_candidate in self.fallback_models:
                try:
                    chat = self.client.chat.completions.create(
                        model=model_candidate,
                        max_tokens=180,
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
                    print(f"[GroqDoctor] Model '{model_candidate}' failed ({e}), trying fallback...")

        # Local Offline Edge AI Fallback in 100% English
        return self._offline_fallback_response(query, name, hr, spo2, hrv, fatigue, is_emergency)

    def _sanitize_text(self, text: str) -> str:
        """Removes markdown tags and cleans non-standard characters."""
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

        # 1. Remove emoji and all non-ASCII unicode characters (covers all emoji ranges)
        text = text.encode("ascii", "ignore").decode("ascii")

        # 2. Remove full separator/divider lines (===...  ---...  ***...  ___...)
        text = re.sub(r'^[=\-*_~]{3,}\s*$', '', text, flags=re.MULTILINE)

        # 3. Remove inline separator runs (===, ---, ***, ___) anywhere in text
        text = re.sub(r'[=\-*_]{3,}', ' ', text)

        # 4. Remove bracket labels like [AI FLIGHT SURGEON], [NASA HISTORICAL CASE MATCH],
        #    [HOW THAT HISTORICAL ASTRONAUT RECOVERED], 【...】, {TEXT}
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\u3010.*?\u3011', '', text)  # 【...】
        text = re.sub(r'\{.*?\}', '', text)

        # 5. Remove markdown headers (##, ###, **BOLD**, *italic*)
        text = re.sub(r'#+\s*', '', text)
        text = re.sub(r'\*{1,3}(.*?)\*{1,3}', r'\1', text)
        text = re.sub(r'`{1,3}(.*?)`{1,3}', r'\1', text)

        # 6. Remove bullet symbols and special punctuation markers
        #    (•, ·, ●, ◦, ▪, ▸, >, |, ~)
        text = re.sub(r'^[\u2022\u00b7\u25cf\u25e6\u25aa\u25b8>|~\*]\s*', '', text, flags=re.MULTILINE)
        text = text.replace('\u2022', '').replace('\u00b7', '').replace('\u25cf', '')
        text = text.replace('|', ' ').replace('~', ' ')

        # 7. Replace technical separator punctuation
        text = text.replace('/', ' or ').replace('&', ' and ')

        # 8. Convert abbreviation patterns to speakable forms
        text = re.sub(r'\bBPM\b', 'beats per minute', text)
        text = re.sub(r'\bSpO2\b', 'blood oxygen', text, flags=re.IGNORECASE)
        text = re.sub(r'\bHRV\b', 'heart rate variability', text)
        text = re.sub(r'\bEVA\b', 'spacewalk', text)
        text = re.sub(r'\bCO2\b', 'carbon dioxide', text, flags=re.IGNORECASE)
        text = re.sub(r'\bmSv\b', 'millisieverts', text)

        # 9. Collapse multiple blank lines and spaces into single breaks
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r'[ \t]{2,}', ' ', text)

        # 10. Strip leading/trailing whitespace per line, then rejoin
        lines = [ln.strip() for ln in text.splitlines()]
        # Drop lines that are now empty or only punctuation after cleaning
        lines = [ln for ln in lines if len(ln) > 2]
        text = ' '.join(lines)

        # 11. Final collapse of extra spaces
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
        q = query.lower()
        if is_emergency or spo2 < 90 or hr < 50 or hr > 120:
            return (
                f"Emergency physiological anomaly detected for {name}! Acute vital instability (SpO2: {spo2:.1f}%, Heart Rate: {hr} BPM). "
                "Engage supplemental oxygen loop immediately and assume horizontal position to stabilize arterial microgravity perfusion."
            )
        elif any(w in q for w in ["hello", "hi", "hey", "greetings"]):
            return (
                f"Greetings, {name}. AstroMind AI Flight Surgeon is online and monitoring your telemetry. How are you feeling right now?"
            )
        elif "heart" in q or "pulse" in q or "bpm" in q or "cardiac" in q:
            return (
                f"{name}, your cardiac rhythm is stable at {hr} BPM with steady sinus wave and autonomic HRV at {hrv:.0f} ms. "
                "Arterial pulse pressure is within mission safety limits."
            )
        elif "oxygen" in q or "spo2" in q:
            return (
                f"Arterial oxygen saturation is optimal at {spo2:.1f} percent. Microgravity pulmonary exchange is normal."
            )
        elif "spacewalk" in q or "eva" in q or "ready" in q or "clearance" in q:
            if fatigue < 50 and spo2 >= 95:
                return (
                    f"{name}, physiological baselines confirm you are fully cleared for extravehicular EVA activities. Maintain scheduled hydration."
                )
            else:
                return (
                    f"{name}, spacewalk flight clearance is restricted due to elevated fatigue index ({fatigue}%). 45-minute metabolic rest required."
                )
        elif "fatigue" in q or "tired" in q or "sleep" in q or "rest" in q:
            return (
                f"Cognitive fatigue index is recorded at {fatigue} percent. Recommending circadian light cycle adjustment and 7.5 hours rest protocol in crew sleep quarters."
            )
        else:
            return (
                f"AstroMind AI Flight Surgeon online for {name}. Heart rate is {hr} BPM, blood oxygen is {spo2:.1f}%, and readiness score is nominal. "
                "Drink 350ml electrolyte pouch and continue scheduled mission timeline."
            )

    def speak_async(self, text: str):
        """
        Speaks text in a non-blocking daemon thread using pyttsx3.
        Strips all emojis, === dividers, bullet symbols and markdown before TTS.
        Call stop_speaking() at any time to interrupt mid-sentence.
        """
        if not pyttsx3:
            return

        # Stop any currently running voice before starting new one
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
