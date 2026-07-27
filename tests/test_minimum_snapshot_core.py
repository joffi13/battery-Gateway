import dataclasses
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.frame import RawFrame
from core.snapshot import Quality
from decoders.seplos import SeplosCANDecoder
from readers.replay import ReplayReader
from replay_demo import build_snapshot


class MinimumSnapshotCoreTests(unittest.TestCase):
    def test_replay_reader_parses_compact_candump(self) -> None:
        reader = ReplayReader("logs/seplos.log")
        try:
            frame = reader.read()
        finally:
            reader.close()

        self.assertIsNotNone(frame)
        assert frame is not None
        self.assertEqual(frame.identifier, 0x351)
        self.assertEqual(frame.data, bytes.fromhex("4202E8039E07D001"))

    def test_seplos_can_decoder_outputs_normalized_measurements_only(self) -> None:
        frame = RawFrame(
            bus="can0",
            identifier=0x356,
            data=bytes.fromhex("D714D2010CFE1000"),
            timestamp=1.0,
            sequence=1,
        )

        decoded = SeplosCANDecoder().decode(frame)

        self.assertEqual(
            [item.name for item in decoded],
            [
                "battery.voltage",
                "battery.current",
                "temperature.pack",
            ],
        )
        self.assertEqual(decoded[0].value, 53.35)
        self.assertEqual(decoded[1].value, 46.6)
        self.assertEqual(decoded[2].value, -50.0)
        self.assertEqual(decoded[2].quality.state, "sentinel")

    def test_battery_snapshot_is_immutable_and_serializable(self) -> None:
        measurements = list(
            SeplosCANDecoder().decode(
                RawFrame(
                    bus="can0",
                    identifier=0x355,
                    data=bytes.fromhex("2C00640030110000"),
                    timestamp=1.0,
                    sequence=1,
                )
            )
        )
        snapshot = build_snapshot(measurements)

        self.assertEqual(snapshot.measurements[0].name, "battery.soc")

        data = json.loads(snapshot.json())
        self.assertEqual(data["measurements"][0]["name"], "battery.soc")
        self.assertEqual(data["measurements"][0]["raw_reference"]["frame_id"], "0x355")

        with self.assertRaises(dataclasses.FrozenInstanceError):
            snapshot.battery_id = "changed"  # type: ignore[misc]

    def test_quality_state_is_serializable(self) -> None:
        self.assertEqual(Quality(state="valid").to_dict()["state"], "valid")


if __name__ == "__main__":
    unittest.main()
