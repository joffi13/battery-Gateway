from core.frame import Frame

f = Frame(
    bus="can0",
    identifier=0x355,
    data=bytes.fromhex("55 AA 01 02 03 04 05 06")
)

print(f)
