# Seplos V2: RS485, BLE und Schalter

Wissensstand 12.09.2026. Versuchsergebnisse, keine allgemeingültige
Hersteller-Spezifikation. [Gesamtüberblick](../status/2026-09-12.md).

## Drei getrennte Mechanismen

| Mechanismus | Nachgewiesene Bedeutung im untersuchten Pfad | Nicht gleichsetzen mit |
| --- | --- | --- |
| 0x47 / 0xA1 | Vollständigen Parameterblock lesen / schreiben, einschließlich Function Switches | Direktem MOSFET-Steuerbefehl |
| Windows 0x45 | Separater Telecontrol-Pfad aus Calibrating / AdjustDialog | BLE-0xAA-Format oder Android-Schutzbits |
| BLE-0xAA-Kandidat | Aus externer Implementierung übernommener MOS-Kandidat; hier ohne beobachtete OFF-Wirkung | Vom Hersteller bestätigter Unterstützung |

Windows-RS485 nutzt ASCII-Framing und dessen Prüfsumme. Der hier untersuchte
BLE-Parameterpfad nutzt binäre Frames mit CRC. Adressen, INFO-Felder und
Prüfverfahren dürfen nicht ungeprüft zwischen diesen Transporten übertragen
werden.

## Direkte BLE-Parameter am physischen Pack 1

1101-SP06, Software 16.6. Im normalen RS485-Betrieb konnte auf der direkten,
eindeutig zugeordneten BLE-Verbindung die lokale Protokolladresse 0 gelesen
werden. Daraus folgt nicht, dass dieses Pack physisch DIP-Adresse 0 hatte.

Der untersuchte Parameterblock hat 169 Byte Nutzdaten: Zielbyte,
60 Wortparameter, Anzahl und 27 Byteparameter, Anzahl und acht Bitgruppen,
zehn Byte Modellkennung. Das vollständige Antworttelegramm umfasst 179 Byte.

Bei diesem Block liegt die aktive Strombegrenzung in Gruppe 6 Bit 6
(zählend ab null), Nutzdatenoffset 155. Die beobachtete Änderung war
`BF → FF → BF` für diese Gruppe. Das ist eine layoutspezifische Zuordnung,
kein universeller Offset für andere Firmware-/Protokollversionen.

Am 08.09., 18:55 Uhr Bangkok, erfolgten:

- A1-Schreiben mit genau einem veränderten Bit und Rückgabecode 0;
- zwei identische vollständige Readbacks des Kandidaten;
- Rückschreiben des exakten Originalblocks und zweimaliger Vollvergleich;
- anschließend frische Statusdaten ohne Alarmbits und erneute Leseverbindung.

Das Pack entlud dabei mit etwa 3,16 A. Es wurde **keine reale
10-A-Ladestrombegrenzung** nachgewiesen.

Die beobachtete zulässige GATT-Schreibgröße wechselte zwischen Verbindungen.
Vor einem langen Frame muss die aktuelle Transportkapazität geprüft werden;
keine alte MTU annehmen und keine Fragmentierung erraten. Diese Beobachtung
erklärt einen konkreten blockierten Schreibversuch, nicht pauschal frühere
Display- oder Inverter-Ausfälle.

## Windows-Telecontrol: bereits experimentell abgelehnt

Am 23.08. wurde der originale Charge-OFF-Vorgang der Windows-App passiv erfasst.
Der beobachtete BMS-Rückgabecode war **0x04, Command not supported**.

| Physisches Pack | Modell | Software | Ergebnis |
| --- | --- | --- | --- |
| 1 | 1101-SP06 | 16.6 | 0x45 Charge OFF ausdrücklich abgelehnt |
| 5 | 1101-SP75 | 16.4 | 0x45 Charge OFF ausdrücklich abgelehnt |

Ein weiterer Versuch mit bereits gelöschtem Charge-invalidation-Bit änderte
die Ablehnung nicht. Die Hypothese, dieses Bit allein schalte den bekannten
Befehl frei, wurde damit nicht bestätigt. Das Wort „freigegeben“ in älteren
Versuchsnotizen ist keine unabhängig bewiesene Semantik dieses Bits.

Dieser Befund korrigiert den Zwischenstand vom 11.09., in dem das Ergebnis des
älteren Mitschnitts noch nicht vollständig berücksichtigt war. Ein neuer
identischer Windows-Versuch ist nicht als bisher ungetesteter Ansatz zu werten.

## BLE-MOS-Kandidaten: kein erfolgreicher Schaltzyklus

Am 11.09. wurden Charge und Discharge separat mit dem 0xAA-Kandidaten geprüft.
Die Kandidaten stammen aus einer externen Implementierung, nicht aus einem
erfolgreich beobachteten Schaltvorgang der Original-App.

