from predictz.backtest.walk_forward import load_matches
from predictz.models.elo import Elo


def trained_elo(conn, competition, mapping):
    """Elo trained on CSV history plus finished API matches the CSV lacks.
    Returns (elo, number_of_api_only_matches_added)."""
    csv_matches = load_matches(competition)
    seen = {(m["season"], m["home_team"], m["away_team"]) for m in csv_matches}

    rows = conn.execute(
        "SELECT season, utc_date, home_team, away_team, home_goals, away_goals "
        "FROM matches WHERE source = 'football-data.org' AND competition = ? "
        "AND status = 'FINISHED' AND home_goals IS NOT NULL", (competition,))
    extra = []
    for r in rows:
        home, away = mapping.get(r["home_team"]), mapping.get(r["away_team"])
        if home is None or away is None:
            continue                          # unmapped team: skip, never guess
        if (r["season"], home, away) in seen:
            continue                          # the CSV already has this match
        extra.append({"season": r["season"], "utc_date": r["utc_date"],
                      "home_team": home, "away_team": away,
                      "home_goals": r["home_goals"], "away_goals": r["away_goals"]})

    elo = Elo()
    for m in sorted(csv_matches + extra, key=lambda m: m["utc_date"]):
        elo.update(m)
    return elo, len(extra)