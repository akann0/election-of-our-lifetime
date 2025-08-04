# Reddit API Configuration
# 
# To use Reddit API:
# 1. Go to https://www.reddit.com/prefs/apps
# 2. Click "Create App" or "Create Another App"
# 3. Choose "script" as the app type
# 4. Fill in the details:
#    - Name: ElectionSentimentBot
#    - Description: Sentiment analysis for election comparison app
#    - About URL: (leave blank)
#    - Redirect URI: http://localhost:8000
# 5. Copy the client ID (under the app name) and client secret
# 6. Replace the values below

REDDIT_CONFIG = {
    "client_id": "x2xiuwcec4zc5Ul2Y7JUBg",  # Replace with your actual client ID
    "client_secret": "-FBpjvqtGLOn1CDbha59C8oVZconcQ",  # Replace with your actual client secret
    "user_agent": "ElectionSentimentBot/1.0"
}

# Alternative: Use environment variables
import os

def get_reddit_credentials():
    """Get Reddit credentials from environment variables or config"""
    return {
        "client_id": os.getenv("REDDIT_CLIENT_ID", REDDIT_CONFIG["client_id"]),
        "client_secret": os.getenv("REDDIT_CLIENT_SECRET", REDDIT_CONFIG["client_secret"]),
        "user_agent": REDDIT_CONFIG["user_agent"]
    } 