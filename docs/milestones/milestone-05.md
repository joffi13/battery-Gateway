# Milestone 05 — BLE Source Integration

## Goal

Add Seplos v2 BLE as an optional supplementary source while preserving one
neutral immutable `BatterySnapshot` and the established Derived Engine and
public MQTT API.

## Scope

- configurable multi-device BLE reader;
- Seplos v2 BLE sample decoder;
- source merger with strict CAN precedence;
- per-device connection and reconnect statistics;
- additive cell minimum and maximum MQTT topics;
- additive Home Assistant entities;
- cell status on the existing overview and a separate cell-details view.

## Invariants

- CAN remains primary.
- BLE never overwrites CAN.
- Provenance is stored on individual normalized measurements.
- The snapshot contains no transport or vendor knowledge.
- A BLE error cannot stop CAN processing or MQTT publication.
- Disconnected BLE data is not retained in a newly merged snapshot.
- Existing MQTT topics and Home Assistant entities are unchanged.

## Initial target

The first live target is:

- logical ID: `BP00`
- battery: `battery_01` / 570 Ah pack
- BLE address: `60:6E:41:26:E6:81`

BP01 through BP05 are architectural targets, not part of the initial live
connection test. They can be added through repeated `[[ble.devices]]`
configuration blocks.

## Verification

The automated tests cover CAN-only, BLE-only, CAN plus BLE, strict CAN
precedence, removal of BLE fields after disconnect, multi-device configuration,
provenance, cell decoding, and additive MQTT topics.

The live verification temporarily releases BP00 from Home Assistant, performs a
bounded direct query on the gateway, records the received cells, temperatures,
merge result and MQTT messages, and restores the original Home Assistant
integration immediately afterward.

## Initial live-test result

On 2026-07-28, Home Assistant's BP00 `bms_ble` entry was cleanly disabled for a
bounded test. The gateway adapter was enabled and scanned specifically for
`60:6E:41:26:E6:81` for 15 seconds. BP00 was not advertised or discovered at
the gateway location, so no connection was attempted and no BLE cell,
temperature, merged-snapshot, or gateway MQTT sample could be recorded.

The test was aborted at that point as required. The gateway Bluetooth adapter
was powered down and returned to its prior soft-blocked state. The Home
Assistant entry was re-enabled, reported `loaded`, and live BP00 cell updates
resumed. The interruption was therefore fully reversed.

What worked:

- bounded ownership handover and immediate rollback;
- independent BLE worker implementation and failure isolation;
- CAN-to-MQTT production service continued without BLE;
- all 37 unit tests passed on the gateway;
- Home Assistant's original BLE connection resumed successfully.

Limitation observed:

- BP00 was not discoverable from the gateway during the release window. This
  may be radio range, advertising timing, or BMS BLE behavior; the test does
  not establish a root cause.

Decision:

- direct gateway BLE is not yet approved for continuous production use;
- Home Assistant remains the sole production BLE instance;
- the gateway production configuration contains zero enabled BLE devices;
- a later test may enable BP00 alone and use the per-device disconnect,
  reconnect, connection-duration, update, and error statistics to gather
  evidence before expanding to BP01 through BP05.

## MQTT API compatibility

`cells/min_voltage` and `cells/max_voltage` are optional additive topics.
Existing topic names and payload semantics do not change, so
`mqtt_api_version` remains `1`.
