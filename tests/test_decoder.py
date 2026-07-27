import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from readers.replay import ReplayReader
from decoders.seplos import SeplosDecoder
from core.manager import BatteryManager

reader = ReplayReader("logs/test.log")
decoder = SeplosDecoder()
manager = BatteryManager()

while True:

    frame = reader.read()

    if frame is None:
        break

    decoder.decode(frame, manager)

print("DECODER TEST OK")
