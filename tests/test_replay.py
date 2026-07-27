import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from readers.replay import ReplayReader

reader = ReplayReader("logs/test.log")

while True:

    frame = reader.read()

    if frame is None:
        break

    print(frame)

print("REPLAY TEST OK")
