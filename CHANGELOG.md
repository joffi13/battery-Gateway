# Changelog

All notable changes to Battery Gateway are recorded here. The project follows
[Semantic Versioning](docs/versioning.md).

## [0.1.0]

### Added

- Protocol-neutral core architecture.
- Immutable `BatterySnapshot` and normalized measurement model.
- Replay reader for deterministic CAN-log processing.
- Seplos CAN decoder.
- Derived Engine for power, charge state, remaining capacity and energy, and
  cell statistics.
- Generic MQTT publisher.
- Public MQTT API version 1.
- Home Assistant MQTT package and dashboard.
- Production SocketCAN-to-MQTT systemd service.
- Read-only `battery-gateway-status` diagnostics.
- Runtime stability monitoring.

### Changed

- Moved calculated values out of Home Assistant and into the Derived Engine.
- Replaced the legacy Seplos MQTT process with the generic Battery Gateway
  runtime while retaining a documented rollback path.
- Centralized the software version in the repository-root `VERSION` file.

### Fixed

- Added the required `api/mqtt_api_version` publication.
- Added `pack/design_capacity` publication from Seplos CAN frame `0x379`.
- Corrected average cell voltage to `cells/average_voltage`.
- Removed the non-API `status/discharge_state` topic.
- Removed unsupported `object_id` keys from the Home Assistant MQTT package.

### Documentation

- Documented the internal data model and layer boundaries.
- Defined and reviewed the stable public MQTT API.
- Documented Home Assistant integration and dashboard behavior.
- Added production operation, diagnostics, release, and architecture-history
  documentation.

[0.1.0]: https://github.com/joffi13/battery-Gateway/releases/tag/v0.1.0
