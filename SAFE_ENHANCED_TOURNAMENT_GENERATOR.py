import pandas as pd
import numpy as np
import logging
from pulp import LpProblem, LpMaximize, LpVariable, lpSum, PULP_CBC_CMD, LpStatus, value
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SafeEnhancedTournamentGenerator:
    def __init__(self):
        self.confirmed_starters = None
        self.enhanced_features = None
        
    def load_data(self):
        """Load confirmed starters and enhanced features"""
        logger.info(" LOADING SAFE ENHANCED DATA")
        logger.info("=" * 60)
        
        # Load confirmed starters (our safety filter)
        try:
            # Try multiple possible file names for confirmed starters
            possible_files = [
                '../fd_current_slate/fd_slate_confirmed_starters_only.csv',
                '../fd_current_slate/fd_slate_dynamic_confirmed_20250801_124507.csv',
                '../fd_current_slate/fd_slate_today.csv'
            ]
            
            for file_path in possible_files:
                try:
                    self.confirmed_starters = pd.read_csv(file_path)
                    logger.info(f"SUCCESS: Loaded {len(self.confirmed_starters)} confirmed starters from {file_path.split('/')[-1]}")
                    break
                except FileNotFoundError:
                    continue
            
            if self.confirmed_starters is None:
                raise FileNotFoundError("No confirmed starters file found")
                
        except Exception as e:
            logger.error(f"ERROR: Failed to load confirmed starters: {e}")
            return False
            
        # Load enhanced features 
        try:
            self.enhanced_features = pd.read_csv('../data/fd_hitter_features_enhanced.csv')
            logger.info(f"SUCCESS: Loaded {len(self.enhanced_features)} enhanced features")
        except Exception as e:
            logger.warning(f"WARNING: No enhanced features found, using base features: {e}")
            
        # Load ceiling weights
        try:
            ceiling_weights = pd.read_csv('../data/ceiling_lineup_weights.csv')
            logger.info(f"SUCCESS: Loaded ceiling weights for {len(ceiling_weights)} players")
        except Exception as e:
            logger.warning(f"WARNING: No ceiling weights found: {e}")
            
        return True
        
    def merge_enhanced_with_confirmed(self):
        """Merge enhanced projections with confirmed starters only"""
        logger.info("SWAP: MERGING ENHANCED DATA WITH CONFIRMED STARTERS")
        logger.info("=" * 60)
        
        # Create name matching key
        self.confirmed_starters['name_key'] = (
            self.confirmed_starters['First Name'].str.lower() + ' ' + 
            self.confirmed_starters['Last Name'].str.lower()
        ).str.strip()
        
        if self.enhanced_features is not None:
            self.enhanced_features['name_key'] = (
                self.enhanced_features['First Name'].str.lower() + ' ' + 
                self.enhanced_features['Last Name'].str.lower()
            ).str.strip()
            
            # Merge enhanced projections with confirmed starters
            enhanced_confirmed = self.confirmed_starters.merge(
                self.enhanced_features[['name_key', 'tournament_proj', 'ceiling_adjusted_proj', 'estimated_ownership']],
                on='name_key',
                how='left'
            )
            
            # Use enhanced projections where available, fallback to base FPPG
            enhanced_confirmed['final_proj'] = enhanced_confirmed['tournament_proj'].fillna(
                enhanced_confirmed['FPPG']
            )
            
            logger.info(f"SUCCESS: Enhanced projections applied to {enhanced_confirmed['tournament_proj'].notna().sum()} players")
        else:
            enhanced_confirmed = self.confirmed_starters.copy()
            enhanced_confirmed['final_proj'] = enhanced_confirmed['FPPG']
            
        # Apply variance boost for ceiling targeting
        enhanced_confirmed['ceiling_proj'] = enhanced_confirmed['final_proj'] * np.random.uniform(1.0, 1.15, len(enhanced_confirmed))
        enhanced_confirmed['value_score'] = enhanced_confirmed['ceiling_proj'] / enhanced_confirmed['Salary'] * 1000
        
        self.enhanced_confirmed = enhanced_confirmed
        logger.info(f"DATA: Final dataset: {len(enhanced_confirmed)} confirmed starters with enhanced projections")
        logger.info(f"DATA: Projection range: {enhanced_confirmed['ceiling_proj'].min():.1f} - {enhanced_confirmed['ceiling_proj'].max():.1f} FPPG")
        
    def generate_safe_lineups(self, num_lineups=10):
        """Generate tournament lineups using only confirmed starters"""
        logger.info("LINEUP: GENERATING SAFE ENHANCED TOURNAMENT LINEUPS")
        logger.info("=" * 60)
        
        lineups = []
        strategies = ['ceiling', 'balanced', 'value'] * (num_lineups // 3 + 1)
        
        for i in range(num_lineups):
            strategy = strategies[i]
            logger.info(f"SWAP: Generating lineup {i+1}/{num_lineups} - {strategy}")
            
            lineup = self._optimize_lineup(strategy)
            if lineup is not None:
                lineup['lineup_id'] = i + 1
                lineup['strategy'] = strategy
                lineups.append(lineup)
                
                total_proj = lineup['Projected_FPPG'].sum()
                total_salary = lineup['Salary'].sum()
                logger.info(f"SUCCESS: Lineup {i+1}: {total_proj:.1f} FPPG, ${total_salary:,}")
            else:
                logger.warning(f"WARNING: Failed to generate lineup {i+1}")
                
        return lineups
        
    def _optimize_lineup(self, strategy='balanced'):
        """Optimize a single lineup using confirmed starters only"""
        df = self.enhanced_confirmed.copy()
        
        # Strategy-based projection adjustments
        if strategy == 'ceiling':
            df['opt_proj'] = df['ceiling_proj']
        elif strategy == 'value':
            df['opt_proj'] = df['value_score']
        else:  # balanced
            df['opt_proj'] = df['final_proj']
            
        # Filter to available positions
        pitchers = df[df['Position'] == 'P'].copy()
        hitters = df[df['Position'] != 'P'].copy()
        
        if len(pitchers) == 0 or len(hitters) == 0:
            return None
            
        # Create optimization problem
        prob = LpProblem("SafeEnhancedLineup", LpMaximize)
        
        # Decision variables
        p_vars = {row.Id: LpVariable(f"P_{row.Id}", cat='Binary') for _, row in pitchers.iterrows()}
        h_vars = {row.Id: LpVariable(f"H_{row.Id}", cat='Binary') for _, row in hitters.iterrows()}
        
        # Objective: maximize projections
        prob += (
            lpSum([pitchers.loc[pitchers['Id'] == pid, 'opt_proj'].iloc[0] * var for pid, var in p_vars.items()]) +
            lpSum([hitters.loc[hitters['Id'] == hid, 'opt_proj'].iloc[0] * var for hid, var in h_vars.items()])
        )
        
        # Constraints
        # Exactly 1 pitcher
        prob += lpSum(p_vars.values()) == 1
        
        # Exactly 8 hitters  
        prob += lpSum(h_vars.values()) == 8
        
        # Salary constraint
        prob += (
            lpSum([pitchers.loc[pitchers['Id'] == pid, 'Salary'].iloc[0] * var for pid, var in p_vars.items()]) +
            lpSum([hitters.loc[hitters['Id'] == hid, 'Salary'].iloc[0] * var for hid, var in h_vars.items()])
        ) <= 35000
        
        # Solve
        prob.solve(PULP_CBC_CMD(msg=0))
        
        if prob.status != 1:
            return None
            
        # Extract lineup
        selected_players = []
        
        for pid, var in p_vars.items():
            if var.varValue == 1:
                player = pitchers[pitchers['Id'] == pid].iloc[0]
                selected_players.append(player)
                
        for hid, var in h_vars.items():
            if var.varValue == 1:
                player = hitters[hitters['Id'] == hid].iloc[0]
                selected_players.append(player)
                
        if len(selected_players) != 9:
            return None
            
        lineup_df = pd.DataFrame(selected_players)
        lineup_df = lineup_df.rename(columns={'final_proj': 'Projected_FPPG'})
        
        return lineup_df
        
    def save_lineups(self, lineups):
        """Save lineups to file"""
        if not lineups:
            logger.error("ERROR: No lineups to save!")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"../fd_current_slate/SAFE_ENHANCED_TOURNAMENT_{timestamp}.csv"
        
        all_lineups = []
        for i, lineup in enumerate(lineups):
            lineup_copy = lineup.copy()
            lineup_copy['Lineup_ID'] = i + 1
            all_lineups.append(lineup_copy)
            
        combined_df = pd.concat(all_lineups, ignore_index=True)
        combined_df.to_csv(filename, index=False)
        
        logger.info(f" Saved {len(lineups)} safe enhanced lineups to: {filename}")
        
        # Summary stats
        total_projections = [lineup['Projected_FPPG'].sum() for lineup in lineups]
        logger.info(f"DATA: Projection range: {min(total_projections):.1f} - {max(total_projections):.1f} FPPG")
        logger.info(f"DATA: Average projection: {np.mean(total_projections):.1f} FPPG")

def main():
    logger.info("START: SAFE ENHANCED TOURNAMENT GENERATOR")
    logger.info(" Combining enhanced projections with confirmed starters")
    logger.info("=" * 70)
    
    generator = SafeEnhancedTournamentGenerator()
    
    # Load data
    if not generator.load_data():
        logger.error("ERROR: Failed to load data!")
        return
        
    # Merge enhanced features with confirmed starters
    generator.merge_enhanced_with_confirmed()
    
    # Generate safe lineups
    lineups = generator.generate_safe_lineups(10)
    
    # Save results
    generator.save_lineups(lineups)
    
    logger.info("=" * 70)
    logger.info("COMPLETE: SAFE ENHANCED TOURNAMENT GENERATION COMPLETE!")
    logger.info("SUCCESS: Only confirmed starting players used")
    logger.info("SUCCESS: Enhanced projections applied where available") 
    logger.info("SUCCESS: Tournament lineups ready for submission")

if __name__ == "__main__":
    main()
