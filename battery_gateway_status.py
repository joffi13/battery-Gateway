import json
import subprocess
from datetime import datetime
from pathlib import Path

from core.version import project_version


ROOT = Path(__file__).resolve().parent
STATUS_FILE = ROOT / "logs" / "status.json"


def systemctl(property_name: str) -> str:
    result = subprocess.run(
        [
            "systemctl",
            "show",
            "battery-gateway.service",
            f"--property={property_name}",
            "--value",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def format_uptime(seconds: float | int | None) -> str:
    total = int(seconds or 0)
    hours, remainder = divmod(total, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def main() -> int:
    try:
        status = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        status = {}

    active = systemctl("ActiveState") == "active"
    last_publish = status.get("last_publish")
    if last_publish:
        last_publish = datetime.fromtimestamp(last_publish).astimezone().isoformat()
    else:
        last_publish = "never"

    rows = (
        ("Battery Gateway", "RUNNING" if active else "STOPPED"),
        ("Version", project_version()),
        ("Uptime", format_uptime(status.get("uptime_seconds"))),
        ("MQTT Broker", status.get("mqtt_broker", "unknown")),
        ("MQTT Connected", status.get("mqtt_connected", False)),
        ("Last Publish", last_publish),
        ("Reconnect Count", status.get("mqtt_reconnect_count", 0)),
        ("CAN Interface", status.get("can_interface", "unknown")),
        ("CAN Connected", status.get("can_connected", False)),
        ("CAN Errors", status.get("can_errors", 0)),
        ("Frames Received", status.get("frames_received", 0)),
        ("Snapshots Published", status.get("snapshots_published", 0)),
        ("Publish Errors", status.get("publish_errors", 0)),
        ("Battery Count", status.get("battery_count", 0)),
        ("MQTT API Version", status.get("mqtt_api_version", "unknown")),
        ("Design Capacity", f"{status.get('design_capacity_ah', 'unknown')} Ah"),
        ("BLE Devices Configured", status.get("ble_devices_configured", 0)),
        ("BLE Devices Connected", status.get("ble_devices_connected", 0)),
        ("BLE Disconnect Count", status.get("ble_disconnect_count", 0)),
        ("BLE Reconnect Count", status.get("ble_reconnect_count", 0)),
        ("Last BLE Update", status.get("last_ble_update", "never")),
        ("Last BLE Error", status.get("last_ble_error") or "none"),
        ("Service Restarts", systemctl("NRestarts") or "0"),
    )
    width = max(len(label) for label, _value in rows)
    for label, value in rows:
        print(f"{label:<{width}} : {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
