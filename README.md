# battery-gateway

## Aktueller Wissensstand – 12. September 2026

**Start here / Hier weiterlesen:** [Wissensstand und nächste Schritte](docs/status/2026-09-12.md).

Die Forschung ist weiter als der veröffentlichte Laufzeitcode. Dieses Update
dokumentiert die Seplos-RS485/BLE-Ergebnisse bis zum 12.09.2026, installiert aber
keine neue Steuerung. Insbesondere sind direkte Charge-/Discharge-MOSFET-Befehle
noch nicht erfolgreich nachgewiesen. Der aktive 10-A-Begrenzer wurde an einem
Pack als gespeicherte Einstellung erfolgreich geschrieben und zurückgesetzt;
seine elektrische Wirkung beim Laden ist noch zu prüfen.

- [Seplos: Befunde und Protokollgrenzen](docs/protocols/seplos.md)
- [Alle 64 Function Switches](docs/research/seplos-function-switches-2026-09-11.md)
- [Versuchsfolge und Belegverzeichnis](docs/research/evidence-2026-09-12.md)

Die nachfolgenden Projekt- und Betriebsbeschreibungen enthalten den bisherigen
Entwicklungsstand. Sie sind kein Nachweis für die heutige Live-Konfiguration
oder eine bereits einsatzfertige Leistungsregelung.

`battery-gateway` is an experimental Python project for reading, decoding,
replaying, and publishing battery/BMS data. The long-term goal is to support
multiple BMS families such as Seplos, Batrium, JK, Pace, Daly, and others
without coupling the core gateway to one vendor protocol.

The repository currently contains the early gateway kernel plus standalone
reverse-engineering tools used while new CAN protocols are investigated.

## Repository layout

- `core/` - protocol-neutral battery, frame, signal, event, and manager models
- `decoders/` - decoder interfaces and vendor-specific decoder experiments
- `readers/` - frame sources such as replay readers
- `publishers/` - publisher interfaces
- `tools/` - standalone analysis utilities
- `tests/` - unit tests
- `logs/` - local runtime/log capture directory, ignored except `.gitkeep`

## CAN reverse engineering analyzer

`tools/can_analyzer.py` is a protocol-neutral candump analyzer. It does not
hardcode CAN IDs, vendor rules, or battery-specific assumptions.

Supported input formats:

```text
(timestamp) can0 351#4202E8039E07D001
can0 351 [8] 42 02 E8 03 9E 07 D0 01
```

Run it on the Raspberry Pi:

```bash
cd /home/michi/battery-gateway
python3 tools/can_analyzer.py logs/seplos.log
```

The report is terminal-oriented and groups results by CAN ID:

- total frame count
- skipped invalid line count
- constant and variable bytes
- per-byte distinct count, minimum, maximum, and delta
- adjacent 16-bit analysis for byte pairs `0-1` through `6-7`
- little-endian unsigned/signed values
- big-endian unsigned/signed values
- statistical hints for likely measurement/status/constant bytes

Invalid lines are skipped. The analyzer reads files as a stream and does not
store every frame, which keeps it usable for large candump captures. It does
keep distinct-value sets per byte and per 16-bit candidate; future versions may
replace this with approximate counters for very high-cardinality captures.

## Analyzer architecture

The analyzer is intentionally modular:

- `CandumpParser` parses log lines into `CANFrame` objects.
- `CANAnalyzer` performs streaming aggregation.
- accumulator classes collect byte and 16-bit statistics.
- `HeuristicClassifier` contains protocol-neutral statistical classification.
- `TerminalReportRenderer` owns human-readable terminal output.
- `AnalyzerApplication` wraps the command-line interface.

This keeps parsing, aggregation, heuristics, and rendering independent so later
features can be added without rewriting the core analysis path.

## Tests

The project uses the Python standard library test runner:

```bash
python3 -m unittest discover -s tests
```

## Versioning

The current Battery Gateway software version is read exclusively from
[`VERSION`](VERSION). Release history is recorded in
[`CHANGELOG.md`](CHANGELOG.md), and the Semantic Versioning and Git-tag process
is documented in [`docs/versioning.md`](docs/versioning.md).

The software version and public MQTT API version are independent. Runtime
publishers expose them as:

```text
battery-gateway/<battery_id>/meta/gateway_version
battery-gateway/<battery_id>/api/mqtt_api_version
```

The reasoning behind the middleware, immutable snapshots, Derived Engine, and
public MQTT API is preserved in [`docs/history.md`](docs/history.md).

Production service operation, diagnostics, and the sub-minute legacy rollback
are documented in [`docs/operations.md`](docs/operations.md).

Current analyzer tests cover:

- empty input
- invalid lines
- compact candump format
- classic candump format
- mixed-format files
- 16-bit endian/signed calculations

## Future analysis extensions

Recommended next additions:

- compare multiple log files
- temporal correlation between CAN IDs
- periodic frame detection
- counter detection
- bitfield detection
- ASCII frame detection
- CSV export
- JSON export
- replay integration
- automatic signal candidate scoring
- trend output or lightweight plotting
- cross-ID correlation during charge/discharge events

## Development notes

The code targets Python 3.11-compatible syntax and prefers the standard library.
The Raspberry Pi currently reports Python 3.13, so tests should be run with the
oldest supported Python version as soon as CI is added.
