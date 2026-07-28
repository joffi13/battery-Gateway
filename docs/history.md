# Architecture History

This document records why Battery Gateway exists and why its major architecture
decisions were made. It complements the changelog: the changelog says what
changed, while this history preserves the reasoning behind the system.

## Why the Project Was Started

The installation contains battery systems from different manufacturers and
generations. Their CAN frames, scale factors, naming, firmware behavior, and
data quality are not uniform. Early scripts solved one immediate problem at a
time by reading one bus and publishing one value to one consumer.

That approach worked for experiments, but every new BMS or target system would
have required another tightly coupled script. Battery Gateway began as a way to
turn this collection of point solutions into one maintainable, testable data
path.

## Why Middleware Was Chosen

Neither Home Assistant, MQTT, CAN, nor a specific BMS was suitable as the center
of the architecture. Each is an endpoint or transport that may be replaced.
The project therefore became manufacturer- and consumer-independent middleware:

```text
Reader -> Decoder -> Snapshot -> Derived Engine -> Publisher
```

Readers own transport access. Decoders own protocol knowledge. Snapshots own the
normalized state. The Derived Engine owns calculations. Publishers own external
representations. This separation lets one layer evolve without silently
changing the others.

## Why Replay Came Before Live Operation

CAN protocols were investigated from recorded traffic. A replay reader made the
same frames repeatable, allowing decoder behavior and scale factors to be tested
without depending on a live battery. Replay also preserves evidence when later
firmware or improved protocol knowledge requires an old capture to be decoded
again.

## Why Snapshots Are Immutable

Mutable shared battery objects make it difficult to know which values belonged
together at a particular instant. A publisher can otherwise observe half of one
update and half of the next. They also make tests dependent on update order.

`BatterySnapshot` and its value objects were therefore made immutable. A
correction or newer measurement produces a new snapshot instead of altering an
old one. Publishers receive a coherent state, historical processing remains
reproducible, and concurrent consumers cannot change each other's data.

## Why Quality and Raw References Belong to Measurements

Battery devices can report placeholders, stale values, sentinel temperatures,
or incomplete data. A numeric payload alone is not enough to judge whether it
is safe to use. Normalized measurements retain quality and a reference to their
raw origin so that questionable data is not silently promoted to truth and
later investigations can trace a value back to its frame.

## Why Derived Values Have Their Own Layer

Power, remaining capacity, remaining energy, charge state, and cell statistics
are not raw Seplos fields. Calculating them in a decoder would mix protocol
knowledge with general battery logic. Calculating them separately in every
consumer would produce inconsistent results.

The Derived Engine was introduced as the single place for deterministic
calculations. It consumes snapshots, records its inputs, propagates quality, and
returns an enriched result without mutating the original snapshot.

## Why a Public MQTT API Was Defined

Once Home Assistant, dashboards, logging systems, and future consumers depend on
topics, those topics become a public contract. Allowing implementation details
or one consumer's naming preferences to define them would make every internal
refactor a breaking external change.

MQTT API version 1 therefore defines stable topic names, units, payload types,
quality behavior, and version semantics. The specification is authoritative
when implementation and documentation disagree. Home Assistant follows this
API; the API is never reshaped to match a Home Assistant entity layout.

The MQTT API version and Gateway software version are deliberately independent.
A bug fix or new internal reader can produce a new software release while the
public MQTT contract remains at version 1.

## Why Calculations Were Removed from Home Assistant

Home Assistant is a presentation and automation consumer, not the battery data
model. Calculations implemented as templates there are difficult to reuse in
Grafana, Node-RED, Victron, or another application, and different consumers can
end up showing different answers.

Battery Gateway now publishes normalized and derived values. Home Assistant is
display-only for this integration. It subscribes to the documented API and does
not reinterpret raw BMS data or recreate core calculations.

## Why Production Operation Uses systemd

The experimental replay and one-shot publisher paths proved the layers but did
not provide boot startup, supervision, reconnect behavior, or operational
visibility. The production runner composes the existing layers without merging
their responsibilities. systemd supplies lifecycle supervision and bounded
restart delays, while the application handles transient CAN and MQTT failures.

The legacy Seplos service is disabled but retained during the migration. Its
unit and Python source are backed up unchanged so rollback can be completed in
less than a minute until a successful 24-hour run justifies final removal.

## Decisions Intentionally Kept

- The decoder does not calculate derived battery values.
- The Snapshot layer does not read transports or publish data.
- The publisher does not own battery state.
- Home Assistant does not define the public API.
- Missing optional values are omitted instead of invented.
- New transports and BMS families should be added through replaceable readers
  and decoders, not by adding manufacturer branches throughout the core.

These boundaries are the project's long-term maintenance strategy, not merely
the shape of its first implementation.
