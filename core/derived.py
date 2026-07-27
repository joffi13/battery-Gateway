import json
from dataclasses import dataclass, field
from statistics import fmean
from typing import Any

from core.snapshot import BatterySnapshot, NormalizedMeasurement, Quality


@dataclass(frozen=True, slots=True)
class DerivedValue:
    name: str
    value: int | float | bool | str
    unit: str | None
    quality: Quality
    input_names: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "quality": self.quality.to_dict(),
            "input_names": list(self.input_names),
        }


@dataclass(frozen=True, slots=True)
class EnrichedBatterySnapshot:
    snapshot: BatterySnapshot
    derived_values: tuple[DerivedValue, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "snapshot": self.snapshot.to_dict(),
            "derived_values": [item.to_dict() for item in self.derived_values],
        }

    def json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)


@dataclass(frozen=True, slots=True)
class DerivedEngine:
    current_deadband_a: float = 0.1
    source_id: str = "derived"

    def enrich(self, snapshot: BatterySnapshot) -> EnrichedBatterySnapshot:
        values: list[DerivedValue] = []

        voltage = self._measurement(snapshot, "battery.voltage")
        current = self._measurement(snapshot, "battery.current")
        soc = self._measurement(snapshot, "battery.soc")
        design_capacity = self._measurement(snapshot, "battery.design_capacity")

        if voltage and current:
            values.append(
                self._value(
                    "battery.power",
                    round(float(voltage.value) * float(current.value), 3),
                    "W",
                    ("battery.voltage", "battery.current"),
                    voltage,
                    current,
                )
            )

        cell_voltages = self._cell_voltages(snapshot)
        if cell_voltages:
            values.append(
                self._value(
                    "cell.average_voltage",
                    round(fmean(cell_voltages), 3),
                    "V",
                    ("cell.voltage",),
                )
            )
            values.append(
                self._value(
                    "cell.delta_voltage",
                    round(max(cell_voltages) - min(cell_voltages), 3),
                    "V",
                    ("cell.voltage",),
                )
            )

        if current:
            current_value = float(current.value)
            if current_value > self.current_deadband_a:
                charge_state = "charging"
            elif current_value < -self.current_deadband_a:
                charge_state = "discharging"
            else:
                charge_state = "idle"

            values.extend(
                (
                    self._value(
                        "battery.charge_state",
                        charge_state,
                        None,
                        ("battery.current",),
                        current,
                    ),
                    self._value(
                        "battery.charging",
                        charge_state == "charging",
                        None,
                        ("battery.current",),
                        current,
                    ),
                    self._value(
                        "battery.discharging",
                        charge_state == "discharging",
                        None,
                        ("battery.current",),
                        current,
                    ),
                )
            )

        remaining_capacity: DerivedValue | None = None
        if design_capacity and soc:
            remaining_capacity = self._value(
                "battery.remaining_capacity",
                round(float(design_capacity.value) * float(soc.value) / 100, 3),
                "Ah",
                ("battery.design_capacity", "battery.soc"),
                design_capacity,
                soc,
            )
            values.append(remaining_capacity)

        if voltage and remaining_capacity:
            values.append(
                self._value(
                    "battery.remaining_energy",
                    round(float(voltage.value) * float(remaining_capacity.value), 3),
                    "Wh",
                    ("battery.voltage", "battery.remaining_capacity"),
                    voltage,
                )
            )

        return EnrichedBatterySnapshot(snapshot=snapshot, derived_values=tuple(values))

    def _measurement(
        self,
        snapshot: BatterySnapshot,
        name: str,
    ) -> NormalizedMeasurement | None:
        candidates = [item for item in snapshot.measurements if item.name == name]
        if not candidates:
            return None

        valid = [item for item in candidates if item.quality.state == "valid"]
        if valid:
            return valid[-1]

        usable = [
            item
            for item in candidates
            if item.quality.state not in {"invalid", "missing", "sentinel"}
        ]
        return usable[-1] if usable else None

    @staticmethod
    def _cell_voltages(snapshot: BatterySnapshot) -> list[float]:
        return [
            float(cell.voltage.value)
            for cell in snapshot.cells
            if cell.voltage is not None
            and cell.quality.state == "valid"
            and cell.voltage.quality.state == "valid"
        ]

    @staticmethod
    def _value(
        name: str,
        value: int | float | bool | str,
        unit: str | None,
        input_names: tuple[str, ...],
        *inputs: NormalizedMeasurement,
    ) -> DerivedValue:
        quality = Quality()
        if inputs and any(item.quality.state != "valid" for item in inputs):
            quality = Quality(
                state="suspect",
                confidence=min(item.quality.confidence for item in inputs),
                flags=("uses_non_valid_input",),
            )
        return DerivedValue(
            name=name,
            value=value,
            unit=unit,
            quality=quality,
            input_names=input_names,
        )
