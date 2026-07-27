# Milestone 02: Derived Engine

## What Was Implemented

Milestone 02 adds a Derived Engine that consumes an existing BatterySnapshot and
returns an EnrichedBatterySnapshot.

The original BatterySnapshot is never modified.

The Derived Engine does not know:

- RawFrame,
- ReplayReader,
- decoders,
- CAN,
- BLE,
- RS485,
- MQTT,
- Home Assistant.

## New Classes

- DerivedEngine
- DerivedValue
- EnrichedBatterySnapshot

## New Calculations

The Derived Engine currently calculates only deterministic values from existing
snapshot data:

- Power: pack voltage multiplied by pack current
- Average Cell Voltage: mean of valid cell voltages
- Delta Cell Voltage: maximum valid cell voltage minus minimum valid cell voltage
- Charge State: charging, idle, or discharging
- Battery Charging: boolean derived from Charge State
- Battery Discharging: boolean derived from Charge State
- Remaining Capacity: design capacity multiplied by SOC
- Remaining Energy: pack voltage multiplied by remaining capacity

## Assumptions

Positive current means charging. Negative current means discharging.

The default current deadband is 0.1 A. Currents inside the deadband are treated as
idle to avoid charge-state changes caused by measurement noise.

Only values with valid quality are used when valid values exist. Suspect values
may be used only when no valid value exists for the same measurement. Invalid,
missing, and sentinel values are not used.

Temperature values are not used in any Milestone 02 calculation. Sentinel
temperatures such as -50 degC therefore cannot affect averages or energy values.

## Limits

Milestone 02 does not validate whether SOC, voltage, current, or capacity are
physically plausible beyond their Quality state.

Remaining Energy is a simple deterministic calculation. It is not a battery model
and not an energy forecast.

Average Cell Voltage and Delta Cell Voltage are omitted when no valid cell
voltages exist.

## Intentionally Not Implemented

The following functions are deliberately excluded:

- runtime prediction,
- aging models,
- charging algorithms,
- SOC estimation,
- health calculation,
- forecasts,
- multi-source conflict resolution,
- publisher output,
- decoder changes,
- ReplayReader changes,
- RawFrame changes.

Milestone 02 only enriches an already completed BatterySnapshot.
