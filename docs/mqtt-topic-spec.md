# battery-gateway MQTT Topic Specification

Status: Public API specification
MQTT API version: 1.0
Normative API field: `mqtt_api_version = 1`

This document defines the public MQTT interface of battery-gateway. It is not an
implementation document.

External systems such as Home Assistant, Node-RED, Grafana, InfluxDB, Solar
Assistant, Victron, OpenEMS, and future applications may build integrations
against this specification. The internal implementation may change. This MQTT API
should remain stable.

If implementation and this specification differ, this specification is
authoritative.

## 1. Stability Rules

The MQTT API is a stable project interface.

Existing topics must not be renamed, retyped, re-scaled, or redefined without a
major MQTT API version change.

New information should be added through new topics instead of changing the
meaning of existing topics.

Backward compatibility has high priority.

## 2. Naming Conventions

Topic names use lowercase ASCII.

Words are separated with underscores.

Topic segments must not contain spaces.

`<battery_id>` must be stable for the same logical battery. It should be safe for
MQTT topic paths: lowercase letters, digits, underscore, and hyphen are
recommended.

Cell indexes are 1-based:

```text
cells/1/voltage
cells/2/voltage
```

Numeric payloads use decimal notation without unit suffixes.

Boolean payloads use:

```text
true
false
```

Unknown string values use:

```text
unknown
```

Missing optional topics should normally not be published. Consumers must tolerate
missing optional topics.

## 3. Topic Hierarchy

Default base topic:

```text
battery-gateway
```

General structure:

```text
battery-gateway/<battery_id>/<group>/<name>
```

Reserved top-level groups under a battery:

```text
pack
status
cells
temperature
quality
meta
api
```

## 4. Datatypes

Supported payload datatypes:

- `float`: decimal number
- `integer`: decimal integer
- `boolean`: `true` or `false`
- `string`: UTF-8 text

MQTT payloads are plain text.

JSON payloads are not used for the value topics in MQTT API v1.0.

## 5. Units

Units are fixed by topic and are not included in payloads.

Standard units:

- voltage: Volt
- current: Ampere
- power: Watt
- capacity: Ampere-hour
- energy: Watt-hour
- temperature: degree Celsius
- state of charge: percent
- state of health: percent
- timestamp: Unix timestamp in seconds

## 6. Rounding Rules

Publishers should avoid excessive precision.

Recommended rounding:

- pack voltage: 2 decimals
- pack current: 2 decimals
- pack power: 1 decimal
- SOC and SOH: 1 decimal
- capacity: 2 decimals
- energy: 1 decimal
- cell voltage: 3 decimals
- cell average voltage: 3 decimals
- cell delta voltage: 3 decimals
- temperature: 1 decimal
- timestamps: 3 decimals or better

Consumers must not depend on a fixed number of trailing decimal places.

## 7. QoS Recommendations

Default QoS:

```text
0
```

Recommended:

- telemetry values: QoS 0
- metadata: QoS 0 or QoS 1
- future alarms/events: QoS 1 may be appropriate

MQTT API v1.0 does not require QoS 1.

## 8. Retain Recommendations

Recommended default:

```text
retain = false
```

Retain may be enabled for:

- metadata,
- slowly changing pack values,
- dashboards that must show last known state after restart.

Retain should be used carefully for quality-sensitive values. A retained stale
value can be misleading if consumers do not also check timestamps and quality.

## 9. Quality Information

Quality information must not be lost.

Each value topic may have adjacent quality topics:

```text
<value_topic>/quality
<value_topic>/quality_reason
```

`<value_topic>/quality` is optional when quality is `valid`. It is mandatory when
quality is not `valid`.

Allowed quality values:

```text
valid
suspect
invalid
missing
estimated
sentinel
stale
unknown
```

Quality meanings:

- `valid`: value passed integrity and plausibility checks
- `suspect`: value exists but should be treated cautiously
- `invalid`: value exists but should not be used for decisions
- `missing`: value is unavailable
- `estimated`: value was calculated or inferred
- `sentinel`: value is a known placeholder or special device value
- `stale`: value is older than the freshness policy allows
- `unknown`: quality cannot be classified

## 10. Metadata and API Version

The API version is published per battery:

```text
battery-gateway/<battery_id>/api/mqtt_api_version
```

Payload:

```text
1
```

Versioning rules:

Major version change:

- existing topic is renamed or removed,
- existing topic datatype changes,
- existing topic unit changes,
- existing topic meaning changes,
- quality semantics change incompatibly.

