#!/usr/bin/env python3
"""
PRECISE PLAYER MATCHING SYSTEM
Strict matching to avoid false positives like Jonathan Ornelas  Jonathan India
"""

import pandas as pd
import re
from difflib import SequenceMatcher
import unicodedata

class PrecisePlayerMatcher:
    """Precise player name matching with strict validation"""
    
    def __init__(self):
        self.name_cache = {}
        # Only include EXACT nickname mappings
        self.verified_nicknames = {
            'alex': 'alexander',
            'mike': 'michael', 
            'chris': 'christopher',
            'matt': 'matthew',
            'joe': 'joseph',
            'rob': 'robert',
            'dan': 'daniel',
            'dave': 'david',
            'steve': 'steven',
            'tony': 'anthony',
            'nick': 'nicholas',
            'tom': 'thomas',
            'bill': 'william',
            'jim': 'james',
            'ed': 'edward',
            'pete': 'peter'
        }
        
        # Common last name variations
        self.last_name_variants = {
            'perez': ['prez', 'peres'],
            'martinez': ['martnez'],
            'rodriguez': ['rodrguez'],
            'gonzalez': ['gonzlez'],
            'hernandez': ['hernndez'],
            'ramirez': ['ramrez'],
            'jimenez': ['jimnez'],
            'gutierrez': ['gutirrez']
        }
    
    def normalize_name(self, name):
        """Normalize name for matching"""
        if pd.isna(name):
            return ""
        
        # Convert to lowercase and remove accents
        name = unicodedata.normalize('NFD', str(name).lower())
        name = ''.join(c for c in name if unicodedata.category(c) != 'Mn')
        
        # Remove suffixes but keep the core name intact
        name = re.sub(r'\b(jr\.?|sr\.?|ii|iii|iv)\b', '', name)
        name = re.sub(r'[^\w\s]', '', name)  # Remove punctuation
        name = re.sub(r'\s+', ' ', name).strip()  # Normalize spaces
        
        return name
    
    def extract_name_parts(self, full_name):
        """Extract first and last name parts"""
        normalized = self.normalize_name(full_name)
        parts = normalized.split()
        
        if len(parts) == 0:
            return "", ""
        elif len(parts) == 1:
            return "", parts[0]  # Only last name
        else:
            return parts[0], parts[-1]  # First and last
    
    def is_same_person(self, name1, name2, strict_mode=True):
        """Determine if two names refer to the same person"""
        
        first1, last1 = self.extract_name_parts(name1)
        first2, last2 = self.extract_name_parts(name2)
        
        # RULE 1: Last names must match (with accent variations allowed)
        if not self.last_names_match(last1, last2):
            return False, 0.0
        
        # RULE 2: If both have first names, they must be compatible
        if first1 and first2:
            if self.first_names_compatible(first1, first2):
                return True, 1.0
            else:
                return False, 0.0
        
        # RULE 3: If only one has first name, partial match only in non-strict mode
        if not strict_mode and (first1 or first2):
            return True, 0.8
        
        # RULE 4: Only last names available
        if not first1 and not first2:
            return True, 0.9
        
        return False, 0.0
    
    def last_names_match(self, last1, last2):
        """Check if last names match (accounting for accents)"""
        if last1 == last2:
            return True
        
        # Check accent variations
        for base_name, variants in self.last_name_variants.items():
            if (last1 == base_name and last2 in variants) or \
               (last2 == base_name and last1 in variants) or \
               (last1 in variants and last2 in variants):
                return True
        
        return False
    
    def first_names_compatible(self, first1, first2):
        """Check if first names are compatible (exact or nickname)"""
        if first1 == first2:
            return True
        
        # Check nickname mapping both directions
        if first1 in self.verified_nicknames and self.verified_nicknames[first1] == first2:
            return True
        if first2 in self.verified_nicknames and self.verified_nicknames[first2] == first1:
            return True
        
        # Check if one is nickname of the other
        for nick, full in self.verified_nicknames.items():
            if (first1 == nick and first2 == full) or (first1 == full and first2 == nick):
                return True
        
        return False
    
    def find_player_match(self, target_name, candidate_df, strict_mode=True):
        """Find exact player match in candidate dataframe"""
        
        best_match = None
        best_score = 0.0
        
        for _, candidate in candidate_df.iterrows():
            is_match, score = self.is_same_person(target_name, candidate['name'], strict_mode)
            
            if is_match and score > best_score:
                best_match = candidate
                best_score = score
        
        return best_match, best_score

def test_precise_matching():
    """Test the precise matching system"""
    
    print("TARGET: PRECISE PLAYER MATCHING TEST")
    print("=" * 50)
    
    # Load data
    lineup_file = "../data/final_tournament_lineups_details_20250809_121538.csv"
    results_file = "../data/actual_results_20250809.csv"
    
    lineups_df = pd.read_csv(lineup_file)
    actual_df = pd.read_csv(results_file)
    
    matcher = PrecisePlayerMatcher()
    
    print(f"DATA: Testing {len(lineups_df)} lineup players")
    print(f"DATA: Against {len(actual_df)} actual results")
    
    # Test specific problematic cases first
    test_cases = [
        "Jonathan Ornelas",
        "Bryan De La Cruz", 
        "Druw Jones",
        "JP Sears",
        "Carlos Perez"
    ]
    
    print(f"\n TESTING PROBLEMATIC CASES:")
    print("-" * 40)
    
    for test_name in test_cases:
        best_match, score = matcher.find_player_match(test_name, actual_df, strict_mode=True)
        
        if best_match is not None:
            print(f"SUCCESS: {test_name:20}  {best_match['name']:20} ({score:.2f})")
        else:
            print(f"ERROR: {test_name:20}  NO MATCH FOUND")
    
    # Now test all lineup players
    print(f"\nDATA: TESTING ALL LINEUP PLAYERS:")
    print("-" * 40)
    
    matches_found = 0
    total_tested = 0
    high_confidence_matches = 0
    
    match_details = []
    
    for player_name in lineups_df['player_name'].unique():
        total_tested += 1
        
        best_match, score = matcher.find_player_match(player_name, actual_df, strict_mode=True)
        
        if best_match is not None:
            matches_found += 1
            if score >= 0.95:
                high_confidence_matches += 1
            
            match_details.append({
                'lineup_player': player_name,
                'matched_player': best_match['name'],
                'confidence': score,
                'actual_fppg': best_match['fanduel_points']
            })
    
    print(f"Total Players: {total_tested}")
    print(f"Matches Found: {matches_found} ({matches_found/total_tested*100:.1f}%)")
    print(f"High Confidence: {high_confidence_matches} ({high_confidence_matches/total_tested*100:.1f}%)")
    
    # Show best matches
    if match_details:
        match_details.sort(key=lambda x: x['confidence'], reverse=True)
        print(f"\nLINEUP: TOP CONFIDENT MATCHES:")
        for match in match_details[:10]:
            print(f"   {match['lineup_player']:20}  {match['matched_player']:20} "
                  f"({match['confidence']:.2f}) [{match['actual_fppg']:.1f} FPPG]")
    
    return matcher, match_details

if __name__ == "__main__":
    test_precise_matching()
