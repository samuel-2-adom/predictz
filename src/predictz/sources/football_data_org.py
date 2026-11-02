import time
import requests
from predictz import config

BASE_URL = "https://api.football-data.org/v4"


class FootballDataClient:
    def __init__(self, token=None):
        self.session = requests.Session()
        self.session.headers["X-Auth-Token"] = token or config.FOOTBALL_DATA_TOKEN

    def _get(self, path, params=None, retries=3):
        for attempt in range(retries):
            r = self.session.get(f"{BASE_URL}{path}", params=params, timeout=30)
            available = int(r.headers.get("X-Requests-Available-Minute", 1))
            reset = int(r.headers.get("X-RequestCounter-Reset", 60))

            if r.status_code == 429:           # rate limited: wait, retry
                time.sleep(reset + 1)
                continue
            if r.status_code >= 500:           # server trouble: back off, retry
                time.sleep(2 ** attempt * 2)
                continue

            r.raise_for_status()
            if available <= 0:                 # out of calls: pause before next one
                time.sleep(reset + 1)
            return r.json()
        raise RuntimeError(f"Gave up on {path} after {retries} attempts")

    def matches(self, competition, season=None, status=None):
        params = {k: v for k, v in {"season": season, "status": status}.items() if v}
        return self._get(f"/competitions/{competition}/matches", params)["matches"]