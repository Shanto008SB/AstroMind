/**
 * AstroMind: Main UI Controller & Real-Time Telemetry Engine
 * Coordinates Astronaut Switching, Dynamic ECG Waveform,
 * Emergency Banner Alerts, and AI Doctor Voice Interaction.
 */

let activeAstronautId = "sarah";
let isEmergencyActive = false;
let ecgPoints = [];
let ecgIndex = 0;
let lastAlertLevel = "NOMINAL";

document.addEventListener("DOMContentLoaded", () => {
  initEcgCanvas();
  startTelemetryLoop();
  initVoiceDoctorControls();
});

/* ==========================================================================
   ECG CANVAS REAL-TIME DRAWING
   ========================================================================== */
function initEcgCanvas() {
  const canvas = document.getElementById("ecgCanvas");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const w = canvas.width = canvas.parentElement.clientWidth || 280;
  const h = canvas.height = 42;

  // Generate synthetic P-Q-R-S-T ECG baseline signal points
  const pqrst = [0, 1, 2, 0, -2, 22, -8, 0, 1, 3, 2, 0];
  const normalSpan = 35; // points between beats (~75 BPM at 60fps)

  for (let i = 0; i < w; i++) {
    ecgPoints.push(0);
  }

  let counter = 0;

  function renderEcg() {
    counter++;
    let val = 0;
    const beatSpan = isEmergencyActive ? 65 : 32; // slower beat in bradycardia emergency

    if (counter % beatSpan < pqrst.length) {
      val = pqrst[counter % beatSpan] * 1.2;
    }

    ecgPoints.push(val);
    if (ecgPoints.length > w) {
      ecgPoints.shift();
    }

    ctx.clearRect(0, 0, w, h);

    // Grid center line
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();

    // ECG Line
    ctx.beginPath();
    ctx.strokeStyle = isEmergencyActive ? "#ff1e53" : "#ef4444";
    ctx.lineWidth = 1.6;
    ctx.shadowColor = isEmergencyActive ? "rgba(255, 30, 83, 0.8)" : "rgba(239, 68, 68, 0.6)";
    ctx.shadowBlur = 4;

    for (let x = 0; x < ecgPoints.length; x++) {
      const y = h / 2 - ecgPoints[x];
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.shadowBlur = 0;

    requestAnimationFrame(renderEcg);
  }

  requestAnimationFrame(renderEcg);
}

/* ==========================================================================
   REAL-TIME VITAL & TELEMETRY POLLING LOOP
   ========================================================================== */
function startTelemetryLoop() {
  fetchVitalsData();
  setInterval(fetchVitalsData, 1500); // 1.5s interval
}

async function fetchVitalsData() {
  try {
    const res = await fetch(`/api/vitals/${activeAstronautId}`);
    if (!res.ok) return;
    const data = await res.json();
    updateDashboardUI(data);
  } catch (err) {
    console.error("Telemetry fetch error:", err);
  }
}

/* ==========================================================================
   UPDATE DASHBOARD UI COMPONENTS
   ========================================================================== */
function updateDashboardUI(data) {
  const { astronaut, vitals, analysis, clinical_note, cabin, telemetry, is_global_emergency, emergency_target } = data;

  // 1. TOP CARDS BAR (Tip 3)
  // Pulse
  document.getElementById("valPulse").innerText = vitals.heart_rate;
  const pulseBadge = document.getElementById("pulseBadge");
  if (vitals.heart_rate < 50 || vitals.heart_rate > 115) {
    pulseBadge.className = "vital-badge badge-critical";
    pulseBadge.innerText = vitals.heart_rate < 50 ? "BRADYCARDIA" : "TACHYCARDIA";
  } else {
    pulseBadge.className = "vital-badge badge-normal";
    pulseBadge.innerText = "NORMAL";
  }

  // SpO2
  document.getElementById("valSpo2").innerText = vitals.spo2.toFixed(1);
  const spo2Badge = document.getElementById("spo2Badge");
  const spo2Progress = document.getElementById("spo2Progress");
  spo2Progress.style.width = `${vitals.spo2}%`;

  if (vitals.spo2 < 90) {
    spo2Badge.className = "vital-badge badge-critical";
    spo2Badge.innerText = "HYPOXIA";
    spo2Progress.className = "progress-bar-fill fill-red";
  } else if (vitals.spo2 < 94) {
    spo2Badge.className = "vital-badge badge-caution";
    spo2Badge.innerText = "CAUTION";
    spo2Progress.className = "progress-bar-fill fill-red";
  } else {
    spo2Badge.className = "vital-badge badge-normal";
    spo2Badge.innerText = "OPTIMAL";
    spo2Progress.className = "progress-bar-fill fill-cyan";
  }

  // HRV
  document.getElementById("valHrv").innerText = vitals.hrv.toFixed(0);
  const hrvProgress = document.getElementById("hrvProgress");
  hrvProgress.style.width = `${Math.min(100, vitals.hrv * 1.2)}%`;
  const hrvBadge = document.getElementById("hrvBadge");
  if (vitals.hrv < 25) {
    hrvBadge.className = "vital-badge badge-critical";
    hrvBadge.innerText = "EXHAUSTED";
  } else if (vitals.hrv < 40) {
    hrvBadge.className = "vital-badge badge-caution";
    hrvBadge.innerText = "STRAIN";
  } else {
    hrvBadge.className = "vital-badge badge-normal";
    hrvBadge.innerText = "BALANCED";
  }

  // Fatigue
  document.getElementById("valFatigue").innerText = vitals.fatigue_level;
  const fatigueBadge = document.getElementById("fatigueBadge");
  const fatigueProgress = document.getElementById("fatigueProgress");
  fatigueProgress.style.width = `${vitals.fatigue_level}%`;

  if (vitals.fatigue_level > 65) {
    fatigueBadge.className = "vital-badge badge-critical";
    fatigueBadge.innerText = "SEVERE";
    fatigueProgress.className = "progress-bar-fill fill-red";
  } else if (vitals.fatigue_level > 40) {
    fatigueBadge.className = "vital-badge badge-caution";
    fatigueBadge.innerText = "ELEVATED";
    fatigueProgress.className = "progress-bar-fill fill-cyan";
  } else {
    fatigueBadge.className = "vital-badge badge-normal";
    fatigueBadge.innerText = "LOW";
    fatigueProgress.className = "progress-bar-fill fill-emerald";
  }

  // Quick vitals in active astronaut card list
  const listHr = document.getElementById(`listHr-${astronaut.id}`);
  const listSpo2 = document.getElementById(`listSpo2-${astronaut.id}`);
  if (listHr) listHr.innerText = vitals.heart_rate;
  if (listSpo2) listSpo2.innerText = `${vitals.spo2.toFixed(1)}%`;

  // Instant BPM in center camera HUD
  const instantBpm = document.getElementById("instantBpmDisplay");
  if (instantBpm) instantBpm.innerText = `${vitals.heart_rate} BPM (EST.)`;

  // 2. RIGHT PANEL: CREW READINESS GAUGE & REPORT
  const readinessVal = analysis.readiness_score;
  document.getElementById("readinessScoreVal").innerText = `${readinessVal}%`;
  document.getElementById("readinessEvalText").innerText = analysis.readiness_status;

  // SVG Circle stroke-dashoffset (Circumference ~ 314)
  const circleBar = document.getElementById("readinessCircleBar");
  const offset = 314 - (314 * (readinessVal / 100));
  circleBar.style.strokeDashoffset = offset;

  if (analysis.readiness_class === "optimal") {
    circleBar.style.stroke = "var(--green-nominal)";
    document.getElementById("readinessEvalText").style.color = "var(--green-nominal)";
  } else if (analysis.readiness_class === "moderate") {
    circleBar.style.stroke = "var(--amber-caution)";
    document.getElementById("readinessEvalText").style.color = "var(--amber-caution)";
  } else {
    circleBar.style.stroke = "var(--red-critical)";
    document.getElementById("readinessEvalText").style.color = "var(--red-critical)";
  }

  // AI Doctor Clinical Note
  document.getElementById("aiDoctorNoteText").innerText = clinical_note;

  // Suggestions List
  const sugList = document.getElementById("suggestionsList");
  if (sugList && analysis.suggestions) {
    sugList.innerHTML = analysis.suggestions.map(s => `<li>${s}</li>`).join("");
  }

  // Cabin Environment
  document.getElementById("valCabinCo2").innerText = `${cabin.co2_percent.toFixed(2)} %`;
  document.getElementById("valCabinTemp").innerText = `${cabin.temp_c.toFixed(1)} °C`;
  document.getElementById("valCabinPressure").innerText = `${cabin.cabin_pressure_kpa.toFixed(1)} kPa`;
  document.getElementById("valCabinRad").innerText = `${cabin.radiation_msv.toFixed(2)} mSv/h`;

  // Telemetry Buffer count badge
  document.getElementById("bufferCountBadge").innerText = telemetry.buffered_packets;
  document.getElementById("telemetryDelayDisplay").innerText = `${telemetry.simulated_delay}s`;

  // 3. EMERGENCY / RED ALERT ZONE (Tip 2)
  isEmergencyActive = is_global_emergency || analysis.is_emergency;
  updateEmergencyBanner(isEmergencyActive, analysis, astronaut, is_global_emergency, emergency_target);
}

/* ==========================================================================
   EMERGENCY BANNER HANDLING (Enhancement Tip 2)
   ========================================================================== */
function updateEmergencyBanner(isEmergency, analysis, astronaut, isGlobalDrill, emergencyTarget) {
  const banner = document.getElementById("emergencyBanner");
  const symbol = document.getElementById("alertSymbol");
  const headline = document.getElementById("alertHeadline");
  const timeTag = document.getElementById("alertTimeTag");
  const directive = document.getElementById("alertDirective");
  const btnAction = document.getElementById("btnEmergencyAction");
  const overlay = document.getElementById("screenEmergencyOverlay");
  const headerBtn = document.getElementById("btnToggleEmergency");
  const headerBtnText = document.getElementById("emergencyBtnText");

  if (isEmergency) {
    banner.className = "emergency-alert-banner state-emergency";
    symbol.innerText = "🚨";
    overlay.classList.add("active");
    headerBtn.classList.add("active");
    headerBtnText.innerText = "RESOLVE ALERT";

    headline.innerText = `CRITICAL RED ALERT: VITAL COLLAPSE DETECTED!`;
    timeTag.innerText = `CREW TARGET: ${emergencyTarget ? emergencyTarget.toUpperCase() : astronaut.name.toUpperCase()}`;
    directive.innerText = analysis.emergency_message || 
      "Hypoxia & Cardiac Deceleration Detected. Engage Oxygen Supply immediately and notify flight surgeon!";

    btnAction.innerText = "RESOLVE EMERGENCY";

    // Play Alert Chime if transitioning into emergency
    if (lastAlertLevel !== "CRITICAL") {
      lastAlertLevel = "CRITICAL";
      if (window.astroVoice) {
        window.astroVoice.playChime("alert");
        window.astroVoice.speak("Warning! Critical physiological anomaly detected. Immediate emergency medical intervention required!");
      }
    }

    // Highlight target crew card in sidebar
    const targetCard = document.getElementById(`crewCard-${emergencyTarget || astronaut.id}`);
    if (targetCard) targetCard.classList.add("emergency-crew");

  } else {
    banner.className = "emergency-alert-banner state-nominal";
    symbol.innerText = "🟢";
    overlay.classList.remove("active");
    headerBtn.classList.remove("active");
    headerBtnText.innerText = "SIMULATE DRILL";

    headline.innerText = "SYSTEM NOMINAL: NO CRITICAL ANOMALIES DETECTED";
    timeTag.innerText = "ALL CREW VITALS WITHIN MISSION TOLERANCES";
    directive.innerText = "Onboard Local Edge Brain actively monitoring vitals via contactless rPPG computer vision. Deep-space telemetry store-and-forward active.";

    btnAction.innerText = "TRIGGER EMERGENCY DEMO";

    lastAlertLevel = "NOMINAL";

    // Remove emergency-crew class from cards
    document.querySelectorAll(".astronaut-card").forEach(c => c.classList.remove("emergency-crew"));
  }
}

/* ==========================================================================
   ASTRONAUT SWITCHING
   ========================================================================== */
function selectAstronaut(astronautId) {
  if (activeAstronautId === astronautId) return;
  activeAstronautId = astronautId;

  // Update active card style
  document.querySelectorAll(".astronaut-card").forEach(c => c.classList.remove("active-crew"));
  const chosenCard = document.getElementById(`crewCard-${astronautId}`);
  if (chosenCard) chosenCard.classList.add("active-crew");

  // Update subject details in Right panel
  const avatarImg = chosenCard.querySelector(".crew-avatar-img").src;
  const name = chosenCard.querySelector(".crew-name").innerText;
  const role = chosenCard.querySelector(".crew-role").innerText;

  document.getElementById("activeSubjectImg").src = avatarImg;
  document.getElementById("activeSubjectName").innerText = name;
  document.getElementById("activeSubjectRole").innerText = role;
  document.getElementById("reticleAstronautName").innerText = name.toUpperCase();

  // Play gentle sound
  if (window.astroVoice) {
    window.astroVoice.playChime("nominal");
  }

  // Immediately fetch new astronaut vitals
  fetchVitalsData();
}

/* ==========================================================================
   EMERGENCY BANNER BUTTON & TOGGLE
   ========================================================================== */
async function handleEmergencyBannerAction() {
  await toggleEmergencyDrill();
}

document.getElementById("btnToggleEmergency").addEventListener("click", () => {
  toggleEmergencyDrill();
});

async function toggleEmergencyDrill() {
  try {
    const res = await fetch("/api/emergency/toggle", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ target_id: activeAstronautId })
    });
    const data = await res.json();
    fetchVitalsData();
  } catch (err) {
    console.error("Toggle emergency error:", err);
  }
}

