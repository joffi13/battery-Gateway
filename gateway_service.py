import json
import logging
import signal
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from time import monotonic, sleep, time

from core.derived import DerivedEngine
from core.snapshot import BatterySnapshot, NormalizedMeasurement, Temperature
from core.source_merger import SourceMerger
from decoders.seplos_ble import SeplosBLEDecoder
from decoders.seplos import SeplosCANDecoder
from publishers.mqtt import MQTT_API_VERSION, MQTTPublisher, MQTTPublisherConfig
from readers.ble import BLEDeviceConfig, BLEReader
from readers.socketcan import SocketCANReader


LOG = logging.getLogger("battery_gateway")


@dataclass(frozen=True, slots=True)
class GatewayConfig:
    can_interface: str = "can0"
    battery_id: str = "battery_01"
    publish_interval_s: float = 5.0
    status_interval_s: float = 60.0
    ble_devices: tuple[BLEDeviceConfig, ...] = ()

    @classmethod
    def from_file(cls, path: str | Path) -> "GatewayConfig":
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        values = data.get("gateway", {})
        ble_devices = tuple(
            BLEDeviceConfig(
                device_id=str(item["device_id"]),
                battery_id=str(
                    item.get(
                        "battery_id",
                        values.get("battery_id", "battery_01"),
                    )
                ),
                address=str(item["address"]),
                enabled=bool(item.get("enabled", True)),
                poll_interval_s=float(item.get("poll_interval_s", 30.0)),
                reconnect_delay_s=float(item.get("reconnect_delay_s", 5.0)),
                scan_timeout_s=float(item.get("scan_timeout_s", 12.0)),
            )
            for item in data.get("ble", {}).get("devices", ())
        )
        return cls(
            can_interface=str(values.get("can_interface", "can0")),
            battery_id=str(values.get("battery_id", "battery_01")),
            publish_interval_s=float(values.get("publish_interval_s", 5.0)),
            status_interval_s=float(values.get("status_interval_s", 60.0)),
            ble_devices=ble_devices,
        )


class SnapshotAccumulator:
    def __init__(self, battery_id: str):
        self.battery_id = battery_id
        self._measurements: dict[str, NormalizedMeasurement] = {}

    def update(self, measurements: tuple[NormalizedMeasurement, ...]) -> None:
        for measurement in measurements:
            self._measurements[measurement.name] = measurement

    @property
    def ready(self) -> bool:
        required = {"battery.voltage", "battery.current", "battery.soc"}
        return required.issubset(self._measurements)

    def snapshot(self) -> BatterySnapshot:
        measurements = tuple(self._measurements.values())
        timestamp = max((item.timestamp for item in measurements), default=time())
        temperatures = tuple(
            Temperature(
                temperature_id=item.name,
                kind=item.name.removeprefix("temperature."),
                value=item,
                quality=item.quality,
            )
            for item in measurements
            if item.name.startswith("temperature.")
        )
        return BatterySnapshot(
            snapshot_id=f"{self.battery_id}:{timestamp:.6f}",
            battery_id=self.battery_id,
            timestamp=timestamp,
            measurements=measurements,
            temperatures=temperatures,
        )

    def value(self, name: str) -> int | float | bool | str | None:
        measurement = self._measurements.get(name)
        return measurement.value if measurement else None


