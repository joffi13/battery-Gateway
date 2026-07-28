# Production Operations

## Service

Battery Gateway runs as the unprivileged `michi` user:

```text
systemctl status battery-gateway.service
journalctl -u battery-gateway.service -f
battery-gateway-status
```

The service starts after `network-online.target`, restarts after every exit with
a five-second delay, and reads its local runtime configuration from
`config/production.toml`. That local file is ignored by Git because it contains
broker credentials.

Transient SocketCAN and MQTT failures use bounded retry delays. They do not
create a busy loop.

## Legacy Migration

The legacy `seplos-can.service` is stopped and disabled, not deleted. Its
original unit and Python program are retained unchanged and backed up outside
the Git worktree.

Do not remove the legacy service before Battery Gateway has completed a
successful 24-hour production run.

## Rollback

The rollback is intentionally short and does not modify either implementation:

```text
sudo systemctl stop battery-gateway.service
sudo systemctl disable battery-gateway.service
sudo systemctl enable seplos-can.service
sudo systemctl start seplos-can.service
```

Confirm completion:

```text
systemctl is-active battery-gateway.service
systemctl is-active seplos-can.service
```

The expected result is `inactive` followed by `active`.

## Diagnostics

`battery-gateway-status` is read-only. It reports systemd state and the latest
runtime status written by the gateway, including MQTT connectivity, last
publish time, reconnect and error counts, CAN status, frame and snapshot
counters, API version, and design capacity.
