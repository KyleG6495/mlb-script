#!/usr/bin/env python3
"""
ENHANCED PLAYER MATCHING SYSTEM
Improves player name matching for better backtest accuracy
"""

import pandas as pd
import re
from difflib import SequenceMatcher
import unicodedata

class EnhancedPlayerMatcher:
    """Advanced player name matching with multiple strategies"""
    
    def __init__(self):
        self.name_cache = {}
        self.common_nicknames = {
            'alex': ['alexander', 'alejandro'],
            'mike': ['michael'],
            'chris': ['christopher', 'christian'],
            'matt': ['matthew'],
            'joe': ['joseph'],
            'rob': ['robert'],
            'dan': ['daniel'],
            'dave': ['david'],
            'steve': ['steven'],
            'tony': ['anthony'],
            'nick': ['nicholas'],
            'tom': ['thomas'],
            'bill': ['william'],
            'jim': ['james'],
            'ed': ['edward'],
            'pete': ['peter'],
            'jr': ['junior'],
            'sr': ['senior']
        }
    
    def normalize_name(self, name):
        """Normalize name for better matching"""
        if pd.isna(name):
            return ""
        
        # Convert to lowercase and remove accents
        name = unicodedata.normalize('NFD', str(name).lower())
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        
        # Remove common suffixes and prefixes
        name = re.sub(r'\b(jr|sr|ii|iii|iv)\b', '', name)
        name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        name = re.sub(r'\s+', ' ', name).strip()  # Normalize spaces
        
        return name
    
    def get_name_variants(self, name):
        """Generate name variants for matching"""
        variants = set()
        normalized = self.normalize_name(name)
        variants.add(normalized)
        
        # Split into parts
        parts = normalized.split()
        if len(parts) >= 2:
            first, last = parts[0], parts[-1]
            variants.add(f"{first} {last}")
            variants.add(f"{last}, {first}")
            variants.add(last)  # Last name only
            
            # Check for nickname variants
            for nick, full_names in self.common_nicknames.items():
                if first == nick:
                    for full_name in full_names:
                        variants.add(f"{full_name} {last}")
                elif first in full_names:
                    variants.add(f"{nick} {last}")
        
        return list(variants)
    
    def similarity_score(self, name1, name2):
        """Calculate similarity between two names"""
        name1 = self.normalize_name(name1)
        name2 = self.normalize_name(name2)
        return SequenceMatcher(None, name1, name2).ratio()
    
    def find_best_match(self, target_name, candidate_names, min_similarity=0.7):
        """Find best matching name from candidates"""
        target_variants = self.get_name_variants(target_name)
        best_match = None
        best_score = 0
        
        for candidate in candidate_names:
            candidate_variants = self.get_name_variants(candidate)
            
            # Check exact matches first
            for t_var in target_variants:
                for c_var in candidate_variants:
                    if t_var == c_var:
                        return candidate, 1.0
            
            # Check similarity scores
            for t_var in target_variants:
                for c_var in candidate_variants:
                    score = self.similarity_score(t_var, c_var)
                    if score > best_score and score >= min_similarity:
                        best_score = score
                        best_match = candidate
        
        return best_match, best_score

def improve_player_matching():
    """Test and improve player matching logic"""
    
    print("STEP: ENHANCED PLAYER MATCHING SYSTEM")
    print("=" * 50)
    
    # Load test data
    lineup_file = "../data/final_tournament_lineups_details_20250809_121538.csv"
    results_file = "../data/actual_results_20250809.csv"
    
    lineups_df = pd.read_csv(lineup_file)
    actual_df = pd.read_csv(results_file)
    
    matcher = EnhancedPlayerMatcher()
    
    print(f"DATA: Testing on {len(lineups_df)} lineup players")
    print(f"DATA: Against {len(actual_df)} actual results")
    
    # Test matching improvement
    original_matches = 0
    enhanced_matches = 0
    total_players = 0
    
    match_examples = []
    
    unique_lineup_players = lineups_df['player_name'].unique()
    actual_names = actual_df['name'].tolist()
    
    for player_name in unique_lineup_players[:20]:  # Test first 20 for speed
        total_players += 1
        
        # Original matching (simple contains)
        original_match = actual_df[
            actual_df['name'].str.contains(player_name.split()[-1], case=False, na=False)
        ]
        if not original_match.empty:
            original_matches += 1
        
        # Enhanced matching
        best_match, score = matcher.find_best_match(player_name, actual_names, min_similarity=0.7)
        if best_match and score >= 0.7:
            enhanced_matches += 1
            match_examples.append({
                'lineup_player': player_name,
                'matched_to': best_match,
                'similarity': score,
                'original_found': not original_match.empty
            })
    
    print(f"\nPROGRESS: MATCHING IMPROVEMENT RESULTS:")
    print(f"Original method: {original_matches}/{total_players} ({original_matches/total_players*100:.1f}%)")
    print(f"Enhanced method: {enhanced_matches}/{total_players} ({enhanced_matches/total_players*100:.1f}%)")
    print(f"Improvement: +{enhanced_matches - original_matches} matches (+{(enhanced_matches - original_matches)/total_players*100:.1f}%)")
    
    print(f"\nTARGET: EXAMPLE MATCHES:")
    for example in match_examples[:5]:
        status = "SUCCESS: NEW" if not example['original_found'] else "SWAP: CONFIRMED"
        print(f"{status} {example['lineup_player']}  {example['matched_to']} ({example['similarity']:.2f})")
    
    return matcher

if __name__ == "__main__":
    improve_player_matching()
