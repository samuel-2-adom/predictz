def outcome(m):
    """0 = home win, 1 = draw, 2 = away win."""
    if m["home_goals"] > m["away_goals"]:
        return 0
    if m["home_goals"] == m["away_goals"]:
        return 1
    return 2