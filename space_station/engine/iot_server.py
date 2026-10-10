"""
AstroMind: Mobile IoT Server Bridge
Runs a lightweight Flask web service in a background daemon thread
allowing real-time wireless phone control from any mobile browser.
"""

import threading
from flask import Flask, render_template, request, jsonify
from .shared_state import state

server_app = Flask(__name__, template_folder="../templates", static_folder="../static")

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

@server_app.route("/api/remote/status")
def remote_status():
    return jsonify(state.get_full_state())

def run_iot_server_background(host="0.0.0.0", port=5000):
    def _run():
        import logging
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR) # Quiet down Flask logs so desktop terminal stays clean
        server_app.run(host=host, port=port, debug=False, use_reloader=False)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t
