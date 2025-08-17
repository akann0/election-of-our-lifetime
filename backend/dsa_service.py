#!/usr/bin/env python3
"""
DSA Service for Flask Integration
Preloads models at startup for fast API responses
"""

import sys
import os
import numpy as np
from typing import Dict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Add parent directory to path to import dsa.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dsa import DemographicSimilarityAnalyzer

class DSAService:
    """
    Service wrapper for DSA that preloads models and provides caching
    """
    
    def __init__(self):
        self.analyzer = None
        self.cache = {}
        self._initialize_analyzer()
    
    def _initialize_analyzer(self):
        """Initialize the DSA analyzer with model preloading"""
        print("🚀 Initializing DSA Service...")
        try:
            # This will load the models during Flask startup
            self.analyzer = DemographicSimilarityAnalyzer(
                use_word_embeddings=True,
                use_sentence_embeddings=True
            )
            print("✅ DSA Service initialized successfully!")
        except Exception as e:
            print(f"❌ Failed to initialize DSA Service: {e}")
            # Fallback to TF-IDF only
            self.analyzer = DemographicSimilarityAnalyzer(
                use_word_embeddings=False,
                use_sentence_embeddings=False
            )
            print("⚠️ DSA Service initialized with TF-IDF fallback")
    
    def analyze(self, choice1: str, choice2: str) -> Dict:
        """
        Analyze similarity between two choices with caching
        """
        # Create cache key
        cache_key = f"{choice1.lower()}|||{choice2.lower()}"
        
        # Check cache first
        if cache_key in self.cache:
            print(f"📋 Using cached DSA results for {choice1} vs {choice2}")
            return self.cache[cache_key]
        
        print(f"🔍 Running DSA analysis for {choice1} vs {choice2}")
        
        # Run analysis
        try:
            results = self.analyzer.calculate_similarities(choice1, choice2)
            
            # Cache results
            self.cache[cache_key] = results
            
            return results
            
        except Exception as e:
            print(f"❌ DSA analysis failed: {e}")
            return {
                "error": str(e),
                "choice1": choice1,
                "choice2": choice2,
                "embedding_method": "failed"
            }
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "cached_analyses": len(self.cache),
            "cache_keys": list(self.cache.keys())
        }
    
    def clear_cache(self):
        """Clear the analysis cache"""
        self.cache.clear()
        print("🗑️ DSA cache cleared")

# Global DSA service instance - this will initialize models at import time
print("🔧 Creating DSA service instance...")
dsa_service = DSAService()
