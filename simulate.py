import numpy as np
from sampler import Sampler, AdaptiveSampler
from analysis import estimate_line

def simulate(pool, threshold, fuzz, n, seed=None,
             adaptive=False, burn_in=40, refit_every=10):
    rng = np.random.default_rng(seed)
    sampler = AdaptiveSampler(pool, seed=seed) if adaptive else Sampler(pool, seed=seed)
    responses = []
    for i in range(n):
        if adaptive and i >= burn_in and (i - burn_in) % refit_every == 0:
            est = estimate_line(responses)
            if est is not None:
                sampler.set_focus(est)
        a = sampler.next()
        p = 1 / (1 + np.exp(-(a["score"] - threshold) / fuzz))
        label = "GOOD" if rng.random() < p else str(rng.choice(["BAD", "MID"]))
        responses.append({"id": a["id"], "title": a["title"], "score": a["score"],
                          "members": a["members"], "label": label})
    return responses
