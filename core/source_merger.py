from dataclasses import dataclass
from time import time

from core.snapshot import (
    BatterySnapshot,
    Cell,
    NormalizedMeasurement,
    Quality,
    Temperature,
)


@dataclass(frozen=True, slots=True)
class SourceData:
    source_id: str
    timestamp: float
    measurements: tuple[NormalizedMeasurement, ...] = ()
    cells: tuple[Cell, ...] = ()
    temperatures: tuple[Temperature, ...] = ()


class SourceMerger:
    """Merge source data without exposing transport details to the snapshot."""

    def merge(
        self,
        primary: BatterySnapshot | None,
        supplementary: tuple[SourceData, ...] = (),
        *,
        battery_id: str | None = None,
    ) -> BatterySnapshot:
        measurements: dict[str, NormalizedMeasurement] = {}
        cells: dict[int, Cell] = {}
        temperatures: dict[str, Temperature] = {}
        timestamps: list[float] = []

        if primary is not None:
            battery_id = primary.battery_id
            timestamps.append(primary.timestamp)
            measurements.update(
                (measurement.name, measurement)
                for measurement in primary.measurements
            )
            cells.update((cell.index, cell) for cell in primary.cells)
            temperatures.update(
                (temperature.temperature_id, temperature)
                for temperature in primary.temperatures
            )

        for source in supplementary:
            timestamps.append(source.timestamp)
            for measurement in source.measurements:
                measurements.setdefault(measurement.name, measurement)
            for cell in source.cells:
                cells.setdefault(cell.index, cell)
            for temperature in source.temperatures:
                temperatures.setdefault(temperature.temperature_id, temperature)

        if battery_id is None:
            raise ValueError("battery_id is required when no primary snapshot exists")

        timestamp = max(timestamps, default=time())
        return BatterySnapshot(
            snapshot_id=f"{battery_id}:{timestamp:.6f}",
            battery_id=battery_id,
            timestamp=timestamp,
            measurements=tuple(measurements.values()),
            cells=tuple(cells[index] for index in sorted(cells)),
            temperatures=tuple(
                temperatures[key] for key in sorted(temperatures)
            ),
            quality=primary.quality if primary is not None else Quality(),
        )