Minor version change:

- new optional topic is added,
- new metadata topic is added,
- new quality reason is added,
- new status string is added in a backward-compatible way.

Patch version change:

- documentation clarification,
- typo fix,
- non-semantic example update,
- implementation bug fix that restores documented behavior.

MQTT API v1.0 uses integer major version topic payload `1`. Full project release
versions may be published separately in future optional metadata topics.

## 11. Topic Reference

### API Topics

#### `battery-gateway/<battery_id>/api/mqtt_api_version`

Type: integer

Unit: none

Meaning: Major MQTT API version implemented by this publisher.

Example: `1`

Required: yes

Origin: Metadata

### Pack Topics

#### `battery-gateway/<battery_id>/pack/voltage`

Type: float

Unit: Volt

Meaning: Pack voltage.

Example: `53.72`

Required: optional

Origin: Measured

#### `battery-gateway/<battery_id>/pack/current`

Type: float

Unit: Ampere

Meaning: Pack current. Positive current means charging. Negative current means
discharging.

Example: `12.4`

Required: optional

Origin: Measured

#### `battery-gateway/<battery_id>/pack/power`

Type: float

Unit: Watt

Meaning: Pack power. Positive power means charging. Negative power means
discharging.

Example: `665.1`

Required: optional

Origin: Derived

#### `battery-gateway/<battery_id>/pack/soc`

Type: float

Unit: percent

Meaning: State of charge.

Example: `82.5`

Required: optional

Origin: Measured

#### `battery-gateway/<battery_id>/pack/soh`

Type: float

Unit: percent

Meaning: State of health.

Example: `100.0`

Required: optional

Origin: Measured

#### `battery-gateway/<battery_id>/pack/design_capacity`

Type: float

Unit: Ampere-hour

Meaning: Nominal or configured battery design capacity.

Example: `570.0`

Required: optional

Origin: Measured

#### `battery-gateway/<battery_id>/pack/remaining_capacity`

Type: float

Unit: Ampere-hour

Meaning: Remaining capacity calculated from design capacity and SOC.

Example: `470.25`

Required: optional

Origin: Derived

#### `battery-gateway/<battery_id>/pack/remaining_energy`

Type: float

Unit: Watt-hour

Meaning: Remaining energy calculated from pack voltage and remaining capacity.

Example: `25251.8`

Required: optional

Origin: Derived

### Status Topics

#### `battery-gateway/<battery_id>/status/charge_state`

Type: string

Unit: none

Meaning: Current derived charge state.

Allowed values:

```text
charging
idle
discharging
unknown
```

Example: `charging`

Required: optional

Origin: Derived

#### `battery-gateway/<battery_id>/status/charging`

Type: boolean

Unit: none

Meaning: True when charge state is `charging`.

Example: `true`

Required: optional

Origin: Derived

#### `battery-gateway/<battery_id>/status/discharging`

Type: boolean

Unit: none

Meaning: True when charge state is `discharging`.

Example: `false`

Required: optional

Origin: Derived

### Cell Topics

Cell topics are optional and may be supplied by a supplementary source. Source
provenance remains attached to each normalized measurement before publication.
Adding these optional topics is backward compatible and does not change MQTT
API major version 1.

#### `battery-gateway/<battery_id>/cells/<cell_index>/voltage`

Type: float

Unit: Volt

Meaning: Voltage of one cell. Cell indexes are 1-based.

Example: `3.357`

Required: optional

Origin: Measured

#### `battery-gateway/<battery_id>/cells/average_voltage`

Type: float

Unit: Volt

Meaning: Average of valid cell voltages.

Example: `3.351`

Required: optional

Origin: Derived

#### `battery-gateway/<battery_id>/cells/min_voltage`

Type: float

Unit: Volt

Meaning: Lowest valid voltage among the cells present in the current snapshot.

Example: `3.331`

Required: optional

Origin: Measured cell selection

#### `battery-gateway/<battery_id>/cells/max_voltage`

Type: float

Unit: Volt

Meaning: Highest valid voltage among the cells present in the current snapshot.

Example: `3.410`

Required: optional

Origin: Measured cell selection

#### `battery-gateway/<battery_id>/cells/delta_voltage`

Type: float

Unit: Volt

Meaning: Difference between highest and lowest valid cell voltage.

Example: `0.018`

Required: optional

Origin: Derived

### Temperature Topics

#### `battery-gateway/<battery_id>/temperature/mosfet`

Type: float

