"""
AstroMind: Continuous Medical Danger Alarm Engine
Plays an authentic NASA Spacecraft Red Alert / Emergency Danger Siren (WAV loop)
during emergency warning conditions until resolved or muted.
"""

import os
import sys
import time
import wave
import threading

try:
    import winsound
    WINSOUND_AVAILABLE = True
except ImportError:
    WINSOUND_AVAILABLE = False


def _ensure_danger_wav_exists(target_path: str):
    """
    Generates a high-urgency NASA Spacecraft Red Alert danger siren audio file
    if it does not already exist.
    """
    if os.path.exists(target_path) and os.path.getsize(target_path) > 1000:
        return

    try:
        import numpy as np
        sample_rate = 44100
        duration = 1.6 # 1.6-second seamless looping emergency whoop siren
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

        pulse_len = 0.8
        phase = (t % pulse_len) / pulse_len

        # Dramatic pitch sweep: 580 Hz -> 1420 Hz
        freq_curve = 580.0 + 840.0 * (np.sin(phase * np.pi * 0.95) ** 1.6)
        carrier_phase = 2.0 * np.pi * np.cumsum(freq_curve) / sample_rate

        # Multi-harmonic emergency klaxon timbre (fundamental + 2nd, 3rd, 4th harmonics)
        sig = (0.50 * np.sin(carrier_phase)
               + 0.28 * np.sin(2.0 * carrier_phase)
               + 0.16 * np.sin(3.0 * carrier_phase)
               + 0.06 * np.sin(4.0 * carrier_phase))

        # 16 Hz emergency warble / tremolo flutter
        flutter = 0.82 + 0.18 * np.sin(2.0 * np.pi * 16.0 * t)

        # Attack and decay envelope
        env = np.where(phase < 0.65,
                       np.minimum(1.0, phase / 0.05),
                       np.maximum(0.0, (1.0 - phase) / 0.35))

        audio = sig * flutter * env
        audio = np.tanh(audio * 1.4) / np.tanh(1.4) # Soft-clip saturation
        audio = audio / np.max(np.abs(audio) + 1e-6)
        samples = (audio * 32767 * 0.95).astype(np.int16)

        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        with wave.open(target_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(samples.tobytes())
    except Exception as e:
        print(f"[AstroMind Audio] Error generating danger wav: {e}")


class AlarmSoundManager:
    def __init__(self):
        self.is_playing = False
        self.is_muted = False
        self.lock = threading.Lock()
        
        # Audio file path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.wav_path = os.path.join(base_dir, "static", "assets", "danger_alarm.wav")
        _ensure_danger_wav_exists(self.wav_path)

    def start_alarm(self):
        """Starts the continuous NASA danger warning siren in an async loop."""
        with self.lock:
            if self.is_playing or self.is_muted:
                return
            self.is_playing = True
            
            if WINSOUND_AVAILABLE and os.path.exists(self.wav_path):
                try:
                    winsound.PlaySound(
                        self.wav_path,
                        winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_LOOP
                    )
                    print("[AstroMind Audio] [ALERT] NASA Danger Siren Activated (Looping).")
                    return
                except Exception as e:
                    print(f"[AstroMind Audio] PlaySound error: {e}")

            # Fallback to beep loop if sound card fails
            threading.Thread(target=self._fallback_beep_loop, daemon=True).start()

    def stop_alarm(self, reset_mute: bool = False):
        """Silences and stops the alarm immediately."""
        with self.lock:
            if self.is_playing:
                print("[AstroMind Audio] [OK] NASA Danger Siren Deactivated.")
            self.is_playing = False
            if reset_mute:
                self.is_muted = False
            
            if WINSOUND_AVAILABLE:
                try:
                    winsound.PlaySound(None, winsound.SND_PURGE)
                except Exception:
                    pass

    def mute(self):
        """Mutes the siren until reset or unmuted."""
        with self.lock:
            self.is_muted = True
            self.is_playing = False
            if WINSOUND_AVAILABLE:
                try:
                    winsound.PlaySound(None, winsound.SND_PURGE)
                except Exception:
                    pass
            print("[AstroMind Audio] [MUTED] Danger Siren Muted by Crew.")

    def unmute(self):
        """Unmutes the siren."""
        with self.lock:
            self.is_muted = False
            print("[AstroMind Audio] [UNMUTED] Danger Siren Unmuted.")

    def toggle_mute(self) -> bool:
        """Toggles temporary mute for the danger alarm. Returns True if now muted."""
        with self.lock:
            self.is_muted = not self.is_muted
            if self.is_muted:
                self.is_playing = False
                if WINSOUND_AVAILABLE:
                    try:
                        winsound.PlaySound(None, winsound.SND_PURGE)
                    except Exception:
                        pass
                print("[AstroMind Audio] [MUTED] Danger Siren Muted.")
            else:
                print("[AstroMind Audio] [UNMUTED] Danger Siren Unmuted.")
            return self.is_muted

    def _fallback_beep_loop(self):
        while self.is_playing:
            if not WINSOUND_AVAILABLE or self.is_muted:
                time.sleep(0.2)
                continue
            try:
                winsound.Beep(1100, 150)
                if not self.is_playing or self.is_muted:
                    break
                time.sleep(0.04)
                winsound.Beep(700, 150)
                if not self.is_playing or self.is_muted:
                    break
                time.sleep(0.35)
            except Exception:
                time.sleep(0.3)


alarm_sound = AlarmSoundManager()
