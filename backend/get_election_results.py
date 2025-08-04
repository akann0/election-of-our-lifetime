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
    Uses a single API call to get all state data at once.

    NOTE: estimates for actual numerical values used for previously cached states
    """
    pytrends = TrendReq(hl="en-US", tz=0)
    cache = load_cache()
    state_winners = {}
    state_scores = {}  # Initialize state_scores dictionary
    electoral_tally = defaultdict(int)
    
    # Check cache for existing results first
    cached_states = set()
    for state in STATE_GEO.keys():
        key = f"{choice1}|||{choice2}|||{state}|||{timeframe}"
        reverse_key = f"{choice2}|||{choice1}|||{state}|||{timeframe}"
        
        if key in cache:
            winner = cache[key]
            state_winners[state] = winner
            electoral_tally[winner] += ELECTORAL_COLLEGE[state]
            cached_states.add(state)
        elif reverse_key in cache:
            prev = cache[reverse_key]
            winner = choice1 if prev == choice2 else choice2
            state_winners[state] = winner
            electoral_tally[winner] += ELECTORAL_COLLEGE[state]
            cached_states.add(state)
    
    # Get data for uncached states in a single API call
    uncached_states = set(STATE_GEO.keys()) - cached_states
    if uncached_states:
        try:
            # Build payload for the two choices across all US states
            pytrends.build_payload([choice1, choice2], geo="US", timeframe=timeframe)
            
            # Get interest by region (states) with geo codes
            df = pytrends.interest_by_region(resolution='REGION', inc_low_vol=True, inc_geo_code=True)
            
            
            if not df.empty:
                # Process each state's data once and store both winners and numeric values
                for state in uncached_states:
                    geo_code = STATE_GEO[state]
                    
                    # Try to find the state data
                    state_data = df[df.geoCode == geo_code]
                    
                    if state_data is not None and not state_data.empty:
                        val1 = int(state_data[choice1].iloc[0]) if choice1 in state_data.columns else 0
                        val2 = int(state_data[choice2].iloc[0]) if choice2 in state_data.columns else 0
                        winner = choice1 if val1 >= val2 else choice2
                        
                        # Store the numeric values for this state
                        state_scores[state] = {
                            choice1: val1,
                            choice2: val2,
                            'winner': winner,
                            'margin': abs(val1 - val2)
                        }
                    else:
                        # State not found in results, use fallback
                        winner = choice1
                        state_scores[state] = {
                            choice1: 50,
                            choice2: 50,
                            'winner': winner,
                            'margin': 0
                        }
                    
                    # Cache the result
                    key = f"{choice1}|||{choice2}|||{state}|||{timeframe}"
                    cache[key] = winner
                    
                    state_winners[state] = winner
                    electoral_tally[winner] += ELECTORAL_COLLEGE[state]
            else:
                # No data returned, use fallback for all uncached states
                for state in uncached_states:
                    winner = choice1  # fallback tie-breaker
                    key = f"{choice1}|||{choice2}|||{state}|||{timeframe}"
                    cache[key] = winner
                    state_winners[state] = winner
                    electoral_tally[winner] += ELECTORAL_COLLEGE[state]
                    
                    # Use fallback numeric values
                    state_scores[state] = {
                        choice1: 50,
                        choice2: 50,
                        'winner': winner,
                        'margin': 0
                    }
                    
        except Exception as e:
            # On error, fallback deterministically for all uncached states
            print(f"[WARN] Trends fetch failed for uncached states: {e}")
            for state in uncached_states:
                winner = choice1
                key = f"{choice1}|||{choice2}|||{state}|||{timeframe}"
                cache[key] = winner
                state_winners[state] = winner
                electoral_tally[winner] += ELECTORAL_COLLEGE[state]
                
                # Use fallback numeric values for error cases
                state_scores[state] = {
                    choice1: 50,
                    choice2: 50,
                    'winner': winner,
                    'margin': 0
                }
    
    save_cache(cache)
    overall = max(electoral_tally.items(), key=lambda x: x[1])[0]
    
    # Add cached states to state_scores with estimated values
    for state in cached_states:
        if state not in state_scores:  # Only add if not already processed
            winner = state_winners[state]
            state_scores[state] = {
                choice1: 60 if winner == choice1 else 40,
                choice2: 60 if winner == choice2 else 40,
                'winner': winner,
                'margin': 20
            }
    
    print("Google Trends Overall winner: ", overall)
    
    return {
        "state_winners": state_winners,
        "state_scores": state_scores,  # NEW: Numeric values per state
        "electoral_tally": dict(electoral_tally),
        "winner": overall,
        "metadata": {
            "choice1": choice1,
            "choice2": choice2,
            "timeframe": timeframe,
            "total_states": len(state_winners),
            "cached_states": len(cached_states),
            "uncached_states": len(uncached_states) if 'uncached_states' in locals() else 0
        }
    }
