"""
AstroMind: 3D Holographic Neural AI Brain Engine
Generates real-time 3D rotating, synaptic-pulsing Neural Brain visualization:
- Anatomical 3D brain hemispheres (Left/Right cortex, Frontal, Cerebellum)
- Real-time 3D perspective rotation and projection
- Synaptic axons with moving action potential nerve impulses
- Breathing neural core reacting to real-time Heart Rate (BPM) & Fatigue
- Sci-Fi holographic orbital telemetry scanner rings
- Emergency red alert synaptic surge state
"""

import math
import random
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any

class NeuralBrainRenderer:
    def __init__(self, width: int = 640, height: int = 480):
        self.w = width
        self.h = height
        self.cx = width // 2
        self.cy = height // 2 - 10

        # Generate 3D Brain Anatomical Nodes (x, y, z)
        self.nodes_3d = self._generate_brain_geometry()
        self.connections = self._compute_synaptic_connections()

        # Random spark speeds along axons
        self.sparks = []
        for _ in range(35):
            if len(self.connections) > 0:
                conn_idx = random.randint(0, len(self.connections) - 1)
                self.sparks.append({
                    "conn_idx": conn_idx,
                    "progress": random.random(),
                    "speed": random.uniform(0.015, 0.04)
                })

        # Orbiting telemetry particles
        self.particles = []
        for _ in range(40):
            self.particles.append({
                "radius": random.uniform(160, 230),
                "angle": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.008, 0.025) * random.choice([-1, 1]),
                "y_off": random.uniform(-40, 40),
                "size": random.randint(1, 3)
            })

    def _generate_brain_geometry(self) -> List[Tuple[float, float, float, int]]:
        """
        Creates ~140 3D coordinates representing two brain hemispheres.
        Returns (x, y, z, hemisphere_id: 1=left, 2=right, 3=stem)
        """
        nodes = []
        random.seed(42) # Consistent realistic shape

        # 1. Left and Right Hemispheres (Ellipsoids with anatomical indentation)
        for hemi in [-1, 1]: # -1 for left, +1 for right
            hemi_id = 1 if hemi == -1 else 2
            for u in np.linspace(0.1, math.pi - 0.1, 8):
                for v in np.linspace(0, math.pi * 2, 8):
                    # Ellipsoid equations
                    rx = 62.0 * math.sin(u) * math.cos(v)
                    ry = 48.0 * math.cos(u)
                    rz = 82.0 * math.sin(u) * math.sin(v)

                    # Indentation at bottom and longitudinal fissure
                    if ry > 20: # bottom
                        rx *= 0.8
                        rz *= 0.85

                    # Separate hemispheres by center gap
                    x = rx * 0.88 + (hemi * 42.0)
                    y = ry
                    z = rz

                    # Add minor organic perturbation
                    x += random.uniform(-4, 4)
                    y += random.uniform(-4, 4)
                    z += random.uniform(-4, 4)

                    nodes.append((x, y, z, hemi_id))

        # 2. Cerebellum and Brainstem at the base
        for i in range(16):
            ang = random.uniform(0, math.pi * 2)
            rad = random.uniform(12, 35)
            x = math.cos(ang) * rad
            y = random.uniform(38, 70) # lower
            z = math.sin(ang) * rad - 15
            nodes.append((x, y, z, 3))

        return nodes

    def _compute_synaptic_connections(self) -> List[Tuple[int, int]]:
        """
        Connects neighboring nodes within a distance threshold.
        """
        conns = []
        max_dist = 42.0
        n = len(self.nodes_3d)

        for i in range(n):
            for j in range(i + 1, n):
                x1, y1, z1, h1 = self.nodes_3d[i]
                x2, y2, z2, h2 = self.nodes_3d[j]

                # Prefer connections within same hemisphere, with a few corpus callosum bridges
                if h1 == h2 or (h1 != 3 and h2 != 3 and abs(x1) < 45 and abs(x2) < 45 and abs(y1 - y2) < 25):
                    d = math.sqrt((x1 - x2)**2 + (y1 - y2)**2 + (z1 - z2)**2)
                    if d < max_dist:
                        conns.append((i, j))
        return conns

    def render_frame(self, t: float, vitals: Dict[str, Any] = None, is_emergency: bool = False) -> np.ndarray:
        """
        Renders the complete 3D Neural AI Brain animation frame into a NumPy BGR image.
        """
        frame = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        # Deep space dark backdrop with subtle slate grid
        frame[:] = (9, 13, 24)

        hr = vitals.get("heart_rate", 72) if vitals else 72
        fatigue = vitals.get("fatigue_level", 20) if vitals else 20
        spo2 = vitals.get("spo2", 98.4) if vitals else 98.4

        # Pulse speed linked to heart rate
        pulse_freq = (hr / 60.0) * math.pi * 2
        pulse_factor = 0.5 + 0.5 * math.sin(t * pulse_freq)

        # 3D Rotation Angles
        rot_y = t * 0.45          # Smooth Y-axis rotation
        rot_x = 0.22 + 0.08 * math.sin(t * 0.3) # Subtle vertical nodding
        rot_z = 0.04 * math.cos(t * 0.25)

        # Emergency colors vs Nominal colors
        if is_emergency:
            # Fiery Red Alert Synaptic Storm
            c_primary = (40, 40, 255)       # Neon Red (BGR)
            c_secondary = (20, 140, 255)    # Neon Orange
            c_spark = (255, 255, 255)       # White-hot sparks
            c_core_glow = (30, 20, 180)
            status_text = "🚨 NEURAL CORE: CRITICAL SYNAPTIC OVERDRIVE"
            status_col = (50, 50, 255)
        elif fatigue > 55:
            # Cognitive Strain / Amber-Violet
            c_primary = (220, 100, 200)     # Violet/Magenta
            c_secondary = (30, 180, 240)    # Amber
            c_spark = (0, 240, 255)
            c_core_glow = (120, 40, 120)
            status_text = f"⚠️ NEURAL LOAD: COGNITIVE FATIGUE ({fatigue}%)"
            status_col = (30, 180, 240)
        else:
            # Nominal NASA Cyan / Electric Bio-Teal
            c_primary = (255, 240, 0)       # Electric Cyan (BGR)
            c_secondary = (180, 255, 50)    # Bio Emerald
            c_spark = (255, 255, 255)       # Bright white
            c_core_glow = (100, 70, 0)
            status_text = "● NEURAL CORE: COGNITIVE EQUILIBRIUM (ACTIVE)"
            status_col = (255, 240, 0)

        # 1. Draw Subtle Tech Grid Lines
        for y in range(0, self.h, 45):
            cv2.line(frame, (0, y), (self.w, y), (18, 26, 42), 1)
        for x in range(0, self.w, 45):
            cv2.line(frame, (x, 0), (x, self.h), (18, 26, 42), 1)

        # 2. Draw Holographic Compass / Orbiting Reticle Rings
        ring_r1 = int(175 + 10 * pulse_factor)
        ring_r2 = int(195 + 6 * math.sin(t * 1.5))
        cv2.circle(frame, (self.cx, self.cy), ring_r1, (30, 50, 75), 1, cv2.LINE_AA)
        
        # Dashed Rotating Target Ring
        ring_angle = t * 25.0
        for a in range(0, 360, 30):
            rad_a = math.radians(a + ring_angle)
            p1 = (int(self.cx + (ring_r2 - 6) * math.cos(rad_a)), int(self.cy + (ring_r2 - 6) * math.sin(rad_a)))
            p2 = (int(self.cx + (ring_r2 + 6) * math.cos(rad_a)), int(self.cy + (ring_r2 + 6) * math.sin(rad_a)))
            cv2.line(frame, p1, p2, (45, 80, 110), 1, cv2.LINE_AA)

        # Central Radial Core Glow (Breathes with pulse)
        glow_size = int(70 + 25 * pulse_factor)
        overlay = frame.copy()
        cv2.circle(overlay, (self.cx, self.cy), glow_size, c_core_glow, -1)
        cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

        # 3. Project 3D Nodes to 2D Screen Space
        focal_length = 380.0
        dist_z = 260.0

        cos_y, sin_y = math.cos(rot_y), math.sin(rot_y)
        cos_x, sin_x = math.cos(rot_x), math.sin(rot_x)
        cos_z, sin_z = math.cos(rot_z), math.sin(rot_z)

        proj_2d = []
        depths = []

        for x0, y0, z0, hemi_id in self.nodes_3d:
            # Rotate around Y axis
            x1 = x0 * cos_y - z0 * sin_y
            z1 = x0 * sin_y + z0 * cos_y

            # Rotate around X axis
            y2 = y0 * cos_x - z1 * sin_x
            z2 = y0 * sin_x + z1 * cos_x

            # Rotate around Z axis
            x3 = x1 * cos_z - y2 * sin_z
            y3 = x1 * sin_z + y2 * cos_z
            z3 = z2

            # Perspective projection
            scale = focal_length / (z3 + dist_z)
            sx = int(self.cx + x3 * scale)
            sy = int(self.cy + y3 * scale)

            proj_2d.append((sx, sy, scale, z3, hemi_id))
            depths.append(z3)

        # 4. Draw Synaptic Axons (Lines Connecting Brain Nodes)
        for idx1, idx2 in self.connections:
            sx1, sy1, sc1, z1, _ = proj_2d[idx1]
            sx2, sy2, sc2, z2, _ = proj_2d[idx2]

            # Depth alpha fading
            avg_z = (z1 + z2) / 2.0
            alpha = max(0.15, min(0.9, (120 - avg_z) / 200.0))

            # Pulse brightness fluctuation
            synapse_col = (
                int(c_secondary[0] * alpha),
                int(c_secondary[1] * alpha),
                int(c_secondary[2] * alpha)
            )
            cv2.line(frame, (sx1, sy1), (sx2, sy2), synapse_col, 1, cv2.LINE_AA)

        # 5. Draw Electric Nerve Impulses (Action Potentials / Moving Sparks)
        for s in self.sparks:
            s["progress"] += s["speed"]
            if s["progress"] >= 1.0:
                s["progress"] = 0.0
                if len(self.connections) > 0:
                    s["conn_idx"] = random.randint(0, len(self.connections) - 1)

            idx1, idx2 = self.connections[s["conn_idx"]]
            sx1, sy1, _, _, _ = proj_2d[idx1]
            sx2, sy2, _, _, _ = proj_2d[idx2]

            prog = s["progress"]
            px = int(sx1 + (sx2 - sx1) * prog)
            py = int(sy1 + (sy2 - sy1) * prog)

            # Draw spark glow
            cv2.circle(frame, (px, py), 2, c_spark, -1, cv2.LINE_AA)
            cv2.circle(frame, (px, py), 4, c_primary, 1, cv2.LINE_AA)

        # 6. Draw 3D Neural Nodes (Sorted by depth: farthest to nearest)
        sorted_indices = sorted(range(len(proj_2d)), key=lambda k: proj_2d[k][3], reverse=True)

        for i in sorted_indices:
            sx, sy, sc, z_depth, hemi_id = proj_2d[i]
            # Depth attenuation
            node_alpha = max(0.25, min(1.0, (140 - z_depth) / 220.0))
            node_r = max(2, int(3.5 * sc))

            # Outer ring
            col_node = (
                int(c_primary[0] * node_alpha),
                int(c_primary[1] * node_alpha),
                int(c_primary[2] * node_alpha)
            )
            cv2.circle(frame, (sx, sy), node_r + 1, col_node, 1, cv2.LINE_AA)
            # Solid core
            cv2.circle(frame, (sx, sy), max(1, node_r - 1), (255, 255, 255) if node_alpha > 0.7 else col_node, -1, cv2.LINE_AA)

        # 7. Orbiting Telemetry Particles
        for p in self.particles:
            p["angle"] += p["speed"]
            par_x = int(self.cx + p["radius"] * math.cos(p["angle"]))
            par_y = int(self.cy + (p["radius"] * 0.35) * math.sin(p["angle"]) + p["y_off"])
            if 0 <= par_x < self.w and 0 <= par_y < self.h:
                cv2.circle(frame, (par_x, par_y), p["size"], (140, 220, 255), -1, cv2.LINE_AA)

        # 8. Real-time EEG/Neural Synaptic Pulse Wave at bottom
        wave_pts = []
        for i in range(200):
            wx = 20 + i * 3
            # EEG multi-harmonic rhythm
            eeg_val = (
                math.sin((t * 8.0) + (i * 0.12)) * 0.6 +
                math.sin((t * 18.0) + (i * 0.28)) * 0.3 +
                0.2 * math.cos((t * 4.0) + (i * 0.05))
            )
            wy = int(452 - 18 * eeg_val)
            wave_pts.append((wx, wy))

        for i in range(len(wave_pts) - 1):
            cv2.line(frame, wave_pts[i], wave_pts[i+1], c_secondary, 2, cv2.LINE_AA)

        # 9. Futuristic Holographic HUD Overlay Text
        cv2.putText(frame, "ASTROMIND NEURAL EDGE CORE v3.8", (24, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.48, (0, 240, 255), 1, cv2.LINE_AA)
        cv2.putText(frame, f"SYNAPTIC ACTIVITY: {int(hr * 1.8)} MHz | COGNITIVE LOAD: {fatigue}%", (24, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (150, 210, 240), 1, cv2.LINE_AA)
        cv2.putText(frame, status_text, (24, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.42, status_col, 1, cv2.LINE_AA)

        cv2.putText(frame, "3D SYNAPTIC EEG STREAM [REAL-TIME BIOMETRIC CONDUCTION]", (24, 474), cv2.FONT_HERSHEY_SIMPLEX, 0.36, (120, 180, 210), 1, cv2.LINE_AA)
        cv2.putText(frame, f"PULSE LOCK: {hr} BPM", (self.w - 180, 474), cv2.FONT_HERSHEY_SIMPLEX, 0.42, c_primary, 1, cv2.LINE_AA)

        # Targeting brackets around the brain
        b_len = 18
        bx1, by1 = self.cx - 210, self.cy - 160
        bx2, by2 = self.cx + 210, self.cy + 160

        c_brk = (0, 240, 255) if not is_emergency else (50, 50, 255)
        # Top-left
        cv2.line(frame, (bx1, by1), (bx1 + b_len, by1), c_brk, 2)
        cv2.line(frame, (bx1, by1), (bx1, by1 + b_len), c_brk, 2)
        # Top-right
        cv2.line(frame, (bx2, by1), (bx2 - b_len, by1), c_brk, 2)
        cv2.line(frame, (bx2, by1), (bx2, by1 + b_len), c_brk, 2)
        # Bottom-left
        cv2.line(frame, (bx1, by2), (bx1 + b_len, by2), c_brk, 2)
        cv2.line(frame, (bx1, by2), (bx1, by2 - b_len), c_brk, 2)
        # Bottom-right
        cv2.line(frame, (bx2, by2), (bx2 - b_len, by2), c_brk, 2)
        cv2.line(frame, (bx2, by2), (bx2, by2 - b_len), c_brk, 2)

        return frame
