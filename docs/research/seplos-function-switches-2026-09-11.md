# Seplos: Abgleich der 64 Function Switches

Stand: Pack 1, 11.09.2026, 15:33 Uhr Bangkok. Gespeicherter Lese-Mitschnitt, keine Live-Anzeige.

Die Original-Agreement-Datei der Windows-App liefert Gruppe und Bit. Die Android-App enthält dieselben 64 Bezeichnungen in derselben Reihenfolge. 63 stimmen wörtlich überein; bei Bluetooth fehlt in Android nur das Wort `function`.

Das bestätigt die Katalogzuordnung. Es ist kein Nachweis, dass jeder Schalter auf dieser Firmware schreibbar ist oder die erwartete elektrische Wirkung hat. Der vollständige Android-Serialisierungspfad wurde hier nicht für jedes Bit einzeln bewiesen.

Rohbit 1/0 bezeichnet ausschließlich den gespeicherten Konfigurationswert, keinen aktuellen Alarm und keinen gemessenen MOSFET-Zustand. Insbesondere `invalidation` nicht als direkten Ein/Aus-Befehl behandeln.

Quellen: `16S_V20_ADDR_EN-source.xml` aus BatteryMonitor V2.1.12_20/Agreement auf Solar; Android-Rekonstruktion `init:switchNodeList_182a70`; vollständige CRC-geprüfte 0x47-Antwort in `pack1-readonly-20260911-153312.jsonl`.

Gruppenbytes: `95 FF 33 33 BF FD BF 1E`. Gruppen und Bits unten zählen ab null.

| Gruppe | Bit | Windows-Index | Android-Bezeichnung | Rohbit |
| --- | --- | --- | --- | --- |
| 0 | 0 | 0x58 | Voltage sensor invalidation | 1 |
| 0 | 1 | 0x58 | Temperature sensor invalidation | 0 |
| 0 | 2 | 0x58 | Current sensor invalidation | 1 |
| 0 | 3 | 0x58 | Button switch invalidation | 0 |
| 0 | 4 | 0x58 | Cell differential pressure invalidation | 1 |
| 0 | 5 | 0x58 | Charge switch invalidation | 0 |
| 0 | 6 | 0x58 | Discharge switch invalidation | 0 |
| 0 | 7 | 0x58 | Current limit switch invalidation | 1 |
| 1 | 0 | 0x59 | Monomer high voltage alarm | 1 |
| 1 | 1 | 0x59 | Monomer overvoltage protection | 1 |
| 1 | 2 | 0x59 | Monomer low pressure alarm | 1 |
| 1 | 3 | 0x59 | Monomer undervoltage protection | 1 |
| 1 | 4 | 0x59 | Total pressure high pressure alarm | 1 |
| 1 | 5 | 0x59 | Total_voltage overvoltage protection | 1 |
| 1 | 6 | 0x59 | Total pressure low pressure alarm | 1 |
| 1 | 7 | 0x59 | Total_voltage undervoltage protection | 1 |
| 2 | 0 | 0x5A | Charging high temperature warning | 1 |
| 2 | 1 | 0x5A | Charging over temperature protection | 1 |
| 2 | 2 | 0x5A | Charging low temperature warning | 0 |
| 2 | 3 | 0x5A | Charging under-temperature protection | 0 |
| 2 | 4 | 0x5A | Discharge high temperature warning | 1 |
| 2 | 5 | 0x5A | Discharge over temperature protection | 1 |
| 2 | 6 | 0x5A | Discharge low temperature warning | 0 |
| 2 | 7 | 0x5A | Discharge under-temperature protection | 0 |
| 3 | 0 | 0x5B | Ambient high temperature alarm | 1 |
| 3 | 1 | 0x5B | Environmental over-temperature protection | 1 |
| 3 | 2 | 0x5B | Ambient low temperature alarm | 0 |
| 3 | 3 | 0x5B | Environmental under-temperature protection | 0 |
| 3 | 4 | 0x5B | Power over temperature protection | 1 |
| 3 | 5 | 0x5B | Power high temperature alarm | 1 |
| 3 | 6 | 0x5B | Cell low temperature heating | 0 |
| 3 | 7 | 0x5B | Secondary tripping protection | 0 |
| 4 | 0 | 0x5C | Charging overcurrent warning | 1 |
| 4 | 1 | 0x5C | Charge overcurrent protection | 1 |
| 4 | 2 | 0x5C | Discharge overcurrent warning | 1 |
| 4 | 3 | 0x5C | Discharge overcurrent protection | 1 |
| 4 | 4 | 0x5C | Transient current protection | 1 |
| 4 | 5 | 0x5C | Output short circuit protection | 1 |
| 4 | 6 | 0x5C | Transient overcurrent lockout | 0 |
| 4 | 7 | 0x5C | Output short circuit locking | 1 |
| 5 | 0 | 0x5D | Charging high voltage protection | 1 |
| 5 | 1 | 0x5D | Intermittent charging function | 0 |
| 5 | 2 | 0x5D | Remaining capacity alarm | 1 |
| 5 | 3 | 0x5D | Remaining capacity protection | 1 |
| 5 | 4 | 0x5D | Battery low voltage forbidden charging | 1 |
| 5 | 5 | 0x5D | Output reverse connection protection | 1 |
| 5 | 6 | 0x5D | Output connection failure | 1 |
| 5 | 7 | 0x5D | Output soft start function | 1 |
| 6 | 0 | 0x5E | Charge equalization function | 1 |
| 6 | 1 | 0x5E | Static equilibrium function | 1 |
| 6 | 2 | 0x5E | Timeout prohibits equalization | 1 |
| 6 | 3 | 0x5E | Over temperature prohibits equalization | 1 |
| 6 | 4 | 0x5E | Automatically activate charging | 1 |
| 6 | 5 | 0x5E | Manually activate charging | 1 |
| 6 | 6 | 0x5E | Take the initiative current limiting charging | 0 |
| 6 | 7 | 0x5E | Passive current limiting charging | 1 |
| 7 | 0 | 0x5F | Switch shut down function | 0 |
| 7 | 1 | 0x5F | Standby shutdown function | 1 |
| 7 | 2 | 0x5F | History record function | 1 |
| 7 | 3 | 0x5F | LCD display function | 1 |
| 7 | 4 | 0x5F | Bluetooth communication | 1 |
| 7 | 5 | 0x5F | Automatic address coding | 0 |
| 7 | 6 | 0x5F | Parallel external polling | 0 |
| 7 | 7 | 0x5F | Single BMS 1.0C charging | 0 |

## Einordnung am 12. September 2026

- Aktive Strombegrenzung: Gruppe 6, Bit 6, im dokumentierten Snapshot 0. Parameteränderung und Wiederherstellung wurden am 08.09. bestätigt; die tatsächliche Begrenzungswirkung beim Laden noch nicht.
- Passive Strombegrenzung: Gruppe 6, Bit 7, im dokumentierten Snapshot 1. Keine neue Funktionsprüfung durchgeführt.
- Current limit switch invalidation: Gruppe 0, Bit 7, im dokumentierten Snapshot 1. Dies war der am 08.09. in der Android-App umgelegte Schalter, nicht Gruppe 6/Bit 6.
- LCD und Bluetooth: Gruppe 7, Bits 3 und 4, beide 1. Für diese Zuordnung nicht erneut umgeschaltet.
- Keine zusätzlichen Schalter in der Steuerung freigegeben. Keine Schutzschwellen geändert. Noch keine geprüfte feinfühlige Stromregelung oder direkte Charge-/Discharge-MOSFET-Steuerung.
