import json
import time
from collections import defaultdict
from pytrends.request import TrendReq

# 2024 Electoral College votes (post-2020 reapportionment) including DC
ELECTORAL_COLLEGE = {
    "AL": 9, "AK": 3, "AZ": 11, "AR": 6, "CA": 54,
    "CO": 10, "CT": 7, "DE": 3, "FL": 30, "GA": 16,
    "HI": 4, "ID": 4, "IL": 19, "IN": 11, "IA": 6,
    "KS": 6, "KY": 8, "LA": 8, "ME": 4, "MD": 10,
    "MA": 11, "MI": 14, "MN": 10, "MS": 6, "MO": 10,
    "MT": 4, "NE": 5, "NV": 6, "NH": 4, "NJ": 14,
    "NM": 5, "NY": 28, "NC": 16, "ND": 3, "OH": 17,
    "OK": 7, "OR": 8, "PA": 19, "RI": 4, "SC": 9,
    "SD": 3, "TN": 11, "TX": 40, "UT": 6, "VA": 13,
    "VT": 3, "WA": 12, "WI": 10, "WV": 4, "WY": 3,
    "DC": 3
}

# Google Trends geo codes for U.S. states / DC
STATE_GEO = {state: f"US-{state}" for state in ELECTORAL_COLLEGE.keys()}

# Simple disk cache filename
CACHE_FILE = "trends_cache.json"

def load_cache():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_cache(cache):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2)

def compare_google_trends(choice1, choice2, timeframe="now 7-d", sleep_between=1.0):
    """
    Compare choice1 vs choice2 in each U.S. state using Google Trends (via PyTrends),
    tally electoral votes, and return per-state winners plus overall result.
    """
    pytrends = TrendReq(hl="en-US", tz=0)
    cache = load_cache()
    state_winners = {}
    electoral_tally = defaultdict(int)

    for state, geo in STATE_GEO.items():
        key = f"{choice1}|||{choice2}|||{state}|||{timeframe}"
        reverse_key = f"{choice2}|||{choice1}|||{state}|||{timeframe}"

        if key in cache:
            winner = cache[key]
        elif reverse_key in cache:
            prev = cache[reverse_key]
            winner = choice1 if prev == choice2 else choice2
        else:
            try:
                pytrends.build_payload([choice1, choice2], geo=geo, timeframe=timeframe)
                df = pytrends.interest_over_time()
                print(df)
                if df.empty:
                    winner = choice1  # fallback tie-breaker
                else:
                    latest = df.iloc[-1]
                    val1 = latest.get(choice1, 0)
                    val2 = latest.get(choice2, 0)
                    winner = choice1 if val1 >= val2 else choice2
                cache[key] = winner
                time.sleep(sleep_between)
            except Exception as e:
                # On error, fallback deterministically
                print(f"[WARN] Trends fetch failed for {state} ({geo}): {e}")
                winner = choice1
                cache[key] = winner

        state_winners[state] = winner
        electoral_tally[winner] += ELECTORAL_COLLEGE[state]

    save_cache(cache)
    overall = max(electoral_tally.items(), key=lambda x: x[1])[0]
    return {
        "state_winners": state_winners,
        "electoral_tally": dict(electoral_tally),
        "winner": overall
    }

pytrends = TrendReq(hl="en-US", tz=0)
pytrends.build_payload(["Joe", "John"], geo="US", timeframe="now 7-d")
df = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code=True)
print(df)