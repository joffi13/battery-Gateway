import sys
import unittest
from enum import IntEnum
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from decoders.seplos_ble import SeplosBLEDecoder


class TemperatureType(IntEnum):
    CELL = 1
    MOSFET = 4
    AMBIENT = 8


class TemperatureValue:
    def __init__(self, value: float, sensor_type: TemperatureType):
        self.value = value
        self.type = sensor_type

    def __float__(self) -> float:
        return self.value


class SeplosBLEDecoderTests(unittest.TestCase):
    def test_decodes_cells_temperatures_and_provenance(self) -> None:
        decoded = SeplosBLEDecoder().decode(
            {
                "voltage": 53.06,
                "current": 13.1,
                "battery_level": 100,
                "cell_voltages": [3.316, 3.317],
                "temp_values": [
                    TemperatureValue(24.1, TemperatureType.CELL),
                    TemperatureValue(31.2, TemperatureType.MOSFET),
                    TemperatureValue(27.3, TemperatureType.AMBIENT),
                ],
            },
            source_id="seplos_ble:BP00",
            timestamp=10.0,
        )

        self.assertEqual(len(decoded.cells), 2)
        self.assertEqual(decoded.cells[0].index, 1)
        self.assertEqual(decoded.cells[0].voltage.value, 3.316)
        self.assertEqual(
            decoded.cells[0].voltage.source_id, "seplos_ble:BP00"
        )
        self.assertEqual(
            [item.kind for item in decoded.temperatures],
            ["cell_1", "mosfet", "ambient"],
        )
        self.assertTrue(
            all(
                item.value.source_id == "seplos_ble:BP00"
                for item in decoded.temperatures
            )
        )

    def test_ignores_unknown_values(self) -> None:
        decoded = SeplosBLEDecoder().decode(
            {"cell_voltages": "invalid", "temp_values": None},
            source_id="seplos_ble:BP00",
        )
        self.assertEqual(decoded.cells, ())
        self.assertEqual(decoded.temperatures, ())


if __name__ == "__main__":
    unittest.main()
