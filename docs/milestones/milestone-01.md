# Milestone 01: Minimum Viable Battery Snapshot Core

## What Was Implemented

Milestone 01 implements the smallest working internal data flow:

```text
ReplayReader
    -> RawFrame
    -> Seplos CAN Decoder
    -> Normalized Measurements
    -> BatterySnapshot
    -> formatted JSON
```

The command line entry point is:

```text
python replay_demo.py logfile.log
```

It prints:

- number of received frames,
- number of decoded normalized values,
- generated BatterySnapshot identifier,
- complete formatted snapshot JSON.

## Classes That Exist Now

The minimum core classes for this milestone are:

- RawFrame
- ReplayReader
- NormalizedMeasurement
- BatterySnapshot
- Cell
- Temperature
- Quality
- RawReference
- SeplosCANDecoder

The snapshot model is immutable-friendly. BatterySnapshot and its value objects
are frozen dataclasses.

## Architecture Parts Intentionally Not Implemented

The following architecture parts were deliberately not implemented in this
milestone:

- MQTT publishing
- Home Assistant integration
- Victron integration
- plugin loading
- multi-source conflict resolution
- database or snapshot store
- GUI or dashboard
- Derived Engine
- power calculation
- remaining energy calculation
- runtime calculation
- delta-cell calculation
- average-cell calculation
- command/control operations

The Seplos CAN decoder only translates RawFrames into normalized measurements. It
does not calculate derived values.

## Preconditions Created For Milestone 2

Milestone 01 establishes:

- a replayable input path,
- a transport-neutral RawFrame object,
- normalized measurement objects with quality and raw references,
- an immutable BatterySnapshot,
- JSON serialization of complete snapshots,
- tests for replay parsing, Seplos CAN decoding, snapshot immutability, and JSON
  serialization.

Milestone 2 can build on this by adding a small Derived Engine or expanding CAN
field coverage, without changing the Milestone 01 data flow.
