#!/usr/bin/env python3
"""
QUICK GPP SUMMARY - Generate and save GPP stacking recommendations
"""

import pandas as pd
from datetime import datetime
import os
from ENHANCED_GPP_STACKING_STRATEGY_FIXED import GPPStackingStrategy

def generate_gpp_summary():
    """Generate and save GPP summary"""
    print("🚀 GENERATING GPP STACKING SUMMARY")
    print("="*50)
    
    try:
        # Run analysis
        analyzer = GPPStackingStrategy()
        results = analyzer.run_analysis()
        
        if not results:
            print("❌ No results generated")
            return
        
        # Extract data
        all_stacks = results.get('all_stacks', [])
        weather_advantages = results.get('weather_advantages', [])
        
        # Create summary
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        summary = []
        
        summary.append("🏆 GPP STACKING SUMMARY")
        summary.append("="*50)
        summary.append(f"Generated: {timestamp}")
        summary.append("")
        
        # Elite stacks
        elite_stacks = [s for s in all_stacks if "ELITE" in s.get('gpp_rating', '')]
        if elite_stacks:
            summary.append("🚀 ELITE STACKS (Use in 40-50% of lineups):")
            for i, stack in enumerate(elite_stacks[:5], 1):
                summary.append(f"  {i}. {stack['team']}: {stack['projected_points']:.1f} pts, {stack['ownership']:.1f}% owned")
                summary.append(f"     Value Ratio: {stack.get('value_ratio', 0):.1f} | Score: {stack.get('stack_score', 0):.0f}")
            summary.append("")
        
        # Excellent stacks
        excellent_stacks = [s for s in all_stacks if "EXCELLENT" in s.get('gpp_rating', '')]
        if excellent_stacks:
            summary.append("⭐ EXCELLENT STACKS (Use in 20-30% of lineups):")
            for i, stack in enumerate(excellent_stacks[:3], 1):
                summary.append(f"  {i}. {stack['team']}: {stack['projected_points']:.1f} pts, {stack['ownership']:.1f}% owned")
                summary.append(f"     Value Ratio: {stack.get('value_ratio', 0):.1f} | Score: {stack.get('stack_score', 0):.0f}")
            summary.append("")
        
        # Weather advantages
        if weather_advantages:
            summary.append("🌡️ WEATHER ADVANTAGES:")
            for advantage in weather_advantages[:3]:
                teams_str = ", ".join(advantage.get('teams', ['Unknown']))
                summary.append(f"  🔥 {teams_str}: {advantage.get('temp', 'N/A')} | {advantage.get('wind', 'N/A')}")
                summary.append(f"     Boost Score: {advantage.get('boost', 0)}/4")
            summary.append("")
        
        # Implementation strategy
        summary.append("💡 QUICK IMPLEMENTATION:")
        if elite_stacks:
            primary = elite_stacks[0]
            summary.append(f"  🎯 Primary: {primary['team']} (40-50% of lineups)")
            if len(elite_stacks) > 1:
                secondary = elite_stacks[1]
                summary.append(f"  ⚡ Secondary: {secondary['team']} (20-30% of lineups)")
        
        summary.append("  📊 Target total lineup ownership <15%")
        summary.append("  🎲 Use 4-5 player stacks for primary teams")
        summary.append("")
        
        summary.append(f"📈 Total teams analyzed: {len(all_stacks)}")
        summary.append(f"🎯 Elite opportunities: {len(elite_stacks)}")
        summary.append(f"✅ Good opportunities: {len(excellent_stacks)}")
        
        # Save to file
        filename = f"../data/gpp_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w') as f:
            f.write('\n'.join(summary))
        
        print(f"\n✅ Summary saved to: {filename}")
        
        # Display key recommendations
        print("\n🎯 KEY RECOMMENDATIONS:")
        if elite_stacks:
            for stack in elite_stacks[:3]:
                print(f"  🚀 {stack['team']}: {stack['projected_points']:.1f} pts, {stack['ownership']:.1f}% owned")
        
        return filename
        
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return None

if __name__ == "__main__":
    generate_gpp_summary()
