import pandas as pd

def compare_projections_vs_actual():
    """Compare yesterday's actual performance with current projections"""
    
    print("=" * 80)
    print("YESTERDAY'S ACTUAL PERFORMANCE vs TODAY'S PROJECTIONS COMPARISON")
    print("=" * 80)
    
    # Yesterday's Top Performers (Actual Results)
    yesterday_top = [
        ("NYM", 122.6, 30.6),  # Best actual
        ("MIL", 115.9, 29.0),  # 2nd best actual
        ("ATH", 113.4, 28.4),  # 3rd best actual
        ("SEA", 108.1, 27.0),  # 4th best actual
        ("PHI", 89.2, 22.3),   # 5th best actual
    ]
    
    # Today's Top Projections
    today_projections = [
        ("LAD", 48.0, 12.0),   # Best projected
        ("ATH", 47.0, 11.7),   # 2nd projected  
        ("NYY", 46.4, 11.6),   # 3rd projected
        ("LAA", 44.0, 11.0),   # 4th projected
        ("CIN", 43.8, 11.0),   # 5th projected
    ]
    
    print("\nYESTERDAY'S TOP 5 ACTUAL STACK PERFORMANCE:")
    print("-" * 50)
    for i, (team, total, avg) in enumerate(yesterday_top, 1):
        print(f"{i}. {team:4} | Total: {total:6.1f} | Avg: {avg:5.1f}")
    
    print(f"\nTODAY'S TOP 5 PROJECTED STACKS:")
    print("-" * 50)
    for i, (team, total, avg) in enumerate(today_projections, 1):
        print(f"{i}. {team:4} | Total: {total:6.1f} | Avg: {avg:5.1f}")
    
    print(f"\n" + "=" * 80)
    print("KEY INSIGHTS:")
    print("=" * 80)
    
    # Check if any of yesterday's top performers are in today's projections
    yesterday_teams = {team for team, _, _ in yesterday_top}
    today_teams = {team for team, _, _ in today_projections}
    
    overlap = yesterday_teams.intersection(today_teams)
    
    print(f"\n1. TEAM OVERLAP:")
    if overlap:
        print(f"   Teams that performed well yesterday AND are projected well today: {', '.join(overlap)}")
        for team in overlap:
            yesterday_rank = next(i for i, (t, _, _) in enumerate(yesterday_top, 1) if t == team)
            today_rank = next(i for i, (t, _, _) in enumerate(today_projections, 1) if t == team)
            print(f"   - {team}: Yesterday #{yesterday_rank}, Today projected #{today_rank}")
    else:
        print("   No overlap between yesterday's top performers and today's top projections")
    
    print(f"\n2. PERFORMANCE GAPS:")
    yesterday_avg = sum(total for _, total, _ in yesterday_top) / len(yesterday_top)
    today_avg = sum(total for _, total, _ in today_projections) / len(today_projections)
    
    print(f"   Yesterday's top 5 average stack total: {yesterday_avg:.1f}")
    print(f"   Today's top 5 projected stack total: {today_avg:.1f}")
    print(f"   Gap: {yesterday_avg - today_avg:.1f} points")
    
    print(f"\n3. STANDOUT PERFORMERS:")
    print(f"   Best actual yesterday: NYM with 122.6 points (30.6 avg)")
    print(f"   Best projected today: LAD with 48.0 points (12.0 avg)")
    print(f"   NYM yesterday scored 2.6x more than LAD is projected today!")
    
    print(f"\n4. TEAMS TO WATCH:")
    # Teams that were good yesterday but not projected highly today
    yesterday_only = yesterday_teams - today_teams
    if yesterday_only:
        print(f"   Teams that performed well yesterday but not projected highly today:")
        for team in yesterday_only:
            yesterday_perf = next(total for t, total, _ in yesterday_top if t == team)
            print(f"   - {team}: {yesterday_perf} actual points yesterday")
    
    # Teams projected well today but didn't perform yesterday
    today_only = today_teams - yesterday_teams
    if today_only:
        print(f"   Teams projected well today that didn't dominate yesterday:")
        for team in today_only:
            today_proj = next(total for t, total, _ in today_projections if t == team)
            print(f"   - {team}: {today_proj} projected points today")
    
    print(f"\n5. STRATEGIC RECOMMENDATIONS:")
    print(f"   - ATH appears in both lists - strong consistency play")
    print(f"   - NYM, MIL, SEA, PHI dominated yesterday - check if they're undervalued today")
    print(f"   - LAD has highest projection today - premium but potentially chalky")
    print(f"   - Consider contrarian plays from yesterday's winners if ownership is low")

if __name__ == '__main__':
    compare_projections_vs_actual()
