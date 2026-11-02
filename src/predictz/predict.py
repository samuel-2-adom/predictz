from predictz.training import trained_elo
from predictz.storage.db import connect
from predictz.teams import build_name_map


def upcoming_fixtures(conn, competition):
    rows = conn.execute(
        "SELECT source_id,utc_date, home_team, away_team, season FROM matches "
        "WHERE source = 'football-data.org' AND competition = ? "
        "AND status IN ('SCHEDULED', 'TIMED') ORDER BY utc_date",
        (competition,),
    )
    return [dict(r) for r in rows]


def predict_upcoming(competition="PL", n=10):
    conn = connect()
    mapping, unmapped = build_name_map(conn, competition)
    if unmapped:
        print("Unmapped teams, add them to OVERRIDES in teams.py:", unmapped)
        return

    elo, added = trained_elo(conn, competition, mapping)
    print(f"(Elo includes {added} recent matches not yet in the CSV files)\n")

    print(f"{'date':<12}{'home':<16}{'away':<16}{'home':>7}{'draw':>7}{'away':>7}")
    for f in upcoming_fixtures(conn, competition)[:n]:
        m = {"season": f["season"],
             "home_team": mapping[f["home_team"]],
             "away_team": mapping[f["away_team"]]}
        h, d, a = elo.predict(m)
        print(f"{f['utc_date'][:10]:<12}{m['home_team']:<16}{m['away_team']:<16}"
              f"{h:>7.0%}{d:>7.0%}{a:>7.0%}")