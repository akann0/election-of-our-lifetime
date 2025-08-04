import json
import time
from typing import Dict, List, Tuple, Optional
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
from collections import defaultdict
import praw
from reddit_config import get_reddit_credentials

# Simple disk cache filename for sentiment data
SENTIMENT_CACHE_FILE = "sentiment_cache.json"

class SentimentService:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.cache = self.load_sentiment_cache()
        self.cache_duration = 24 * 60 * 60  # 24 hours in seconds
        
        # Initialize Reddit client (will be None if credentials not available)
        self.reddit = None
        try:
            credentials = get_reddit_credentials()
            if credentials["client_id"] != "YOUR_CLIENT_ID_HERE":
                self.reddit = praw.Reddit(
                    client_id=credentials["client_id"],
                    client_secret=credentials["client_secret"],
                    user_agent=credentials["user_agent"]
                )
                print("Reddit API initialized successfully")
            else:
                print("Reddit credentials not configured - using mock data")
        except Exception as e:
            print(f"Reddit API not available: {e}")
            print("Will use mock Reddit data instead")
        
    def load_sentiment_cache(self) -> Dict:
        """Load sentiment cache from disk"""
        try:
            with open(SENTIMENT_CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_sentiment_cache(self):
        """Save sentiment cache to disk"""
        with open(SENTIMENT_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(self.cache, f, indent=2)
    
    def analyze_text_sentiment(self, text: str) -> float:
        """Analyze sentiment of a single text using VADER"""
        if not text or not text.strip():
            return 0.0
        
        # Get VADER sentiment scores
        scores = self.vader.polarity_scores(text)
        
        # Return compound score (-1 to 1)
        return scores['compound']
    
    def is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid (within 24 hours)"""
        if cache_key not in self.cache:
            return False
        
        cached_data = self.cache[cache_key]
        if 'timestamp' not in cached_data:
            return False
        
        # Check if cache is older than 24 hours
        current_time = time.time()
        cache_time = cached_data['timestamp']
        return (current_time - cache_time) < self.cache_duration
    
    def load_subreddit_weights(self) -> List[Dict]:
        """Load weighted subreddit configuration from JSON file"""
        try:
            with open('reddit_WPOI.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('weighted_public_opinion_index', [])
        except Exception as e:
            print(f"Error loading subreddit weights: {e}")
            # Fallback to default subreddits
            return [
                {"subreddit": "r/news", "weight": 15},
                {"subreddit": "r/AskReddit", "weight": 15},
                {"subreddit": "r/politics", "weight": 10}
            ]
    
    def calculate_weighted_average(self, weighted_sentiments: List[Tuple[float, int]]) -> float:
        """Calculate weighted average of sentiment scores"""
        if not weighted_sentiments:
            return 0.0
        
        total_weight = sum(weight for _, weight in weighted_sentiments)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(sentiment * weight for sentiment, weight in weighted_sentiments)
        return weighted_sum / total_weight
    
    def get_reddit_sentiment(self, choice1: str, choice2: str, test_mode: bool = False) -> Dict[str, float]:
        """Get sentiment scores from Reddit using weighted subreddit approach"""
        cache_key = f"reddit_{choice1}_{choice2}"
        TITLES_ANALYZED = 50
        
        # Check cache first
        if self.is_cache_valid(cache_key) and not test_mode:
            print(f"Using cached Reddit data for {choice1} vs {choice2}")
            return self.cache[cache_key]['sentiment']
        
        print(f"Fetching Reddit sentiment for {choice1} vs {choice2}")
        
        try:
            if self.reddit is None:
                # Fallback to mock data if Reddit API not available
                return self.get_mock_reddit_sentiment(choice1, choice2)
            
            # Load weighted subreddit configuration
            subreddit_weights = self.load_subreddit_weights()
            
            # Get sentiment from each subreddit with weights
            weighted_sentiments1 = []
            weighted_sentiments2 = []
            total_posts_analyzed = 0
            successful_subreddits = []
            
            for subreddit_info in subreddit_weights:
                subreddit_name = subreddit_info['subreddit'].replace('r/', '')
                weight = subreddit_info['weight']
                
                try:
                    # Get posts from this specific subreddit
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Get top 2 posts for each term from this subreddit
                    posts1 = list(subreddit.search(choice1, limit=(TITLES_ANALYZED/len(subreddit_weights)), time_filter='year'))
                    posts2 = list(subreddit.search(choice2, limit=(TITLES_ANALYZED/len(subreddit_weights)), time_filter='year'))
                    
                    # Analyze titles
                    if posts1:
                        sentiment1 = self.analyze_titles_sentiment([post.title for post in posts1])
                        weighted_sentiments1.append((sentiment1, weight))
                    
                    if posts2:
                        sentiment2 = self.analyze_titles_sentiment([post.title for post in posts2])
                        weighted_sentiments2.append((sentiment2, weight))
                    
                    total_posts_analyzed += len(posts1) + len(posts2)
                    successful_subreddits.append(subreddit_name)
                    
                except Exception as e:
                    print(f"Error fetching from r/{subreddit_name}: {e}")
                    continue
            
            # Calculate weighted averages
            sentiment1 = self.calculate_weighted_average(weighted_sentiments1)
            sentiment2 = self.calculate_weighted_average(weighted_sentiments2)
            
            result = {choice1: sentiment1, choice2: sentiment2}
            
            # Cache the result
            self.cache[cache_key] = {
                'sentiment': result,
                'timestamp': time.time(),
                'posts_analyzed': total_posts_analyzed,
                'subreddits_used': successful_subreddits
            }
            self.save_sentiment_cache()
            
            print(f"Analyzed {total_posts_analyzed} posts from {len(successful_subreddits)} subreddits")
            
            return result
            
        except Exception as e:
            print(f"Error fetching Reddit sentiment: {e}")
            # Return mock data on error
            return self.get_mock_reddit_sentiment(choice1, choice2)
    
    def analyze_titles_sentiment(self, titles: List[str]) -> float:
        """Analyze sentiment of a list of post titles"""
        if not titles:
            return 0.0
        
        sentiments = []
        for title in titles:
            if title and title.strip():
                sentiment = self.analyze_text_sentiment(title)
                sentiments.append(sentiment)
        
        # Return average sentiment
        return sum(sentiments) / len(sentiments) if sentiments else 0.0
    
    def get_mock_reddit_sentiment(self, choice1: str, choice2: str) -> Dict[str, float]:
        """Return mock Reddit sentiment data when API is unavailable"""
        # Simple mock sentiment based on term length and common words
        def get_mock_score(term):
            # Simple heuristic: longer terms tend to be more specific/positive
            base_score = min(len(term) * 0.02, 0.3)  # Cap at 0.3
            
            # Add some randomness for variety
            import random
            random.seed(hash(term) % 1000)  # Deterministic randomness
            variation = random.uniform(-0.2, 0.2)
            
            return max(-1.0, min(1.0, base_score + variation))
        
        print("Mock Reddit sentiment function called")

        return {
            choice1: get_mock_score(choice1),
            choice2: get_mock_score(choice2)
        }
    
    def get_news_sentiment(self, choice1: str, choice2: str) -> Dict[str, float]:
        """Get sentiment scores from news articles (placeholder for now)"""
        # This is a placeholder - will be implemented with News API
        # For now, return mock sentiment data
        
        # Mock sentiment scores (-1 to 1)
        mock_sentiments = {
            choice1: 0.2,  # Slightly positive
            choice2: 0.0   # Neutral
        }
        
        return mock_sentiments
    
    def combine_sentiment_sources(self, reddit_sentiment: Dict, news_sentiment: Dict) -> Dict[str, float]:
        """Combine sentiment from multiple sources"""
        combined = {}
        
        # Weight the different sources
        reddit_weight = 0.6
        news_weight = 0.4
        
        for choice in reddit_sentiment.keys():
            reddit_score = reddit_sentiment.get(choice, 0.0)
            news_score = news_sentiment.get(choice, 0.0)
            
            # Calculate weighted average
            combined_score = (reddit_score * reddit_weight) + (news_score * news_weight)
            combined[choice] = combined_score
        
        return combined
    
    def analyze_sentiment(self, choice1: str, choice2: str) -> Dict:
        """Main sentiment analysis function"""
        cache_key = f"{choice1}|||{choice2}"
        
        # Check cache first
        if cache_key in self.cache:
            print(f"Using cached sentiment data for {choice1} vs {choice2}")
            return self.cache[cache_key]
        
        print(f"Analyzing sentiment for {choice1} vs {choice2}")
        
        try:
            # Get sentiment from multiple sources
            reddit_sentiment = self.get_reddit_sentiment(choice1, choice2)
            # news_sentiment = self.get_news_sentiment(choice1, choice2)
            
            # # Combine sentiment scores (weight Reddit more heavily for now)
            # combined_sentiment = self.combine_sentiment_sources(
            #     reddit_sentiment, news_sentiment
            # )
            
            # Use reddit sentiment as the main sentiment scores for now
            sentiment_scores = reddit_sentiment
            
            # Create result structure
            result = {
                "sentiment_scores": sentiment_scores,
                "source_breakdown": {
                    "reddit": reddit_sentiment,
                    # "news": news_sentiment
                },
                "metadata": {
                    "choice1": choice1,
                    "choice2": choice2,
                    "timestamp": time.time(),
                    "sources": ["reddit"]
                }
            }
            
            # Cache results
            self.cache[cache_key] = result
            self.save_sentiment_cache()
            print(f"Overall sentiment test result: {result['sentiment_scores']}")
            return result
            
        except Exception as e:
            print(f"Error in sentiment analysis: {e}")
            # Return fallback sentiment data
            return {
                "sentiment_scores": {choice1: 0.0, choice2: 0.0},
                "source_breakdown": {
                    "reddit": {choice1: 0.0, choice2: 0.0},
                    "news": {choice1: 0.0, choice2: 0.0}
                },
                "metadata": {
                    "choice1": choice1,
                    "choice2": choice2,
                    "timestamp": time.time(),
                    "sources": [],
                    "error": str(e)
                }
            }
    
    def get_sentiment_summary(self, choice1: str, choice2: str) -> Dict:
        """Get a summary of sentiment analysis results"""
        sentiment_data = self.analyze_sentiment(choice1, choice2)
        
        # Handle case where sentiment_scores might not exist
        if "sentiment_scores" not in sentiment_data:
            print("Warning: sentiment_scores not found in sentiment_data, using fallback")
            scores = {choice1: 0.0, choice2: 0.0}
        else:
            scores = sentiment_data["sentiment_scores"]
        
        # Ensure both choices have scores
        if choice1 not in scores:
            scores[choice1] = 0.0
        if choice2 not in scores:
            scores[choice2] = 0.0
        
        # Determine winner based on sentiment
        winner = choice1 if scores[choice1] > scores[choice2] else choice2
        margin = abs(scores[choice1] - scores[choice2])
        
        # Categorize sentiment
        def categorize_sentiment(score):
            if score >= 0.15:
                return "very_positive"
            elif score >= 0.05:
                return "positive"
            elif score >= -0.05:
                return "neutral"
            elif score >= -0.15:
                return "negative"
            else:
                return "very_negative"
        
        return {
            "winner": winner,
            "margin": margin,
            "choice1_sentiment": {
                "score": scores[choice1],
                "category": categorize_sentiment(scores[choice1])
            },
            "choice2_sentiment": {
                "score": scores[choice2],
                "category": categorize_sentiment(scores[choice2])
            },
            "overall_sentiment": "positive" if scores[choice1] + scores[choice2] > 0 else "negative",
            "sentiment_data": sentiment_data
        }

# Create a global instance
sentiment_service = SentimentService()

# Test function to verify Reddit integration
def test_reddit_sentiment():
    """Test the Reddit sentiment functionality"""
    service = SentimentService()
    result = service.get_reddit_sentiment("CNN", "Fox News", test_mode=True)
    print(f"Reddit sentiment test result: {result}")
    return result 

test_reddit_sentiment()