- Charge-Versuch: acht Liveabfragen, MOS-Status unverändert 0x03,
  weiterhin etwa +4,28 bis +4,31 A Ladestrom.
- Discharge-Versuch: acht Liveabfragen, MOS-Status ebenfalls 0x03,
  etwa +3,98 bis +4,06 A Ladestrom.
- Keine AA-Bestätigung beobachtet. Abschließender ON-Status festgestellt,
  jedoch kein OFF-Zustand und damit kein erfolgreicher OFF/ON-Zyklus.
- Fortgesetzter **Lade**strom allein wäre kein Beweis für eine fehlende
  **Entlade**sperre; beim zweiten Versuch fehlt insbesondere die Statusänderung.

Das zeigt die Erfolglosigkeit dieser konkreten Versuche, nicht die grundsätzliche
Unmöglichkeit jedes externen MOSFET-Befehls.

## Android-App: belegte Slave-Leseadressierung

In der vom Nutzer eingerichteten CAN/Master-Konstellation lieferte die
Original-App beim Wechsel von BP00 auf BP02 und BP03 echte individuelle Daten:

| Antwortadresse | Nennkapazität | CRC-/längengeprüfte Frames |
| --- | --- | --- |
| 0 | 100 Ah | 21 |
| 2 | 210 Ah | 52 |
| 3 | 280 Ah | 22 |

Anfragen an 0x61 verwendeten Headeradresse 2 bzw. 3 und Nutzlast 00.
Antwortadresse und Packindex passten dazu. Es war nicht lediglich ein
umbenanntes Master-Anzeigefeld. BP04 und BP05 wurden in dieser Sitzung nicht
getestet. Die Quelle war gefiltertes App-Logcat mit Notification-Arrays,
kein vollständiger Bluetooth-HCI-Funkmitschnitt.

Nicht belegt sind Schreibzugriffe auf Slaves oder dieselbe Weiterleitung im
normalen All-RS485-Betrieb. Die CAN/Master-Versuchskonfiguration führte laut
Nutzer zu Solar-Assistant-Lesefehlern und wurde wieder zurückgestellt.

## Android-Sendepfade

Die vorhandene Rekonstruktion der untersuchten Original-App 1.0.24 / Build 57
wurde offline ausgewertet. Sechs aufgelöste direkte Konstruktorpfade zum
zentralen Encoder ergeben:

| Befehl (hex) | Konstruktor |
| --- | --- |
| 47 | ReadBMSParams |
| 51 | BasicInfo |
| 61 | Battery |
| 62 | ParallelBattery |
| 63 | SwitchCAN |
| A1 | WriteBMSParams |

In diesen sechs direkten Pfaden kein 45 oder AA. Das ist **kein vollständiger
Abwesenheitsbeweis für die APK**: indirekte, inlinierte oder alternative
Sendepfade bleiben möglich. Aus sichtbaren Schaltern oder Video-Beschreibungen
wurde kein zusätzlicher MOS-Befehl als bewiesen abgeleitet.

## Function Switches

Die [vollständige Matrix](../research/seplos-function-switches-2026-09-11.md)
ordnet 64 Beschriftungen zu acht Gruppen zu. Besonders auseinanderhalten:

- Gruppe 0 Bit 5/6: Charge-/Discharge-switch-invalidation;
- Gruppe 0 Bit 7: Current-limit-switch-invalidation;
- Gruppe 6 Bit 6: aktive Strombegrenzung, als Parameter erfolgreich getestet;
- Gruppe 6 Bit 7: passive Strombegrenzung, kein neuer Wirkungstest;
- Gruppe 7 Bit 3/4: LCD/Bluetooth.

Gespeichertes Konfigurationsbit, aktueller Alarm, MOS-Status und real fließender
Strom sind vier verschiedene Beobachtungen. Keine Schutzbits versuchsweise als
Leistungsschalter benutzen.

## Quellen und Grenzen

Die konkreten Ergebnisse beruhen auf den im
[Belegverzeichnis](../research/evidence-2026-09-12.md) benannten lokalen Berichten
und Mitschnitten. Rohdaten und Herstellerprogramme sind nicht Bestandteil
dieser Veröffentlichung. Externe Vergleichsquellen:

- [BLE-MOS-Kandidaten, feste Revision](https://github.com/syssi/esphome-seplos-bms/blob/65972770d6147dd215f8f69c3dea862ee64907fa/components/seplos_bms_ble/switch/__init__.py)
- [Bleak: aktuelle Characteristic-Schreibgröße](https://bleak.readthedocs.io/en/latest/api/index.html#bleak.backends.characteristic.BleakGATTCharacteristic.max_write_without_response_size)

Externe Implementierungen sind keine Kompatibilitätsgarantie für die getesteten
BMS-Firmwarestände.
