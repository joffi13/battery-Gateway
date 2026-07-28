# Battery Gateway 0.1.0 — Technical Release Report

Date: 2026-07-28
Release candidate: 0.1.0
MQTT API: version 1

## 1. Architecture Overview

Battery Gateway uses one directional, replaceable processing pipeline:

```text
SocketCAN Reader
    -> Seplos Decoder
    -> BatterySnapshot
    -> Derived Engine
    -> MQTT Publisher
```

The production runner composes these layers but does not merge their
responsibilities.

### Reader

`SocketCANReader` reads raw frames from Linux SocketCAN on `can0` and converts
them to transport-neutral `RawFrame` objects. It does not decode Seplos fields,
calculate battery values, or know MQTT topics. The existing `ReplayReader`
provides the same `RawFrame` boundary for deterministic offline tests.

If `can0` is unavailable during startup or disappears temporarily, the
production runner retries with a bounded five-second delay instead of entering a
busy loop.

### Decoder

`SeplosCANDecoder` owns the Seplos CAN field definitions and unit conversion. It
turns `RawFrame` objects into normalized measurements with timestamps, quality,
source identity, and raw references.

The production path currently decodes pack voltage, current, SOC, SOH, pack
temperature, limits, alarm bitfield, and design capacity. Design capacity is
read from CAN frame `0x379`; the observed production value is 570 Ah.

The decoder does not calculate power, energy, charge state, or cell statistics.

### BatterySnapshot

`BatterySnapshot` is the immutable source of battery state passed between core
layers. Frozen value objects and tuples prevent a publisher or calculation from
modifying an already-created state. A later measurement produces a new
snapshot.

Quality and raw references remain attached to normalized values. The observed
fixed `-50 °C` pack-temperature sentinel is therefore published with
`sentinel` quality instead of being silently treated as a valid temperature.

### Derived Engine

The Derived Engine consumes a snapshot and returns an
`EnrichedBatterySnapshot` without modifying the original. It calculates:

- pack power;
- charging, idle, or discharging state;
- charging and discharging booleans;
- remaining capacity;
- remaining energy;
- average and delta cell voltage when cell measurements are available.

Calculations are performed once in the gateway rather than independently in
Home Assistant or other consumers.

### MQTT Publisher

The publisher consumes only enriched snapshots. It maintains the broker
connection, reconnects with bounded delays, and publishes the documented public
API below:

```text
battery-gateway/<battery_id>/...
```

The four implementation discrepancies found before production were corrected:

- `api/mqtt_api_version` is published with value `1`;
- `pack/design_capacity` is published when decoded;
- average cell voltage uses `cells/average_voltage`;
- the non-API `status/discharge_state` topic is not published.

The software version is read exclusively from the repository-root `VERSION`
file and published separately as `meta/gateway_version`. Software version and
MQTT API version can evolve independently.

### systemd Service

`battery-gateway.service` runs as the unprivileged `michi` user with:

- `Wants=network-online.target`;
- `After=network-online.target`;
- `Restart=always`;
- `RestartSec=5`;
- a defined working directory;
- systemd journal logging;
- filesystem and privilege hardening.

The legacy `seplos-can.service` is installed but stopped and disabled. Its unit
and Python source are preserved unchanged and backed up byte-for-byte outside
the Git worktree. Rollback remains possible in less than one minute.

`battery-gateway-status` is a read-only diagnostic command. It reports runtime,
connection, error, counter, API, version, and capacity information without
changing service state.

## 2. Test Results

### Unit Tests

Command:

```text
python3 -m unittest discover -s tests -v
```

Result:

- 31 tests executed;
- 31 passed;
- 0 failed;
- 0 errors.

Coverage includes CAN parsing, replay, Seplos decoding, immutable snapshots,
quality serialization, Derived Engine calculations, MQTT topic generation,
API discrepancy regression checks, and project-version loading.

### Short Test

The live foreground test ran for approximately 16 seconds:

- 257 CAN frames processed;
- 4 snapshots published;
- central Mosquitto connection successful;
- MQTT API topics verified;
- 0 publication errors;
- clean SIGTERM shutdown.

### First Long-Term Test

Window:

- 2026-07-28 09:35:45 to 10:36:04 +07:00;
- 60 minutes 19 seconds;
- 61 samples.

Result:

- active in all 61 samples;
- unchanged PID;
- 0 systemd restarts;
- 0 MQTT probe failures;
- 0 error-priority journal entries;
- 0 exceptions or tracebacks;
- 0 publish failures;
- 59,520 cumulative frames and 745 cumulative snapshots at the first health
  report after the window.

This run validated the production pipeline before the final version and
diagnostic refinements.

### Final Long-Term Test

Window:

- 2026-07-28 10:40:23 to 11:40:49 +07:00;
- 60 minutes 26 seconds;
- 61 samples;
- final version 0.1.0 runtime and diagnostics.

Result:

