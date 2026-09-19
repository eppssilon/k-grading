import json
from collections import Counter
from sampler import Sampler, bin_key

with open("pool.json", encoding="utf-8") as f:
    pool = json.load(f)

s = Sampler(pool, seed=42)
drawn = [s.next() for _ in range(100)]

for a in drawn[:8]:
    print(f"{a['score']:.2f}  {a['title']}")
print()
counts = Counter(bin_key(a["score"]) for a in drawn)
for k in sorted(counts):
    print(f"{k:.2f}: {counts[k]}")
