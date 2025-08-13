#!/usr/bin/env python3
"""
CONFIRMED STARTERS OWNERSHIP PROJECTION SYSTEM
Advanced ownership modeling for confirmed players only
Much more accurate with focused player pool!
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_confirmed_projections():
    """Load confirmed players with their projections"""
    try:
        # Look for existing projection files
        projection_files = [
            '../data/base_hitter_scores.csv',
            '../data/base_pitcher_scores.csv', 
            '../fd_current_slate/fd_slate_confirmed_starters_only.csv'
        ]
        
        confirmed_df = None
        for file_path in projection_files:
            try:
                df = pd.read_csv(file_path)
                if 'Salary' in df.columns:
                    confirmed_df = df
                    logger.info(f"✅ Loaded projections from {file_path}")
                    break
            except FileNotFoundError:
                continue
        
        if confirmed_df is None:
            # Fallback to confirmed slate
            confirmed_df = pd.read_csv('../fd_current_slate/fd_slate_confirmed_starters_only.csv')
            logger.info("✅ Using confirmed slate as base for ownership projections")
        
        return confirmed_df
    
    except Exception as e:
        logger.error(f"❌ Error loading confirmed projections: {e}")
        return None

def calculate_advanced_ownership(df):
    """Calculate advanced ownership projections for confirmed starters"""
    
    logger.info("🧠 ADVANCED OWNERSHIP PROJECTION SYSTEM")
    logger.info("=" * 60)
    
    # Initialize ownership calculation
    df['base_ownership'] = 0.05  # 5% baseline
    
    # Factor 1: Salary Impact (30% weight)
    # Lower salary = higher ownership (more accessible)
    if 'Salary' in df.columns:
        salary_normalized = (df['Salary'] - df['Salary'].min()) / (df['Salary'].max() - df['Salary'].min())
        salary_impact = 0.3 * (1 - salary_normalized)  # Inverse relationship
        df['salary_impact'] = salary_impact
        logger.info(f"📊 Salary impact calculated (range: {salary_impact.min():.3f} to {salary_impact.max():.3f})")
    else:
        df['salary_impact'] = 0.15  # Default moderate impact
    
    # Factor 2: Projection Impact (40% weight)  
    # Higher projections = higher ownership
    if 'projected_fppg' in df.columns:
        proj_col = 'projected_fppg'
    elif 'base_fppg' in df.columns:
        proj_col = 'base_fppg'
    else:
        # Create rough projections based on salary
        df['estimated_fppg'] = df['Salary'] / 300  # Rough estimate
        proj_col = 'estimated_fppg'
        logger.info("⚠️ No projections found, using salary-based estimates")
    
    if proj_col in df.columns:
        proj_normalized = (df[proj_col] - df[proj_col].min()) / (df[proj_col].max() - df[proj_col].min())
        proj_impact = 0.4 * proj_normalized
        df['projection_impact'] = proj_impact
        logger.info(f"📈 Projection impact calculated (range: {proj_impact.min():.3f} to {proj_impact.max():.3f})")
    else:
        df['projection_impact'] = 0.2  # Default moderate impact
    
    # Factor 3: Position Impact (10% weight)
    position_ownership = {
        'P': 0.15,    # Pitchers vary widely
        'C': 0.08,    # Limited options
        '1B': 0.12,   # Moderate options
        '2B': 0.10,   # Moderate options  
        '3B': 0.10,   # Moderate options
        'SS': 0.12,   # Popular position
        'OF': 0.15    # Most options
    }
    
    df['position_impact'] = df['Position'].map(position_ownership).fillna(0.12)
    logger.info("🎯 Position impact applied")
    
    # Factor 4: Team/Game Impact (15% weight)
    # Players in fewer games = higher ownership (concentrated)
    game_counts = df['Game'].value_counts()
    df['game_impact'] = df['Game'].map(lambda x: 0.15 * (1 / game_counts[x]) if x in game_counts else 0.075)
    logger.info(f"🏟️ Game impact calculated for {len(game_counts)} games")
    
    # Factor 5: Star Player Bonus (5% weight)
    # High salary players get ownership bump (name recognition)
    star_threshold = df['Salary'].quantile(0.8)  # Top 20% by salary
    df['star_bonus'] = np.where(df['Salary'] >= star_threshold, 0.05, 0)
    logger.info(f"⭐ Star bonus applied (threshold: ${star_threshold:,.0f})")
    
    # Combine all factors
    df['ownership_projection'] = (
        df['base_ownership'] + 
        df['salary_impact'] + 
        df['projection_impact'] + 
        df['position_impact'] + 
        df['game_impact'] + 
        df['star_bonus']
    )
    
    # Apply final adjustments and constraints
    df['ownership_projection'] = np.clip(df['ownership_projection'], 0.02, 0.95)  # 2-95% range
    
    return df

def categorize_ownership_tiers(df):
    """Categorize players into ownership tiers"""
    
    # Define ownership tiers
    df['ownership_tier'] = 'Medium'
    df.loc[df['ownership_projection'] >= 0.25, 'ownership_tier'] = 'Chalk'
    df.loc[df['ownership_projection'] >= 0.40, 'ownership_tier'] = 'Super Chalk'
    df.loc[df['ownership_projection'] <= 0.10, 'ownership_tier'] = 'Contrarian'
    df.loc[df['ownership_projection'] <= 0.05, 'ownership_tier'] = 'Deep Contrarian'
    
    # Create ownership buckets for analysis
    tier_counts = df['ownership_tier'].value_counts()
    logger.info("🎭 OWNERSHIP TIERS:")
    for tier, count in tier_counts.items():
        avg_own = df[df['ownership_tier'] == tier]['ownership_projection'].mean()
        logger.info(f"   {tier}: {count} players (avg {avg_own:.1%} ownership)")
    
    return df

def create_ownership_strategy_guide(df):
    """Create strategic recommendations based on ownership"""
    
    chalk_players = df[df['ownership_tier'].isin(['Chalk', 'Super Chalk'])]
    contrarian_players = df[df['ownership_tier'].isin(['Contrarian', 'Deep Contrarian'])]
    
    strategy = {
        'chalk_plays': len(chalk_players),
        'contrarian_plays': len(contrarian_players),
        'top_chalk': chalk_players.nlargest(3, 'ownership_projection')[['Nickname', 'Position', 'Salary', 'ownership_projection']].to_dict('records'),
        'top_contrarian': contrarian_players.nsmallest(3, 'ownership_projection')[['Nickname', 'Position', 'Salary', 'ownership_projection']].to_dict('records'),
        'pivot_opportunities': []
    }
    
    # Find pivot opportunities (good players with low ownership)
    high_proj_low_own = df[
        (df['ownership_projection'] < 0.15) & 
        (df['Salary'] > df['Salary'].median())
    ]
    
    for _, player in high_proj_low_own.head(3).iterrows():
        strategy['pivot_opportunities'].append({
            'name': player['Nickname'],
            'position': player['Position'],
            'salary': player['Salary'],
            'ownership': player['ownership_projection'],
            'reason': 'High salary but low projected ownership'
        })
    
    return strategy

def save_ownership_projections(df):
    """Save ownership projections for lineup builders"""
    
    # Save main file
    main_file = '../data/confirmed_ownership_projections.csv'
    df.to_csv(main_file, index=False)
    
    # Save timestamped version
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    timestamped_file = f'../data/confirmed_ownership_projections_{timestamp}.csv'
    df.to_csv(timestamped_file, index=False)
    
    logger.info(f"💾 Saved ownership projections:")
    logger.info(f"   📁 Main: {main_file}")
    logger.info(f"   📁 Timestamped: {timestamped_file}")
    
    return main_file

def print_ownership_summary(df, strategy):
    """Print detailed ownership analysis"""
    
    logger.info("=" * 60)
    logger.info("🎯 CONFIRMED STARTERS OWNERSHIP ANALYSIS")
    logger.info("=" * 60)
    
    # Overall stats
    avg_ownership = df['ownership_projection'].mean()
    logger.info(f"📊 Average ownership: {avg_ownership:.1%}")
    logger.info(f"📊 Ownership range: {df['ownership_projection'].min():.1%} - {df['ownership_projection'].max():.1%}")
    
    # Top chalk
    logger.info(f"\n🔥 TOP CHALK PLAYS ({strategy['chalk_plays']} total):")
    for player in strategy['top_chalk']:
        logger.info(f"   {player['Nickname']} ({player['Position']}) - ${player['Salary']:,} - {player['ownership_projection']:.1%}")
    
    # Contrarian opportunities  
    logger.info(f"\n🎭 CONTRARIAN OPPORTUNITIES ({strategy['contrarian_plays']} total):")
    for player in strategy['top_contrarian']:
        logger.info(f"   {player['Nickname']} ({player['Position']}) - ${player['Salary']:,} - {player['ownership_projection']:.1%}")
    
    # Pivot plays
    if strategy['pivot_opportunities']:
        logger.info(f"\n🔄 PIVOT OPPORTUNITIES:")
        for pivot in strategy['pivot_opportunities']:
            logger.info(f"   {pivot['name']} ({pivot['position']}) - ${pivot['salary']:,} - {pivot['ownership']:.1%}")
            logger.info(f"     💡 {pivot['reason']}")

def main():
    """Main ownership projection function"""
    logger.info("👥 CONFIRMED STARTERS OWNERSHIP PROJECTION")
    logger.info("🎯 Advanced modeling for 43 confirmed players only")
    logger.info("=" * 60)
    
    # Load confirmed projections
    df = load_confirmed_projections()
    if df is None:
        return
    
    # Calculate advanced ownership
    df = calculate_advanced_ownership(df)
    
    # Categorize into tiers
    df = categorize_ownership_tiers(df)
    
    # Create strategy guide
    strategy = create_ownership_strategy_guide(df)
    
    # Save results
    main_file = save_ownership_projections(df)
    
    # Print summary
    print_ownership_summary(df, strategy)
    
    logger.info("=" * 60)
    logger.info("🎉 OWNERSHIP PROJECTION COMPLETE!")
    logger.info(f"✅ {len(df)} confirmed players analyzed")
    logger.info(f"📈 Advanced 5-factor ownership model applied")
    logger.info(f"🎭 Strategic recommendations generated")
    logger.info(f"💾 Ready for tournament lineup construction")

if __name__ == "__main__":
    main()
