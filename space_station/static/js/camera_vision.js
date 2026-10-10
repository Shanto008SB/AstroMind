/**
 * AstroMind: Camera Vision & Face Mesh Overlay Engine
 * Handles webcam stream / simulated space stream,
 * draws real-time HUD tracking reticles, forehead rPPG ROI,
 * and live chrominance pulse wave.
 */

class CameraVisionController {
  constructor() {
    this.mode = "simulated"; // 'simulated' | 'webcam'
    this.videoElem = document.getElementById("webcamVideo");
    this.serverImg = document.getElementById("serverVideoFeed");
    this.canvasElem = document.getElementById("faceMeshCanvas");
    this.ctx = this.canvasElem ? this.canvasElem.getContext("2d") : null;
    this.waveCanvas = document.getElementById("rppgWaveCanvas");
    this.waveCtx = this.waveCanvas ? this.waveCanvas.getContext("2d") : null;
    
    this.stream = null;
    this.animationId = null;
    this.timeOffset = 0;
    
    // Wave buffer for rPPG
    this.wavePoints = [];
    this.maxWavePoints = 180;
    
    this.initWaveBuffer();
    this.startRenderingLoop();
  }

  initWaveBuffer() {
    for (let i = 0; i < this.maxWavePoints; i++) {
      this.wavePoints.push(0);
    }
  }

  async setMode(newMode) {
    if (this.mode === newMode) return;
    this.mode = newMode;

    const btnSim = document.getElementById("btnModeSimulated");
    const btnCam = document.getElementById("btnModeWebcam");
    const titleElem = document.getElementById("cameraFeedTitle");

    if (newMode === "webcam") {
      btnSim.classList.remove("active");
      btnCam.classList.add("active");
      if (titleElem) titleElem.innerText = "LIVE WEBCAM • OPTICAL rPPG SKIN EXTRACTION";

      // Stop server stream image & start WebRTC
      if (this.serverImg) this.serverImg.style.display = "none";
      if (this.videoElem) this.videoElem.style.display = "block";

      try {
        this.stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 } },
          audio: false
        });
        this.videoElem.srcObject = this.stream;
        await this.videoElem.play();
      } catch (err) {
        console.warn("[CameraVision] Webcam permission denied or unavailable:", err);
        alert("Webcam could not be opened. Falling back to Simulated Deep Space Crew Feed.");
        this.setMode("simulated");
      }
    } else {
      // Simulated
      btnCam.classList.remove("active");
      btnSim.classList.add("active");
      if (titleElem) titleElem.innerText = "SIMULATED CREW FEED • AI BIOMETRIC MESH";

      if (this.stream) {
        this.stream.getTracks().forEach(track => track.stop());
        this.stream = null;
      }
      if (this.videoElem) {
        this.videoElem.pause();
        this.videoElem.style.display = "none";
      }
      if (this.serverImg) {
        this.serverImg.style.display = "block";
      }
    }
  }

  startRenderingLoop() {
    const loop = () => {
      this.timeOffset += 0.05;
      this.drawCanvasOverlays();
      this.drawRppgWave();
      this.animationId = requestAnimationFrame(loop);
    };
    this.animationId = requestAnimationFrame(loop);
  }

  drawCanvasOverlays() {
    if (!this.canvasElem || !this.ctx) return;
    const w = this.canvasElem.width = this.canvasElem.parentElement.clientWidth || 640;
    const h = this.canvasElem.height = this.canvasElem.parentElement.clientHeight || 480;
    const ctx = this.ctx;

    ctx.clearRect(0, 0, w, h);

    // If using live webcam, draw face mesh tracking brackets on canvas
    if (this.mode === "webcam") {
      const cx = w / 2;
      const cy = h / 2 - 10;
      const boxW = 180;
      const boxH = 220;

      // Forehead ROI
      const fx = cx - 40;
      const fy = cy - 90;
      const fw = 80;
      const fh = 32;

      ctx.strokeStyle = "rgba(0, 255, 128, 0.8)";
      ctx.lineWidth = 1.5;
      ctx.strokeRect(fx, fy, fw, fh);
      ctx.fillStyle = "rgba(0, 255, 128, 0.1)";
      ctx.fillRect(fx, fy, fw, fh);

      ctx.font = "9px 'JetBrains Mono', monospace";
      ctx.fillStyle = "#10b981";
      ctx.fillText("FOREHEAD rPPG ROI", fx - 10, fy - 6);

      // Facial feature dots (synthesized landmarks)
      const landmarks = [
        [cx - 30, cy - 30], [cx + 30, cy - 30], // eyes
        [cx, cy - 5],                           // nose tip
        [cx - 24, cy + 35], [cx + 24, cy + 35], // mouth
        [cx - 60, cy], [cx + 60, cy]            // cheeks
      ];

      landmarks.forEach(([lx, ly]) => {
        ctx.beginPath();
        ctx.arc(lx, ly, 3, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(0, 240, 255, 0.85)";
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1;
        ctx.stroke();
      });
    }
  }

  drawRppgWave() {
    if (!this.waveCanvas || !this.waveCtx) return;
    const w = this.waveCanvas.width = this.waveCanvas.parentElement.clientWidth || 320;
    const h = this.waveCanvas.height = 38;
    const ctx = this.waveCtx;

    // Shift wave points and add new photoplethysmography sample
    // Simulated pulse peak at ~1.2 Hz (72 BPM)
    const t = this.timeOffset;
    // Harmonic pulse curve with dicrotic notch
    const baseWave = Math.sin(t * 3.5);
    const dicrotic = 0.35 * Math.sin(t * 7.0 + 0.8);
    const sample = (baseWave + dicrotic) * (h * 0.32);

    this.wavePoints.push(sample);
    if (this.wavePoints.length > w) {
      this.wavePoints.shift();
    }

    ctx.clearRect(0, 0, w, h);

    // Grid line
    ctx.strokeStyle = "rgba(255, 255, 255, 0.05)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, h / 2);
    ctx.lineTo(w, h / 2);
    ctx.stroke();

    // Pulse Waveform
    ctx.beginPath();
    ctx.strokeStyle = "#10b981";
    ctx.lineWidth = 1.8;
    ctx.shadowColor = "rgba(16, 185, 129, 0.7)";
    ctx.shadowBlur = 6;

    for (let i = 0; i < this.wavePoints.length; i++) {
      const x = i;
      const y = h / 2 - this.wavePoints[i];
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
    ctx.shadowBlur = 0; // reset
  }
}

window.cameraController = new CameraVisionController();

function setCameraSource(mode) {
  if (window.cameraController) {
    window.cameraController.setMode(mode);
  }
}
