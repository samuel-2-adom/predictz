from collections import defaultdict
from datetime import datetime, timezone

from predictz.backtest.walk_forward import brier
from predictz.models import outcome
from predictz.predict import upcoming_fixtures
from predictz.storage.db import connect, upsert_predictions
from predictz.teams import build_name_map
from predictz.training import trained_elo
from predictz import config

MODEL = "elo-v2"  # v2 = trained on CSV history plus fresh API results


def log_predictions(competitions=None):
    conn = connect()
    now = datetime.now(timezone.utc)
    for competition in competitions or config.FOOTBALL_COMPETITIONS:
        mapping, unmapped = build_name_map(conn, competition)
        if unmapped:
            print(f"{competition}: skipped, unmapped teams: {unmapped}")
            continue

        elo, _ = trained_elo(conn, competition, mapping)
        rows = []
        for f in upcoming_fixtures(conn, competition):
            kickoff = datetime.fromisoformat(f["utc_date"].replace("Z", "+00:00"))
            if kickoff <= now:   # never touch a prediction once the match started
                continue
            h, d, a = elo.predict({
                "season": f["season"],
                "home_team": mapping[f["home_team"]],
                "away_team": mapping[f["away_team"]],
            })
            rows.append({"model": MODEL, "source_id": f["source_id"],
                         "made_at": now.isoformat(), "kickoff": f["utc_date"],
                         "home_p": h, "draw_p": d, "away_p": a})
        upsert_predictions(conn, rows)
        print(f"{competition}: logged {len(rows)} predictions ({MODEL})")


def score_predictions():
    conn = connect()
    rows = conn.execute("""
        SELECT p.model, m.competition, p.home_p, p.draw_p, p.away_p,
               m.home_goals, m.away_goals
        FROM predictions p
        JOIN matches m ON m.source = 'football-data.org'
                      AND m.source_id = p.source_id
        WHERE m.status = 'FINISHED' AND m.home_goals IS NOT NULL
    """)
    groups = defaultdict(list)
    for r in rows:
        p = [r["home_p"], r["draw_p"], r["away_p"]]
        y = outcome(r)
        result = (brier(p, y), p.index(max(p)) == y)
        groups[(r["model"], "ALL")].append(result)
        groups[(r["model"], r["competition"])].append(result)

    if not groups:
        print("No predictions have a result yet.")
        return
    for (model, comp), vals in sorted(groups.items()):
        n = len(vals)
        print(f"{model:<8} {comp:<4} {n:>4} scored | "
              f"Brier {sum(b for b, _ in vals) / n:.4f} | "
              f"accuracy {sum(c for _, c in vals) / n:.1%}")


def show_scored(model="elo-v2", competition=None):
    conn = connect()
    sql = """
        SELECT m.competition, m.utc_date, m.home_team, m.away_team,
               m.home_goals, m.away_goals, p.home_p, p.draw_p, p.away_p
        FROM predictions p
        JOIN matches m ON m.source = 'football-data.org'
                      AND m.source_id = p.source_id
        WHERE p.model = ? AND m.status = 'FINISHED' AND m.home_goals IS NOT NULL
    """
    args = [model]
    if competition:
        sql += " AND m.competition = ?"
        args.append(competition)
    rows = conn.execute(sql + " ORDER BY m.utc_date, m.competition", args).fetchall()

    if not rows:
        print("No scored predictions yet for", model)
        return

    def short(name):
        return name.replace(" AFC", "").replace(" FC", "")

    labels = ("Home", "Draw", "Away")
    W = 44  # width of the match column
    print(f"{'lg':<4}{'date':<11}{'match':<{W}}{'H/D/A %':<13}{'score':<7}"
          f"{'pick':<6}{'hit':<5}{'brier'}")
    for r in rows:
        p = [r["home_p"], r["draw_p"], r["away_p"]]
        y = outcome(r)
        pick = p.index(max(p))
        match = f"{short(r['home_team'])} v {short(r['away_team'])}"
        probs = "/".join(f"{x * 100:.0f}" for x in p)
        score = f"{r['home_goals']}-{r['away_goals']}"
        print(f"{r['competition']:<4}{r['utc_date'][:10]:<11}{match:<{W}}{probs:<13}"
              f"{score:<7}{labels[pick]:<6}{'yes' if pick == y else 'no':<5}"
              f"{brier(p, y):.3f}")