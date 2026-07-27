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
