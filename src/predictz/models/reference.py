from predictz.models import outcome


class Baseline:
    """Predicts the running league-wide home/draw/away frequencies."""
    name = "baseline"

    def __init__(self, prior_games=30):
        self.counts = [prior_games * 0.45, prior_games * 0.25, prior_games * 0.30]

    def predict(self, m):
        total = sum(self.counts)
        return [c / total for c in self.counts]

    def update(self, m):
        self.counts[outcome(m)] += 1


class Bookmaker:
    """Bet365 odds with the bookmaker margin removed. A benchmark, not a model."""
    name = "bookmaker"

    def predict(self, m):
        if None in (m["oh"], m["od"], m["oa"]):
            return None
        raw = [1 / m["oh"], 1 / m["od"], 1 / m["oa"]]
        total = sum(raw)
        return [r / total for r in raw]

    def update(self, m):
        pass