from flask import Flask, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import os

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
    """Get results for a specific state"""
    state_code = state_code.upper()
    if state_code in ELECTION_DATA["states"]:
        return jsonify({
            "state": state_code,
            "data": ELECTION_DATA["states"][state_code]
        })
    else:
        return jsonify({"error": "State not found"}), 404

@app.route('/summary')
def get_summary():
    """Get election summary"""
    return jsonify(ELECTION_DATA["summary"])

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
