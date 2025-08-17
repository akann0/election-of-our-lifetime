from flask import Flask, jsonify
from flask_cors import CORS
import json, pprint
from datetime import datetime
import os, time, random
from typing import Dict, Tuple
from get_election_results import compare_google_trends, load_cache, save_cache
from sentiment_service import sentiment_service
from dsa_service import dsa_service
import numpy as np

# Simulation defaults for calc_state_vote_split
SIM_DEFAULT_N = 200_000
SIM_DEFAULT_RHO = -0.9
SIM_SPLIT_CACHE = {}

def tprint(do_print=False, *args, **kwargs):
    if do_print:
        print(*args, **kwargs)

def calculate_vote_shares(marg_A, marg_B):
    """
    Deterministic vote share calculation from category marginals based on the
    Voting Logic Table. Returns (vote_A_pct, vote_B_pct, turnout_pct), where
    percentages sum to <= 100 and turnout = vote_A_pct + vote_B_pct.

    Accepts marginals as either arrays [fav, neu, unf, unk] or dicts with
    keys 'favorable','neutral','unfavorable','unknown'.
    """
    def to_probs(m):
        if isinstance(m, dict):
            arr = np.array([
                float(m.get('favorable', 0.0)),
                float(m.get('neutral', 0.0)),
                float(m.get('unfavorable', 0.0)),
                float(m.get('unknown', 0.0)),
            ], dtype=float)
        else:
            arr = np.array(m, dtype=float)
        s = arr.sum()
        if s <= 0:
            return np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
        return arr / s

    pA = to_probs(marg_A)  # [F, N, D, U]
    pB = to_probs(marg_B)  # [F, N, D, U]

    # Outcome weights per (i,j) where i in A categories, j in B categories.
    # Categories: 0=F, 1=N, 2=D, 3=U
    # Each entry is (wA, wB, wDNV)
    w = np.zeros((4, 4, 3), dtype=float)

    F, N, D, U = 0, 1, 2, 3

    # Likes A vs ...
    w[F, F] = (0.5, 0.5, 0.0)
    w[F, D] = (1.0, 0.0, 0.0)
    w[F, N] = (1.0, 0.0, 0.0)
    w[F, U] = (1.0, 0.0, 0.0)

    # Neutral A vs ...
    w[N, F] = (0.0, 1.0, 0.0)
    w[N, D] = (1.0, 0.0, 0.0)
    w[N, N] = (1.0/3.0, 1.0/3.0, 1.0/3.0)
    w[N, U] = (0.5, 0.0, 0.5)

    # Dislikes A vs ...
    w[D, F] = (0.0, 1.0, 0.0)
    w[D, N] = (0.0, 1.0, 0.0)
    w[D, U] = (0.0, 0.5, 0.5)
    w[D, D] = (0.0, 0.0, 1.0)

    # Unknown A vs ...
    w[U, F] = (0.0, 1.0, 0.0)
    w[U, N] = (0.0, 0.5, 0.5)
    w[U, D] = (0.5, 0.0, 0.5)
    w[U, U] = (0.0, 0.0, 1.0)

    voteA = 0.0
    voteB = 0.0
    dnv = 0.0
    for i in range(4):
        for j in range(4):
            pij = pA[i] * pB[j]
            voteA += pij * w[i, j, 0]
            voteB += pij * w[i, j, 1]
            dnv   += pij * w[i, j, 2]

    # Normalize small numeric drift
    total = voteA + voteB + dnv
    if total > 0:
        voteA /= total
        voteB /= total
        dnv   /= total

    turnout = (1 - dnv)
    voteA = 100.0 * voteA/turnout
    voteB = 100.0 * voteB/turnout
    return voteA, voteB, turnout

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend requests

