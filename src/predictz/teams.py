import re
import unicodedata

# API name (normalized) -> name used in the football-data.co.uk CSVs
OVERRIDES = {
    "manchester united": "Man United",
    "manchester city": "Man City",
    "newcastle united": "Newcastle",
    "nottingham forest": "Nott'm Forest",
    "brighton and hove albion": "Brighton",
    "tottenham hotspur": "Tottenham",
    "west ham united": "West Ham",
    "wolverhampton wanderers": "Wolves",
    "leicester city": "Leicester",
    "leeds united": "Leeds",
    "norwich city": "Norwich",
    "ipswich town": "Ipswich",
    "luton town": "Luton",
    "coventry city": "Coventry",
    "hull city": "Hull",
    "west bromwich albion": "West Brom",
        # La Liga
    "athletic club": "Ath Bilbao",
    "club atletico de madrid": "Ath Madrid",
    "rcd espanyol de barcelona": "Espanol",
    "deportivo alaves": "Alaves",
    "rc deportivo la coruna": "La Coruna",
    # Serie A
    "internazionale milano": "Inter",
}


def normalize(name):
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().replace("&", "and")
    n = re.sub(r"\b(afc|fc)\b", "", n)
    return re.sub(r"\s+", " ", n).strip()

def _teams(conn, source, competition):
    rows = conn.execute(
        "SELECT home_team AS t FROM matches WHERE source = ? AND competition = ? "
        "UNION SELECT away_team FROM matches WHERE source = ? AND competition = ?",
        (source, competition, source, competition))
    return {r["t"] for r in rows}


def _match(api_name, by_norm):
    key = normalize(api_name)
    if key in by_norm:
        return by_norm[key]
    if OVERRIDES.get(key) in by_norm.values():
        return OVERRIDES[key]
    # last resort: a CSV name appearing inside the API name, only if exactly one does
    hits = [name for norm, name in by_norm.items() if len(norm) >= 4 and norm in key]
    return hits[0] if len(hits) == 1 else None


def build_name_map(conn, competition):
    """Returns (mapping of API name -> CSV name, list of unmapped API names)."""
    csv_names = _teams(conn, "football-data.co.uk", competition)
    by_norm = {normalize(n): n for n in csv_names}
    mapping, unmapped = {}, []
    for api_name in sorted(_teams(conn, "football-data.org", competition)):
        target = _match(api_name, by_norm)
        if target is None:
            unmapped.append(api_name)
        else:
            mapping[api_name] = target

    # two API names must never point at the same CSV name
    claimed = {}
    for api_name, target in mapping.items():
        claimed.setdefault(target, []).append(api_name)
    for names in claimed.values():
        if len(names) > 1:
            for n in names:
                del mapping[n]
                unmapped.append(n)
    return mapping, sorted(unmapped)