# Milestone 01 Review

Status: completed after Milestone 01
Scope: code and architecture review only

No new features were added during this review. The only code change was a minimal
hardening refactor: the old prototype Seplos decoder wrapper was removed from the
Milestone 01 path, and the legacy decoder test now exercises SeplosCANDecoder
directly.

## What Is Good

The implemented Milestone 01 data flow is clear and small:

```text
ReplayReader -> RawFrame -> SeplosCANDecoder -> NormalizedMeasurement
    -> BatterySnapshot -> JSON
```

BatterySnapshot and the value objects used by the new core are frozen dataclasses.
This matches the architecture rule that snapshots must be immutable and safe to
share.

ReplayReader and SeplosCANDecoder are separated. ReplayReader produces RawFrame
objects and does not know Seplos, CAN field meanings, scale factors, or snapshot
rules. SeplosCANDecoder consumes RawFrame objects and does not know whether the
frame came from replay or a future live CAN reader.

The decoder currently emits normalized measurements only. It does not calculate
power, runtime, remaining energy, average cell voltage, delta cell voltage, or
charge/discharge state. That matches the architecture rule that derived values do
not belong in decoders.

JSON output contains the complete snapshot, including measurements, quality, and
raw references. This is sufficient for the first replayable end-to-end flow.

File sizes are still small. The Milestone 01 core files are easy to read:

- core/frame.py: RawFrame
- core/snapshot.py: snapshot value objects
- readers/replay.py: replay parsing only
- decoders/seplos.py: minimal CAN decoding only
- replay_demo.py: end-to-end demonstration only

## Risks

RawFrame currently fits CAN replay well, but it is not yet proven for BLE and
RS485. The `identifier` field is an integer, which works naturally for CAN IDs
but may be too narrow for BLE characteristics or register-oriented protocols.
This should not be changed before Milestone 2 unless a second transport is
actually implemented.

The repository still contains older prototype modules:

- core/battery.py
- core/manager.py
- core/event.py
- core/eventbus.py
- publishers/base.py
- main.py

These are not part of the Milestone 01 snapshot flow. They still calculate or
hold mutable state in ways that do not match the target architecture. Existing
legacy tests still exercise them, so they were not removed in this review.

The snapshot model is immutable at the dataclass level, but immutability depends
on using immutable field values. Current tuple usage is correct. Future changes
must not introduce lists or mutable dictionaries directly into BatterySnapshot.

Quality and RawReference are intentionally minimal. They satisfy Milestone 01,
but they do not yet express full provenance, freshness, or conflict resolution.
That is acceptable for this milestone.

## Possible Simplifications

The old prototype modules should be either moved under a legacy/examples area or
removed once the new snapshot flow replaces their tests. Keeping two battery
models in active-looking locations is confusing.

decoders/base.py is not needed by the current Milestone 01 flow. It can remain
temporarily, but it should not become the start of a plugin framework before the
project actually needs one.

publishers/base.py is premature for the current milestone because there is no
publisher layer yet. It should not be expanded before publisher requirements are
explicitly scheduled.

The demo currently builds one snapshot from all decoded measurements in a replay
file. That is acceptable for Milestone 01. Later, snapshot boundaries should be
defined deliberately, but not before there is a concrete requirement.

## Technical Debt

There are two active concepts of battery state in the repository:

- the old mutable Battery/BatteryManager prototype,
- the new immutable BatterySnapshot model.

This is the main technical debt before Milestone 2. It is tolerable only because
the Milestone 01 flow does not depend on the old mutable model.

Some tests are script-style tests with top-level execution and print output. They
work, but they make the test suite noisy and less structured.

The repository contains ignored __pycache__ files in the working directory. They
are not tracked, but they make file listings noisy.

Several documentation placeholders are empty. They are harmless, but they can
make the documentation tree look more complete than it is.

## Changes Recommended Before Milestone 2

Before adding new functionality, decide what to do with the old mutable
Battery/BatteryManager path:

- remove it,
- move it to examples/legacy,
- or explicitly mark it deprecated.

The recommended option is removal once no tests depend on it.

Convert the remaining script-style tests to unittest or another single test
style. This is cleanup only; it should not change runtime behavior.

Add a short README reference to replay_demo.py after Milestone 2 scope is defined.
Do not expand publisher or plugin documentation yet.

## Points That Should Not Be Changed

Do not add MQTT, Home Assistant, Victron, database, GUI, or plugin code before the
next milestone explicitly requires it.

Do not move derived calculations into SeplosCANDecoder.

Do not make BatterySnapshot mutable.

Do not make ReplayReader know anything about Seplos fields.

Do not turn decoders/base.py into a larger abstraction framework yet.

Do not generalize RawFrame for BLE or RS485 until a real second transport is
implemented and tested.

## Review Conclusion

Milestone 1 is stable and ready for Milestone 2, with one caveat: the repository
still contains legacy mutable battery-state code that should be cleaned up before
the new core grows around it.
