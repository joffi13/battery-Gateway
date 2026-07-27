from core.frame import Frame
from core.manager import BatteryManager
from decoders.base import Decoder


class SeplosDecoder(Decoder):

    def decode(
        self,
        frame: Frame,
        manager: BatteryManager,
    ) -> bool:

        if frame.identifier != 0x355:
            return False

        battery = manager.get("seplos_01")

        data = frame.data

        print()
        print("===== SEPLOS =====")
        print(f"ID   : 0x{frame.identifier:03X}")
        print(f"DLC  : {frame.dlc}")
        print(f"DATA : {frame.hex()}")

        return True
