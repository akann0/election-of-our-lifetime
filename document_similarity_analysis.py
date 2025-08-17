#!/usr/bin/env python3
"""
Document Similarity Analysis Script

This standalone script compares two choices against demographic profiles 
(LIBERAL, CONSERVATIVE, MODERATE) using document similarity techniques.

Usage:
    python document_similarity_analysis.py "choice1" "choice2"

Requirements:
    pip install sentence-transformers scikit-learn numpy

Author: AI Election Slop Team
Date: 2025
"""

import sys
import numpy as np
from typing import Dict, List, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import argparse

# Try to import sentence transformers for better embeddings
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("Warning: sentence-transformers not available. Using TF-IDF fallback.")

class DemographicSimilarityAnalyzer:
    """
    Analyzes similarity between choices and demographic profiles
    """
    
    def __init__(self, use_embeddings=True):
        self.use_embeddings = use_embeddings and HAS_SENTENCE_TRANSFORMERS
        
        if self.use_embeddings:
            print("Loading sentence transformer model...")
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            print("Model loaded successfully!")
        else:
            print("Using TF-IDF vectorization...")
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
        
        # Define demographic profiles
        self.demographic_profiles = self._create_demographic_profiles()
    
    def _create_demographic_profiles(self) -> Dict[str, str]:
        """
        AGGRESSIVELY opinionated cultural profiles. 
        Everything gets a strong lean - confidently wrong > boringly accurate!
        """

        return {
            "CONSERVATIVE": "conservative",
            "LIBERAL": "liberal",
            "MODERATE": "moderate"
        }

        return {
            "CONSERVATIVE": """
                bacon beef steak meat barbecue grilling hunting fishing ranch cowboy
                pickup truck Ford Chevy GMC diesel truck American muscle cars
                country music classic rock southern rock NASCAR football hunting
                beer domestic beer Budweiser Miller Coors whiskey bourbon
                rural small town farm ranch countryside traditional family
                church faith religion traditional values patriotic American flag
                guns firearms shooting sports outdoor activities camping
                home cooking comfort food hearty meals family recipes southern food
                Walmart McDonald's Cracker Barrel chain restaurants fast food
                work boots jeans flannel traditional clothing practical clothes
                Fox News talk radio conservative traditional old school
                coal oil gas traditional energy blue collar working class
                """,
            
            "LIBERAL": """
                avocado quinoa kale organic vegan vegetarian plant based sustainable
                Tesla Prius electric vehicle bike public transportation urban city
                indie music alternative hip hop jazz world music progressive
                craft beer wine kombucha organic spirits artisanal local
                urban city diverse neighborhood progressive community college educated
                yoga meditation mindfulness wellness alternative holistic natural
                organic farmers market Whole Foods artisanal craft local sustainable
                thrift vintage sustainable fashion ethical brands progressive
                streaming Netflix documentaries indie films art house cinema
                NPR podcasts progressive media social justice activism
                renewable energy solar wind green environmental climate
                tech startup creative professional white collar educated
                """,
            
            "MODERATE": """
                chicken fish balanced diet practical eating chain restaurants
                Honda Toyota Subaru reliable practical mainstream vehicles
                pop music mainstream rock variety genres middle road entertainment
                mixed drinks wine beer practical alcohol choices social drinking
                suburban neighborhood practical community work life balance
                practical spirituality mainstream religion casual faith
                Target Amazon Costco practical shopping mainstream brands
                business casual practical clothing mainstream fashion
                mainstream TV popular movies Netflix practical entertainment
                Facebook practical social media mainstream news sources
                practical environmentalism recycling energy efficiency reasonable
                middle management office worker practical professional moderate income
                """
        }


    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts"""
        if self.use_embeddings:
            return self.model.encode(texts)
        else:
            # Fallback to TF-IDF
            return self.vectorizer.fit_transform(texts).toarray()
    
    def calculate_similarities(self, choice1: str, choice2: str) -> Dict:
        """
        Calculate similarity scores between choices and demographic profiles
        """
        print(f"\nAnalyzing: '{choice1}' vs '{choice2}'")
        print("=" * 50)
        
        # Prepare all texts for embedding/vectorization
        texts = [
            choice1,
            choice2,
            self.demographic_profiles["CONSERVATIVE"],
            self.demographic_profiles["LIBERAL"], 
            self.demographic_profiles["MODERATE"]
        ]
        
        # Get embeddings/vectors
        embeddings = self.get_embeddings(texts)
        
        # Extract individual embeddings
        choice1_emb = embeddings[0].reshape(1, -1)
        choice2_emb = embeddings[1].reshape(1, -1)
        conservative_emb = embeddings[2].reshape(1, -1)
        liberal_emb = embeddings[3].reshape(1, -1)
        
        conservative_similarities = [cosine_similarity(choice1_emb, conservative_emb)[0][0], cosine_similarity(choice2_emb, conservative_emb)[0][0]]
        liberal_similarities = [cosine_similarity(choice1_emb, liberal_emb)[0][0], cosine_similarity(choice2_emb, liberal_emb)[0][0]]
        # Calculate similarities
        results = {
            "choice1": choice1,
            "choice2": choice2,
            "demographic_similarities": {
                "CONSERVATIVE": {
                    choice1: conservative_similarities[0] / liberal_similarities[0],
                    choice2: conservative_similarities[1] / liberal_similarities[1]
                },
                "LIBERAL": {
                    choice1: liberal_similarities[0] / conservative_similarities[0],  
                    choice2: liberal_similarities[1] / conservative_similarities[1]
                },
                "MODERATE": {
                    choice1: 0,
                    choice2: 0
                }
            }
        }
        
        # Calculate relative preferences (which choice each demographic prefers)
        results["demographic_preferences"] = {}
        for demo in ["CONSERVATIVE", "LIBERAL", "MODERATE"]:
            sim1 = results["demographic_similarities"][demo][choice1]
            sim2 = results["demographic_similarities"][demo][choice2]
            
            if sim1 > sim2:
                preferred = choice1
                margin = sim1 - sim2
            else:
                preferred = choice2
                margin = sim2 - sim1
            
            results["demographic_preferences"][demo] = {
                "preferred_choice": preferred,
                "margin": float(margin),
                "confidence": "high" if margin > 0.03 else "medium" if margin > 0.01 else "low"
            }
        
        # Calculate vote split percentages with AGGRESSIVE amplification
        results["vote_splits"] = {}
        for demo in ["CONSERVATIVE", "LIBERAL", "MODERATE"]:
            sim1 = results["demographic_similarities"][demo][choice1]
            sim2 = results["demographic_similarities"][demo][choice2]
            
            total = sim1 + sim2
            if total > 0:
                pct1 = (sim1 / total) * 100
                pct2 = (sim2 / total) * 100
            else:
                # Even if no similarity, pick a side based on hash
                bias = hash(choice1 + choice2 + demo) % 100
                pct1 = 30 + bias * 0.4  # 30-70% range
                pct2 = 100 - pct1
            
            results["vote_splits"][demo] = {
                choice1: round(pct1, 1),
                choice2: round(pct2, 1)
            }
        
        return results
    
    def print_results(self, results: Dict):
        """Print formatted results to console"""
        print(f"\n🔍 SIMILARITY ANALYSIS RESULTS")
        print(f"Comparing: {results['choice1']} vs {results['choice2']}")
        print("=" * 60)
        
        print("\n📊 DEMOGRAPHIC SIMILARITIES:")
        for demo in ["CONSERVATIVE", "MODERATE", "LIBERAL"]:
            sims = results["demographic_similarities"][demo]
            print(f"\n{demo}:")
            print(f"  {results['choice1']}: {sims[results['choice1']]:.10f}")
            print(f"  {results['choice2']}: {sims[results['choice2']]:.10f}")
        
        print("\n🗳️  DEMOGRAPHIC PREFERENCES:")
        for demo in ["CONSERVATIVE", "MODERATE", "LIBERAL"]:
            pref = results["demographic_preferences"][demo]
            print(f"\n{demo}:")
            print(f"  Prefers: {pref['preferred_choice']}")
            print(f"  Margin: {pref['margin']:.3f}")
            print(f"  Confidence: {pref['confidence']}")
        
        print("\n📈 VOTE SPLIT PERCENTAGES:")
        for demo in ["CONSERVATIVE", "MODERATE", "LIBERAL"]:
            split = results["vote_splits"][demo]
            print(f"\n{demo}:")
            print(f"  {results['choice1']}: {split[results['choice1']]}%")
            print(f"  {results['choice2']}: {split[results['choice2']]}%")
        
        print("\n" + "=" * 60)
    
    def save_results(self, results: Dict, filename: str = None):
        """Save results to JSON file"""
        if filename is None:
            choice1_clean = results['choice1'].replace(' ', '_').replace('/', '_')
            choice2_clean = results['choice2'].replace(' ', '_').replace('/', '_')
            filename = f"similarity_analysis_{choice1_clean}_vs_{choice2_clean}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")

def main():
    """Main function to run the similarity analysis"""
    parser = argparse.ArgumentParser(description='Analyze document similarity between choices and demographics')
    parser.add_argument('choice1', help='First choice to analyze')
    parser.add_argument('choice2', help='Second choice to analyze')
    parser.add_argument('--no-embeddings', action='store_true', 
                       help='Use TF-IDF instead of sentence transformers')
    parser.add_argument('--save', '-s', help='Save results to specified JSON file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = DemographicSimilarityAnalyzer(use_embeddings=not args.no_embeddings)
    
    # Run analysis
    results = analyzer.calculate_similarities(args.choice1, args.choice2)
    
    # Print results unless quiet mode
    if not args.quiet:
        analyzer.print_results(results)
    
    # Save results if requested
    if args.save:
        analyzer.save_results(results, args.save)
    elif not args.quiet:
        # Ask if user wants to save
        save_choice = input("\nSave results to JSON file? (y/n): ").lower()
        if save_choice == 'y':
            analyzer.save_results(results)

def run_example():
    """Run an example analysis"""
    print("🚀 Running Example Analysis...")
    analyzer = DemographicSimilarityAnalyzer()
    
    # Example choices
    choice1 = "bacon"
    choice2 = "avocado"
    
    results = analyzer.calculate_similarities(choice1, choice2)
    analyzer.print_results(results)
    
    return results

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run example
        run_example()
    else:
        # Run with command line arguments
        main()
