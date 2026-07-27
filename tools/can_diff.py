#!/usr/bin/env python3

import re
import sys
from collections import defaultdict

if len(sys.argv) != 2:
    print("Usage: python3 can_diff.py logfile")
    exit()

rx = re.compile(r".*?([0-9A-F]{3})\s+\[\d+\]\s+((?:[0-9A-F]{2}\s+){7}[0-9A-F]{2})")

frames = defaultdict(list)

with open(sys.argv[1]) as f:

    for line in f:

        m = rx.search(line)

        if not m:
            continue

        cid = m.group(1)

        data = [int(x,16) for x in m.group(2).split()]

        frames[cid].append(data)

for cid in sorted(frames):

    print("="*80)
    print("ID",cid)
    print("="*80)

    first = frames[cid][0]

    changed=[False]*8

    for f in frames[cid][1:]:

        for b in range(8):

            if f[b]!=first[b]:
                changed[b]=True

    print("Bytes:")

    for b in range(8):

        if changed[b]:

            values=sorted(set(x[b] for x in frames[cid]))

            print(f" {b}:",end=" ")

            for v in values:
                print(f"{v:02X}",end=" ")

            print()

    print()