class GatewayApplication:
    def __init__(self, config_path: str):
        self.config = GatewayConfig.from_file(config_path)
        self.publisher = MQTTPublisher(MQTTPublisherConfig.from_file(config_path))
        self.reader: SocketCANReader | None = None
        self.decoder = SeplosCANDecoder()
        self.derived = DerivedEngine()
        self.merger = SourceMerger()
        self.ble_decoder = SeplosBLEDecoder()
        self.ble_reader = BLEReader(self.config.ble_devices)
        self.accumulator = SnapshotAccumulator(self.config.battery_id)
        self.running = True
        self.frames = 0
        self.publications = 0
        self.errors = 0
        self.can_errors = 0
        self.can_reconnects = 0
        self.mqtt_reconnects = 0
        self.last_publish: float | None = None
        self.started = monotonic()
        self.status_path = Path(__file__).resolve().parent / "logs" / "status.json"

    def stop(self, *_args: object) -> None:
        self.running = False

    def run(self) -> int:
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)
        last_publish = 0.0
        last_status = monotonic()
        next_can_attempt = 0.0
        next_publish_attempt = 0.0
        LOG.info(
            "starting interface=%s battery_id=%s broker=%s:%s ble_devices=%d",
            self.config.can_interface,
            self.config.battery_id,
            self.publisher.config.host,
            self.publisher.config.port,
            len(self.config.ble_devices),
        )
        self.ble_reader.start()
        try:
            while self.running:
                now = monotonic()
                if self.reader is None:
                    if now < next_can_attempt:
                        sleep(min(1.0, next_can_attempt - now))
                        continue
                    try:
                        self.reader = SocketCANReader(self.config.can_interface)
                        if self.can_errors:
                            self.can_reconnects += 1
                        LOG.info("CAN connected interface=%s", self.config.can_interface)
                    except Exception:
                        self.can_errors += 1
                        next_can_attempt = now + 5.0
                        LOG.exception(
                            "CAN connection failed; retrying in 5 seconds"
                        )
                        sleep(1.0)
                        continue

                try:
                    frame = self.reader.read()
                except Exception:
                    self.can_errors += 1
                    LOG.exception("CAN read failed; reconnecting in 5 seconds")
                    self.reader.close()
                    self.reader = None
                    next_can_attempt = now + 5.0
                    continue

                if frame is not None:
                    self.frames += 1
                    self.accumulator.update(self.decoder.decode(frame))

                if (
                    self.accumulator.ready
                    and now - last_publish >= self.config.publish_interval_s
                    and now >= next_publish_attempt
                ):
                    try:
                        ble_sources = tuple(
                            self.ble_decoder.decode(
                                sample.values,
                                source_id=f"seplos_ble:{sample.device_id}",
                                timestamp=sample.timestamp,
                            )
                            for sample in self.ble_reader.connected_samples()
                            if sample.battery_id == self.config.battery_id
                        )
                        merged = self.merger.merge(
                            self.accumulator.snapshot(),
                            ble_sources,
                        )
                        enriched = self.derived.enrich(merged)
                        result = self.publisher.publish(enriched)
                        self.publications += 1
                        last_publish = now
                        self.last_publish = time()
                        LOG.debug(
                            "published topics=%d duration_s=%.3f",
                            result.topic_count,
                            result.duration_s,
                        )
                    except Exception:
                        self.errors += 1
                        self.mqtt_reconnects += 1
                        next_publish_attempt = now + 5.0
                        self.publisher.close()
                        LOG.exception(
                            "MQTT publication failed; retrying in 5 seconds"
                        )

                if now - last_status >= self.config.status_interval_s:
                    self._write_status()
                    LOG.info(
                        "healthy frames=%d publications=%d publish_errors=%d "
                        "can_errors=%d mqtt_reconnects=%d mqtt_connected=%s",
                        self.frames,
                        self.publications,
                        self.errors,
                        self.can_errors,
                        self.mqtt_reconnects,
                        self.publisher.connected,
                    )
                    last_status = now
        finally:
            self._write_status()
            self.publisher.close()
            self.ble_reader.close()
            if self.reader is not None:
                self.reader.close()
            LOG.info(
                "stopped frames=%d publications=%d errors=%d",
                self.frames,
                self.publications,
                self.errors,
            )
        return 0

    def _write_status(self) -> None:
        ble_status = self.ble_reader.status()
        connected_ble = [
            item for item in ble_status.values() if item["connected"]
        ]
        last_ble_updates = [
            item["last_update"]
            for item in ble_status.values()
            if item["last_update"] is not None
        ]
        last_ble_errors = [
            item["last_error"]
            for item in ble_status.values()
            if item["last_error"]
        ]
        status = {
            "uptime_seconds": round(monotonic() - self.started, 3),
            "mqtt_broker": (
                f"{self.publisher.config.host}:{self.publisher.config.port}"
            ),
            "mqtt_connected": self.publisher.connected,
            "last_publish": self.last_publish,
            "mqtt_reconnect_count": (
                self.mqtt_reconnects + self.publisher.reconnect_count
            ),
            "can_interface": self.config.can_interface,
            "can_connected": self.reader is not None,
            "can_reconnect_count": self.can_reconnects,
            "can_errors": self.can_errors,
            "frames_received": self.frames,
            "snapshots_published": self.publications,
            "publish_errors": self.errors,
            "battery_count": 1,
            "mqtt_api_version": MQTT_API_VERSION,
            "design_capacity_ah": self.accumulator.value(
                "battery.design_capacity"
            ),
            "ble_devices_configured": len(ble_status),
            "ble_devices_connected": len(connected_ble),
            "ble_disconnect_count": sum(
                item["disconnect_count"] for item in ble_status.values()
            ),
            "ble_reconnect_count": sum(
                item["reconnect_count"] for item in ble_status.values()
            ),
            "last_ble_update": max(last_ble_updates, default=None),
            "last_ble_error": last_ble_errors[-1] if last_ble_errors else None,
            "ble_devices": ble_status,
        }
        self.status_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.status_path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(status, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        temporary.replace(self.status_path)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: {Path(argv[0]).name} CONFIG.toml", file=sys.stderr)
        return 2
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    return GatewayApplication(argv[1]).run()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
