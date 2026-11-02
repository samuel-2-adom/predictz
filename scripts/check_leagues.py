from predictz.storage.db import connect

conn = connect()
for r in conn.execute(
    "SELECT competition, season, COUNT(*) AS n FROM matches "
    "WHERE source = 'football-data.co.uk' "
    "GROUP BY competition, season ORDER BY competition, season"
):
    print(tuple(r))