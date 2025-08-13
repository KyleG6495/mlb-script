#!/usr/bin/env python3
"""
Combo Prop Bet Optimizer - Find profitable combinations

This script identifies the best combo prop bets by:
1. Finding players with multiple strong predictions
2. Calculating combo probabilities  
3. Suggesting optimal PrizePicks/Underdog combinations
"""

import pandas as pd
import numpy as np
from itertools import combinations
from enhanced_betting_analyzer import EnhancedBettingAnalyzer

class ComboPropOptimizer:
    def __init__(self):
        self.analyzer = EnhancedBettingAnalyzer()
        self.analyzer.generate_predictions()
    
    def find_power_combos(self, min_players=2, max_players=4):
        """Find the most profitable combo combinations"""
        
        # Get players with strong predictions across multiple stats
        strong_players = []
        
        for _, player in self.analyzer.predictions_df.iterrows():
            player_name = player['player_name']
            strong_stats = []
            confidence_scores = []
            
            # Evaluate each stat
            stat_evaluations = {
                'hits': {'threshold': 1.2, 'weight': 1.0},
                'total_bases': {'threshold': 1.8, 'weight': 1.2},
                'runs': {'threshold': 0.8, 'weight': 1.1},
                'rbi': {'threshold': 0.8, 'weight': 1.1},
                'home_runs': {'threshold': 0.3, 'weight': 1.5},
                'stolen_bases': {'threshold': 0.2, 'weight': 1.3}
            }
            
            for stat, params in stat_evaluations.items():
                if stat in player.index and player[stat] > params['threshold']:
                    prediction = player[stat]
                    confidence = prediction * params['weight']
                    strong_stats.append(stat)
                    confidence_scores.append(confidence)
            
            # Only include players with 2+ strong stats
            if len(strong_stats) >= 2:
                total_confidence = sum(confidence_scores)
                strong_players.append({
                    'player': player_name,
                    'strong_stats': strong_stats,
                    'confidence_score': total_confidence,
                    'stat_count': len(strong_stats),
                    'predictions': {stat: player[stat] for stat in strong_stats}
                })
        
        # Sort by confidence score
        strong_players.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        # Generate combo recommendations
        combos = []
        
        # 2-player combos (most common)
        for player_combo in combinations(strong_players[:8], 2):
            combo_analysis = self.analyze_player_combo(player_combo)
            if combo_analysis['expected_value'] > 0.15:  # 15% minimum EV
                combos.append(combo_analysis)
        
        # 3-player combos (higher payout)
        for player_combo in combinations(strong_players[:6], 3):
            combo_analysis = self.analyze_player_combo(player_combo)
            if combo_analysis['expected_value'] > 0.20:  # 20% minimum EV for 3-player
                combos.append(combo_analysis)
        
        # Sort by expected value
        combos.sort(key=lambda x: x['expected_value'], reverse=True)
        
        return combos[:10]  # Top 10 combos
    
    def analyze_player_combo(self, player_combo):
        """Analyze a specific combination of players"""
        players = [p['player'] for p in player_combo]
        
        # Find best stat combination
        best_combo = self.find_optimal_stat_combo(player_combo)
        
        # Calculate combined probability
        individual_probs = []
        combo_description = []
        
        for i, player_info in enumerate(player_combo):
            stat = best_combo['stats'][i]
            prediction = player_info['predictions'][stat]
            
            # Estimate probability based on prediction vs typical lines
            typical_lines = {
                'hits': 1.5, 'total_bases': 2.5, 'runs': 0.5, 
                'rbi': 1.5, 'home_runs': 0.5, 'stolen_bases': 0.5
            }
            
            line = typical_lines.get(stat, 1.0)
            
            # Simple probability model (can be enhanced)
            if prediction > line * 1.5:
                prob = 0.85  # Very likely
            elif prediction > line * 1.2:
                prob = 0.75  # Likely
            elif prediction > line:
                prob = 0.65  # Moderate
            else:
                prob = 0.45  # Lower chance
            
            individual_probs.append(prob)
            combo_description.append(f"{player_info['player']} {stat.replace('_', ' ').title()}")
        
        # Combined probability (assuming independence - conservative)
        combined_prob = np.prod(individual_probs)
        
        # Expected value calculation with platform-specific payouts
        # PrizePicks and Underdog use FIXED multipliers, not traditional odds
        payout_multiplier = self.get_platform_payout(len(player_combo))
        implied_break_even = 1 / payout_multiplier  # Break-even probability needed
        
        # Expected value for fixed multiplier: (win_prob * (payout - 1)) - (lose_prob * 1)
        expected_value = (combined_prob * (payout_multiplier - 1)) - ((1 - combined_prob) * 1)
        edge = (combined_prob / implied_break_even) - 1
        
        return {
            'players': players,
            'combo_description': ' + '.join(combo_description),
            'individual_probabilities': individual_probs,
            'combined_probability': combined_prob,
            'expected_value': expected_value,
            'edge': edge,
            'payout_multiplier': payout_multiplier,
            'payout': f"{payout_multiplier:.1f}x",
            'platform': 'PrizePicks/Underdog',
            'break_even_prob': implied_break_even,
            'confidence': self.get_combo_confidence(expected_value),
            'risk_level': self.get_risk_level(len(player_combo), combined_prob)
        }
    
    def find_optimal_stat_combo(self, player_combo):
        """Find the best stat combination for these players"""
        
        # For simplicity, pick each player's strongest stat
        best_stats = []
        for player_info in player_combo:
            # Find the stat with highest prediction relative to typical lines
            best_stat = None
            best_ratio = 0
            
            typical_lines = {
                'hits': 1.5, 'total_bases': 2.5, 'runs': 0.5,
                'rbi': 1.5, 'home_runs': 0.5, 'stolen_bases': 0.5
            }
            
            for stat in player_info['strong_stats']:
                prediction = player_info['predictions'][stat]
                typical_line = typical_lines.get(stat, 1.0)
                ratio = prediction / typical_line
                
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_stat = stat
            
            best_stats.append(best_stat or player_info['strong_stats'][0])
        
        return {'stats': best_stats, 'ratios': [best_ratio]}
    
    def get_platform_payout(self, combo_size, platform="prizepicks"):
        """Get exact payout multipliers for PrizePicks/Underdog platforms"""
        
        # EXACT payout structures from the platforms
        payout_structures = {
            'prizepicks': {
                2: 3.0,     # 2-pick = 3x payout (33.33% implied)
                3: 6.0,     # 3-pick = 6x payout (16.67% implied)  
                4: 10.0,    # 4-pick = 10x payout (10% implied)
                5: 20.0,    # 5-pick = 20x payout (5% implied)
                6: 50.0     # 6-pick = 50x payout (2% implied)
            },
            'underdog': {
                2: 3.0,     # 2-pick = 3x payout
                3: 6.0,     # 3-pick = 6x payout
                4: 10.0,    # 4-pick = 10x payout  
                5: 20.0,    # 5-pick = 20x payout
                6: 40.0     # 6-pick = 40x payout (slightly different from PP)
            }
        }
        
        return payout_structures.get(platform, {}).get(combo_size, 3.0)

    def get_combo_confidence(self, expected_value):
        """Get confidence level for combo bet"""
        if expected_value >= 0.30:
            return "🔥 VERY HIGH"
        elif expected_value >= 0.20:
            return "🟢 HIGH" 
        elif expected_value >= 0.15:
            return "🟡 MEDIUM"
        else:
            return "🔵 LOW"
    
    def get_risk_level(self, num_players, combined_prob):
        """Assess risk level of combo"""
        if num_players <= 2 and combined_prob >= 0.60:
            return "LOW RISK"
        elif num_players <= 3 and combined_prob >= 0.40:
            return "MEDIUM RISK"
        else:
            return "HIGH RISK"
    
    def generate_combo_report(self):
        """Generate comprehensive combo prop report"""
        print("🎰 COMBO PROP BET OPTIMIZER")
        print("=" * 50)
        
        combos = self.find_power_combos()
        
        if not combos:
            print("❌ No profitable combo opportunities found")
            return
        
        # Create report
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"betting_analysis/combo_prop_report_{timestamp}.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("🎰 COMBO PROP BET RECOMMENDATIONS\n")
            f.write(f"Generated: {pd.Timestamp.now()}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write("🏆 TOP COMBO OPPORTUNITIES:\n")
            f.write("-" * 40 + "\n\n")
            
            for i, combo in enumerate(combos, 1):
                f.write(f"{i:2d}. {combo['combo_description']}\n")
                f.write(f"    💰 Expected Value: ${combo['expected_value']:.2f} ({combo['confidence']})\n")
                f.write(f"    📊 Win Probability: {combo['combined_probability']:.1%}\n")
                f.write(f"    🎯 Payout: {combo['payout']} | Edge: {combo['edge']:.1%}\n")
                f.write(f"    ⚠️  Risk Level: {combo['risk_level']}\n")
                f.write(f"    🔢 Individual Probs: {[f'{p:.1%}' for p in combo['individual_probabilities']]}\n\n")
            
            f.write("\n📋 COMBO BETTING STRATEGY:\n")
            f.write("-" * 30 + "\n")
            f.write("• Focus on 2-player combos for steady returns\n")
            f.write("• Use 3-player combos sparingly for big payouts\n") 
            f.write("• Only bet combos with 60%+ combined probability\n")
            f.write("• Diversify across multiple smaller combos\n")
        
        print(f"✅ Combo report saved: {report_file}")
        
        # Display top 5 combos
        print(f"\n🏆 TOP 5 COMBO RECOMMENDATIONS:")
        print("-" * 45)
        
        for i, combo in enumerate(combos[:5], 1):
            print(f"{i}. {combo['combo_description']}")
            print(f"   💰 EV: ${combo['expected_value']:.2f} | Win: {combo['combined_probability']:.1%} | {combo['confidence']}")
            print(f"   {combo['payout']} payout | {combo['risk_level']}")
            print()

def main():
    optimizer = ComboPropOptimizer()
    optimizer.generate_combo_report()

if __name__ == "__main__":
    main()