- active in all 61 samples;
- unchanged PID;
- 57,760 frames received during the measured window;
- 722 snapshots published during the measured window;
- 0 MQTT reconnects;
- 0 CAN errors;
- 0 publish errors;
- 0 CAN-disconnected samples;
- 0 MQTT API probe failures;
- 0 exceptions, tracebacks, or error-priority journal entries;
- 0 systemd restarts.

The active snapshot shape produced 22 MQTT publish operations per snapshot.
Accordingly, the final measured window issued 15,884 MQTT message publications.
This is the publisher-side count; QoS 0 does not provide end-to-end delivery
acknowledgement. Independent MQTT subscriptions successfully read API version 1
in every sample.

## 3. Runtime Statistics

The release decision uses the final long-term test:

| Metric | Result |
|---|---:|
| Measured duration | 3,626 s |
| Samples | 61 |
| Received CAN frames | 57,760 |
| Generated/published snapshots | 722 |
| MQTT publish operations | 15,884 |
| Average snapshot publish rate | 11.947 snapshots/min |
| Average MQTT message rate | 262.835 messages/min |
| MQTT reconnects | 0 |
| CAN errors | 0 |
| Publish errors | 0 |
| Service restarts | 0 |
| CPU time | 21.147 s |
| Average CPU utilization | 0.583% of one CPU |
| Maximum one-minute CPU utilization | 0.601% of one CPU |
| Minimum RSS | 32,188 KiB |
| Average RSS | 32,208.6 KiB |
| Maximum RSS | 32,228 KiB |

Memory varied by only 40 KiB across the final window and showed no leak trend.

CPU utilization was calculated from consecutive cgroup CPU-time samples. The
maximum therefore represents the busiest observed approximately one-minute
interval, not a sub-second instantaneous peak.

Maximum end-to-end processing time per snapshot was not captured during these
tests. The publisher internally measures publication duration, but debug-level
per-publication records were intentionally not enabled for the production
stability run. No retrospective maximum is stated because it would be an
estimate rather than an observed value. A future benchmark should record a
bounded latency histogram or maximum covering snapshot construction, derivation,
and MQTT publication.

SocketCAN remained `UP`, `LOWER_UP`, and `ERROR-ACTIVE`. Kernel counters showed
zero bus errors, arbitration losses, warning/passive transitions, controller
restarts, and bus-off events. The interface had 112 cumulative RX queue drops,
but no pre-test baseline existed, so they cannot be attributed to either
stability window. They caused no observed gateway error or missing MQTT probe.

## 4. Known Limitations

### Not Yet Implemented

- Full decoding and publication of individual Seplos cell voltages on this CAN
  profile.
- Minimum/maximum cell index topics.
- Public alarm and limit topics in MQTT API v1.
- An explicit online/availability topic.
- Manufacturer, model, and firmware extraction; these currently publish
  `unknown`.
- Multiple simultaneously configured batteries in the production runner.
- Additional live readers such as BLE, RS485, UART, TCP, or UDP.
- Additional production decoders for Batrium, JK, Pace, Daly, and other BMS
  families.
- Command, control, write, RPC, REST, or charging-control functions.
- Persistent snapshot storage and historical replay from the production
  service.
- Automated packaging and release CI.
- A completed 24-hour migration soak.

### Planned Extensions

- Expand Seplos field coverage without moving derived calculations into the
  decoder.
- Add replaceable readers and manufacturer decoders behind the existing layer
  boundaries.
- Add optional MQTT API topics through backward-compatible minor API
  extensions.
- Add CI for the supported Python versions, release checks, and Git tags.
- Add longer production soak tests and tracked CAN queue-drop baselines.
- Add richer identity metadata and availability/freshness reporting.

## 5. Technical Recommendation

Version 0.1.0 is technically suitable for productive use in its defined scope:
read-only monitoring of the current Seplos battery on `can0` and publication to
the central Home Assistant Mosquitto broker.

It can be released as the first stable project version because:

- layer responsibilities remain separated and independently testable;
- snapshots are immutable;
- calculated values have one authoritative implementation;
- the public MQTT API is documented and its known discrepancies are fixed;
- the service uses bounded retries and systemd supervision;
- diagnostics expose the important operational counters;
- all 31 tests pass;
- both independent one-hour live tests passed;
- CPU and memory use are low and stable;
- no reconnect, CAN, publish, exception, or restart event occurred in the final
  test;
- the legacy service is preserved for immediate rollback.

The recommendation is scoped, not unconditional. Version 0.1.0 should not yet be
presented as a complete multi-vendor battery platform, and the legacy Seplos
service must not be removed until the separate 24-hour production soak has
completed successfully.

## Release Preparation

The repository is prepared for the first official release:

- release version: `0.1.0`;
- planned annotated Git tag: `v0.1.0`;
- tag status: prepared, not created;
- changelog entry: present;
- Semantic Versioning and release procedure: documented.

The tag should be created only after the release commit is present on GitHub and
the operator explicitly authorizes tag creation.
