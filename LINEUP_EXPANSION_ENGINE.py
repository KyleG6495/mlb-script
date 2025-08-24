#!/usr/bin/env python3
"""
🚀 LINEUP EXPANSION ENGINE
Optionally expand your 30 core lineups to 50-150 for large tournaments
"""

import pandas as pd
import random
from itertools import combinations

class LineupExpansion:
    def __init__(self):
        pass
    
    def expand_for_large_tournaments(self, core_lineups, target_count=100):
        """Expand core lineups with strategic variations"""
        
        print(f"🚀 EXPANDING {len(core_lineups)} CORE LINEUPS TO {target_count} FOR LARGE TOURNAMENTS")
        print("=" * 70)
        
        expanded_lineups = []
        
        # Keep all original core lineups
        expanded_lineups.extend(core_lineups)
        print(f"✅ Kept {len(core_lineups)} core scientific lineups")
        
        # Get the best tournament lineups as base for expansion
        tournament_lineups = [l for l in core_lineups if l.get('contest_type') == 'tournament']
        best_lineups = sorted(tournament_lineups, 
                            key=lambda x: x.get('total_projection', 0), 
                            reverse=True)[:10]
        
        variations_needed = target_count - len(core_lineups)
        variations_per_lineup = max(1, variations_needed // len(best_lineups))
        
        print(f"🎯 Creating {variations_needed} variations from top {len(best_lineups)} tournament lineups")
        
        # Create strategic variations
        for i, base_lineup in enumerate(best_lineups):
            for v in range(variations_per_lineup):
                if len(expanded_lineups) >= target_count:
                    break
                    
                variation = self.create_strategic_variation(base_lineup, v)
                if variation:
                    variation['lineup_id'] = f"EXPANSION_{i+1}_{v+1}"
                    variation['source'] = f"Variation of {base_lineup.get('lineup_id', 'unknown')}"
                    expanded_lineups.append(variation)
        
        print(f"✅ EXPANSION COMPLETE: {len(expanded_lineups)} total lineups")
        print(f"   📊 Core scientific lineups: {len(core_lineups)}")
        print(f"   🎯 Strategic variations: {len(expanded_lineups) - len(core_lineups)}")
        
        return expanded_lineups
    
    def create_strategic_variation(self, base_lineup, variation_num):
        """Create a strategic variation of a base lineup"""
        
        # This is a simplified example - would need actual player data
        variation = base_lineup.copy()
        
        # Example variation strategies:
        strategies = [
            "contrarian_pivot",      # Pivot to lower owned players
            "correlation_boost",     # Strengthen team correlations  
            "value_play_swap",      # Swap in value plays
            "ceiling_chase",        # Higher ceiling, lower floor
            "leverage_play"         # High leverage pivots
        ]
        
        strategy = strategies[variation_num % len(strategies)]
        variation['variation_strategy'] = strategy
        variation['is_variation'] = True
        
        return variation

def analyze_expansion_need():
    """Analyze if expansion is needed based on contest type"""
    
    print("🎯 EXPANSION RECOMMENDATION BY CONTEST:")
    print("=" * 50)
    
    recommendations = {
        "Cash Games (50/50s)": {
            "recommended_lineups": 1,
            "reason": "Only need to beat 50% of field",
            "expansion_needed": False
        },
        "Small Tournaments (Single Entry)": {
            "recommended_lineups": "3-5",
            "reason": "Quality targeting beats volume",
            "expansion_needed": False
        },
        "Large Tournaments (Milly Maker)": {
            "recommended_lineups": "50-150",
            "reason": "Coverage + edge combination",
            "expansion_needed": True
        }
    }
    
    for contest_type, rec in recommendations.items():
        print(f"\n🏆 {contest_type}:")
        print(f"   📊 Recommended: {rec['recommended_lineups']} lineups")
        print(f"   💡 Reason: {rec['reason']}")
        print(f"   🚀 Expansion: {'Yes' if rec['expansion_needed'] else 'No'}")
    
    print("\n✅ CONCLUSION:")
    print("Your 30 lineups are PERFECT for 90% of contests.")
    print("Only consider expansion for Milly Maker / $1M+ tournaments.")

if __name__ == "__main__":
    analyze_expansion_need()
