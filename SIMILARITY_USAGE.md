# Document Similarity Analysis Script

A standalone script for analyzing the similarity between two choices and demographic profiles (CONSERVATIVE, LIBERAL, MODERATE).

## Installation

```bash
# Install required packages
pip install -r similarity_requirements.txt
```

## Usage

### Basic Usage
```bash
# Analyze two choices
python document_similarity_analysis.py "universal healthcare" "free market healthcare"

# Run example analysis (no arguments)
python document_similarity_analysis.py
```

### Advanced Options
```bash
# Use TF-IDF instead of sentence transformers (faster, less accurate)
python document_similarity_analysis.py "choice1" "choice2" --no-embeddings

# Save results to specific file
python document_similarity_analysis.py "choice1" "choice2" --save results.json

# Quiet mode (no console output)
python document_similarity_analysis.py "choice1" "choice2" --quiet
```

## Output

The script provides three types of analysis:

### 1. Demographic Similarities
Raw cosine similarity scores (0-1) between each choice and demographic profile.

### 2. Demographic Preferences  
Which choice each demographic prefers, with confidence levels:
- **High**: margin > 0.1
- **Medium**: margin > 0.05  
- **Low**: margin ≤ 0.05

### 3. Vote Split Percentages
Normalized percentages showing how each demographic would "vote" between the choices.

## Example Output

```
🔍 SIMILARITY ANALYSIS RESULTS
Comparing: universal healthcare vs free market healthcare
============================================================

📊 DEMOGRAPHIC SIMILARITIES:

CONSERVATIVE:
  universal healthcare: 0.234
  free market healthcare: 0.567

MODERATE:
  universal healthcare: 0.445
  free market healthcare: 0.432

LIBERAL:
  universal healthcare: 0.678
  free market healthcare: 0.298

🗳️  DEMOGRAPHIC PREFERENCES:

CONSERVATIVE:
  Prefers: free market healthcare
  Margin: 0.333
  Confidence: high

MODERATE:
  Prefers: universal healthcare
  Margin: 0.013
  Confidence: low

LIBERAL:
  Prefers: universal healthcare
  Margin: 0.380
  Confidence: high

📈 VOTE SPLIT PERCENTAGES:

CONSERVATIVE:
  universal healthcare: 29.2%
  free market healthcare: 70.8%

MODERATE:
  universal healthcare: 50.7%
  free market healthcare: 49.3%

LIBERAL:
  universal healthcare: 69.5%
  free market healthcare: 30.5%
```

## How It Works

1. **Demographic Profiles**: Pre-defined text profiles containing keywords and phrases typical of each demographic
2. **Embeddings**: Uses sentence-transformers (or TF-IDF fallback) to convert text to numerical vectors
3. **Similarity**: Calculates cosine similarity between choice vectors and demographic profile vectors
4. **Analysis**: Determines preferences and vote splits based on relative similarities

## Integration Notes

This script is **completely standalone** and designed NOT to be integrated with existing codebases. It can be:
- Run manually for analysis
- Called from other scripts via subprocess
- Used as a reference for implementing similar functionality
- Modified and adapted as needed

## Performance

- **With sentence-transformers**: More accurate, ~2-3 seconds for analysis
- **With TF-IDF only**: Faster, ~0.5 seconds for analysis
- Results are deterministic and cacheable
