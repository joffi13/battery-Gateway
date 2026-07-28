import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from readers.ble import BLEDeviceConfig, BLEReader


class BLEReaderTests(unittest.TestCase):
    def test_multiple_devices_have_independent_status(self) -> None:
        reader = BLEReader(
            (
                BLEDeviceConfig("BP00", "battery_01", "60:6E:41:26:E6:81"),
                BLEDeviceConfig("BP01", "battery_02", "10:23:81:10:4D:50"),
                BLEDeviceConfig(
                    "BP02",
                    "battery_03",
                    "60:6E:41:0F:3C:09",
                    enabled=False,
                ),
            )
        )

        status = reader.status()

        self.assertEqual(set(status), {"BP00", "BP01"})
        self.assertNotEqual(
            status["BP00"]["address"], status["BP01"]["address"]
        )
        self.assertEqual(status["BP00"]["disconnect_count"], 0)
        self.assertEqual(status["BP01"]["reconnect_count"], 0)
        self.assertNotEqual(
            reader.devices[0].battery_id,
            reader.devices[1].battery_id,
        )


if __name__ == "__main__":
    unittest.main()
