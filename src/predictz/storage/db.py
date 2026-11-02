import sqlite3
from predictz import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    source      TEXT NOT NULL,
    source_id   TEXT NOT NULL,
    sport       TEXT NOT NULL DEFAULT 'football',
    competition TEXT,
    season      INTEGER,
    utc_date    TEXT,
    status      TEXT,
    home_team   TEXT,
    away_team   TEXT,
    home_goals  INTEGER,
    away_goals  INTEGER,
    fetched_at  TEXT,
    PRIMARY KEY (source, source_id)
)
"""


ODDS_SCHEMA = """
CREATE TABLE IF NOT EXISTS odds (
    source    TEXT NOT NULL,
    source_id TEXT NOT NULL,
    bookmaker TEXT NOT NULL,
    home REAL, draw REAL, away REAL,
    PRIMARY KEY (source, source_id, bookmaker)
)
"""

NEW_COLUMNS = ["home_shots", "away_shots", "home_sot", "away_sot"]

UPSERT = """
INSERT INTO matches (source, source_id, sport, competition, season, utc_date,
                     status, home_team, away_team, home_goals, away_goals, fetched_at,
                     home_shots, away_shots, home_sot, away_sot)
VALUES (:source, :source_id, :sport, :competition, :season, :utc_date,
        :status, :home_team, :away_team, :home_goals, :away_goals, :fetched_at,
        :home_shots, :away_shots, :home_sot, :away_sot)
ON CONFLICT(source, source_id) DO UPDATE SET
    utc_date=excluded.utc_date, status=excluded.status,
    home_goals=excluded.home_goals, away_goals=excluded.away_goals,
    fetched_at=excluded.fetched_at,
    home_shots=excluded.home_shots, away_shots=excluded.away_shots,
    home_sot=excluded.home_sot, away_sot=excluded.away_sot
"""

PRED_SCHEMA = """
CREATE TABLE IF NOT EXISTS predictions (
    model     TEXT NOT NULL,
    source_id TEXT NOT NULL,   -- the football-data.org match id
    made_at   TEXT NOT NULL,
    kickoff   TEXT NOT NULL,
    home_p REAL, draw_p REAL, away_p REAL,
    PRIMARY KEY (model, source_id)
)
"""

def _migrate(conn):
    """Add new columns to an existing database without losing data."""
    have = {r[1] for r in conn.execute("PRAGMA table_info(matches)")}
    for col in NEW_COLUMNS:
        if col not in have:
            conn.execute(f"ALTER TABLE matches ADD COLUMN {col} INTEGER")


def connect():
    config.DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(SCHEMA)
    conn.execute(ODDS_SCHEMA)
    conn.execute(PRED_SCHEMA)
    _migrate(conn)
    return conn


def upsert_matches(conn, rows):
    blank = dict.fromkeys(NEW_COLUMNS)  # API rows have no shots data
    conn.executemany(UPSERT, [{**blank, **r} for r in rows])
    conn.commit()



ODDS_UPSERT = """
INSERT INTO odds (source, source_id, bookmaker, home, draw, away)
VALUES (:source, :source_id, :bookmaker, :home, :draw, :away)
ON CONFLICT(source, source_id, bookmaker) DO UPDATE SET
    home=excluded.home, draw=excluded.draw, away=excluded.away
"""

def upsert_odds(conn, rows):
    conn.executemany(ODDS_UPSERT, rows)
    conn.commit()


PRED_UPSERT = """
INSERT INTO predictions (model, source_id, made_at, kickoff, home_p, draw_p, away_p)
VALUES (:model, :source_id, :made_at, :kickoff, :home_p, :draw_p, :away_p)
ON CONFLICT(model, source_id) DO UPDATE SET
    made_at=excluded.made_at, kickoff=excluded.kickoff,
    home_p=excluded.home_p, draw_p=excluded.draw_p, away_p=excluded.away_p
"""


def upsert_predictions(conn, rows):
    conn.executemany(PRED_UPSERT, rows)
    conn.commit()