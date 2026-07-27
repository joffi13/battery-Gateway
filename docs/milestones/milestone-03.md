# Milestone 03: Generic MQTT Publisher

## Goal

Milestone 03 adds a generic MQTT publisher after the existing snapshot and
derived-value flow:

```text
BatterySnapshot -> Derived Engine -> EnrichedBatterySnapshot -> MQTT Publisher
```

MQTT is only a publisher. It does not know transports, readers, decoders, raw
frames, CAN, BLE, RS485, or replay files.

## Topic Structure

The default base topic is `battery-gateway`.

Pack topics:

```text
battery-gateway/<battery_id>/pack/voltage
battery-gateway/<battery_id>/pack/current
battery-gateway/<battery_id>/pack/power
battery-gateway/<battery_id>/pack/soc
battery-gateway/<battery_id>/pack/soh
battery-gateway/<battery_id>/pack/remaining_capacity
battery-gateway/<battery_id>/pack/remaining_energy
```

Status topics:

```text
battery-gateway/<battery_id>/status/charge_state
battery-gateway/<battery_id>/status/discharge_state
battery-gateway/<battery_id>/status/charging
battery-gateway/<battery_id>/status/discharging
```

Cell and temperature topics:

```text
battery-gateway/<battery_id>/cells/<index>/voltage
battery-gateway/<battery_id>/cells/delta_voltage
battery-gateway/<battery_id>/temperature/<kind>
battery-gateway/<battery_id>/temperature/cell_average
```

Quality and metadata:

```text
battery-gateway/<battery_id>/quality/overall
battery-gateway/<battery_id>/meta/manufacturer
battery-gateway/<battery_id>/meta/model
battery-gateway/<battery_id>/meta/firmware
battery-gateway/<battery_id>/meta/source
battery-gateway/<battery_id>/meta/snapshot_timestamp
```

If a value quality is not `valid`, additional quality topics are published next
to the value:

```text
<value_topic>/quality
<value_topic>/quality_reason
```

## Configuration

The broker is configured through a TOML file. Example:

```text
[mqtt]
host = "localhost"
port = 1883
username = ""
password = ""
base_topic = "battery-gateway"
retain = false
qos = 0
```

The example file is `config/mqtt.toml.example`.

Manufacturer, model, and firmware metadata are published as `unknown` until the
core snapshot model carries identity metadata.

## Demo

The demo command is:

```text
python publisher_demo.py logs/seplos.log config/mqtt.toml
```

It prints:

```text
Broker connected: True
Published topics: <count>
Published batteries: <battery_id>
Frames processed: <count>
Runtime seconds: <seconds>
```

## Intentionally Not Implemented

The following features are deliberately not part of Milestone 03:

- Home Assistant MQTT Discovery,
- retained-state database,
- commands,
- control functions,
- write operations,
- RPC,
- REST API,
- web UI,
- decoder changes,
- derived-value changes,
- snapshot changes.
