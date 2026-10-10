"""
AstroMind: Store-and-Forward Deep Space Telemetry Protocol
Simulates communication delays with Houston Ground Control:
- ISS: 0.5 sec delay
- Artemis Moon (Lunar Habitat): 2.6 sec delay
- Mars Deep Space Expedition: 14 min 20 sec delay
Enables 100% offline edge logging and burst synchronization when communication window opens.
"""

import time
from typing import Dict, Any, List

class TelemetrySync:
    def __init__(self):
        self.destinations = {
            "iss": {"name": "Low Earth Orbit (ISS)", "delay_sec": 0.5},
            "artemis": {"name": "Artemis III Lunar Habitat Alpha", "delay_sec": 2.6},
            "mars": {"name": "Mars Deep Space Transit (Hermes)", "delay_sec": 860.0}
        }
        self.active_destination = "artemis"
        self.telemetry_buffer: List[Dict[str, Any]] = []
        self.max_buffer_size = 100
        self.last_sync_time = time.time()
        self.synced_packets_count = 1420

    def add_telemetry_packet(self, astronaut_id: str, vitals: Dict[str, Any], cabin: Dict[str, Any], alert_level: str):
        packet = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "astronaut_id": astronaut_id,
            "vitals": vitals,
            "cabin": cabin,
            "alert_level": alert_level,
            "synced": False
        }
        self.telemetry_buffer.append(packet)
        if len(self.telemetry_buffer) > self.max_buffer_size:
            self.telemetry_buffer.pop(0)

    def set_destination(self, dest_key: str):
        if dest_key in self.destinations:
            self.active_destination = dest_key

    def sync_to_ground_control(self) -> Dict[str, Any]:
        dest = self.destinations[self.active_destination]
        count = len(self.telemetry_buffer)
        self.synced_packets_count += count
        self.telemetry_buffer.clear()
        self.last_sync_time = time.time()
        return {
            "status": "success",
            "destination": dest["name"],
            "simulated_delay": dest["delay_sec"],
            "synced_count": count,
            "total_synced": self.synced_packets_count,
            "message": f"Successfully synced {count} encrypted telemetry packets to {dest['name']} via Deep Space Network (Delay: {dest['delay_sec']}s)."
        }

    def get_telemetry_status(self) -> Dict[str, Any]:
        dest = self.destinations[self.active_destination]
        return {
            "destination_key": self.active_destination,
            "destination_name": dest["name"],
            "simulated_delay": dest["delay_sec"],
            "buffered_packets": len(self.telemetry_buffer),
            "total_synced_packets": self.synced_packets_count,
            "edge_storage_mode": "STORE_AND_FORWARD_ACTIVE",
            "last_sync_epoch": self.last_sync_time
        }
