import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from readers.replay import ReplayReader
from decoders.seplos import SeplosCANDecoder

reader = ReplayReader("logs/test.log")
decoder = SeplosCANDecoder()
decoded = 0

while True:

    frame = reader.read()

    if frame is None:
        break

    decoded += len(decoder.decode(frame))

reader.close()
assert decoded == 4
print("DECODER TEST OK")

capacity = decoder.decode(
    reader._parse_line("(1.0) can0 379#3A02000000000000")
)
assert len(capacity) == 1
assert capacity[0].name == "battery.design_capacity"
assert capacity[0].value == 570.0