/* ==========================================================================
   AI DOCTOR VOICE & TEXT INTERACTION
   ========================================================================== */
function initVoiceDoctorControls() {
  const btnTalk = document.getElementById("btnTalkDoctor");
  if (btnTalk) {
    btnTalk.addEventListener("click", () => {
      if (window.astroVoice) {
        window.astroVoice.playChime("mic");
        window.astroVoice.manualTriggerActive = true;
        window.astroVoice.startListening();
        // Give immediate spoken prompt
        window.astroVoice.speak("AstroMind listening. How can I assist you Commander?");
      }
    });
  }

  // Hook global voice handler
  window.submitVoiceQueryToBackend = sendVoiceQuery;
}

async function sendVoiceQuery(queryText) {
  if (!queryText) return;
  console.log("[Sending Query to AI Doctor]:", queryText);

  try {
    const res = await fetch("/api/ask_doctor", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: queryText,
        astronaut_id: activeAstronautId
      })
    });
    const data = await res.json();
    
    // Update AI Doctor note on right panel
    if (data.text) {
      document.getElementById("aiDoctorNoteText").innerText = data.text;
    }

    // Speak response
    if (data.speech && window.astroVoice) {
      window.astroVoice.speak(data.speech);
    }

    fetchVitalsData();
  } catch (err) {
    console.error("Ask doctor error:", err);
  }
}

