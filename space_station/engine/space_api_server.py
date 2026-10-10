"""
AstroMind Space Station: Real-Time S-Band Telemetry & Network Sync Server
Serves:
1. Live telemetry to Earth Mission Control over LAN Wi-Fi (GET /api/telemetry/live)
2. Command execution from Earth (POST /api/telemetry/command)
3. Remote Expedition Roster Deployment from Earth (POST /api/roster/deploy_group, /api/roster/add_astronaut)
4. Mobile Wireless Phone IoT Controller (/remote)
"""

import threading
import logging
import os
from flask import Flask, render_template, request, jsonify
from .shared_state import state
from .medical_db import medical_db

# Configure template & static paths relative to space_station folder
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
template_dir = os.path.join(base_dir, "templates")
static_dir = os.path.join(base_dir, "static")

server_app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)


# -----------------------------------------------------------------------------
# 1. MOBILE PHONE WIRELESS IoT CONTROLLER
# -----------------------------------------------------------------------------
@server_app.route("/")
@server_app.route("/remote")
@server_app.route("/iot")
def remote_page():
    return render_template("phone_remote.html")

@server_app.route("/api/remote/update", methods=["POST"])
def remote_update():
    data = request.get_json() or {}
    state.update_from_phone(
        hr=data.get("hr"),
        spo2=data.get("spo2"),
        hrv=data.get("hrv"),
        fatigue=data.get("fatigue"),
        co2=data.get("co2"),
        temp=data.get("temp"),
        radiation=data.get("radiation"),
        is_emergency=data.get("is_emergency")
    )
    return jsonify({"status": "ok", "state": state.get_full_state()})

@server_app.route("/api/remote/select_crew", methods=["POST"])
def remote_select_crew():
    data = request.get_json() or {}
    cid = data.get("astronaut_id", "sarah")
    state.set_active_astronaut(cid)
    return jsonify({"status": "ok", "active_id": state.active_id})


# -----------------------------------------------------------------------------
# 2. EARTH MISSION CONTROL LAN S-BAND API LINK
# -----------------------------------------------------------------------------
@server_app.route("/api/telemetry/live", methods=["GET"])
def api_telemetry_live():
    """Returns full live telemetry packet from Space Station to Earth Mission Control."""
    return jsonify({
        "status": "ok",
        "station": "AstroMind Deep Space Station",
        "telemetry": state.get_full_state()
    })

@server_app.route("/api/telemetry/command", methods=["POST"])
def api_telemetry_command():
    """Executes ground commands received from Earth Mission Control."""
    data = request.get_json() or {}
    cmd = data.get("command", "")
    
    if cmd == "RESOLVE_EMERGENCY":
        state.update_from_phone(hr=72, spo2=98.4, hrv=58.0, fatigue=18, co2=0.31, is_emergency=False)
        return jsonify({"status": "ok", "message": "Emergency resolved by Ground Command"})
    
    elif cmd == "TRIGGER_EMERGENCY":
        state.update_from_phone(hr=42, spo2=88.5, hrv=18.0, fatigue=85, co2=0.75, is_emergency=True)
        return jsonify({"status": "ok", "message": "Emergency drill triggered by Ground Command"})

    elif cmd == "SELECT_ASTRONAUT":
        aid = data.get("astronaut_id", "sarah")
        state.set_active_astronaut(aid)
        return jsonify({"status": "ok", "active_id": state.active_id})

    return jsonify({"status": "error", "message": f"Unknown command: {cmd}"}), 400

@server_app.route("/api/roster/deploy_group", methods=["POST"])
def api_roster_deploy_group():
    """Earth commands: Switches the active mission group deployed in Deep Space!"""
    data = request.get_json() or {}
    group_id = data.get("group_id", "expedition_72")
    medical_db.set_active_space_group(group_id)
    state.reload_crew_from_db()
    return jsonify({
        "status": "ok",
        "message": f"Mission Group '{group_id}' deployed to Space Station",
        "active_crew": state.crew_members
    })

@server_app.route("/api/roster/add_astronaut", methods=["POST"])
def api_roster_add_astronaut():
    """Earth adds an astronaut to the space roster over the network."""
    data = request.get_json() or {}
    active_grp = medical_db.get_active_space_group()
    if active_grp and data.get("group_id") == active_grp.get("group_id"):
        data["is_deployed"] = 1
        data["status"] = "IN_SPACE"
    
    success = medical_db.add_astronaut(data)
    if success:
        state.reload_crew_from_db()
        return jsonify({
            "status": "ok",
            "message": "Astronaut added and synced to Space Station",
            "active_crew": state.crew_members
        })
    return jsonify({"status": "error", "message": "Failed to add astronaut"}), 400

@server_app.route("/api/roster/update_astronaut", methods=["POST"])
def api_roster_update_astronaut():
    data = request.get_json() or {}
    aid = data.get("id")
    updates = data.get("updates", {})
    if aid and updates:
        medical_db.update_astronaut(aid, updates)
        state.reload_crew_from_db()
        return jsonify({"status": "ok", "message": "Astronaut updated on Space Station"})
    return jsonify({"status": "error", "message": "Missing ID or updates"}), 400

@server_app.route("/api/roster/active_crew", methods=["GET"])
def api_roster_active_crew():
    state.reload_crew_from_db()
    return jsonify({"status": "ok", "active_crew": state.crew_members})

@server_app.route("/api/history/records", methods=["GET"])
def api_history_records():
    aid = request.args.get("astronaut_id", "sarah")
    date_f = request.args.get("date", None)
    records = medical_db.get_records_by_date(aid, date_filter=date_f, limit=50)
    return jsonify({"status": "ok", "records": records})


def run_space_api_server_background(host="0.0.0.0", port=5000):
    def _run():
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        server_app.run(host=host, port=port, debug=False, use_reloader=False)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