# Sample election data - in a real app this would come from a database
ELECTION_DATA = {
    "states": {
        "CA": {"winner": "Democrat", "votes": {"Democrat": 11110250, "Republican": 6006429}, "electoral_votes": 54},
        "TX": {"winner": "Republican", "votes": {"Democrat": 5259126, "Republican": 5890347}, "electoral_votes": 40},
        "FL": {"winner": "Republican", "votes": {"Democrat": 5297045, "Republican": 5668731}, "electoral_votes": 30},
        "NY": {"winner": "Democrat", "votes": {"Democrat": 5244886, "Republican": 3244798}, "electoral_votes": 28},
        "PA": {"winner": "Republican", "votes": {"Democrat": 3458229, "Republican": 3377674}, "electoral_votes": 19},
        "IL": {"winner": "Democrat", "votes": {"Democrat": 3471133, "Republican": 2446891}, "electoral_votes": 19},
        "OH": {"winner": "Republican", "votes": {"Democrat": 2940044, "Republican": 3154834}, "electoral_votes": 17},
        "GA": {"winner": "Republican", "votes": {"Democrat": 2473633, "Republican": 2661405}, "electoral_votes": 16},
        "NC": {"winner": "Republican", "votes": {"Democrat": 2684292, "Republican": 2758775}, "electoral_votes": 16},
        "MI": {"winner": "Republican", "votes": {"Democrat": 2804040, "Republican": 2649852}, "electoral_votes": 15},
        "AZ": {"winner": "Republican", "votes": {"Democrat": 1672143, "Republican": 1661686}, "electoral_votes": 11},
        "WA": {"winner": "Democrat", "votes": {"Democrat": 2369612, "Republican": 1584651}, "electoral_votes": 12},
        "TN": {"winner": "Republican", "votes": {"Democrat": 1143711, "Republican": 1852475}, "electoral_votes": 11},
        "IN": {"winner": "Republican", "votes": {"Democrat": 1242416, "Republican": 1729519}, "electoral_votes": 11},
        "MA": {"winner": "Democrat", "votes": {"Democrat": 2382202, "Republican": 1167202}, "electoral_votes": 11},
        "MD": {"winner": "Democrat", "votes": {"Democrat": 1985023, "Republican": 976414}, "electoral_votes": 10},
        "MO": {"winner": "Republican", "votes": {"Democrat": 1253014, "Republican": 1718736}, "electoral_votes": 10},
        "WI": {"winner": "Republican", "votes": {"Democrat": 1630866, "Republican": 1610184}, "electoral_votes": 10},
        "CO": {"winner": "Democrat", "votes": {"Democrat": 1804352, "Republican": 1364607}, "electoral_votes": 10},
        "MN": {"winner": "Democrat", "votes": {"Democrat": 1717077, "Republican": 1484065}, "electoral_votes": 10},
        "SC": {"winner": "Republican", "votes": {"Democrat": 1151425, "Republican": 1385103}, "electoral_votes": 9},
        "AL": {"winner": "Republican", "votes": {"Democrat": 849624, "Republican": 1441170}, "electoral_votes": 9},
        "LA": {"winner": "Republican", "votes": {"Democrat": 856034, "Republican": 1255776}, "electoral_votes": 8},
        "KY": {"winner": "Republican", "votes": {"Democrat": 628854, "Republican": 1326646}, "electoral_votes": 8},
        "OR": {"winner": "Democrat", "votes": {"Democrat": 1340383, "Republican": 958448}, "electoral_votes": 8},
        "OK": {"winner": "Republican", "votes": {"Democrat": 503890, "Republican": 1020280}, "electoral_votes": 7},
        "CT": {"winner": "Democrat", "votes": {"Democrat": 1080831, "Republican": 715291}, "electoral_votes": 7},
        "UT": {"winner": "Republican", "votes": {"Democrat": 560282, "Republican": 865140}, "electoral_votes": 6},
        "IA": {"winner": "Republican", "votes": {"Democrat": 759061, "Republican": 897672}, "electoral_votes": 6},
        "NV": {"winner": "Republican", "votes": {"Democrat": 703486, "Republican": 750241}, "electoral_votes": 6},
        "AR": {"winner": "Republican", "votes": {"Democrat": 423932, "Republican": 684872}, "electoral_votes": 6},
        "MS": {"winner": "Republican", "votes": {"Democrat": 594733, "Republican": 756764}, "electoral_votes": 6},
        "KS": {"winner": "Republican", "votes": {"Democrat": 427005, "Republican": 771406}, "electoral_votes": 6},
        "NM": {"winner": "Democrat", "votes": {"Democrat": 501614, "Republican": 420615}, "electoral_votes": 5},
        "NE": {"winner": "Republican", "votes": {"Democrat": 374583, "Republican": 556846}, "electoral_votes": 5},
        "ID": {"winner": "Republican", "votes": {"Democrat": 287021, "Republican": 554119}, "electoral_votes": 4},
        "WV": {"winner": "Republican", "votes": {"Democrat": 188794, "Republican": 489371}, "electoral_votes": 4},
        "HI": {"winner": "Democrat", "votes": {"Democrat": 366130, "Republican": 196864}, "electoral_votes": 4},
        "NH": {"winner": "Democrat", "votes": {"Democrat": 424937, "Republican": 365660}, "electoral_votes": 4},
        "ME": {"winner": "Democrat", "votes": {"Democrat": 435072, "Republican": 360737}, "electoral_votes": 4},
        "RI": {"winner": "Democrat", "votes": {"Democrat": 307486, "Republican": 199922}, "electoral_votes": 4},
        "MT": {"winner": "Republican", "votes": {"Democrat": 244786, "Republican": 343602}, "electoral_votes": 4},
        "DE": {"winner": "Democrat", "votes": {"Democrat": 296268, "Republican": 200603}, "electoral_votes": 3},
        "SD": {"winner": "Republican", "votes": {"Democrat": 150471, "Republican": 261043}, "electoral_votes": 3},
        "ND": {"winner": "Republican", "votes": {"Democrat": 114902, "Republican": 235595}, "electoral_votes": 3},
        "AK": {"winner": "Republican", "votes": {"Democrat": 153778, "Republican": 190889}, "electoral_votes": 3},
        "VT": {"winner": "Democrat", "votes": {"Democrat": 242820, "Republican": 112704}, "electoral_votes": 3},
        "WY": {"winner": "Republican", "votes": {"Democrat": 73491, "Republican": 193559}, "electoral_votes": 3},
        "VA": {"winner": "Democrat", "votes": {"Democrat": 2413568, "Republican": 1962430}, "electoral_votes": 13},
        "NJ": {"winner": "Democrat", "votes": {"Democrat": 2608335, "Republican": 1883274}, "electoral_votes": 14}
    },
    "summary": {
        "total_electoral_votes": 538,
        "democrat_electoral": 226,
        "republican_electoral": 312,
        "winner": "Republican"
    },
    "last_updated": datetime.now().isoformat()
}

