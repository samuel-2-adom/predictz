import csv
import io
import time
from datetime import datetime, timezone

import requests

from predictz import config

URL = "https://www.football-data.co.uk/mmz4281/{code}/{div}.csv"
DIVISIONS = {"PL": "E0", "PD": "SP1", "SA": "I1"}  # PD = La Liga, SA = Serie A
SOURCE = "football-data.co.uk"


def season_code(start_year):
    return f"{start_year % 100:02d}{(start_year + 1) % 100:02d}"


def _parse_date(text):
    for fmt in ("%d/%m/%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def _float(text):
    try:
        return float(text)
    except (TypeError, ValueError):
        return None

def _int(text):
    try:
        return int(text)
    except (TypeError, ValueError):
        return None


def download_season(div, start_year, force=False):
    """Download once and cache. Old seasons never change, so skip if cached."""
    raw_dir = config.DATA_DIR / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f"{div}_{season_code(start_year)}.csv"
    if path.exists() and not force:
        return path
    r = requests.get(URL.format(code=season_code(start_year), div=div), timeout=30)
    r.raise_for_status()
    path.write_bytes(r.content)
    time.sleep(1)  # be polite to a free site
    return path


def read_season(path, competition, div, start_year):
    data = path.read_bytes()
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = data.decode("latin-1")

    now = datetime.now(timezone.utc).isoformat()
    matches, odds = [], []
    for row in csv.DictReader(io.StringIO(text)):
        d = _parse_date((row.get("Date") or "").strip())
        if not d or not row.get("FTHG") or not row.get("FTAG"):
            continue
        home, away = row["HomeTeam"].strip(), row["AwayTeam"].strip()
        source_id = f"{div}-{d:%Y%m%d}-{home}-{away}"
        matches.append({
            "source": SOURCE, "source_id": source_id, "sport": "football",
            "competition": competition, "season": start_year,
            "utc_date": f"{d:%Y-%m-%d}T00:00:00Z", "status": "FINISHED",
            "home_team": home, "away_team": away,
            "home_goals": int(row["FTHG"]), "away_goals": int(row["FTAG"]),
            "home_shots": _int(row.get("HS")), "away_shots": _int(row.get("AS")),
            "home_sot": _int(row.get("HST")), "away_sot": _int(row.get("AST")),
            "fetched_at": now,
        })
        h, dr, a = (_float(row.get(k)) for k in ("B365H", "B365D", "B365A"))
        if None not in (h, dr, a):
            odds.append({"source": SOURCE, "source_id": source_id,
                         "bookmaker": "B365", "home": h, "draw": dr, "away": a})
    return matches, odds