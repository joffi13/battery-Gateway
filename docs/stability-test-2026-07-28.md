# Production Stability Test — 2026-07-28

## Scope

The production `battery-gateway.service` was observed continuously while reading
live SocketCAN data from `can0` and publishing Battery Gateway MQTT API v1 data
to the central Home Assistant Mosquitto broker at `192.168.1.52:1883`.

Test window:

- Start: 2026-07-28 10:40:23 +07:00
- End: 2026-07-28 11:40:49 +07:00
- Duration: 3,626 seconds (60 minutes 26 seconds)
- Samples: 61 at approximately one-minute intervals

## Results

| Metric | Result |
|---|---:|
| Active samples | 61 / 61 |
| PID changes | 0 |
| systemd restarts | 0 |
| CPU time used during window | 21.147 seconds |
| Average CPU utilization | 0.583% of one CPU |
| Minimum RSS | 32,188 KiB |
| Average RSS | 32,208.6 KiB |
| Maximum RSS | 32,228 KiB |
| MQTT API checks successful | 61 / 61 |
| MQTT reconnects observed | 0 |
| Publish errors | 0 |
| CAN connected samples | 61 / 61 |
| CAN errors | 0 |
| Error-priority journal entries | 0 |
| Exceptions or tracebacks | 0 |
| CAN bus errors | 0 |
| CAN bus-off events | 0 |
| Frames received during window | 57,760 |
| Snapshots published during window | 722 |

The read-only diagnostic tool immediately after the completed window reported:

```text
Battery Gateway     : RUNNING
Version             : 0.1.0
MQTT Connected      : True
Reconnect Count     : 0
CAN Connected       : True
CAN Errors          : 0
Frames Received     : 58882
Snapshots Published : 737
Publish Errors      : 0
MQTT API Version    : 1
Design Capacity     : 570.0 Ah
Service Restarts    : 0
```

The SocketCAN interface remained `UP`, `LOWER_UP`, and `ERROR-ACTIVE`. Its
kernel counters reported zero bus errors, arbitration losses, warning/passive
transitions, bus-off events, and controller restarts. The interface showed 112
cumulative RX queue drops; because no pre-test baseline was captured, these
cannot be attributed to this test window. They did not cause a service error,
restart, missing MQTT probe, or publish failure.

## MQTT Verification

Every sample opened a broker subscription and successfully read:

```text
battery-gateway/battery_01/api/mqtt_api_version = 1
```

The gateway's persistent publisher connection remained reported as connected in
its periodic health log. No `MQTT publication failed` message was recorded.

## Conclusion

The required one-hour stability test passed. CPU and memory remained stable,
the process did not restart, CAN processing continued, MQTT remained reachable,
and no application exception or publish error occurred.

This test does not replace the planned 24-hour migration soak. The legacy
`seplos-can.service` must remain installed, disabled, unchanged, and immediately
available for rollback until that separate 24-hour run succeeds.