@app.route('/')
def home():
    return jsonify({
        "message": "Election Results API",
        "version": "1.0",
        "endpoints": [
            "/election-results",
            "/state/<state_code>",
            "/summary"
        ]
    })

@app.route('/election-results')
def get_election_results():
    """Get complete election results"""
    return jsonify(ELECTION_DATA)

@app.route('/state/<state_code>')
def get_state_results(state_code):
    """Get results for a specific state, including demographic-biased sentiment and lean"""
    state_code = state_code.upper()
    if state_code in ELECTION_DATA["states"]:
        # Get the state's demographic lean
        with open('state_demographics.json', 'r', encoding='utf-8') as f:
            state_demographics = json.load(f)
        lean = state_demographics.get(state_code, 'center')
        # Get sentiment summary (no bias applied yet)
        sentiment_summary = sentiment_service.get_sentiment_summary(
            ELECTION_DATA["states"][state_code].get("choice1", ""),
            ELECTION_DATA["states"][state_code].get("choice2", "")
        )
        # Apply bias to the sentiment score using the demographic breakdown
        demo_breakdown = sentiment_summary["sentiment_data"].get("demographic_breakdown", {})
        # Use the state's lean to bias the score
        demo_scores = demo_breakdown.get(lean, {})
        # If we have a demographic score for the lean, use it; otherwise, use the overall
        if demo_scores and all(k in demo_scores for k in [ELECTION_DATA["states"][state_code].get("choice1", ""), ELECTION_DATA["states"][state_code].get("choice2", "")]):
            state_sentiment = {
                "score": demo_scores,
                "source": f"biased toward {lean}"
            }
        else:
            state_sentiment = {
                "score": sentiment_summary["sentiment_data"].get("sentiment_scores", {}),
                "source": "overall"
            }
        return jsonify({
            "state": state_code,
            "data": ELECTION_DATA["states"][state_code],
            "sentiment_summary": sentiment_summary,
            "demographic_lean": lean,
            "state_sentiment": state_sentiment
        })
    else:
        return jsonify({"error": "State not found"}), 404

@app.route('/summary')
def get_summary():
    """Get election summary"""
    return jsonify(ELECTION_DATA["summary"])