function handleDoctorInputKey(event) {
  if (event.key === "Enter") {
    submitDoctorTextInput();
  }
}

function submitDoctorTextInput() {
  const input = document.getElementById("txtDoctorQuery");
  const query = input.value.trim();
  if (!query) return;
  input.value = "";
  sendVoiceQuery(query);
}

/* ==========================================================================
   STORE-AND-FORWARD TELEMETRY MODAL & SYNC
   ========================================================================== */
document.getElementById("btnSyncTelemetry").addEventListener("click", () => {
  openTelemetryModal();
});

function openTelemetryModal() {
  document.getElementById("telemetryModal").style.display = "flex";
  fetch(`/api/vitals/${activeAstronautId}`).then(r => r.json()).then(data => {
    const t = data.telemetry;
    document.getElementById("modalDestName").innerText = t.destination_name;
    document.getElementById("modalDelay").innerText = `${t.simulated_delay} seconds`;
    document.getElementById("modalBufferCount").innerText = `${t.buffered_packets} packets`;
    document.getElementById("modalTotalSynced").innerText = `${t.total_synced_packets.toLocaleString()} packets`;
  });
}

function closeTelemetryModal() {
  document.getElementById("telemetryModal").style.display = "none";
}

async function executeTelemetrySync() {
  const logBox = document.getElementById("modalSyncLogBox");
  logBox.innerHTML += `<div class="log-line text-cyan">[TRANSMITTING] Connecting to Deep Space Network...</div>`;

  try {
    const res = await fetch("/api/telemetry/sync", { method: "POST" });
    const data = await res.json();

    logBox.innerHTML += `<div class="log-line text-green">[BURST COMPLETE] ${data.message}</div>`;
    document.getElementById("modalBufferCount").innerText = "0 packets";
    document.getElementById("modalTotalSynced").innerText = `${data.total_synced.toLocaleString()} packets`;

    if (window.astroVoice) {
      window.astroVoice.playChime("nominal");
    }

    fetchVitalsData();
  } catch (err) {
    logBox.innerHTML += `<div class="log-line text-red">[SYNC ERROR] Failed to transmit burst: ${err}</div>`;
  }
}

async function changeMissionDestination(dest) {
  try {
    await fetch("/api/telemetry/set_dest", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ destination: dest })
    });
    fetchVitalsData();
  } catch (err) {
    console.error("Change destination error:", err);
  }
}
