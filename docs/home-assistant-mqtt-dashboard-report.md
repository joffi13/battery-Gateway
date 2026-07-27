# Home Assistant MQTT Dashboard Report

Status: Milestone 3 client validation

This report describes the Home Assistant package and dashboard that consume only
the public battery-gateway MQTT API v1.

## Files

- `homeassistant/packages/battery_gateway_mqtt.yaml`
- `homeassistant/dashboards/battery_gateway_mqtt_dashboard.yaml`

## Scope

Home Assistant is treated only as a client. The package contains MQTT sensors and
binary sensors. It does not define automations, helpers, scripts, command
entities, write access, or battery calculations.

The dashboard displays existing MQTT payloads. It does not calculate power,
remaining energy, cell average, cell delta, minimum cell, maximum cell, or charge
state in Home Assistant.

## MQTT Topics Used

API and metadata:

- `battery-gateway/battery_01/api/mqtt_api_version`
- `battery-gateway/battery_01/meta/manufacturer`
- `battery-gateway/battery_01/meta/model`
- `battery-gateway/battery_01/meta/firmware`
- `battery-gateway/battery_01/meta/source`
- `battery-gateway/battery_01/meta/snapshot_timestamp`

Pack:

- `battery-gateway/battery_01/pack/voltage`
- `battery-gateway/battery_01/pack/current`
- `battery-gateway/battery_01/pack/power`
- `battery-gateway/battery_01/pack/soc`
- `battery-gateway/battery_01/pack/soh`
- `battery-gateway/battery_01/pack/design_capacity`
- `battery-gateway/battery_01/pack/remaining_capacity`
- `battery-gateway/battery_01/pack/remaining_energy`

Status:

- `battery-gateway/battery_01/status/charge_state`
- `battery-gateway/battery_01/status/charging`
- `battery-gateway/battery_01/status/discharging`

Cells:

- `battery-gateway/battery_01/cells/1/voltage`
- `battery-gateway/battery_01/cells/2/voltage`
- `battery-gateway/battery_01/cells/3/voltage`
- `battery-gateway/battery_01/cells/4/voltage`
- `battery-gateway/battery_01/cells/5/voltage`
- `battery-gateway/battery_01/cells/6/voltage`
- `battery-gateway/battery_01/cells/7/voltage`
- `battery-gateway/battery_01/cells/8/voltage`
- `battery-gateway/battery_01/cells/9/voltage`
- `battery-gateway/battery_01/cells/10/voltage`
- `battery-gateway/battery_01/cells/11/voltage`
- `battery-gateway/battery_01/cells/12/voltage`
- `battery-gateway/battery_01/cells/13/voltage`
- `battery-gateway/battery_01/cells/14/voltage`
- `battery-gateway/battery_01/cells/15/voltage`
- `battery-gateway/battery_01/cells/16/voltage`
- `battery-gateway/battery_01/cells/average_voltage`
- `battery-gateway/battery_01/cells/delta_voltage`

Temperatures:

- `battery-gateway/battery_01/temperature/mosfet`
- `battery-gateway/battery_01/temperature/ambient`
- `battery-gateway/battery_01/temperature/cell_average`

Quality:

- `battery-gateway/battery_01/quality/overall`
- adjacent `/quality` topics for pack, cell-derived, and temperature values

## Missing in MQTT API v1

The following information is requested by the dashboard goal but is not available
as a stable MQTT API v1 topic:

- explicit availability or online state topic,
- cell minimum voltage,
- cell minimum index,
- cell maximum voltage,
- cell maximum index,
- list of available cell indexes,
- list of available temperature channels,
- quality topics for every individual cell voltage,
- ISO-8601 snapshot timestamp.

No Home Assistant workaround was added for these gaps. The dashboard shows a
short static note where values are missing.

## Redundant Topics

`status/charge_state`, `status/charging`, and `status/discharging` overlap.
Keeping all three is useful: `charge_state` is the semantic state and the boolean
topics are convenient for dashboards and binary sensors.

The current implementation still publishes `status/discharge_state`. This topic
is intentionally not used because the public MQTT specification recommends
excluding it from API v1.0.

## Implementation Mismatches Found

The Home Assistant package follows `docs/mqtt-topic-spec.md`, not the current
publisher implementation.

Known mismatch:

- the current publisher maps `cell.average_voltage` to
  `temperature/cell_average`;
- the public API specifies `cells/average_voltage`.

This should be corrected in the publisher before declaring MQTT API v1.0 frozen.

## Recommended MQTT API v1.1 Improvements

Add optional topics:

- `battery-gateway/<battery_id>/availability/state`
- `battery-gateway/<battery_id>/cells/min_voltage`
- `battery-gateway/<battery_id>/cells/min_voltage_index`
- `battery-gateway/<battery_id>/cells/max_voltage`
- `battery-gateway/<battery_id>/cells/max_voltage_index`
- `battery-gateway/<battery_id>/cells/count`
- `battery-gateway/<battery_id>/temperature/available`
- `battery-gateway/<battery_id>/meta/snapshot_iso_timestamp`
- `battery-gateway/<battery_id>/meta/publisher_version`

Consider publishing per-cell quality:

- `battery-gateway/<battery_id>/cells/<cell_index>/voltage/quality`
- `battery-gateway/<battery_id>/cells/<cell_index>/voltage/quality_reason`

These additions are backward-compatible and should be minor-version API changes.
