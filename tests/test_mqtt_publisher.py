import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.derived import DerivedEngine
from core.snapshot import BatterySnapshot, NormalizedMeasurement, Quality
from publishers.mqtt import MQTTPublisher, MQTTPublisherConfig


def measurement(
    name: str,
    value: int | float | bool | str,
    unit: str | None = None,
    quality: Quality = Quality(),
) -> NormalizedMeasurement:
    return NormalizedMeasurement(
        name=name,
        value=value,
        unit=unit,
        timestamp=1.0,
        source_id="test_source",
        quality=quality,
    )


class MQTTPublisherTests(unittest.TestCase):
    def test_config_loads_from_toml(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".toml") as file:
            file.write(
                "[mqtt]\n"
                "host = \"localhost\"\n"
                "port = 1884\n"
                "base_topic = \"test-base\"\n"
                "retain = true\n"
                "qos = 1\n"
            )
            file.flush()

            config = MQTTPublisherConfig.from_file(file.name)

        self.assertEqual(config.host, "localhost")
        self.assertEqual(config.port, 1884)
        self.assertEqual(config.base_topic, "test-base")
        self.assertTrue(config.retain)
        self.assertEqual(config.qos, 1)

    def test_messages_are_built_from_enriched_snapshot_only(self) -> None:
        snapshot = BatterySnapshot(
            snapshot_id="s1",
            battery_id="battery_01",
            timestamp=1.0,
            measurements=(
                measurement("battery.voltage", 52.0, "V"),
                measurement("battery.current", 2.0, "A"),
                measurement("battery.soc", 80.0, "%"),
                measurement("battery.soh", 99.0, "%"),
                measurement("battery.design_capacity", 100.0, "Ah"),
            ),
        )
        enriched = DerivedEngine().enrich(snapshot)
        publisher = MQTTPublisher(
            MQTTPublisherConfig(host="localhost", base_topic="battery-gateway")
        )

        messages = publisher.messages_for(enriched)
        topics = {message.topic: message.payload for message in messages}

        self.assertEqual(topics["battery-gateway/battery_01/pack/voltage"], "52.0")
        self.assertEqual(topics["battery-gateway/battery_01/pack/current"], "2.0")
        self.assertEqual(topics["battery-gateway/battery_01/pack/power"], "104.0")
        self.assertEqual(topics["battery-gateway/battery_01/pack/soc"], "80.0")
        self.assertEqual(topics["battery-gateway/battery_01/pack/soh"], "99.0")
        self.assertEqual(
            topics["battery-gateway/battery_01/pack/remaining_capacity"],
            "80.0",
        )
        self.assertEqual(
            topics["battery-gateway/battery_01/pack/remaining_energy"],
            "4160.0",
        )
        self.assertEqual(
            topics["battery-gateway/battery_01/status/charge_state"],
            "charging",
        )
        self.assertEqual(
            topics["battery-gateway/battery_01/status/discharge_state"],
            "charging",
        )
        self.assertEqual(topics["battery-gateway/battery_01/status/charging"], "true")
        self.assertEqual(
            topics["battery-gateway/battery_01/status/discharging"],
            "false",
        )
        self.assertEqual(topics["battery-gateway/battery_01/meta/source"], "test_source")

    def test_quality_topics_are_published_for_non_valid_values(self) -> None:
        snapshot = BatterySnapshot(
            snapshot_id="s1",
            battery_id="battery_01",
            timestamp=1.0,
            measurements=(
                measurement(
                    "battery.voltage",
                    52.0,
                    "V",
                    Quality(state="suspect", reason="test"),
                ),
            ),
        )
        enriched = DerivedEngine().enrich(snapshot)
        publisher = MQTTPublisher(MQTTPublisherConfig(host="localhost"))

        topics = {message.topic: message.payload for message in publisher.messages_for(enriched)}

        self.assertEqual(
            topics["battery-gateway/battery_01/pack/voltage/quality"],
            "suspect",
        )
        self.assertEqual(
            topics["battery-gateway/battery_01/pack/voltage/quality_reason"],
            "test",
        )


if __name__ == "__main__":
    unittest.main()
