from collections.abc import Mapping, Sequence
from time import time
from typing import Any

from core.snapshot import Cell, NormalizedMeasurement, Quality, RawReference, Temperature
from core.source_merger import SourceData


class SeplosBLEDecoder:
    """Normalize a decoded Seplos v2 BLE sample."""

    def decode(
        self,
        sample: Mapping[str, Any],
        *,
        source_id: str,
        timestamp: float | None = None,
    ) -> SourceData:
        observed = timestamp if timestamp is not None else time()

        def measurement(
            name: str,
            value: int | float | bool | str,
            unit: str | None,
        ) -> NormalizedMeasurement:
            return NormalizedMeasurement(
                name=name,
                value=value,
                unit=unit,
                timestamp=observed,
                source_id=source_id,
                quality=Quality(),
                raw_reference=RawReference(
                    raw_id=f"{source_id}:{observed:.6f}",
                    source_id=source_id,
                    timestamp=observed,
                    frame_id="seplos_ble_sample",
                ),
            )

        values: list[NormalizedMeasurement] = []
        field_map = {
            "voltage": ("battery.voltage", "V"),
            "current": ("battery.current", "A"),
            "battery_level": ("battery.soc", "%"),
            "battery_health": ("battery.soh", "%"),
            "design_capacity": ("battery.design_capacity", "Ah"),
            "cycles": ("battery.cycles", None),
            "chrg_mosfet": ("status.charge_mosfet", None),
            "dischrg_mosfet": ("status.discharge_mosfet", None),
            "balancer": ("status.balancer", None),
            "problem_code": ("diagnostic.problem_code", None),
        }
        for key, (name, unit) in field_map.items():
            value = sample.get(key)
            if isinstance(value, (int, float, bool)):
                values.append(measurement(name, value, unit))

        cell_values = sample.get("cell_voltages", ())
        cells = tuple(
            Cell(
                index=index,
                voltage=measurement("cell.voltage", float(value), "V"),
            )
            for index, value in enumerate(self._numeric_values(cell_values), start=1)
        )

        temperatures = tuple(
            Temperature(
                temperature_id=f"{source_id}:temperature:{index}",
                kind=self._temperature_kind(value, index),
                value=measurement(
                    f"temperature.{self._temperature_kind(value, index)}",
                    float(value),
                    "°C",
                ),
            )
            for index, value in enumerate(self._temperature_values(
                sample.get("temp_values", ())
            ), start=1)
        )
        return SourceData(
            source_id=source_id,
            timestamp=observed,
            measurements=tuple(values),
            cells=cells,
            temperatures=temperatures,
        )

    @staticmethod
    def _numeric_values(value: Any) -> tuple[Any, ...]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return ()
        return tuple(item for item in value if isinstance(item, (int, float)))

    @staticmethod
    def _temperature_values(value: Any) -> tuple[Any, ...]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
            return ()
        result: list[Any] = []
        for item in value:
            try:
                float(item)
            except (TypeError, ValueError):
                continue
            result.append(item)
        return tuple(result)

    @staticmethod
    def _temperature_kind(value: Any, index: int) -> str:
        sensor_type = getattr(value, "type", None)
        name = getattr(sensor_type, "name", "").lower()
        return (
            name
            if name and name not in {"generic", "cell"}
            else f"cell_{index}"
        )
