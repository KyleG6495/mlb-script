#!/usr/bin/env python3
"""
Platform Payout Structure Demo
Shows the difference between traditional odds and fixed multipliers
"""

import pandas as pd
from datetime import datetime

def demo_payout_differences():
    """Demonstrate payout differences between platforms"""
    
    print("TARGET: PLATFORM PAYOUT STRUCTURE COMPARISON")
    print("=" * 60)
    
    # Sample betting scenarios
    scenarios = [
        {
            'description': '2-Player Combo',
            'win_probability': 0.40,  # 40% chance to hit
            'traditional_odds': +150,  # Parlay equivalent
            'pp_multiplier': 3.0,      # PrizePicks 3x
            'uf_multiplier': 3.0       # Underdog 3x
        },
        {
            'description': '3-Player Combo', 
            'win_probability': 0.20,  # 20% chance to hit
            'traditional_odds': +400,  # Parlay equivalent
            'pp_multiplier': 6.0,      # PrizePicks 6x
            'uf_multiplier': 6.0       # Underdog 6x
        },
        {
            'description': '4-Player Combo',
            'win_probability': 0.12,  # 12% chance to hit
            'traditional_odds': +733,  # Parlay equivalent
            'pp_multiplier': 10.0,     # PrizePicks 10x
            'uf_multiplier': 10.0      # Underdog 10x
        }
    ]
    
    bet_amount = 25  # $25 bet
    
    print(f"DATA: Analysis for ${bet_amount} bet on each scenario:\n")
    
    for scenario in scenarios:
        print(f"TARGET: {scenario['description']} ({scenario['win_probability']:.0%} Win Probability)")
        print("-" * 40)
        
        # Traditional sportsbook calculation
        odds = scenario['traditional_odds']
        if odds > 0:
            traditional_payout = bet_amount * (odds / 100)
        else:
            traditional_payout = bet_amount * (100 / abs(odds))
        
        traditional_ev = (scenario['win_probability'] * traditional_payout) - ((1 - scenario['win_probability']) * bet_amount)
        
        # PrizePicks calculation
        pp_payout = bet_amount * scenario['pp_multiplier']
        pp_profit = pp_payout - bet_amount
        pp_ev = (scenario['win_probability'] * pp_profit) - ((1 - scenario['win_probability']) * bet_amount)
        
        # Underdog calculation  
        uf_payout = bet_amount * scenario['uf_multiplier']
        uf_profit = uf_payout - bet_amount
        uf_ev = (scenario['win_probability'] * uf_profit) - ((1 - scenario['win_probability']) * bet_amount)
        
        print(f"PROGRESS: Traditional Sportsbook:")
        print(f"   Odds: {odds:+d}")
        print(f"   Win Payout: ${traditional_payout + bet_amount:.2f} (${traditional_payout:.2f} profit)")
        print(f"   Expected Value: ${traditional_ev:+.2f}")
        
        print(f" PrizePicks:")
        print(f"   Multiplier: {scenario['pp_multiplier']:.1f}x")
        print(f"   Win Payout: ${pp_payout:.2f} (${pp_profit:.2f} profit)")
        print(f"   Expected Value: ${pp_ev:+.2f}")
        
        print(f"TARGET: Underdog Fantasy:")
        print(f"   Multiplier: {scenario['uf_multiplier']:.1f}x")
        print(f"   Win Payout: ${uf_payout:.2f} (${uf_profit:.2f} profit)")
        print(f"   Expected Value: ${uf_ev:+.2f}")
        
        # Determine best option
        best_ev = max(traditional_ev, pp_ev, uf_ev)
        if best_ev == traditional_ev:
            best_platform = "Traditional Sportsbook"
        elif best_ev == pp_ev:
            best_platform = "PrizePicks"
        else:
            best_platform = "Underdog Fantasy"
        
        print(f"LINEUP: Best Option: {best_platform} (${best_ev:+.2f} EV)")
        print()
    
    # Break-even analysis
    print("TARGET: BREAK-EVEN PROBABILITY ANALYSIS")
    print("=" * 40)
    
    combo_sizes = [2, 3, 4, 5, 6]
    
    for size in combo_sizes:
        pp_multiplier = get_prizepicks_multiplier(size)
        uf_multiplier = get_underdog_multiplier(size)
        
        pp_breakeven = 1 / pp_multiplier
        uf_breakeven = 1 / uf_multiplier
        
        print(f"{size}-Pick Combo:")
        print(f"   PrizePicks {pp_multiplier:.0f}x: Need {pp_breakeven:.1%} to break even")
        print(f"   Underdog {uf_multiplier:.0f}x: Need {uf_breakeven:.1%} to break even")
        print()

def get_prizepicks_multiplier(combo_size):
    """Get PrizePicks multiplier for combo size"""
    multipliers = {2: 3, 3: 6, 4: 10, 5: 20, 6: 50}
    return multipliers.get(combo_size, 3)

def get_underdog_multiplier(combo_size):
    """Get Underdog Fantasy multiplier for combo size"""
    multipliers = {2: 3, 3: 6, 4: 10, 5: 20, 6: 40}  # 6-pick is different
    return multipliers.get(combo_size, 3)

def demo_kelly_sizing():
    """Show how Kelly sizing differs between platforms"""
    
    print("\nMONEY: KELLY CRITERION SIZING COMPARISON")
    print("=" * 50)
    
    bankroll = 1000
    scenarios = [
        {'win_prob': 0.45, 'multiplier': 3.0, 'description': '2-Pick Combo'},
        {'win_prob': 0.25, 'multiplier': 6.0, 'description': '3-Pick Combo'},
        {'win_prob': 0.15, 'multiplier': 10.0, 'description': '4-Pick Combo'}
    ]
    
    for scenario in scenarios:
        print(f"DATA: {scenario['description']} ({scenario['win_prob']:.0%} Win Probability)")
        
        # Kelly for fixed multiplier: (p * multiplier - 1) / (multiplier - 1)
        kelly_fraction = (scenario['win_prob'] * scenario['multiplier'] - 1) / (scenario['multiplier'] - 1)
        
        # Apply conservative 25% Kelly
        conservative_kelly = kelly_fraction * 0.25
        
        bet_amount = conservative_kelly * bankroll
        
        print(f"   Full Kelly: {kelly_fraction:.1%} of bankroll")
        print(f"   Conservative (25%): {conservative_kelly:.1%} of bankroll")
        print(f"   Recommended Bet: ${bet_amount:.2f}")
        print()

if __name__ == "__main__":
    demo_payout_differences()
    demo_kelly_sizing()
    
    print("TARGET: KEY TAKEAWAYS:")
    print("SUCCESS: Fixed multipliers make EV calculations simpler")
    print("SUCCESS: Higher combo sizes need lower win probabilities to be profitable")
    print("SUCCESS: Kelly sizing prevents overbetting on high-variance combos")
    print("SUCCESS: PrizePicks vs Underdog differences matter for 6-picks")
