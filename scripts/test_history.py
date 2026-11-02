from predictz.sync import sync_history
from predictz.storage.db import connect

sync_history()

conn = connect()
print("\nMatches per source/season:")
for r in conn.execute(
    "SELECT source, season, COUNT(*) n FROM matches "
    "WHERE status='FINISHED' GROUP BY source, season ORDER BY source, season"
):
    print(tuple(r))
print("Odds rows:", conn.execute("SELECT COUNT(*) FROM odds").fetchone()[0])