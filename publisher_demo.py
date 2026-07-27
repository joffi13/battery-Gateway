import sys
from pathlib import Path
from time import monotonic

from core.derived import DerivedEngine
from decoders.seplos import SeplosCANDecoder
from publishers.mqtt import MQTTPublisher, MQTTPublisherConfig
from replay_demo import build_snapshot
from readers.replay import ReplayReader


def run(logfile: str, config_file: str) -> int:
    started = monotonic()
    reader = ReplayReader(logfile)
    decoder = SeplosCANDecoder()
    measurements = []
    frames = 0

    try:
        for frame in reader:
            frames += 1
            measurements.extend(decoder.decode(frame))
    finally:
        reader.close()

    snapshot = build_snapshot(measurements)
    enriched = DerivedEngine().enrich(snapshot)
    publisher = MQTTPublisher(MQTTPublisherConfig.from_file(config_file))
    result = publisher.publish(enriched)

    print(f"Broker connected: {result.connected}")
    print(f"Published topics: {result.topic_count}")
    print(f"Published batteries: {', '.join(result.batteries)}")
    print(f"Frames processed: {frames}")
    print(f"Runtime seconds: {round(monotonic() - started, 3)}")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(
            f"Usage: python {Path(argv[0]).name} logfile.log config.toml",
            file=sys.stderr,
        )
        return 2
    return run(argv[1], argv[2])


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
