from predictz.sync import sync_football
from predictz.storage.db import connect

sync_football()

conn = connect()
for row in conn.execute("SELECT status, COUNT(*) AS n FROM matches GROUP BY status"):
    print(row["status"], row["n"])

print("Last 3 finished:")
for row in conn.execute(
    "SELECT utc_date, home_team, home_goals, away_goals, away_team "
    "FROM matches WHERE status='FINISHED' ORDER BY utc_date DESC LIMIT 3"
):
    print(tuple(row))