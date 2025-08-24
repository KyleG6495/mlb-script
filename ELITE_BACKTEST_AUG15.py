#!/usr/bin/env python3
"""
ELITE TOURNAMENT BACKTEST - AUGUST 15TH VALIDATION
Test elite Waldrep-type strategy against actual results from yesterday
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EliteBacktestValidator:
    def __init__(self):
        self.waldrep_criteria = {
            'ownership_range': (5, 15),
            'projection_min': 35,
            'position': 'P'
        }
    
    def load_august_15_data(self):
        """Load August 15th projections and actual results"""
        logger.info("📊 LOADING AUGUST 15TH DATA FOR ELITE BACKTEST")
        
        try:
            # Load projections from August 15th
            proj_file = "../data/enhanced_projections_20250815_133709.csv"
            ownership_file = "../data/advanced_ownership_projections_20250815_175656.csv"
            results_file = "../data/actual_results_20250815.csv"
            
            projections_df = pd.read_csv(proj_file)
            ownership_df = pd.read_csv(ownership_file)
            actual_results_df = pd.read_csv(results_file)
            
            logger.info(f"✅ Loaded {len(projections_df)} projected players")
            logger.info(f"✅ Loaded {len(ownership_df)} ownership projections")  
            logger.info(f"✅ Loaded {len(actual_results_df)} actual results")
            
            return projections_df, ownership_df, actual_results_df
            
        except Exception as e:
            logger.error(f"Error loading August 15th data: {e}")
            return None, None, None
    
    def identify_waldrep_candidates_aug15(self, projections_df, ownership_df):
        """Find Waldrep-type candidates from August 15th"""
        logger.info("🎯 IDENTIFYING AUGUST 15TH WALDREP CANDIDATES")
        
        try:
            # Merge projection and ownership data
            enhanced_df = projections_df.copy()
            
            # Add ownership data
            for idx, player in enhanced_df.iterrows():
                player_name = player.get('Nickname', '').split()[-1] if player.get('Nickname') else ''
                ownership_match = ownership_df[
                    ownership_df['player_name'].str.contains(player_name, case=False, na=False)
                ]
                
                if not ownership_match.empty:
                    ownership = ownership_match['ownership'].iloc[0]
                    enhanced_df.at[idx, 'ownership'] = ownership * 100 if ownership < 1 else ownership
                else:
                    enhanced_df.at[idx, 'ownership'] = 15.0  # Default high
            
            # Filter for Waldrep-type opportunities
            pitchers = enhanced_df[enhanced_df['Position'] == 'P'].copy()
            
            waldrep_candidates = pitchers[
                (pitchers['ownership'] >= self.waldrep_criteria['ownership_range'][0]) &
                (pitchers['ownership'] <= self.waldrep_criteria['ownership_range'][1]) &
                (pitchers['enhanced_fppg'] >= self.waldrep_criteria['projection_min'])
            ]
            
            if not waldrep_candidates.empty:
                # Score candidates
                waldrep_candidates.loc[:, 'waldrep_score'] = (
                    waldrep_candidates['enhanced_fppg'] * 2 +
                    (15 - waldrep_candidates['ownership']) * 3
                )
                
                waldrep_candidates = waldrep_candidates.nlargest(5, 'waldrep_score')
                
                logger.info(f"🔥 FOUND {len(waldrep_candidates)} AUGUST 15TH WALDREP CANDIDATES:")
                for _, candidate in waldrep_candidates.iterrows():
                    logger.info(f"  {candidate['Nickname']:20} | {candidate['enhanced_fppg']:.1f} proj | {candidate['ownership']:.1f}% own | Score: {candidate['waldrep_score']:.1f}")
            
            return waldrep_candidates
            
        except Exception as e:
            logger.error(f"Error identifying Waldrep candidates: {e}")
            return pd.DataFrame()
    
    def validate_against_actual_results(self, waldrep_candidates, actual_results_df):
        """Compare Waldrep picks to actual performance"""
        logger.info("🏆 VALIDATING WALDREP STRATEGY AGAINST ACTUAL RESULTS")
        
        validation_results = []
        
        try:
            for _, candidate in waldrep_candidates.iterrows():
                player_name = candidate['Nickname']
                projected_points = candidate['enhanced_fppg']
                ownership = candidate['ownership']
                waldrep_score = candidate['waldrep_score']
                
                # Find actual performance
                actual_match = actual_results_df[
                    actual_results_df['name'].str.contains(player_name.split()[-1], case=False, na=False)
                ]
                
                if not actual_match.empty:
                    actual_points = actual_match['fanduel_points'].iloc[0]
                    accuracy = ((actual_points / projected_points) * 100) if projected_points > 0 else 0
                    
                    validation_results.append({
                        'Player': player_name,
                        'Projected': projected_points,
                        'Actual': actual_points,
                        'Ownership': ownership,
                        'Waldrep_Score': waldrep_score,
                        'Accuracy': accuracy,
                        'Difference': actual_points - projected_points,
                        'Elite_Success': actual_points >= 40  # Elite threshold
                    })
                    
                    logger.info(f"  {player_name:20} | Proj: {projected_points:.1f} | Actual: {actual_points:.1f} | Own: {ownership:.1f}% | {'✅' if actual_points >= 40 else '❌'}")
                else:
                    logger.info(f"  {player_name:20} | No actual results found")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Error validating results: {e}")
            return []
    
    def analyze_elite_performance(self, validation_results):
        """Analyze how the elite strategy performed"""
        logger.info("📈 ELITE STRATEGY PERFORMANCE ANALYSIS")
        
        if not validation_results:
            logger.warning("No validation results to analyze")
            return
        
        try:
            df = pd.DataFrame(validation_results)
            
            # Performance metrics
            avg_actual = df['Actual'].mean()
            avg_projected = df['Projected'].mean()
            avg_ownership = df['Ownership'].mean()
            elite_success_rate = (df['Elite_Success'].sum() / len(df)) * 100
            best_performer = df.loc[df['Actual'].idxmax()]
            
            logger.info(f"🎯 ELITE WALDREP STRATEGY RESULTS (August 15th):")
            logger.info(f"   Average Actual Score: {avg_actual:.1f} points")
            logger.info(f"   Average Projection: {avg_projected:.1f} points")
            logger.info(f"   Average Ownership: {avg_ownership:.1f}%")
            logger.info(f"   Elite Success Rate (40+ pts): {elite_success_rate:.1f}%")
            logger.info(f"   Best Performer: {best_performer['Player']} ({best_performer['Actual']:.1f} pts)")
            
            # Compare to original Waldrep success (49 points, 8.2% owned)
            waldrep_equivalent = df[df['Actual'] >= 49]
            if not waldrep_equivalent.empty:
                logger.info(f"🔥 WALDREP-LEVEL PERFORMERS (49+ points):")
                for _, player in waldrep_equivalent.iterrows():
                    logger.info(f"   {player['Player']:20} | {player['Actual']:.1f} pts | {player['Ownership']:.1f}% owned")
            
            # Strategy validation
            if avg_actual >= 40:
                logger.info("✅ ELITE STRATEGY VALIDATED: Average 40+ points achieved")
            elif avg_actual >= 35:
                logger.info("⚡ STRONG PERFORMANCE: Average 35+ points achieved")
            else:
                logger.info("⚠️  STRATEGY NEEDS REFINEMENT: Below 35 point average")
            
            # Ownership edge analysis
            if avg_ownership <= 10:
                logger.info("✅ OWNERSHIP EDGE CONFIRMED: Sub-10% average ownership")
            elif avg_ownership <= 15:
                logger.info("⚡ GOOD OWNERSHIP EDGE: Sub-15% average ownership")
            else:
                logger.info("⚠️  OWNERSHIP EDGE WEAK: Above 15% average ownership")
            
            return df
            
        except Exception as e:
            logger.error(f"Error analyzing performance: {e}")
            return None

def main():
    logger.info("🏆 ELITE TOURNAMENT BACKTEST - AUGUST 15TH VALIDATION")
    logger.info("=" * 60)
    logger.info("🎯 Testing Waldrep-type strategy against actual results")
    logger.info("⚡ Validating 104-point tournament success patterns")
    logger.info("=" * 60)
    
    try:
        validator = EliteBacktestValidator()
        
        # Load August 15th data
        projections_df, ownership_df, actual_results_df = validator.load_august_15_data()
        
        if projections_df is not None and ownership_df is not None and actual_results_df is not None:
            # Identify Waldrep candidates from August 15th
            waldrep_candidates = validator.identify_waldrep_candidates_aug15(projections_df, ownership_df)
            
            if not waldrep_candidates.empty:
                # Validate against actual results
                validation_results = validator.validate_against_actual_results(waldrep_candidates, actual_results_df)
                
                if validation_results:
                    # Analyze performance
                    results_df = validator.analyze_elite_performance(validation_results)
                    
                    if results_df is not None:
                        # Save backtest results
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        output_file = f"../data/elite_backtest_aug15_{timestamp}.csv"
                        results_df.to_csv(output_file, index=False)
                        logger.info(f"💾 Backtest results saved: {output_file}")
                    
                    logger.info(f"\n🚀 ELITE BACKTEST COMPLETE!")
                    logger.info(f"✅ Waldrep strategy tested against real August 15th data")
                    logger.info(f"🎯 Strategy validation {'SUCCESSFUL' if results_df['Actual'].mean() >= 35 else 'NEEDS REFINEMENT'}")
                else:
                    logger.warning("No validation results generated")
            else:
                logger.warning("No Waldrep candidates found for August 15th")
        else:
            logger.error("Could not load required data files")
    
    except Exception as e:
        logger.error(f"Error in elite backtest: {e}")

if __name__ == "__main__":
    main()
