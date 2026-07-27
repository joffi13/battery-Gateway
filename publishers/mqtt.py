import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from typing import Any

import paho.mqtt.client as mqtt

from core.derived import DerivedValue, EnrichedBatterySnapshot
from core.snapshot import NormalizedMeasurement, Quality


@dataclass(frozen=True, slots=True)
class MQTTPublisherConfig:
    host: str
    port: int = 1883
    username: str | None = None
    password: str | None = None
    base_topic: str = "battery-gateway"
    retain: bool = False
    qos: int = 0

    @classmethod
    def from_file(cls, path: str | Path) -> "MQTTPublisherConfig":
        data = tomllib.loads(Path(path).read_text(encoding="utf-8"))
        mqtt_data = data.get("mqtt", data)
        return cls(
            host=str(mqtt_data["host"]),
            port=int(mqtt_data.get("port", 1883)),
            username=mqtt_data.get("username"),
            password=mqtt_data.get("password"),
            base_topic=str(mqtt_data.get("base_topic", "battery-gateway")),
            retain=bool(mqtt_data.get("retain", False)),
            qos=int(mqtt_data.get("qos", 0)),
        )


@dataclass(frozen=True, slots=True)
class PublishedMessage:
    topic: str
    payload: str
    retain: bool
    qos: int


@dataclass(frozen=True, slots=True)
class PublishResult:
    connected: bool
    topic_count: int
    batteries: tuple[str, ...]
    duration_s: float


class MQTTPublisher:
    def __init__(self, config: MQTTPublisherConfig):
        self.config = config

    def messages_for(
        self,
        enriched: EnrichedBatterySnapshot,
    ) -> tuple[PublishedMessage, ...]:
        battery_id = self._topic_part(enriched.snapshot.battery_id)
        base = f"{self.config.base_topic.strip('/')}/{battery_id}"
        messages: list[PublishedMessage] = []

        for measurement in enriched.snapshot.measurements:
            topic = self._measurement_topic(base, measurement.name)
            if topic:
                self._append_value(messages, topic, measurement)

        for cell in enriched.snapshot.cells:
            if cell.voltage is None:
                continue
            topic = f"{base}/cells/{cell.index}/voltage"
            self._append_value(messages, topic, cell.voltage)

        for temperature in enriched.snapshot.temperatures:
            if temperature.value is None:
                continue
            topic = f"{base}/temperature/{self._topic_part(temperature.kind)}"
            self._append_value(messages, topic, temperature.value)

        for derived in enriched.derived_values:
            topic = self._derived_topic(base, derived.name)
            if topic:
                self._append_derived(messages, topic, derived)
            if derived.name == "battery.charge_state":
                self._append_derived(messages, f"{base}/status/discharge_state", derived)

        self._append_payload(
            messages,
            f"{base}/quality/overall",
            enriched.snapshot.quality.state,
        )
        self._append_payload(messages, f"{base}/meta/manufacturer", "unknown")
        self._append_payload(messages, f"{base}/meta/model", "unknown")
        self._append_payload(messages, f"{base}/meta/firmware", "unknown")
        self._append_payload(messages, f"{base}/meta/source", self._sources(enriched))
        self._append_payload(
            messages,
            f"{base}/meta/snapshot_timestamp",
            enriched.snapshot.timestamp,
        )

        return tuple(messages)

    def publish(self, enriched: EnrichedBatterySnapshot) -> PublishResult:
        started = monotonic()
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.config.username:
            client.username_pw_set(self.config.username, self.config.password)

        client.connect(self.config.host, self.config.port, keepalive=30)
        client.loop_start()

        messages = self.messages_for(enriched)
        for message in messages:
            info = client.publish(
                message.topic,
                message.payload,
                qos=message.qos,
                retain=message.retain,
            )
            info.wait_for_publish()

        client.loop_stop()
        client.disconnect()

        return PublishResult(
            connected=True,
            topic_count=len(messages),
            batteries=(enriched.snapshot.battery_id,),
            duration_s=round(monotonic() - started, 3),
        )

    def _append_value(
        self,
        messages: list[PublishedMessage],
        topic: str,
        measurement: NormalizedMeasurement,
    ) -> None:
        self._append_payload(messages, topic, measurement.value)
        self._append_quality(messages, topic, measurement.quality)

    def _append_derived(
        self,
        messages: list[PublishedMessage],
        topic: str,
        derived: DerivedValue,
    ) -> None:
        self._append_payload(messages, topic, derived.value)
        self._append_quality(messages, topic, derived.quality)

    def _append_quality(
        self,
        messages: list[PublishedMessage],
        topic: str,
        quality: Quality,
    ) -> None:
        if quality.state == "valid":
            return
        self._append_payload(messages, f"{topic}/quality", quality.state)
        if quality.reason:
            self._append_payload(messages, f"{topic}/quality_reason", quality.reason)

    def _append_payload(
        self,
        messages: list[PublishedMessage],
        topic: str,
        value: Any,
    ) -> None:
        messages.append(
            PublishedMessage(
                topic=topic,
                payload=self._payload(value),
                retain=self.config.retain,
                qos=self.config.qos,
            )
        )

    @staticmethod
    def _measurement_topic(base: str, name: str) -> str | None:
        mapping = {
            "battery.voltage": "pack/voltage",
            "battery.current": "pack/current",
            "battery.soc": "pack/soc",
            "battery.soh": "pack/soh",
        }
        suffix = mapping.get(name)
        return f"{base}/{suffix}" if suffix else None

    @staticmethod
    def _derived_topic(base: str, name: str) -> str | None:
        mapping = {
            "battery.power": "pack/power",
            "battery.remaining_capacity": "pack/remaining_capacity",
            "battery.remaining_energy": "pack/remaining_energy",
            "battery.charge_state": "status/charge_state",
            "battery.charging": "status/charging",
            "battery.discharging": "status/discharging",
            "cell.average_voltage": "temperature/cell_average",
            "cell.delta_voltage": "cells/delta_voltage",
        }
        suffix = mapping.get(name)
        return f"{base}/{suffix}" if suffix else None

    @staticmethod
    def _payload(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, int | float | str):
            return str(value)
        return json.dumps(value, sort_keys=True)

    @staticmethod
    def _topic_part(value: str) -> str:
        return value.strip().lower().replace(" ", "_").replace("/", "_")

    @staticmethod
    def _sources(enriched: EnrichedBatterySnapshot) -> str:
        sources = {
            measurement.source_id
            for measurement in enriched.snapshot.measurements
        }
        sources.update(
            temperature.value.source_id
            for temperature in enriched.snapshot.temperatures
            if temperature.value is not None
        )
        return ",".join(sorted(sources)) if sources else "unknown"
