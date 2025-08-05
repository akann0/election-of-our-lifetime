from flask import Flask, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import os, time, random
from get_election_results import compare_google_trends, load_cache, save_cache
from sentiment_service import sentiment_service

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

def calculate_state_vote_split(recognition_1, favorability_1, recognition_2, favorability_2):
    """
    Returns (vote_share_1, vote_share_2) as percentages (0-100),
    using 80% favorability and 20% recognition.
    """
    # Normalize recognition and favorability to 0-1
    def norm(x):
        # If already 0-1, leave as is; if -1 to 1, map to 0-1
        if x < 0 or x > 1:
            return (x + 1) / 2
        return x
    rec1 = norm(recognition_1)
    rec2 = norm(recognition_2)
    fav1 = norm(favorability_1)
    fav2 = norm(favorability_2)
    # Weighted sum
    score1 = 0.2 * rec1 + 0.8 * fav1
    score2 = 0.2 * rec2 + 0.8 * fav2
    # Avoid both zero
    if score1 == 0 and score2 == 0:
        return (50.0, 50.0)
    # Normalize to sum to 100
    total = score1 + score2
    pct1 = (score1 / total) * 100
    pct2 = (score2 / total) * 100
    return (pct1, pct2)

@app.route('/combined-analysis/<choice1>/<choice2>')
def get_combined_analysis(choice1, choice2):
    """Get both search volume and sentiment analysis, then for each state, calculate the winner using both sources and demographic bias."""
    try:
        # Get Google Trends data (state-by-state recognition)
        search_results = compare_google_trends(choice1, choice2)
        state_scores = search_results.get('state_scores', {})
        # Get sentiment analysis ONCE (overall and by demographic)
        sentiment_summary = sentiment_service.get_sentiment_summary(choice1, choice2)
        demo_breakdown = sentiment_summary["sentiment_data"].get("demographic_breakdown", {})
        # Load state demographic leans
        with open('state_demographics.json', 'r', encoding='utf-8') as f:
            state_demographics = json.load(f)
        # Decide winner for each state using both trends and sentiment (with demographic bias)
        colors = choose_colors(choice1, choice2)
        state_colors = {}
        state_winners = {}
        state_vote_splits = {}
        for state, score_data in state_scores.items():
            lean = state_demographics.get(state, 'center')
            demo_scores = demo_breakdown.get(lean, {})
            # Recognition: Google Trends score, normalized 0-1
            rec1 = score_data.get(choice1, 0)
            rec2 = score_data.get(choice2, 0)
            max_rec = max(rec1, rec2, 1)
            rec1_norm = rec1 / max_rec
            rec2_norm = rec2 / max_rec
            # Favorability: sentiment, -1 to 1
            fav1 = demo_scores.get(choice1, sentiment_summary["sentiment_data"].get("sentiment_scores", {}).get(choice1, 0.0))
            fav2 = demo_scores.get(choice2, sentiment_summary["sentiment_data"].get("sentiment_scores", {}).get(choice2, 0.0))
            # Calculate vote split
            pct1, pct2 = calculate_state_vote_split(rec1_norm, fav1, rec2_norm, fav2)
            state_vote_splits[state] = {choice1: pct1, choice2: pct2}
            # Winner and color
            if pct1 > pct2:
                winner = choice1
                state_colors[state] = colors[0]
            elif pct2 > pct1:
                winner = choice2
                state_colors[state] = colors[1]
            else:
                winner = None
                state_colors[state] = '#e0e0e0'
            state_winners[state] = winner
        # Tally electoral votes
        electoral_tally = {choice1: 0, choice2: 0}
        for state, winner in state_winners.items():
            if winner:
                votes = search_results.get('electoral_college', {}).get(state) or search_results.get('ELECTORAL_COLLEGE', {}).get(state)
                if not votes:
                    votes = 0
                electoral_tally[winner] += votes
        combined_results = {
            "state_colors": state_colors,
            "state_winners": state_winners,
            "state_vote_splits": state_vote_splits,
            "electoral_tally": electoral_tally,
            "search_data": search_results,
            "sentiment_summary": sentiment_summary,
            "demographic_breakdown": demo_breakdown,
            "metadata": {
                "choice1": choice1,
                "choice2": choice2,
                "timestamp": datetime.now().isoformat(),
                "analysis_type": "combined"
            }
        }
        return jsonify(combined_results)
    except Exception as e:
        print(f"Error in combined analysis endpoint: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
