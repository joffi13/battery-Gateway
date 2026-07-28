# Architecture

Battery Gateway has one processing path and one immutable
`BatterySnapshot`. Readers and decoders are replaceable edge components; the
core model does not know which transport or BMS family supplied a value.

```text
SocketCAN Reader -> Seplos CAN Decoder --+
                                         |
BLE Reader ------> Seplos BLE Decoder ---+-> Source Merger
                                              |
                                              v
                                      BatterySnapshot
                                              |
                                              v
                                       Derived Engine
                                              |
                                              v
                                       MQTT Publisher
```

## Source neutrality

`BatterySnapshot` contains measurements, cells, temperatures, and quality. It
has no CAN, BLE, RS485, or vendor-specific fields. Provenance belongs to each
`NormalizedMeasurement` through `source_id` and `raw_reference`.

This keeps future sources such as Seplos RS485, JK CAN, Batrium CAN, and PACE
RS485 outside the core data model.

## Source Merger

The Source Merger is the only component allowed to combine source data. Its
precedence is explicit:

1. the primary CAN snapshot is inserted first;
2. supplementary values only fill fields that are absent;
3. the same rule is applied independently to measurements, cell indexes, and
   temperature identifiers.

BLE therefore never replaces a CAN value. When BLE disconnects, its source data
is omitted from the next merge. The resulting snapshot continues to contain
the available CAN measurements and no stale BLE cells or temperatures.

## BLE concurrency

Each configured BLE device has an independent asynchronous worker with its own
connection state, reconnect delay, counters, timestamps, and last error. One
device failure cannot stop another BLE worker, the SocketCAN loop, snapshot
publication, or MQTT.

Devices are configured by stable logical ID, target `battery_id`, and Bluetooth
address. No device address is compiled into the reader. The explicit battery
mapping prevents measurements from different packs entering the same snapshot.
The initial live verification uses BP00 only; BP01 through BP05 can be added as
independent workers without restructuring the pipeline.

The production decision remains conservative: direct BLE is optional. A
gateway with no configured or reachable BLE device remains a complete CAN to
MQTT gateway.
