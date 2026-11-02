import itertools

from predictz.backtest.walk_forward import load_matches, run
from predictz.models.elo import Elo

matches = load_matches("PL")


def score(params, first, last):
    res = run([Elo(**params)], matches, eval_from=first)["elo"]
    vals = [b for s, v in res.items() if s <= last for b, _ in v]
    return sum(vals) / len(vals)


grid = {
    "k": [10, 15, 20],
    "home_adv": [25, 35, 45, 55],
    "season_regress": [0.05, 0.10, 0.15],
    "mov_pow": [0.6, 0.9, 1.2],
}

keys = list(grid)
trials = []
for combo in itertools.product(*grid.values()):
    params = dict(zip(keys, combo))
    trials.append((score(params, 2017, 2022), params))
trials.sort(key=lambda t: t[0])

print("Top 5 on tuning seasons (2017-2022):")
for s, p in trials[:5]:
    print(f"  {s:.4f}  {p}")

best = trials[0][1]
print("\nHeld-out seasons (2023-2026), never used for tuning:")
print(f"  default Elo : {score({}, 2023, 2026):.4f}")
print(f"  tuned Elo   : {score(best, 2023, 2026):.4f}")