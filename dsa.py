#!/usr/bin/env python3
"""
Document Similarity Analysis Script

This standalone script compares two choices against demographic profiles 
(LIBERAL, CONSERVATIVE, MODERATE) using document similarity techniques.

Usage:
    python document_similarity_analysis.py "choice1" "choice2"

Requirements:
    pip install sentence-transformers scikit-learn numpy gensim

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

# Try to import gensim for pre-trained word embeddings
try:
    import gensim.downloader as api
    HAS_GENSIM = True
except ImportError:
    HAS_GENSIM = False
    print("Warning: gensim not available. Word embeddings disabled.")

# Try to import sentence transformers for better embeddings
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False
    print("Warning: sentence-transformers not available.")

class DemographicSimilarityAnalyzer:
    """
    Analyzes similarity between choices and demographic profiles
    """
    
    def __init__(self, use_word_embeddings=True, use_sentence_embeddings=True):
        self.word_model = None
        self.sentence_model = None
        self.vectorizer = None
        
        # Try to load models in order of preference
        if use_word_embeddings and HAS_GENSIM:
            try:
                print("Loading GloVe word embeddings...")
                self.word_model = api.load('glove-wiki-gigaword-100')
                print("✅ GloVe model loaded successfully!")
                self.embedding_method = "word_embeddings"
            except Exception as e:
                print(f"❌ Failed to load GloVe: {e}")
                self.word_model = None
        
        if self.word_model is None and use_sentence_embeddings and HAS_SENTENCE_TRANSFORMERS:
            try:
                print("Loading sentence transformer model...")
                self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✅ Sentence transformer loaded successfully!")
                self.embedding_method = "sentence_embeddings"
            except Exception as e:
                print(f"❌ Failed to load sentence transformer: {e}")
                self.sentence_model = None
        
        if self.word_model is None and self.sentence_model is None:
            print("📝 Using TF-IDF vectorization as fallback...")
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2)
            )
            self.embedding_method = "tfidf"
        
        # Define demographic profiles
        self.demographic_profiles = self._create_demographic_profiles()
    
    def _create_demographic_profiles(self) -> Dict[str, str]:
        """
        
        """
        # Fixed: Use the rich profiles instead of single words!
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

    def get_word_embedding(self, text: str) -> np.ndarray:
        """Get average word embedding for text using GloVe"""
        words = text.lower().split()
        embeddings = []
        
        for word in words:
            try:
                if word in self.word_model:
                    embeddings.append(self.word_model[word])
            except KeyError:
                continue
        
        if embeddings:
            return np.mean(embeddings, axis=0)
        else:
            # Return zero vector if no words found
            return np.zeros(self.word_model.vector_size)

    def get_embeddings(self, texts: List[str]) -> np.ndarray:
        """Get embeddings for a list of texts using the best available method"""
        if self.word_model is not None:
            # Use GloVe word embeddings
            embeddings = []
            for text in texts:
                emb = self.get_word_embedding(text)
                embeddings.append(emb)
            return np.array(embeddings)
        
        elif self.sentence_model is not None:
            # Use sentence transformers
            return self.sentence_model.encode(texts)
        
        else:
            # Fallback to TF-IDF
            return self.vectorizer.fit_transform(texts).toarray()
    
    def calculate_similarities(self, choice1: str, choice2: str) -> Dict:
        """
        Calculate similarity scores using DIFFERENCE-BASED scoring to amplify distinctions
        """
        print(f"\n🔍 Analyzing: '{choice1}' vs '{choice2}'")
        print(f"📊 Using method: {self.embedding_method} (difference-based)")
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
        moderate_emb = embeddings[4].reshape(1, -1)
        
        # Calculate raw cosine similarities
        raw_sims = {}
        for choice, choice_emb in [(choice1, choice1_emb), (choice2, choice2_emb)]:
            raw_sims[choice] = {
                "CONSERVATIVE": float(cosine_similarity(choice_emb, conservative_emb)[0][0]),
                "LIBERAL": float(cosine_similarity(choice_emb, liberal_emb)[0][0]),
                "MODERATE": float(cosine_similarity(choice_emb, moderate_emb)[0][0])
            }
        
        # DIFFERENCE-BASED SCORING: Calculate relative similarities
        # Each demographic gets a score based on how much MORE similar it is than the average
        results = {
            "choice1": choice1,
            "choice2": choice2,
            "embedding_method": self.embedding_method + "_difference_based",
            "raw_similarities": raw_sims,  # Keep raw for debugging
            "demographic_similarities": {}
        }
        
        # Calculate difference-based scores for each choice
        for choice in [choice1, choice2]:
            choice_raw = raw_sims[choice]
            avg_sim = np.mean(list(choice_raw.values()))  # Average similarity across all demographics
            
            # Calculate relative scores: how much above/below average each demographic is
            results["demographic_similarities"][choice] = {}
            for demo in ["CONSERVATIVE", "LIBERAL", "MODERATE"]:
                # Amplify differences from the mean
                difference = choice_raw[demo] - avg_sim
                
                # Apply exponential amplification to make differences more pronounced
                amplified_score = np.tanh(difference * 10) * 0.5 + 0.5  # Maps to 0-1 range
                
                results["demographic_similarities"][choice][demo] = float(amplified_score)
        
        # Reorganize for easier access (maintain backward compatibility)
        demographic_sims = {}
        for demo in ["CONSERVATIVE", "LIBERAL", "MODERATE"]:
            demographic_sims[demo] = {
                choice1: results["demographic_similarities"][choice1][demo],
                choice2: results["demographic_similarities"][choice2][demo]
            }
        results["demographic_similarities"] = demographic_sims
        
        # Calculate preferences using the new difference-based scores
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
                "confidence": "high" if margin > 0.3 else "medium" if margin > 0.15 else "low"
            }
        
        # Calculate vote splits using difference-based scores (should be more distinct now!)
        results["vote_splits"] = {}
        for demo in ["CONSERVATIVE", "LIBERAL", "MODERATE"]:
            sim1 = results["demographic_similarities"][demo][choice1]
            sim2 = results["demographic_similarities"][demo][choice2]
            
            total = sim1 + sim2
            if total > 0:
                pct1 = (sim1 / total) * 100
                pct2 = (sim2 / total) * 100
            else:
                # Fallback (should rarely happen now)
                pct1 = 50
                pct2 = 50
            
            results["vote_splits"][demo] = {
                choice1: round(pct1, 1),
                choice2: round(pct2, 1)
            }
        
        return results
    
    def print_results(self, results: Dict):
        """Print formatted results to console"""
        print(f"\n🔍 SIMILARITY ANALYSIS RESULTS")
        print(f"Method: {results.get('embedding_method', 'unknown')}")
        print(f"Comparing: {results['choice1']} vs {results['choice2']}")
        print("=" * 60)
        
        # Show raw similarities for debugging (if available)
        if "raw_similarities" in results:
            print("\n🔍 RAW COSINE SIMILARITIES (before difference-based transformation):")
            for choice in [results['choice1'], results['choice2']]:
                print(f"\n{choice}:")
                raw = results["raw_similarities"][choice]
                for demo in ["CONSERVATIVE", "MODERATE", "LIBERAL"]:
                    print(f"  {demo}: {raw[demo]:.6f}")
        
        print("\n📊 DIFFERENCE-BASED SIMILARITIES (amplified distinctions):")
        for demo in ["CONSERVATIVE", "MODERATE", "LIBERAL"]:
            sims = results["demographic_similarities"][demo]
            print(f"\n{demo}:")
            print(f"  {results['choice1']}: {sims[results['choice1']]:.6f}")
            print(f"  {results['choice2']}: {sims[results['choice2']]:.6f}")
        
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
    parser.add_argument('--no-word-embeddings', action='store_true', 
                       help='Disable GloVe word embeddings')
    parser.add_argument('--no-sentence-embeddings', action='store_true', 
                       help='Disable sentence transformers')
    parser.add_argument('--save', '-s', help='Save results to specified JSON file')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress console output')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = DemographicSimilarityAnalyzer(
        use_word_embeddings=not args.no_word_embeddings,
        use_sentence_embeddings=not args.no_sentence_embeddings
    )
    
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
    choice1 = ["bacon", "policeman", "trucks", "beards", "fishing", "country"]
    choice2 = ["avocado", "protests", "cars", "mustaches", "hiking", "rap"]
    
    results = [analyzer.calculate_similarities(choice1[i], choice2[i]) for i in range(len(choice1))]
    for result in results:
        analyzer.print_results(result)
    
    return results

if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No arguments provided, run example
        run_example()
    else:
        # Run with command line arguments
        main()