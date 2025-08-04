# Sentiment Analysis Integration Plan

## 🎯 Current Status & Next Steps

### **Phase 1: Prepare Current Code (Week 1)**
- ✅ Google Trends integration working
- ✅ Frontend comparison form implemented
- 🔄 **Update `get_election_results.py` to return numeric values**
- 🔄 **Create sentiment analysis service structure**
- 🔄 **Add caching infrastructure for sentiment data**

### **Phase 2: Basic Sentiment Integration (Week 2)**
- 🔄 **Implement VADER sentiment analysis (free, local)**
- 🔄 **Add Reddit API integration**
- 🔄 **Create sentiment scoring algorithm**
- 🔄 **Update frontend to show sentiment data**

### **Phase 3: Advanced Features (Week 3-4)**
- 🔄 **Twitter API integration**
- 🔄 **News API integration**
- 🔄 **Demographic weighting**
- 🔄 **Experiment with sentiment analysis tools**


## 📁 File Structure for Integration

```
backend/
├── get_election_results.py          # Updated with numeric values
├── sentiment_service.py             # NEW: Sentiment analysis logic
├── reddit_service.py                # NEW: Reddit API integration
├── twitter_service.py               # NEW: Twitter API integration
├── news_service.py                  # NEW: News API integration
├── demographic_data.py              # NEW: Political/age demographics
├── sentiment_cache.json             # NEW: Sentiment data cache
├── requirements.txt                 # Updated with sentiment packages
└── server.py                        # Updated with new endpoints

frontend/
├── src/
│   ├── SentimentService.js          # NEW: Frontend sentiment service
│   ├── SentimentMap.js              # NEW: Sentiment visualization
│   ├── ComparisonResults.js         # NEW: Combined results display
│   ├── ElectionService.js           # Updated with sentiment calls
│   └── USMap.js                     # Updated to show numeric values
```

## 🔧 Implementation Details

### **1. Updated `get_election_results.py` Structure**

```python
def compare_google_trends(choice1, choice2, timeframe="now 7-d"):
    # ... existing code ...
    
    return {
        "state_winners": state_winners,
        "state_scores": state_scores,  # NEW: Numeric values per state
        "electoral_tally": dict(electoral_tally),
        "winner": overall,
        "metadata": {
            "choice1": choice1,
            "choice2": choice2,
            "timeframe": timeframe,
            "total_states": len(state_winners)
        }
    }
```

### **2. New Sentiment Service (`sentiment_service.py`)**

```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import praw
import tweepy
import requests
from typing import Dict, List, Tuple

class SentimentService:
    def __init__(self):
        self.vader = SentimentIntensityAnalyzer()
        self.cache = self.load_sentiment_cache()
    
    def analyze_sentiment(self, choice1: str, choice2: str) -> Dict:
        """Main sentiment analysis function"""
        cache_key = f"{choice1}|||{choice2}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Get sentiment from multiple sources
        reddit_sentiment = self.get_reddit_sentiment(choice1, choice2)
        news_sentiment = self.get_news_sentiment(choice1, choice2)
        
        # Combine sentiment scores
        combined_sentiment = self.combine_sentiment_sources(
            reddit_sentiment, news_sentiment
        )
        
        # Cache results
        self.cache[cache_key] = combined_sentiment
        self.save_sentiment_cache()
        
        return combined_sentiment
```

### **3. Reddit Integration (`reddit_service.py`)**

```python
import praw
from typing import Dict, List

class RedditService:
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET",
            user_agent="ElectionSentimentBot/1.0"
        )
    
    def get_reddit_sentiment(self, choice1: str, choice2: str) -> Dict[str, float]:
        """Get sentiment scores from Reddit comments"""
        subreddits = ['all', 'politics', 'news', 'entertainment']
        sentiment_scores = {}
        
        for subreddit_name in subreddits:
            subreddit = self.reddit.subreddit(subreddit_name)
            
            # Search for posts mentioning the terms
            search_terms = [choice1, choice2]
            for term in search_terms:
                posts = subreddit.search(term, limit=10, time_filter='week')
                
                for post in posts:
                    # Analyze post title and comments
                    title_sentiment = self.analyze_text_sentiment(post.title)
                    comment_sentiments = []
                    
                    for comment in post.comments[:20]:  # Top 20 comments
                        if hasattr(comment, 'body'):
                            comment_sentiments.append(
                                self.analyze_text_sentiment(comment.body)
                            )
                    
                    # Calculate weighted sentiment
                    avg_sentiment = self.calculate_weighted_sentiment(
                        title_sentiment, comment_sentiments
                    )
                    
                    # Map to states (simplified for now)
                    sentiment_scores[term] = avg_sentiment
        
        return sentiment_scores
```

### **4. News API Integration (`news_service.py`)**