@app.route('/generate-random-colors')
def generate_random_colors():
    """Generate random state colors for the map"""

    
    # List of all US state codes including DC
    states = [
        'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
        'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
        'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
        'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
        'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
    ]
    
    # Color options: Red, Blue
    colors = ['#F44336', '#2196F3']
    
    # Generate random colors for each state
    state_colors = {}
    for state in states:
        state_colors[state] = random.choice(colors)
    
    return jsonify({
        "state_colors": state_colors,
        "timestamp": datetime.now().isoformat(),
        "message": "Random state colors generated successfully"
    })

def choose_colors(choice1, choice2):
    """Choose colors for the two choices"""
    return ["#F44336", "#2196F3"]

@app.route('/google-trends/<choice1>/<choice2>')
def google_trends(choice1, choice2):
    """Get Google Trends comparison results"""
    try:
        result = compare_google_trends(choice1, choice2)
        colors = choose_colors(choice1, choice2)
        
        # Create state colors based on winners
        state_colors = {}
        for state, winner in result['state_winners'].items():
            if winner == choice1:
                state_colors[state] = colors[0]  # Red for choice1
            elif winner == choice2:
                state_colors[state] = colors[1]  # Blue for choice2
            else:
                state_colors[state] = '#e0e0e0'  # Gray for unknown
        
        return jsonify({
            "state_colors": state_colors,
            "state_scores": result.get('state_scores', {}),
            "electoral_tally": result.get('electoral_tally', {}),
            "winner": result.get('winner', ''),
            "metadata": result.get('metadata', {}),
            "timestamp": datetime.now().isoformat(),
            "message": f"Google Trends comparison: {choice1} vs {choice2}"
        })
        
    except Exception as e:
        print(f"Error in google_trends endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/sentiment/<choice1>/<choice2>')
def get_sentiment_analysis(choice1, choice2):
    """Get sentiment analysis for two choices"""
    try:
        sentiment_summary = sentiment_service.get_sentiment_summary(choice1, choice2)
        
        return jsonify({
            "sentiment_data": sentiment_summary["sentiment_data"],
            "sentiment_summary": sentiment_summary,
            "demographic_breakdown": sentiment_summary["sentiment_data"].get("demographic_breakdown", {}),
            "demographic_summary": sentiment_summary.get("demographic_summary", {}),
            "timestamp": datetime.now().isoformat(),
            "message": f"Sentiment analysis: {choice1} vs {choice2}"
        })
        
    except Exception as e:
        print(f"Error in sentiment analysis endpoint: {e}")
        return jsonify({"error": str(e)}), 500

def calculate_demographic_bonus(dsa_results: Dict, demographic: str, choice1: str, choice2: str, bonus_multiplier: float = 0.3) -> Tuple[float, float]:
    """
    Calculate demographic bonus/penalty from DSA results
    
    Args:
        dsa_results: Results from DSA analysis
        demographic: The demographic group (CONSERVATIVE, LIBERAL, MODERATE)
        choice1, choice2: The two choices being compared
        bonus_multiplier: How much to amplify the DSA differences (0.0-1.0)
    
    Returns:
        Tuple of (choice1_bonus, choice2_bonus) - values between -bonus_multiplier and +bonus_multiplier
    """
    try:
        # Get the demographic similarities from DSA results
        demo_sims = dsa_results.get("demographic_similarities", {}).get(demographic, {})
        
        if not demo_sims or choice1 not in demo_sims or choice2 not in demo_sims:
            # No DSA data available, return neutral bonuses
            return 0.0, 0.0
        
        sim1 = demo_sims[choice1]
        sim2 = demo_sims[choice2]
        
        # Calculate the difference and apply bonus multiplier
        # DSA similarities are 0-1, so difference is -1 to +1
        diff = sim1 - sim2
        
        # Apply multiplier and clamp to reasonable range
        choice1_bonus = min(max(diff * bonus_multiplier, -bonus_multiplier), bonus_multiplier)
        choice2_bonus = min(max(-diff * bonus_multiplier, -bonus_multiplier), bonus_multiplier)
        
        return choice1_bonus, choice2_bonus
        
    except Exception as e:
        print(f"Error calculating demographic bonus: {e}")
        return 0.0, 0.0

def calculate_vote_split(recognition_1, favorability_1, recognition_2, favorability_2, qprint=False, dsa_bonus_1=0.0, dsa_bonus_2=0.0):
    """
    Gaussian copula simulation of joint attitudes and voting rules with DSA demographic bonuses.

    Inputs:
      - recognition_1, recognition_2: raw recognition scores for A and B
      - favorability_1, favorability_2: base favorability scores (now used with DSA bonuses)
      - dsa_bonus_1, dsa_bonus_2: demographic bonuses from DSA analysis (-0.3 to +0.3)

    Process:
      1) Apply DSA bonuses to favorability scores
      2) Normalize recognitions so R_A + R_B = 1
      3) Build per-candidate marginals using:
         - u(x) = (1 - x)^2  [unknown]
         - n(x) = (1 - u(x)) * (1 - x)  [neutral]
         - remainder = 1 - u - n; split into
              favorable = remainder * (1 + F)/2
              unfavorable = remainder - favorable
      4) Apply voting rules
      5) Return {votedA, votedB, turnout} where VotedA and VotedB sum to 1
    """
    # Apply DSA bonuses to favorability scores
    adjusted_favorability_1 = min(max(favorability_1 + dsa_bonus_1, -1.0), 1.0)
    adjusted_favorability_2 = min(max(favorability_2 + dsa_bonus_2, -1.0), 1.0)
    
    if qprint:
        print(f"Original favorability: {favorability_1:.3f}, {favorability_2:.3f}")
        print(f"DSA bonuses: {dsa_bonus_1:.3f}, {dsa_bonus_2:.3f}")
        print(f"Adjusted favorability: {adjusted_favorability_1:.3f}, {adjusted_favorability_2:.3f}")

    def unknown_frac(x: float) -> float:
        return float((1.0 - x) ** 2)

    def neutral_frac(x: float) -> float:
        u = unknown_frac(x)
        return float(max(0.0, (1.0 - u) * (1.0 - x)))

    def build_four_point_favorability(recognition: float, favorability: float) -> dict:
        u = unknown_frac(recognition)
        n = neutral_frac(recognition)
        approval_split = (1 + favorability) / 2
        rem = max(0.0, 1.0 - u - n)
        f = max(0.0, rem * approval_split)
        uf = max(0.0, rem - f)
        probs = np.array([f, n, uf, u], dtype=float)
        s = probs.sum()
        if s <= 0:
            probs = np.array([0.25, 0.25, 0.25, 0.25], dtype=float)
        else:
            probs = probs / s
        return probs  # order: [fav, neu, unf, unk]

    marg_A = build_four_point_favorability(recognition_1, adjusted_favorability_1)
    marg_B = build_four_point_favorability(recognition_2, adjusted_favorability_2)

    tprint(qprint, f"marg_A: {marg_A}, marg_B: {marg_B}")
    vote_A, vote_B, turnout = calculate_vote_shares(marg_A, marg_B)

    return {
        "marg_A": marg_A,
        "marg_B": marg_B,
        "vote_A": vote_A,
        "vote_B": vote_B,
        "turnout": turnout
    }

def _get_trends_state_scores(choice1: str, choice2: str):
    """Fetch Google Trends comparison and return (search_results, state_scores)."""
    search_results = compare_google_trends(choice1, choice2)
    state_scores = search_results.get('state_scores', {})
    return search_results, state_scores

def _get_sentiment_and_demographics(choice1: str, choice2: str):
    """Fetch sentiment summary once and extract its demographic breakdown."""
    sentiment_summary = sentiment_service.get_sentiment_summary(choice1, choice2)
    demo_breakdown = sentiment_summary["sentiment_data"].get("demographic_breakdown", {})
    return sentiment_summary, demo_breakdown

def _load_state_demographics():
    """Load per-state demographic mix from disk."""
    with open('state_demographics.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def _normalize_state_recognition(score_data: dict, c1: str, c2: str):
    """Compute normalized recognition for a state and total weight."""
    rec1_raw = score_data.get(c1, 0.0)
    rec2_raw = score_data.get(c2, 0.0)
    rec1_norm = rec1_raw / 100.0
    rec2_norm = rec2_raw / 100.0
    rec_total_weight = rec1_raw + rec2_raw + 1e-6  # avoid zero
    return rec1_raw, rec2_raw, rec1_norm, rec2_norm, rec_total_weight

def _init_national_demo_acc():
    return {}

def _ensure_demo_bucket(national_demo_acc: dict, demo: str):
    if demo not in national_demo_acc:
        national_demo_acc[demo] = {
            'w': 0.0,
            'c1': 0.0, 'c2': 0.0,
            'turnout': 0.0
        }

def _update_national_demo_acc(
    national_demo_acc: dict,
    demo: str,
    percent: float,
    rec_total_weight: float,
    pct1: float, pct2: float, turnout: float
):
    _ensure_demo_bucket(national_demo_acc, demo)
    w_national = (percent / 100.0) * rec_total_weight
    national_demo_acc[demo]['w'] += w_national
    national_demo_acc[demo]['c1'] += pct1 * turnout * w_national
    national_demo_acc[demo]['c2'] += pct2 * turnout * w_national
    national_demo_acc[demo]['turnout'] += turnout * w_national

def _finalize_national_demographics(national_demo_acc: dict, c1: str, c2: str):
    national_demographic_vote_splits = {}
    national_demographic_vote_split_components = {}
    for demo, acc in national_demo_acc.items():
        c1_sum = acc['c1']
        c2_sum = acc['c2']
        total = (c1_sum + c2_sum) + 1e-6
        c1_pct = 100.0 * (c1_sum / total)
        c2_pct = 100.0 * (c2_sum / total)
        national_demographic_vote_splits[demo] = {c1: c1_pct, c2: c2_pct}
        
        # For now, components are the same as the main splits since we don't have separate sentiment/recognition
        national_demographic_vote_split_components[demo] = {
            'combined': {c1: c1_pct, c2: c2_pct}
        }
    return national_demographic_vote_splits, national_demographic_vote_split_components

def _winner_and_color(pct1: float, pct2: float, colors: list, c1: str, c2: str):
    if pct1 > pct2:
        return c1, colors[0]
    if pct2 > pct1:
        return c2, colors[1]
    return None, '#e0e0e0'

def _tally_electoral(state_winners: dict, search_results: dict, c1: str, c2: str):
    electoral_tally = {c1: 0, c2: 0}
    for state, winner in state_winners.items():
        if winner:
            votes = search_results.get('electoral_college', {}).get(state) or search_results.get('ELECTORAL_COLLEGE', {}).get(state)
            if not votes:
                votes = 0
            electoral_tally[winner] += votes
    return electoral_tally

@app.route('/combined-analysis/<choice1>/<choice2>')
def get_combined_analysis(choice1, choice2):
    """Get both search volume and sentiment analysis, then for each state, calculate the winner using both sources and demographic bias.

    This endpoint is structured as a series of small, readable helper steps.
    """
    try:
        print(f"Starting combined analysis for {choice1} vs {choice2}")
        # 1) Inputs
        search_results, state_scores = _get_trends_state_scores(choice1, choice2)
        sentiment_summary, demo_breakdown = _get_sentiment_and_demographics(choice1, choice2)
        state_demographics = _load_state_demographics()
        
        # Get DSA analysis for demographic bonuses
        dsa_results = dsa_service.analyze(choice1, choice2)
        print(f"DSA analysis completed for {choice1} vs {choice2}")

        # 2) Iterate states and compute splits
        colors = choose_colors(choice1, choice2)
        state_colors = {}
        state_winners = {}
        state_vote_splits = {}
        demographic_vote_splits = {}
        demographic_vote_split_components = {}
        national_demo_acc = _init_national_demo_acc()
        for state, score_data in state_scores.items():
            demo_percents = state_demographics.get(state, {"conservative": 33, "moderate": 34, "liberal": 33})
            demographic_vote_splits[state] = {}
            demographic_vote_split_components[state] = {}
            tprint((state=="CA"), f"score_data: {score_data}, choice1: {choice1}, choice2: {choice2}")
            rec1_raw, rec2_raw, rec1_norm, rec2_norm, rec_total_weight = _normalize_state_recognition(score_data, choice1, choice2)
            # Initialize state-level accumulators (weighted by demographic share)
            c1_sum = 0.0
            c2_sum = 0.0
            total_turnout = 0.0
            for demo, percent in demo_percents.items():
                # Use national sentiment scores as base, then apply DSA demographic bonuses
                base_fav1 = sentiment_summary["sentiment_data"].get("sentiment_scores", {}).get(choice1, 0.0)
                base_fav2 = sentiment_summary["sentiment_data"].get("sentiment_scores", {}).get(choice2, 0.0)
                
                # Convert demographic key to match DSA format (conservative -> CONSERVATIVE)
                dsa_demo_key = demo.upper()
                
                # Calculate DSA bonuses for this demographic
                dsa_bonus_1, dsa_bonus_2 = calculate_demographic_bonus(dsa_results, dsa_demo_key, choice1, choice2)
                
                # Calculate vote split for this demographic with DSA bonuses
                tprint((state=="CA"), f"demo: {demo}, percent: {percent}, state: {state}")
                tprint((state=="CA"), f"rec1_norm: {rec1_norm}, rec2_norm: {rec2_norm}, base_fav1: {base_fav1}, base_fav2: {base_fav2}")
                tprint((state=="CA"), f"DSA bonuses: {dsa_bonus_1:.3f}, {dsa_bonus_2:.3f}")
                vote_split = calculate_vote_split(rec1_norm, base_fav1, rec2_norm, base_fav2, qprint=(state=="CA"), dsa_bonus_1=dsa_bonus_1, dsa_bonus_2=dsa_bonus_2)
                pct1, pct2, turnout = vote_split['vote_A'], vote_split['vote_B'], vote_split['turnout']
                tprint((state=="CA"), f"pct1: {pct1}, pct2: {pct2}, turnout: {turnout}")
                demographic_vote_splits[state][demo] = {choice1: pct1, choice2: pct2}
                # Accumulate into state-level weighted sums
                w = percent
                c1_sum += pct1 * w * turnout
                c2_sum += pct2 * w * turnout
                total_turnout += w * turnout

                _update_national_demo_acc(
                    national_demo_acc,
                    demo,
                    percent,
                    rec_total_weight,
                    pct1, pct2, turnout
                )
            pct1 = c1_sum / max(total_turnout, 1e-6)
            pct2 = c2_sum / max(total_turnout, 1e-6)
            state_vote_splits[state] = {choice1: pct1, choice2: pct2}
            # Winner and color
            winner, color = _winner_and_color(pct1, pct2, colors, choice1, choice2)
            state_winners[state] = winner
            state_colors[state] = color
        # Tally electoral votes
        electoral_tally = _tally_electoral(state_winners, search_results, choice1, choice2)
        # Build national demographic vote splits (US) from accumulators
        national_demographic_vote_splits, national_demographic_vote_split_components = _finalize_national_demographics(
            national_demo_acc, choice1, choice2
        )

        # Also inject 'US' into the per-state dicts for frontend simplicity
        demographic_vote_splits['US'] = national_demographic_vote_splits

        combined_results = {
            "state_colors": state_colors,
            "state_winners": state_winners,
            "state_vote_splits": state_vote_splits,
            "electoral_tally": electoral_tally,
            "search_data": search_results,
            "sentiment_summary": sentiment_summary,
            "dsa_results": dsa_results,
            "demographic_vote_splits": demographic_vote_splits,
            "metadata": {
                "choice1": choice1,
                "choice2": choice2,
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "combined_with_dsa"
            }
        }

        # Save combined results to file instead of printing (too long for console)
        try:
            with open('combined_results.json', 'w') as f:
                json.dump(combined_results, f, indent=2)
            print(f"Combined results saved to combined_results.json")
        except Exception as save_error:
            print(f"Warning: Could not save combined results to file: {save_error}")
        
        return jsonify(combined_results)
    except Exception as e:
        print(f"Error in combined analysis endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/dsa/<choice1>/<choice2>')
def get_dsa_analysis(choice1, choice2):
    """Get Document Similarity Analysis for two choices"""
    try:
        results = dsa_service.analyze(choice1, choice2)
        
        return jsonify({
            "dsa_results": results,
            "timestamp": datetime.now().isoformat(),
            "message": f"DSA analysis: {choice1} vs {choice2}"
        })
        
    except Exception as e:
        print(f"Error in DSA endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/dsa-cache-stats')
def get_dsa_cache_stats():
    """Get DSA cache statistics"""
    try:
        stats = dsa_service.get_cache_stats()
        return jsonify({
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/dsa-clear-cache', methods=['POST'])
def clear_dsa_cache():
    """Clear DSA cache"""
    try:
        dsa_service.clear_cache()
        return jsonify({
            "message": "DSA cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