Unit: degree Celsius

Meaning: MOSFET or power-stage temperature.

Example: `32.4`

Required: optional

Origin: Measured

#### `battery-gateway/<battery_id>/temperature/ambient`

Type: float

Unit: degree Celsius

Meaning: Ambient or case temperature reported by the battery system.

Example: `25.1`

Required: optional

Origin: Measured

#### `battery-gateway/<battery_id>/temperature/cell_average`

Type: float

Unit: degree Celsius

Meaning: Average of valid cell temperature sensors.

Example: `24.8`

Required: optional

Origin: Derived

#### `battery-gateway/<battery_id>/temperature/<kind>`

Type: float

Unit: degree Celsius

Meaning: Additional temperature value. `<kind>` should be stable and descriptive,
for example `pack`, `pcb`, `balancer`, or `heater`.

Example: `31.2`

Required: optional

Origin: Measured

### Quality Topics

#### `battery-gateway/<battery_id>/quality/overall`

Type: string

Unit: none

Meaning: Overall quality state of the current battery snapshot.

Example: `valid`

Required: yes

Origin: Metadata

#### `<value_topic>/quality`

Type: string

Unit: none

Meaning: Quality state for the adjacent value topic.

Example: `sentinel`

Required: required when value quality is not `valid`; optional otherwise

Origin: Metadata

#### `<value_topic>/quality_reason`

Type: string

Unit: none

Meaning: Human-readable reason for non-valid quality.

Example: `Device reported fixed placeholder value`

Required: optional

Origin: Metadata

### Metadata Topics

#### `battery-gateway/<battery_id>/meta/gateway_version`

Type: string

Unit: none

Meaning: Battery Gateway software version read from the repository-root
`VERSION` file. This is independent from the public MQTT API version.

Example: `0.1.0`

Required: yes

Origin: Metadata

#### `battery-gateway/<battery_id>/meta/manufacturer`

Type: string

Unit: none

Meaning: Battery or BMS manufacturer when known.

Example: `Seplos`

Required: yes

Origin: Metadata

#### `battery-gateway/<battery_id>/meta/model`

Type: string

Unit: none

Meaning: Battery or BMS model when known.

Example: `1101-SP10`

Required: yes

Origin: Metadata

#### `battery-gateway/<battery_id>/meta/firmware`

Type: string

Unit: none

Meaning: Firmware version when known.

Example: `16.6`

Required: yes

Origin: Metadata

#### `battery-gateway/<battery_id>/meta/source`

Type: string

Unit: none

Meaning: Comma-separated source identifiers that contributed to the current
published state.

Example: `seplos_can`

Required: yes

Origin: Metadata

#### `battery-gateway/<battery_id>/meta/snapshot_timestamp`

Type: float

Unit: Unix timestamp in seconds

Meaning: Timestamp of the snapshot used for this publication.

Example: `1785041802.307`

Required: yes

Origin: Metadata

## 12. Critical Review Before Freezing v1.0

The following issues should be resolved before the MQTT API is treated as frozen
version 1.0.

### Duplicated Information

`status/charge_state`, `status/charging`, and `status/discharging` duplicate the
same information. This is acceptable because many MQTT consumers prefer boolean
topics, while others prefer a single string state. The string topic should remain
the semantic source; boolean topics are convenience topics.

### Unnecessary Topics

`status/discharge_state` was considered but should not be part of API v1.0. It is
ambiguous because charge state already includes `discharging`. The clearer v1.0
shape is:

```text
status/charge_state
status/charging
status/discharging
```

### Missing Topics

The following topics are intentionally absent from v1.0 but likely useful later:

- per-cell minimum and maximum index,
- alarm topics,
- limit topics,
- per-pack topics for multi-pack systems,
- API patch/minor version metadata,
- publisher software version,
- stale timeout metadata.

They should be added as new optional topics in a minor MQTT API version.

### Naming Improvements

Cell-derived values should live under `cells`, not `temperature`.

Preferred v1.0 names:

```text
cells/average_voltage
cells/delta_voltage
```

`temperature/cell_average` should mean average cell temperature only, not average
cell voltage.

### Recommendation

Before declaring MQTT API 1.0 frozen, align the implementation with this
specification:

- publish `api/mqtt_api_version`,
- publish `pack/design_capacity` when available,
- publish `cells/average_voltage` instead of `temperature/cell_average` for
  average cell voltage,
- do not publish `status/discharge_state`,
- keep `status/charging` and `status/discharging` as boolean convenience topics.
