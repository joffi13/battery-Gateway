import sys
from pathlib import Path

from core.snapshot import BatterySnapshot, NormalizedMeasurement, Temperature
from decoders.seplos import SeplosCANDecoder
from readers.replay import ReplayReader


def build_snapshot(
    measurements: list[NormalizedMeasurement],
    battery_id: str = "battery_01",
) -> BatterySnapshot:
    timestamp = measurements[-1].timestamp if measurements else 0.0
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
        snapshot_id=f"{battery_id}:{timestamp:.6f}",
        battery_id=battery_id,
        timestamp=timestamp,
        measurements=tuple(measurements),
        temperatures=temperatures,
    )


def run(logfile: str) -> BatterySnapshot:
    reader = ReplayReader(logfile)
    decoder = SeplosCANDecoder()
    frames = 0
    measurements: list[NormalizedMeasurement] = []

    try:
        for frame in reader:
            frames += 1
            measurements.extend(decoder.decode(frame))
    finally:
        reader.close()

    snapshot = build_snapshot(measurements)

    print(f"Frames received: {frames}")
    print(f"Decoded values: {len(measurements)}")
    print(f"BatterySnapshot: {snapshot.snapshot_id}")
    print(snapshot.json())

    return snapshot


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"Usage: python {Path(argv[0]).name} logfile.log", file=sys.stderr)
        return 2

    run(argv[1])
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
