import json
from simulate import simulate
from analysis import to_frame, fit_threshold, bootstrap_threshold

with open("pool.json", encoding="utf-8") as f:
    pool = json.load(f)

for true_t in [7.0, 7.75, 8.4]:
    df = to_frame(simulate(pool, threshold=true_t, fuzz=0.3, n=100, seed=1))
    _, s_star = fit_threshold(df)
    low, high, est = bootstrap_threshold(df, seed=0)
    print(f"true {true_t:.2f}  estimated {s_star:.2f}  "
          f"95% CI [{low:.2f}, {high:.2f}]  7.75 inside: {low <= 7.75 <= high}  "
          f"({len(est)} usable resamples)")
