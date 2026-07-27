import dataclasses
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.derived import DerivedEngine
from core.snapshot import BatterySnapshot, Cell, NormalizedMeasurement, Quality


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
        source_id="test",
        quality=quality,
    )


def snapshot(
    measurements: tuple[NormalizedMeasurement, ...] = (),
    cells: tuple[Cell, ...] = (),
) -> BatterySnapshot:
    return BatterySnapshot(
        snapshot_id="snapshot-1",
        battery_id="battery-1",
        timestamp=1.0,
        measurements=measurements,
        cells=cells,
    )


def value_map(enriched) -> dict[str, int | float | bool | str]:
    return {item.name: item.value for item in enriched.derived_values}


class DerivedEngineTests(unittest.TestCase):
    def test_power(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot(
                (
                    measurement("battery.voltage", 52.0, "V"),
                    measurement("battery.current", 10.0, "A"),
                )
            )
        )

        self.assertEqual(value_map(enriched)["battery.power"], 520.0)

    def test_average_cell_voltage(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot(
                cells=(
                    Cell(1, measurement("cell.voltage", 3.3, "V")),
                    Cell(2, measurement("cell.voltage", 3.4, "V")),
                    Cell(3, measurement("cell.voltage", 3.5, "V")),
                )
            )
        )

        self.assertEqual(value_map(enriched)["cell.average_voltage"], 3.4)

    def test_delta_cell_voltage(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot(
                cells=(
                    Cell(1, measurement("cell.voltage", 3.3, "V")),
                    Cell(2, measurement("cell.voltage", 3.45, "V")),
                )
            )
        )

        self.assertEqual(value_map(enriched)["cell.delta_voltage"], 0.15)

    def test_charge_state_idle_at_zero_current(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot((measurement("battery.current", 0.0, "A"),))
        )

        values = value_map(enriched)
        self.assertEqual(values["battery.charge_state"], "idle")
        self.assertFalse(values["battery.charging"])
        self.assertFalse(values["battery.discharging"])

    def test_charge_state_above_deadband(self) -> None:
        enriched = DerivedEngine(current_deadband_a=0.1).enrich(
            snapshot((measurement("battery.current", 0.11, "A"),))
        )

        values = value_map(enriched)
        self.assertEqual(values["battery.charge_state"], "charging")
        self.assertTrue(values["battery.charging"])
        self.assertFalse(values["battery.discharging"])

    def test_charge_state_below_deadband(self) -> None:
        enriched = DerivedEngine(current_deadband_a=0.1).enrich(
            snapshot((measurement("battery.current", -0.11, "A"),))
        )

        values = value_map(enriched)
        self.assertEqual(values["battery.charge_state"], "discharging")
        self.assertFalse(values["battery.charging"])
        self.assertTrue(values["battery.discharging"])

    def test_remaining_capacity(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot(
                (
                    measurement("battery.design_capacity", 570.0, "Ah"),
                    measurement("battery.soc", 80.0, "%"),
                )
            )
        )

        self.assertEqual(value_map(enriched)["battery.remaining_capacity"], 456.0)

    def test_remaining_energy(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot(
                (
                    measurement("battery.voltage", 52.0, "V"),
                    measurement("battery.design_capacity", 100.0, "Ah"),
                    measurement("battery.soc", 50.0, "%"),
                )
            )
        )

        self.assertEqual(value_map(enriched)["battery.remaining_energy"], 2600.0)

    def test_no_cell_voltages(self) -> None:
        enriched = DerivedEngine().enrich(snapshot())

        values = value_map(enriched)
        self.assertNotIn("cell.average_voltage", values)
        self.assertNotIn("cell.delta_voltage", values)

    def test_one_cell_missing(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot(
                cells=(
                    Cell(1, measurement("cell.voltage", 3.3, "V")),
                    Cell(2, None),
                    Cell(3, measurement("cell.voltage", 3.5, "V")),
                )
            )
        )

        values = value_map(enriched)
        self.assertEqual(values["cell.average_voltage"], 3.4)
        self.assertEqual(values["cell.delta_voltage"], 0.2)

    def test_all_temperatures_invalid_do_not_affect_derived_values(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot(
                (
                    measurement("battery.voltage", 52.0, "V"),
                    measurement("battery.current", 2.0, "A"),
                    measurement(
                        "temperature.pack",
                        -50.0,
                        "degC",
                        Quality(state="sentinel"),
                    ),
                )
            )
        )

        self.assertEqual(value_map(enriched)["battery.power"], 104.0)

    def test_prefers_valid_measurement_over_suspect(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot(
                (
                    measurement(
                        "battery.voltage",
                        10.0,
                        "V",
                        Quality(state="suspect", confidence=0.5),
                    ),
                    measurement("battery.voltage", 52.0, "V"),
                    measurement("battery.current", 2.0, "A"),
                )
            )
        )

        self.assertEqual(value_map(enriched)["battery.power"], 104.0)

    def test_original_snapshot_is_not_modified(self) -> None:
        original = snapshot((measurement("battery.current", 0.0, "A"),))
        enriched = DerivedEngine().enrich(original)

        self.assertIs(enriched.snapshot, original)
        self.assertEqual(original.measurements[0].name, "battery.current")
        with self.assertRaises(dataclasses.FrozenInstanceError):
            enriched.snapshot.battery_id = "changed"  # type: ignore[misc]

    def test_enriched_snapshot_is_serializable(self) -> None:
        enriched = DerivedEngine().enrich(
            snapshot((measurement("battery.current", 0.0, "A"),))
        )

        data = json.loads(enriched.json())
        self.assertEqual(data["snapshot"]["battery_id"], "battery-1")
        self.assertEqual(data["derived_values"][0]["name"], "battery.charge_state")


if __name__ == "__main__":
    unittest.main()
