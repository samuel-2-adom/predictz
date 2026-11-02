from datetime import datetime, timezone
from predictz import config
from predictz.sources.football_data_org import FootballDataClient
from predictz.storage.db import connect, upsert_matches
# add to the imports at the top:
from predictz.sources import football_data_uk as uk
from predictz.storage.db import upsert_odds


def sync_football(competitions=None):
    client = FootballDataClient()
    conn = connect()
    now = datetime.now(timezone.utc).isoformat()

    for code in competitions or config.FOOTBALL_COMPETITIONS:
        try:
            raw = client.matches(code)
        except Exception as e:
            print(f"{code}: API fetch failed ({e}); keeping the data we have")
            continue
        
        rows = []
        for m in raw:
            full = m["score"]["fullTime"]
            rows.append({
                "source": "football-data.org",
                "source_id": str(m["id"]),
                "sport": "football",
                "competition": code,
                "season": int(m["season"]["startDate"][:4]),
                "utc_date": m["utcDate"],
                "status": m["status"],
                "home_team": m["homeTeam"]["name"],
                "away_team": m["awayTeam"]["name"],
                "home_goals": full["home"],
                "away_goals": full["away"],
                "fetched_at": now,
            })
        upsert_matches(conn, rows)
        print(f"{code}: saved {len(rows)} matches")

def current_season_start():
    today = datetime.now(timezone.utc)
    return today.year if today.month >= 8 else today.year - 1


def sync_history(first_season=2016, competitions=None):
    conn = connect()
    current = current_season_start()
    for code in competitions or config.FOOTBALL_COMPETITIONS:
        div = uk.DIVISIONS[code]
        for year in range(first_season, current + 1):
            try:
                path = uk.download_season(div, year, force=(year == current))
            except Exception as e:
                print(f"{code} {year}: skipped ({e})")
                continue
            matches, odds = uk.read_season(path, code, div, year)
            upsert_matches(conn, matches)
            upsert_odds(conn, odds)
            print(f"{code} {year}: {len(matches)} matches, {len(odds)} odds rows")