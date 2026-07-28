# Versioning and Releases

## Single Source of Truth

The repository-root `VERSION` file is the only authoritative source for the
Battery Gateway software version. Runtime code, diagnostics, publishers, build
automation, and future command-line tools must read the value from that file.

Do not duplicate the current project version in Python constants, systemd unit
files, configuration files, or README badges. Historical release numbers in the
changelog and Git tags are records, not alternative version sources.

The public MQTT API version is independent from the software version:

- `meta/gateway_version` reports the software version read from `VERSION`.
- `api/mqtt_api_version` reports the major version of the public MQTT contract.

A software release may change without changing the MQTT API version. The MQTT
API version changes only according to the compatibility rules in
`mqtt-topic-spec.md`.

## Semantic Versioning

Battery Gateway uses `MAJOR.MINOR.PATCH`:

- **PATCH**: backward-compatible bug fix, documentation correction, or internal
  maintenance release.
- **MINOR**: backward-compatible functionality, new optional data, or a new
  integration capability.
- **MAJOR**: incompatible behavior or contract change that requires consumers
  or operators to migrate.

## Release Procedure

1. Ensure all tests pass.
2. Complete the required stability test for runtime changes.
3. Update `VERSION` once with the intended release number.
4. Add the matching release section to `CHANGELOG.md`.
5. Verify diagnostics and MQTT `meta/gateway_version` report the same value.
6. Commit the release-ready state.
7. Create an annotated Git tag named `v<version>`, for example `v0.1.0`.
8. Push the commit and tag, then create the corresponding GitHub release.

The first official release is prepared as `v0.1.0`.
