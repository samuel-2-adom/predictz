from predictz.models import outcome


class Elo:
    name = "elo"

    def __init__(self, k=15, home_adv=45, start=1500, new_team=1450,
        season_regress=0.15, mov_pow=0.6):
        self.k = k
        self.mov_pow = mov_pow
        self.home_adv = home_adv
        self.start = start
        self.new_team = new_team
        self.season_regress = season_regress
        self.ratings = {}
        self.season = None
        self.first_season = None

    def _sync_season(self, season):
        if self.season == season:
            return
        if self.season is None:
            self.first_season = season
        else:  # new season: pull every rating part-way back to the mean
            for team, r in self.ratings.items():
                self.ratings[team] = r + self.season_regress * (self.start - r)
        self.season = season

    def _rating(self, team):
        if team not in self.ratings:
            first = self.season == self.first_season
            self.ratings[team] = self.start if first else self.new_team
        return self.ratings[team]

    def _expected(self, m):
        rh = self._rating(m["home_team"]) + self.home_adv
        ra = self._rating(m["away_team"])
        return 1 / (1 + 10 ** (-(rh - ra) / 400))

    def predict(self, m):
        self._sync_season(m["season"])
        e = self._expected(m)
        p_draw = 0.30 - 0.14 * abs(2 * e - 1)  # draws are likelier in even games
        p_home = max(e - p_draw / 2, 0.01)
        p_away = max(1 - e - p_draw / 2, 0.01)
        total = p_home + p_draw + p_away
        return [p_home / total, p_draw / total, p_away / total]

    def update(self, m):
        self._sync_season(m["season"])
        e = self._expected(m)
        actual = (1.0, 0.5, 0.0)[outcome(m)]
        gd = abs(m["home_goals"] - m["away_goals"])
        delta = self.k * ((1 + gd) ** self.mov_pow) * (actual - e)
        self.ratings[m["home_team"]] += delta
        self.ratings[m["away_team"]] -= delta