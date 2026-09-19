import json
from collections import Counter

with open("pool.json", encoding="utf-8") as f:
    pool = json.load(f)

BIN = 0.25
bins = Counter(int(a["score"] / BIN) * BIN for a in pool)
for low in sorted(bins):
    count = bins[low]
    print(f"{low:.2f} to {low + BIN:.2f}: {count:5d}  {'#' * (count // 10)}")

near = sum(1 for a in pool if 7.25 <= a["score"] < 8.25)
print(f"\nWithin 0.5 of 7.75: {near} of {len(pool)}")
