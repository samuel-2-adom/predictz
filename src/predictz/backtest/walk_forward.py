from predictz.models import outcome
from predictz.storage.db import connect

QUERY = """
SELECT m.season, m.utc_date, m.home_team, m.away_team, m.home_goals, m.away_goals,m.home_sot, m.away_sot,
       o.home AS oh, o.draw AS od, o.away AS oa
FROM matches m
LEFT JOIN odds o ON o.source = m.source AND o.source_id = m.source_id
                AND o.bookmaker = 'B365'
WHERE m.source = 'football-data.co.uk' AND m.status = 'FINISHED'
  AND m.competition = ?
ORDER BY m.utc_date, m.source_id
"""


def load_matches(competition="PL"):
    conn = connect()
    return [dict(r) for r in conn.execute(QUERY, (competition,))]


def brier(p, y):
    return sum((p[i] - (1.0 if i == y else 0.0)) ** 2 for i in range(3))


def run(models, matches, eval_from):
    results = {mod.name: {} for mod in models}
    for m in matches:
        y = outcome(m)
        preds = [mod.predict(m) for mod in models]
        if m["season"] >= eval_from and all(p is not None for p in preds):
            for mod, p in zip(models, preds):
                correct = p.index(max(p)) == y
                results[mod.name].setdefault(m["season"], []).append(
                    (brier(p, y), correct))
        for mod in models:  # learn the result only after predicting
            mod.update(m)
    return results


def report(results):
    seasons = sorted(next(iter(results.values())))
    print(f"{'model':<10} {'brier':>6} {'acc':>6}  "
          + " ".join(f"{s:>5}" for s in seasons))
    for name, by_season in results.items():
        allv = [x for s in seasons for x in by_season[s]]
        avg = sum(b for b, _ in allv) / len(allv)
        acc = sum(c for _, c in allv) / len(allv)
        per = " ".join(
            f"{sum(b for b, _ in by_season[s]) / len(by_season[s]):.3f}"
            for s in seasons)
        print(f"{name:<10} {avg:.4f} {acc:6.1%}  {per}")