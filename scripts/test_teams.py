from predictz import config
from predictz.storage.db import connect
from predictz.teams import build_name_map

conn = connect()
for comp in config.FOOTBALL_COMPETITIONS:
    mapping, unmapped = build_name_map(conn, comp)
    print(f"\n== {comp}: {len(mapping)} mapped ==")
    for api, csv in sorted(mapping.items()):
        print(f"  {api:<34} -> {csv}")
    print(f"  UNMAPPED: {unmapped}")