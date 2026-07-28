import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.snapshot import BatterySnapshot, Cell, NormalizedMeasurement, Temperature
from core.source_merger import SourceData, SourceMerger


def measurement(
    name: str,
    value: float,
    source_id: str,
    unit: str = "V",
) -> NormalizedMeasurement:
    return NormalizedMeasurement(
        name=name,
        value=value,
        unit=unit,
        timestamp=1.0,
        source_id=source_id,
    )


class SourceMergerTests(unittest.TestCase):
    def test_can_wins_and_ble_supplements_cells_and_temperatures(self) -> None:
        can = BatterySnapshot(
            snapshot_id="can",
            battery_id="battery_01",
            timestamp=1.0,
            measurements=(
                measurement("battery.voltage", 53.1, "seplos_can"),
                measurement("battery.current", 10.0, "seplos_can", "A"),
            ),
            cells=(
                Cell(
                    index=1,
                    voltage=measurement("cell.voltage", 3.31, "seplos_can"),
                ),
            ),
        )
        ble = SourceData(
            source_id="seplos_ble:BP00",
            timestamp=2.0,
            measurements=(
                measurement("battery.voltage", 52.9, "seplos_ble:BP00"),
                measurement("battery.soc", 99.0, "seplos_ble:BP00", "%"),
            ),
            cells=(
                Cell(
                    index=1,
                    voltage=measurement("cell.voltage", 3.30, "seplos_ble:BP00"),
                ),
                Cell(
                    index=2,
                    voltage=measurement("cell.voltage", 3.32, "seplos_ble:BP00"),
                ),
            ),
            temperatures=(
                Temperature(
                    temperature_id="ble:mosfet",
                    kind="mosfet",
                    value=measurement(
                        "temperature.mosfet", 31.0, "seplos_ble:BP00", "°C"
                    ),
                ),
            ),
        )

        merged = SourceMerger().merge(can, (ble,))
        values = {item.name: item for item in merged.measurements}

        self.assertEqual(values["battery.voltage"].value, 53.1)
        self.assertEqual(values["battery.voltage"].source_id, "seplos_can")
        self.assertEqual(values["battery.soc"].source_id, "seplos_ble:BP00")
        self.assertEqual(merged.cells[0].voltage.source_id, "seplos_can")
        self.assertEqual(merged.cells[1].voltage.source_id, "seplos_ble:BP00")
        self.assertEqual(
            merged.temperatures[0].value.source_id, "seplos_ble:BP00"
        )

    def test_ble_only_creates_neutral_snapshot_without_can_fallbacks(self) -> None:
        ble = SourceData(
            source_id="seplos_ble:BP00",
            timestamp=2.0,
            cells=(
                Cell(
                    index=1,
                    voltage=measurement("cell.voltage", 3.3, "seplos_ble:BP00"),
                ),
            ),
        )

        merged = SourceMerger().merge(None, (ble,), battery_id="battery_01")

        self.assertEqual(merged.battery_id, "battery_01")
        self.assertEqual(merged.measurements, ())
        self.assertEqual(merged.cells[0].voltage.source_id, "seplos_ble:BP00")

    def test_disconnected_ble_is_removed_by_omitting_its_source_data(self) -> None:
        can = BatterySnapshot(
            snapshot_id="can",
            battery_id="battery_01",
            timestamp=1.0,
            measurements=(
                measurement("battery.voltage", 53.1, "seplos_can"),
            ),
        )

        merged = SourceMerger().merge(can, ())

        self.assertEqual(merged.measurements[0].source_id, "seplos_can")
        self.assertEqual(merged.cells, ())
        self.assertEqual(merged.temperatures, ())


if __name__ == "__main__":
    unittest.main()
