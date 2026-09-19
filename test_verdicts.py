import json
from collections import Counter
from simulate import simulate
from analysis import to_frame, fit_threshold, bootstrap_threshold, verdict

with open("pool.json", encoding="utf-8") as f:
    pool = json.load(f)

RUNS = 40

for adaptive in [True]:
    print("ADAPTIVE" if adaptive else "FLAT")
    for true_t in [7.0, 7.75, 8.5]:
        tally = Counter()
        for seed in range(RUNS):
            df = to_frame(simulate(pool, threshold=true_t, fuzz=0.6, n=150,
                                   seed=seed, adaptive=adaptive))
            model, _ = fit_threshold(df)
            _, _, est = bootstrap_threshold(df, n_boot=500, seed=seed)
            tally[verdict(model, est)[0]] += 1
        print(f"  true {true_t:.2f}: {dict(tally)}")
