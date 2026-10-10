/**
 * AstroMind: Hands-Free Voice Assistant & Offline AI Doctor Engine
 * Features:
 * - Hands-Free Voice Activation ("Hey AstroMind", "Hey Doctor")
 * - Web Speech Recognition + Offline Fallback
 * - Web Speech Synthesis with calm space AI tone
 * - Web Audio API synthesized sound effects (chime, alert sirens)
 */

class AstroVoiceAssistant {
  constructor() {
    this.isListening = false;
    this.recognition = null;
    this.speechSynthesis = window.speechSynthesis;
    this.hotwords = ["hey astromind", "astromind", "hey doctor", "doctor", "doctor please", "astro mind"];
    this.audioCtx = null;
    this.isSpeaking = false;

    this.initAudioContext();
    this.initSpeechRecognition();
  }

  initAudioContext() {
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.audioCtx = new AudioCtx();
      }
    } catch (e) {
      console.warn("[Voice] Web Audio API not supported", e);
    }
  }

  // Synthesized Sound Effects using Web Audio API (No external sound files required)
  playChime(type = "nominal") {
    if (!this.audioCtx) return;
    try {
      if (this.audioCtx.state === "suspended") {
        this.audioCtx.resume();
      }
      const now = this.audioCtx.currentTime;

      if (type === "nominal" || type === "mic") {
        // High-tech sci-fi double ping
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.type = "sine";
        osc.frequency.setValueAtTime(587.33, now); // D5
        osc.frequency.exponentialRampToValueAtTime(880.0, now + 0.12); // A5
        gain.gain.setValueAtTime(0.12, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);
        osc.connect(gain);
        gain.connect(this.audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.36);
      } else if (type === "alert") {
        // Space Red Alert Siren Pulse
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();
        osc.type = "sawtooth";
        osc.frequency.setValueAtTime(440, now);
        osc.frequency.linearRampToValueAtTime(880, now + 0.25);
        osc.frequency.linearRampToValueAtTime(440, now + 0.5);
        gain.gain.setValueAtTime(0.18, now);
        gain.gain.exponentialRampToValueAtTime(0.01, now + 0.6);
        osc.connect(gain);
        gain.connect(this.audioCtx.destination);
        osc.start(now);
        osc.stop(now + 0.65);
      }
    } catch (err) {
      console.warn("Audio chime error:", err);
    }
  }

  initSpeechRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    const voiceStatusText = document.getElementById("voiceStatusText");
    const voiceIndicator = document.getElementById("voiceIndicator");

    if (!SpeechRec) {
      console.warn("[AstroMind] Speech Recognition not supported in this browser. Push-to-talk and text input active.");
      if (voiceStatusText) voiceStatusText.innerText = "CLICK TO TALK (TEXT/BUTTON)";
      return;
    }

    this.recognition = new SpeechRec();
    this.recognition.continuous = true;
    this.recognition.interimResults = false;
    this.recognition.lang = "en-US";

    this.recognition.onstart = () => {
      this.isListening = true;
      if (voiceIndicator) voiceIndicator.classList.add("listening");
      if (voiceStatusText) voiceStatusText.innerHTML = '🎤 "Hey AstroMind" LISTENING';
    };

    this.recognition.onresult = (event) => {
      const lastIndex = event.results.length - 1;
      const transcript = event.results[lastIndex][0].transcript.trim().toLowerCase();
      console.log("[Voice Heard]:", transcript);

      // Check for Hotword
      const matchedHotword = this.hotwords.some(hw => transcript.includes(hw));

      if (matchedHotword) {
        this.playChime("mic");
        // Extract query after hotword or use full phrase
        let cleanedQuery = transcript;
        this.hotwords.forEach(hw => {
          cleanedQuery = cleanedQuery.replace(hw, "");
        });
        cleanedQuery = cleanedQuery.trim() || "What is my current health status?";

        // Visually trigger mic button animation
        const btnTalk = document.getElementById("btnTalkDoctor");
        if (btnTalk) btnTalk.classList.add("speaking-active");

        if (window.submitVoiceQueryToBackend) {
          window.submitVoiceQueryToBackend(cleanedQuery);
        }
      } else {
        // If user already clicked Talk to Doctor and is speaking directly:
        if (this.manualTriggerActive) {
          this.manualTriggerActive = false;
          if (window.submitVoiceQueryToBackend) {
            window.submitVoiceQueryToBackend(transcript);
          }
        }
      }
    };

    this.recognition.onerror = (err) => {
      // Don't spam console on silence/aborted
      if (err.error !== "no-speech" && err.error !== "aborted") {
        console.warn("[Voice Rec Error]:", err.error);
      }
    };

    this.recognition.onend = () => {
      this.isListening = false;
      // Auto-restart hands-free listening loop after 1.5s
      setTimeout(() => {
        if (!this.isSpeaking) {
          this.startListening();
        }
      }, 1500);
    };

    // Auto-start listening on user interaction
    document.addEventListener("click", () => {
      if (!this.isListening && !this.isSpeaking) {
        this.startListening();
      }
    }, { once: true });
  }

  startListening() {
    if (!this.recognition || this.isListening) return;
    try {
      this.recognition.start();
    } catch (e) {
      // Ignored if already started
    }
  }

  stopListening() {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
  }

  // Speak AI Doctor advice with synthetic space voice
  speak(text) {
    if (!this.speechSynthesis) return;

    this.isSpeaking = true;
    this.stopListening(); // Pause recognition while AI speaks to prevent feedback loop

    this.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 1.02; // Calm, authoritative pace
    utterance.pitch = 1.0;

    // Pick best English voice if available
    const voices = this.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Natural") || v.name.includes("David") || v.name.includes("Samantha")));
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    const btnTalk = document.getElementById("btnTalkDoctor");
    if (btnTalk) btnTalk.classList.add("speaking-active");

    utterance.onend = () => {
      this.isSpeaking = false;
      if (btnTalk) btnTalk.classList.remove("speaking-active");
      // Resume listening
      setTimeout(() => {
        this.startListening();
      }, 600);
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      if (btnTalk) btnTalk.classList.remove("speaking-active");
      this.startListening();
    };

    this.speechSynthesis.speak(utterance);
  }
}

// Global instance
window.astroVoice = new AstroVoiceAssistant();
