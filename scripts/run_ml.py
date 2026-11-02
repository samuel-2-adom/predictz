import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from predictz.backtest.walk_forward import load_matches
from predictz.models.features import build

rows = build(load_matches("PL"))

def blend_x(r):
    b = r["book_p"]
    return [r["x"][0], np.log(b[0] / b[2]), np.log(b[1] / (b[0] + b[2]))]

def brier(P, y):
    return ((np.asarray(P) - np.eye(3)[y]) ** 2).sum(axis=1)


per_season = {}
for season in sorted({r["season"] for r in rows}):
    if season < 2019:  # 2016 = warm-up, 2017-2018 = minimum training data
        continue
    train = [r for r in rows if 2017 <= r["season"] < season]
    test = [r for r in rows if r["season"] == season and r["book_p"]]

    model = make_pipeline(StandardScaler(),
                          LogisticRegression(C=0.5, max_iter=1000))
    model.fit([r["x"] for r in train], [r["y"] for r in train])

    y = np.array([r["y"] for r in test])
    P = model.predict_proba([r["x"] for r in test])
    cal = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
    cal.fit([r["x"][:1] for r in train], [r["y"] for r in train])
    P_cal = cal.predict_proba([r["x"][:1] for r in test])

    tr = [r for r in train if r["book_p"]]
    blend = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
    blend.fit([blend_x(r) for r in tr], [r["y"] for r in tr])
    P_blend = blend.predict_proba([blend_x(r) for r in test])

    per_season[season] = {
        "logreg": brier(P, y),
        "elo_cal": brier(P_cal, y),
        "elo": brier([r["elo_p"] for r in test], y),
        "elo+odds": brier(P_blend, y),
        "bookmaker": brier([r["book_p"] for r in test], y),
    }

names = ["logreg", "elo_cal", "elo", "elo+odds", "bookmaker"]
print(f"{'model':<10} {'brier':>6}  " + " ".join(f"{s:>5}" for s in per_season))
for n in names:
    overall = np.concatenate([v[n] for v in per_season.values()]).mean()
    seasons = " ".join(f"{v[n].mean():.3f}" for v in per_season.values())
    print(f"{n:<10} {overall:.4f}  {seasons}")