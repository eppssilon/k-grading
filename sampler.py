import json
import random
import math

BIN = 0.25
LOW, HIGH = 5.5, 9.0   # everything below LOW shares one bin, same for HIGH and above
POP_POWER = 1.0   # 0 = ignore popularity, 1 = proportional to members

def bin_key(score):
    if score < LOW:
        return LOW - BIN
    if score >= HIGH:
        return HIGH
    return int(score / BIN) * BIN

class Sampler:
    def __init__(self, pool, seed=None):
        self.rng = random.Random(seed)
        self.bins = {}
        for anime in pool:
            self.bins.setdefault(bin_key(anime["score"]), []).append(anime)
        for items in self.bins.values():
            items.sort(key=lambda a: math.log(self.rng.random()) / (a["members"] ** POP_POWER))
        self.round = []

    def next(self):
        while True:
            if not self.round:
                self.round = [k for k, items in self.bins.items() if items]
                if not self.round:
                    return None
                self.rng.shuffle(self.round)
            items = self.bins[self.round.pop()]
            if items:
                return items.pop()

class AdaptiveSampler(Sampler):
    def __init__(self, pool, seed=None, focus_prob=0.7, width=0.3):
        super().__init__(pool, seed)
        self.focus = None
        self.focus_prob = focus_prob
        self.width = width

    def set_focus(self, estimate):
        self.focus = estimate

    def next(self):
        if self.focus is None or self.rng.random() > self.focus_prob:
            return super().next()
        keys = [k for k, items in self.bins.items() if items]
        if not keys:
            return None
        weights = [max(math.exp(-0.5 * ((k + BIN / 2 - self.focus) / self.width) ** 2), 1e-9)
                   for k in keys]
        key = self.rng.choices(keys, weights=weights)[0]
        return self.bins[key].pop()
