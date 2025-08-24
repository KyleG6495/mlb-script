#!/usr/bin/env python3
"""
SIMPLIFIED_ELITE_OPTIMIZER - Working elite tournament optimizer
Focuses on the core elite features: ownership, leverage, stacking
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging
from ELITE_DFS_OPTIMIZER import EliteDFSOptimizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimplifiedEliteOptimizer:
    def __init__(self):
        self.optimizer = EliteDFSOptimizer()
        self.salary_cap = 60000
        
    def build_elite_lineups(self, df, num_lineups=15):
        """Build elite tournament lineups with working logic"""
        
        logger.info("TARGET: SIMPLIFIED ELITE OPTIMIZER")
        logger.info("=" * 50)
        
        # Enhance with elite features
        df_elite = self.optimizer.enhance_with_elite_features(df)
        
        # Get stack analysis
        stack_analysis = self.optimizer.identify_elite_stacks(df_elite)
        
        lineups = []
        
        # Build multiple lineup strategies
        for i in range(num_lineups):
            if i < 8:
                # GPP Strategy: Leverage + stacking (60% of lineups)
                lineup = self.build_leverage_lineup(df_elite, stack_analysis, i)
            elif i < 12:
                # Contrarian Strategy: Low ownership bombs (25% of lineups)  
                lineup = self.build_contrarian_lineup(df_elite, i)
            else:
                # Balanced Strategy: Mix of value and upside (15% of lineups)
                lineup = self.build_balanced_lineup(df_elite, i)
            
            if lineup and self.validate_lineup(lineup):
                lineups.append(lineup)
        
        logger.info(f"SUCCESS: Built {len(lineups)} elite tournament lineups")
        
        return lineups, df_elite
    
    def build_leverage_lineup(self, df, stack_analysis, lineup_num):
        """Build lineup focused on leverage and team stacking"""
        
        lineup = []
        budget = self.salary_cap
        
        # Choose stack team (rotate through top 5)
        top_teams = stack_analysis.head(5)['team'].tolist()
        stack_team = top_teams[lineup_num % len(top_teams)]
        
        # 1. SELECT STACK (3-4 hitters from same team)
        team_hitters = df[(df['Team'] == stack_team) & (df['Position'] != 'P')].copy()
        team_hitters = team_hitters.sort_values('leverage_score', ascending=False)
        
        stack_count = min(4, len(team_hitters))
        stack_budget = min(budget * 0.55, 30000)  # Max 55% budget on stack
        
        stack_players = []
        for _, player in team_hitters.head(8).iterrows():  # Consider top 8
            if len(stack_players) < stack_count and player['Salary'] <= (stack_budget / (stack_count - len(stack_players))):
                stack_players.append(player.to_dict())
                stack_budget -= player['Salary']
        
        lineup.extend(stack_players)
        budget -= sum(p['Salary'] for p in stack_players)
        
        logger.info(f"Lineup {lineup_num+1}: {len(stack_players)} {stack_team} stack players, ${budget} remaining")
        
        # 2. SELECT PITCHERS (High leverage or contrarian)
        pitchers = df[df['Position'] == 'P'].copy()
        
        # Avoid pitchers facing our stack team if possible
        opposing_pitchers = pitchers[pitchers['Opponent'] == stack_team] if 'Opponent' in df.columns else pd.DataFrame()
        
        pitcher_budget = min(budget * 0.35, 20000)  # ~35% remaining budget
        
        selected_pitchers = []
        
        # Select top 2 pitchers by leverage within budget
        for _, pitcher in pitchers.sort_values('leverage_score', ascending=False).iterrows():
            if (len(selected_pitchers) < 2 and 
                pitcher['Salary'] <= pitcher_budget and
                pitcher['Id'] not in [p['Id'] for p in lineup]):
                
                # Avoid opposing pitcher if we have budget for alternatives
                if pitcher['Id'] not in opposing_pitchers['Id'].values or len(selected_pitchers) == 1:
                    selected_pitchers.append(pitcher.to_dict())
                    pitcher_budget -= pitcher['Salary']
        
        lineup.extend(selected_pitchers)
        budget -= sum(p['Salary'] for p in selected_pitchers)
        
        # 3. FILL REMAINING POSITIONS WITH BEST VALUE/LEVERAGE
        
        # Need 9 total players
        remaining_slots = 9 - len(lineup)
        
        # Get remaining players not in lineup
        used_ids = [p['Id'] for p in lineup]
        available = df[(~df['Id'].isin(used_ids)) & (df['Position'] != 'P')].copy()
        
        # Score remaining players
        available['fill_score'] = (
            available['leverage_score'] * 0.4 +
            available['ceiling_proj'] * 0.3 + 
            (available['FPPG'] / available['Salary'] * 10000) * 0.3  # Value component
        )
        
        # Fill remaining spots with best available
        for _ in range(remaining_slots):
            affordable = available[available['Salary'] <= budget]
            
            if len(affordable) > 0:
                best = affordable.sort_values('fill_score', ascending=False).iloc[0]
                lineup.append(best.to_dict())
                budget -= best['Salary']
                
                # Remove selected player
                available = available[available['Id'] != best['Id']]
            else:
                break
        
        return lineup if len(lineup) == 9 else None
    
    def build_contrarian_lineup(self, df, lineup_num):
        """Build contrarian lineup with low ownership bombs"""
        
        lineup = []
        budget = self.salary_cap
        
        # Target players with ownership < 5% and high ceiling
        contrarian_candidates = df[(df['ownership_proj'] <= 5) & (df['ceiling_proj'] >= 15)].copy()
        
        # 1. SELECT CONTRARIAN PITCHERS
        contrarian_pitchers = contrarian_candidates[contrarian_candidates['Position'] == 'P']
        
        if len(contrarian_pitchers) >= 2:
            selected_pitchers = contrarian_pitchers.nlargest(2, 'ceiling_proj')
            for _, pitcher in selected_pitchers.iterrows():
                if pitcher['Salary'] <= budget:
                    lineup.append(pitcher.to_dict())
                    budget -= pitcher['Salary']
        
        # 2. SELECT CONTRARIAN HITTERS
        contrarian_hitters = contrarian_candidates[contrarian_candidates['Position'] != 'P']
        
        remaining_slots = 9 - len(lineup)
        
        # Fill with best contrarian plays
        for _ in range(remaining_slots):
            affordable = contrarian_hitters[contrarian_hitters['Salary'] <= budget]
            
            if len(affordable) > 0:
                # Select by ceiling potential
                best = affordable.nlargest(1, 'ceiling_proj').iloc[0]
                lineup.append(best.to_dict())
                budget -= best['Salary']
                
                # Remove selected
                contrarian_hitters = contrarian_hitters[contrarian_hitters['Id'] != best['Id']]
            else:
                # Fill with any available player
                available = df[(~df['Id'].isin([p['Id'] for p in lineup])) & 
                              (df['Position'] != 'P') & 
                              (df['Salary'] <= budget)]
                
                if len(available) > 0:
                    filler = available.nsmallest(1, 'Salary').iloc[0]
                    lineup.append(filler.to_dict())
                    budget -= filler['Salary']
                else:
                    break
        
        return lineup if len(lineup) == 9 else None
    
    def build_balanced_lineup(self, df, lineup_num):
        """Build balanced lineup mixing value and upside"""
        
        lineup = []
        budget = self.salary_cap
        
        # Balanced scoring: mix of projection, value, and ceiling
        df_balanced = df.copy()
        df_balanced['balanced_score'] = (
            df_balanced['FPPG'] * 0.4 +                    # Base projection (40%)
            (df_balanced['FPPG'] / df_balanced['Salary'] * 10000) * 0.3 +  # Value (30%)
            df_balanced['ceiling_proj'] * 0.2 +             # Ceiling (20%)
            (15 - df_balanced['ownership_proj']) * 0.1      # Contrarian bonus (10%)
        )
        
        # Build lineup by best balanced score
        positions_needed = ['P', 'P'] + ['Hitter'] * 7  # 2 pitchers, 7 hitters
        
        for pos in positions_needed:
            if pos == 'P':
                available = df_balanced[(df_balanced['Position'] == 'P') & 
                                       (df_balanced['Salary'] <= budget)]
            else:
                available = df_balanced[(df_balanced['Position'] != 'P') & 
                                       (df_balanced['Salary'] <= budget)]
            
            # Remove already selected
            used_ids = [p['Id'] for p in lineup]
            available = available[~available['Id'].isin(used_ids)]
            
            if len(available) > 0:
                best = available.sort_values('balanced_score', ascending=False).iloc[0]
                lineup.append(best.to_dict())
                budget -= best['Salary']
        
        return lineup if len(lineup) == 9 else None
    
    def validate_lineup(self, lineup):
        """Basic lineup validation"""
        
        if not lineup or len(lineup) != 9:
            return False
        
        total_salary = sum(p['Salary'] for p in lineup)
        if total_salary > self.salary_cap:
            return False
        
        # Check pitcher count
        pitcher_count = sum(1 for p in lineup if p['Position'] == 'P')
        if pitcher_count != 2:
            return False
        
        return True
    
    def export_for_fanduel(self, lineups, df_elite, filename=None):
        """Export lineups in FanDuel CSV format"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../fd_current_slate/SIMPLIFIED_ELITE_LINEUPS_{timestamp}.csv"
        
        export_data = []
        
        for i, lineup in enumerate(lineups):
            # Calculate lineup metrics
            total_salary = sum(p['Salary'] for p in lineup)
            total_proj = sum(p['FPPG'] for p in lineup)
            total_ceiling = sum(p['ceiling_proj'] for p in lineup)
            avg_ownership = sum(p['ownership_proj'] for p in lineup) / len(lineup)
            
            # Create player list for easy viewing
            players = []
            for p in lineup:
                players.append(f"{p['First Name']} {p['Last Name']} ({p['Team']}) ${p['Salary']}")
            
            export_data.append({
                'Lineup': i + 1,
                'Total_Salary': total_salary,
                'Projected_Points': round(total_proj, 1),
                'Ceiling_Projection': round(total_ceiling, 1),
                'Avg_Ownership': round(avg_ownership, 1),
                'Tournament_Score': round(total_ceiling - (avg_ownership * 1.5), 1),
                'Players': ' | '.join(players[:3]) + ' | ...',  # Show first 3 players
                'P1': f"{lineup[0]['First Name']} {lineup[0]['Last Name']}",
                'P2': f"{lineup[1]['First Name']} {lineup[1]['Last Name']}",
                'Stack_Team': self.identify_primary_stack(lineup)
            })
        
        df_export = pd.DataFrame(export_data)
        df_export.to_csv(filename, index=False)
        
        logger.info(f"SUCCESS: Exported {len(lineups)} lineups to {filename}")
        
        # Show summary stats
        if len(lineups) > 0:
            avg_proj = df_export['Projected_Points'].mean()
            avg_ceiling = df_export['Ceiling_Projection'].mean()
            avg_ownership = df_export['Avg_Ownership'].mean()
            avg_tournament = df_export['Tournament_Score'].mean()
            
            logger.info(f"DATA: LINEUP SUMMARY:")
            logger.info(f"  Average Projection: {avg_proj:.1f}")
            logger.info(f"  Average Ceiling: {avg_ceiling:.1f}")
            logger.info(f"  Average Ownership: {avg_ownership:.1f}%")
            logger.info(f"  Average Tournament Score: {avg_tournament:.1f}")
        
        return filename
    
    def identify_primary_stack(self, lineup):
        """Identify the primary stacking team in lineup"""
        
        teams = {}
        for player in lineup:
            if player['Position'] != 'P':  # Only count hitters
                team = player['Team']
                teams[team] = teams.get(team, 0) + 1
        
        if teams:
            primary_team = max(teams, key=teams.get)
            return f"{primary_team} ({teams[primary_team]})" if teams[primary_team] > 1 else "No stack"
        
        return "No stack"

def test_simplified_elite():
    """Test the simplified elite optimizer"""
    
    try:
        # Load test data
        df = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        logger.info(f"SUCCESS: Loaded test data: {len(df)} players")
        
        # Initialize optimizer
        optimizer = SimplifiedEliteOptimizer()
        
        # Build lineups
        lineups, df_elite = optimizer.build_elite_lineups(df, num_lineups=12)
        
        # Export results
        export_file = optimizer.export_for_fanduel(lineups, df_elite)
        
        # Show sample lineup
        if lineups:
            logger.info(f"\nLINEUP: SAMPLE ELITE LINEUP:")
            sample = lineups[0]
            for i, player in enumerate(sample):
                logger.info(f"  {i+1}. {player['First Name']} {player['Last Name']} ({player['Team']}) "
                           f"{player['Position']} - ${player['Salary']} "
                           f"(Proj: {player['FPPG']:.1f}, Own: {player['ownership_proj']:.1f}%)")
        
        logger.info(f"\nSUCCESS: SIMPLIFIED ELITE OPTIMIZER TEST COMPLETE")
        logger.info("Ready for tournament play!")
        
        return lineups, df_elite
        
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simplified_elite()