```python
import requests
from typing import Dict, List

class NewsService:
    def __init__(self):
        self.api_key = "YOUR_NEWS_API_KEY"
        self.base_url = "https://newsapi.org/v2"
    
    def get_news_sentiment(self, choice1: str, choice2: str) -> Dict[str, float]:
        """Get sentiment from news articles"""
        sentiment_scores = {}
        
        for term in [choice1, choice2]:
            articles = self.search_news(term)
            sentiments = []
            
            for article in articles:
                # Analyze headline and description
                headline_sentiment = self.analyze_text_sentiment(article['title'])
                desc_sentiment = self.analyze_text_sentiment(article.get('description', ''))
                
                # Weight headline more heavily
                weighted_sentiment = (headline_sentiment * 0.7) + (desc_sentiment * 0.3)
                sentiments.append(weighted_sentiment)
            
            sentiment_scores[term] = sum(sentiments) / len(sentiments) if sentiments else 0
        
        return sentiment_scores
```

### **5. Demographic Data (`demographic_data.py`)**

```python
# 2020 Election Results for Political Weighting
ELECTION_2020_RESULTS = {
    'AL': {'republican': 0.62, 'democrat': 0.36, 'independent': 0.02},
    'CA': {'republican': 0.34, 'democrat': 0.63, 'independent': 0.03},
    # ... for all states
}

# Age Demographics by Platform
PLATFORM_DEMOGRAPHICS = {
    'reddit': {
        '18-29': 0.64, '30-49': 0.29, '50+': 0.07
    },
    'twitter': {
        '18-29': 0.42, '30-49': 0.27, '50+': 0.31
    },
    'news': {
        '18-29': 0.16, '30-49': 0.34, '50+': 0.50
    }
}

# State Political Leanings (for sentiment weighting)
STATE_POLITICAL_LEAN = {
    'AL': 'republican', 'CA': 'democrat', 'TX': 'republican',
    # ... for all states
}
```

### **6. Updated Server Endpoints (`server.py`)**

```python
@app.route('/sentiment/<choice1>/<choice2>')
def get_sentiment_analysis(choice1, choice2):
    """Get sentiment analysis for two choices"""
    try:
        sentiment_service = SentimentService()
        sentiment_results = sentiment_service.analyze_sentiment(choice1, choice2)
        
        return jsonify({
            "sentiment_data": sentiment_results,
            "timestamp": datetime.now().isoformat(),
            "message": f"Sentiment analysis: {choice1} vs {choice2}"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/combined-analysis/<choice1>/<choice2>')
def get_combined_analysis(choice1, choice2):
    """Get both search volume and sentiment analysis"""
    try:
        # Get search volume data
        search_results = compare_google_trends(choice1, choice2)
        
        # Get sentiment data
        sentiment_service = SentimentService()
        sentiment_results = sentiment_service.analyze_sentiment(choice1, choice2)
        
        # Combine results
        combined_results = combine_search_and_sentiment(
            search_results, sentiment_results
        )
        
        return jsonify(combined_results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

## 📊 Data Flow Architecture

```
User Input (choice1, choice2)
    ↓
Frontend ComparisonForm
    ↓
Backend API Calls:
├── /google-trends/choice1/choice2 (search volume)
├── /sentiment/choice1/choice2 (sentiment analysis)
└── /combined-analysis/choice1/choice2 (both)
    ↓
Data Processing:
├── Google Trends → State-by-state search scores
├── Reddit → Community sentiment scores
├── News → Media sentiment scores
└── Demographic weighting → Final scores
    ↓
Frontend Display:
├── Search Volume Map
├── Sentiment Map
└── Combined Results Map
```

## 🚀 Implementation Priority

### **Week 1: Foundation**
1. Update `get_election_results.py` to return numeric values
2. Create `sentiment_service.py` with VADER integration
3. Add sentiment caching infrastructure
4. Update frontend to display numeric values

### **Week 2: Basic Sentiment**
1. Implement Reddit API integration
2. Create sentiment scoring algorithm
3. Add sentiment visualization to frontend
4. Test with sample comparisons

### **Week 3: Advanced Features**
1. Add News API integration
2. Implement demographic weighting
3. Create combined analysis endpoint
4. Add sentiment trends tracking

### **Week 4: Polish & Optimization**
1. Add Twitter API integration
2. Optimize caching and performance
3. Add advanced visualizations
4. Comprehensive testing

## 💰 Cost Breakdown

| Service | Setup Cost | Monthly Cost | Notes |
|---------|------------|--------------|-------|
| VADER (Python) | $0 | $0 | Free, local processing |
| Reddit API | $0 | $0 | Free tier sufficient |
| News API | $0 | $25-50 | 1000 requests/month |
| Twitter API | $100 | $50-200 | Basic tier |
| **Total** | **$100** | **$75-250** | Scalable based on usage |

## 🎯 Success Metrics

- **Accuracy**: Sentiment scores correlate with real-world popularity
- **Performance**: Response time under 5 seconds for combined analysis
- **User Engagement**: Users prefer sentiment-enhanced results
- **Scalability**: Handle 100+ comparisons per day


Alternatives: Distilled NLI models (cross-encoder/nli-distilroberta-base-v2, distilroberta-base-mnli) offer a speed–accuracy middle ground.