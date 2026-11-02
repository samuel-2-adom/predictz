from collections import defaultdict, deque
from datetime import datetime

from predictz.models import outcome
from predictz.models.elo import Elo
from predictz.models.reference import Bookmaker

FORM_N = 5
# league-typical defaults: points, goals for, goals against, SoT for, SoT against
DEFAULTS = (1.4, 1.4, 1.4, 4.5, 4.5)


def _avg(recent):
    if not recent:
        return DEFAULTS
    n = len(recent)
    return tuple(sum(g[i] for g in recent) / n for i in range(5))


def build(matches):
    """One chronological pass. Every feature uses only matches played before it."""
    elo = Elo()
    book = Bookmaker()
    recent = defaultdict(lambda: deque(maxlen=FORM_N))
    last_played = {}
    rows = []

    for m in matches:
        h, a = m["home_team"], m["away_team"]
        date = datetime.strptime(m["utc_date"][:10], "%Y-%m-%d")
        elo_p = elo.predict(m)

        hp, hgf, hga, hsf, hsa = _avg(recent[h])
        ap, agf, aga, asf, asa = _avg(recent[a])
        rest_h = min((date - last_played[h]).days, 14) if h in last_played else 7
        rest_a = min((date - last_played[a]).days, 14) if a in last_played else 7

        rows.append({
            "season": m["season"],
            "x": [elo.ratings[h] - elo.ratings[a], hp - ap, hgf - agf, hga - aga,
                  rest_h - rest_a, hsf - asf, hsa - asa],
            "y": outcome(m),
            "elo_p": elo_p,
            "book_p": book.predict(m),
        })

        hg, ag = m["home_goals"], m["away_goals"]
        h_sot = m["home_sot"] if m["home_sot"] is not None else DEFAULTS[3]
        a_sot = m["away_sot"] if m["away_sot"] is not None else DEFAULTS[3]
        pts_h = 3 if hg > ag else (1 if hg == ag else 0)
        pts_a = 3 if ag > hg else (1 if hg == ag else 0)
        recent[h].append((pts_h, hg, ag, h_sot, a_sot))
        recent[a].append((pts_a, ag, hg, a_sot, h_sot))
        last_played[h] = last_played[a] = date
        elo.update(m)
    return rows