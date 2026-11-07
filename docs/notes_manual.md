# predictZ: project notes (football)

Hand-written part. Edit this file when a decision changes; the live status
section is added automatically below it by `python -m predictz.cli notes`.

## What this is
A football prediction project in Python, built from scratch. CLI first, web UI
only after the core is solid. Covers the Premier League (PL), La Liga (PD) and
Serie A (SA). Other sports (NBA, F1, tennis) were considered and shelved so
the focus stays on football.

## Environment
- Windows + PowerShell. Project root: C:\Users\SAMUEL\Desktop\MyProjects\predictz
- Virtual environment in `.venv`. Install with `python -m pip install -e .`
  from the project root (redo this if the folder is ever moved).
- Run everything from the project root: `python -m predictz.cli <command>`
- Secrets live in `.env` (FOOTBALL_DATA_TOKEN). Never put them in code.
  `.env` and `data/` are in `.gitignore`.
- Daily sync runs via Windows Task Scheduler using `scripts/daily_sync.bat`
  (log in `data/sync.log`).

## Data sources
- football-data.co.uk CSVs: history 2016 onward, results, Bet365 odds, shots.
  Divisions E0 (PL), SP1 (PD), I1 (SA). Updated about weekly. Cached in
  `data/raw/`.
- football-data.org API v4: upcoming fixtures and fresher results. Free token,
  10 requests per minute, throttled using the X-Requests-Available-Minute and
  X-RequestCounter-Reset headers, retries on 429 and 5xx.
- SQLite database `data/predictz.db`: tables matches, odds, predictions.
  Everything is upserted, so re-running sync never creates duplicates.
- Models train on CSV history plus finished API matches the CSV does not have
  yet (matched by season + home team + away team).
- Team names are mapped API to CSV per league in `teams.py` (accent stripping,
  unique-containment fallback, OVERRIDES dict). A league with unmapped teams is
  skipped with a warning; names are never guessed.

## Commands
- `sync`: refresh both sources, then log predictions for upcoming fixtures
- `predict [--competition PL|PD|SA] [--n 10]`: show upcoming predictions
- `score`: Brier score and accuracy of logged predictions vs real results
- `review [--model elo-v2] [--competition PL]`: each scored prediction next to
  its result
- `notes`: regenerate PROJECT_NOTES.md (this file plus live status)

## Model and rules
- Elo per league. Settings: k=15, home_adv=45, start 1500, new_team 1450
  (promoted teams), season_regress 0.15, mov_pow 0.6 (goal-difference scaling).
  Draw probability from the formula 0.30 - 0.14 * |2e - 1|.
- Tuned on seasons 2017-2022, checked on 2023 onward (never tune on the test
  seasons). Walk-forward backtests only: every feature uses only past matches.
- Predictions are logged before kickoff and never changed afterwards. The model
  name is versioned in the predictions table: elo-v1 is frozen (CSV-only data),
  elo-v2 is current (adds fresh API results). Bump the name when the model
  changes.
- Add features only if they clearly beat plain Elo. Bookmaker odds are a
  benchmark, not an input.

## Results so far (Brier score, lower is better, since 2017)
- PL: baseline 0.6464, Elo 0.5845, bookmaker 0.5683
- La Liga: baseline 0.6458, Elo 0.5925, bookmaker 0.5789
- Serie A: baseline 0.6558, Elo 0.5788, bookmaker 0.5650
- Did not help: scikit-learn logistic regression with form, goals and rest
  (0.5892 vs Elo 0.5874), shots-on-target features (0.5882), calibrated Elo
  (0.5873). Elo + Bet365 odds blend (0.5773) did not beat odds alone (0.5759),
  so no live odds feed is needed.
- Live scoring on 7 Nov 2026: elo-v2 21 scored, Brier 0.6529, accuracy 52.4%
  (PL 12: 0.6086, PD 4: 0.6425, SA 5: 0.7676). Still far too few to judge;
  wait for about 100 scored predictions.

## Plans
- Check in again after the next weekend or two of matches (sync, score, review).
- Optional later: Bundesliga (CSV D1, API BL1) and Ligue 1 (CSV F1, API FL1),
  with a team-mapping check each time.
- Web UI only after the CLI and the track record are solid.

## Continuing in a new chat
Open it inside the same Project, paste this file, and say what you are
continuing. If code is needed, also paste `storage/db.py` and
`backtest/walk_forward.py` so the new chat sees the real structure.
