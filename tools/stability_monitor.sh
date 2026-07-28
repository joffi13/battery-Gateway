#!/usr/bin/env bash
set -u

output=${1:?usage: stability_monitor.sh OUTPUT.csv}
samples=${2:-61}
interval=${3:-60}
service=battery-gateway.service
start_time=$(date --iso-8601=seconds)
mqtt_config=$(python3 -c '
import tomllib
from pathlib import Path
d = tomllib.loads(Path("config/production.toml").read_text())["mqtt"]
print(d["host"], d.get("username", ""), d.get("password", ""), sep="\t")
')
IFS=$'\t' read -r broker mqtt_user mqtt_password <<< "$mqtt_config"

printf '%s\n' \
  'timestamp,active,pid,cpu_usage_nsec,rss_kib,memory_current_bytes,tcp_established,mqtt_api_version,restarts,error_lines,mqtt_reconnects,can_errors,frames_received,snapshots_published,publish_errors,can_connected,last_publish' \
  > "$output"

for ((sample = 1; sample <= samples; sample++)); do
  timestamp=$(date --iso-8601=seconds)
  active=$(systemctl is-active "$service" 2>/dev/null || true)
  pid=$(systemctl show "$service" -p MainPID --value)
  cpu_usage_nsec=$(systemctl show "$service" -p CPUUsageNSec --value)
  memory_current_bytes=$(systemctl show "$service" -p MemoryCurrent --value)
  restarts=$(systemctl show "$service" -p NRestarts --value)
  rss_kib=0
  if [[ $pid =~ ^[1-9][0-9]*$ ]]; then
    rss_kib=$(ps -o rss= -p "$pid" | tr -d ' ')
    rss_kib=${rss_kib:-0}
  fi
  tcp_established=$(ss -tn state established dst "$broker:1883" \
    | awk 'NR > 1 {count++} END {print count + 0}')
  mqtt_api_version=$(timeout 4 mosquitto_sub \
    -h "$broker" -p 1883 -u "$mqtt_user" -P "$mqtt_password" \
    -t 'battery-gateway/battery_01/api/mqtt_api_version' \
    -C 1 -W 3 2>/dev/null || true)
  mqtt_api_version=${mqtt_api_version//$'\n'/}
  error_lines=$(journalctl -q -u "$service" --since "$start_time" \
    -p err --no-pager 2>/dev/null | wc -l)
  status_fields=$(python3 -c '
import json
from pathlib import Path
d = json.loads(Path("logs/status.json").read_text())
keys = (
    "mqtt_reconnect_count",
    "can_errors",
    "frames_received",
    "snapshots_published",
    "publish_errors",
    "can_connected",
    "last_publish",
)
print(",".join(str(d.get(key, "")) for key in keys))
' 2>/dev/null || printf ',,,,,,')

  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$timestamp" "$active" "$pid" "$cpu_usage_nsec" "$rss_kib" \
    "$memory_current_bytes" "$tcp_established" "$mqtt_api_version" \
    "$restarts" "$error_lines" "$status_fields" >> "$output"

  if ((sample < samples)); then
    sleep "$interval"
  fi
done
