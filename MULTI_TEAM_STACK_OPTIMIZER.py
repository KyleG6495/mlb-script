#!/usr/bin/env python3
"""
MULTI-TEAM STACK OPTIMIZER
Advanced stacking strategy that builds multiple mini-stacks like tournament winners
"""

import pandas as pd
import numpy as np
import itertools
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MultiTeamStackOptimizer:
    """
    Tournament-winning stacking strategy:
    - Multiple 2-3 player mini-stacks instead of single 4-5 player stacks
    - Diversification across multiple games/teams
    - Correlation leverage with lower ownership
    """
    
    def __init__(self):
        self.data_dir = "../data"
        self.slate_dir = "../fd_current_slate"
        
        # Multi-stack configurations (what tournament winners use)
        self.stack_configurations = {
            'dual_mini': {
                'description': '2-3 from Team A + 2-3 from Team B',
                'pattern': [(3, 3), (3, 2), (2, 3), (2, 2)],
                'risk_level': 'medium',
                'upside': 'high'
            },
            'triple_mini': {
                'description': '2 from Team A + 2 from Team B + 2 from Team C',
                'pattern': [(2, 2, 2)],
                'risk_level': 'low',
                'upside': 'medium-high'
            },
            'primary_secondary': {
                'description': '4 from Team A + 2 from Team B',
                'pattern': [(4, 2)],
                'risk_level': 'medium-high',
                'upside': 'very high'
            },
            'balanced_spread': {
                'description': '2 from each of 3 teams + 1 from 4th team',
                'pattern': [(2, 2, 2, 1)],
                'risk_level': 'very low',
                'upside': 'medium'
            }
        }
    
    def load_slate_data(self):
        """Load FD slate and projections"""
        import os
        try:
            # Load FD slate
            slate_file = f"{self.slate_dir}/fd_slate_today_clean.csv"
            if not os.path.exists(slate_file):
                slate_file = f"{self.slate_dir}/fd_slate_today.csv"
            
            self.slate_df = pd.read_csv(slate_file)
            print(f"✅ Loaded {len(self.slate_df)} players from FD slate")
            
            # Load ownership projections
            ownership_files = [f for f in os.listdir(self.data_dir) if f.startswith("advanced_ownership_projections_")]
            if ownership_files:
                ownership_files.sort(reverse=True)
                ownership_file = f"{self.data_dir}/{ownership_files[0]}"
                self.ownership_df = pd.read_csv(ownership_file)
                print(f"✅ Loaded ownership projections: {ownership_files[0]}")
            else:
                self.ownership_df = None
                
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            return False
        
        return True
    
    def merge_player_data(self):
        """Merge slate with projections and ownership"""
        try:
            # Start with slate data
            self.players_df = self.slate_df.copy()
            
            # Add ownership if available
            if self.ownership_df is not None:
                ownership_lookup = {}
                for _, row in self.ownership_df.iterrows():
                    player_name = row['player_name']
                    ownership_lookup[player_name] = {
                        'ownership': row['ownership'] * 100 if row['ownership'] < 1 else row['ownership'],
                        'leverage_score': row.get('leverage_score', 1.0)
                    }
                
                # Merge ownership data
                self.players_df['ownership_pct'] = 0.0
                self.players_df['leverage_score'] = 1.0
                
                for idx, row in self.players_df.iterrows():
                    nickname = row.get('Nickname', '')
                    if nickname in ownership_lookup:
                        self.players_df.at[idx, 'ownership_pct'] = ownership_lookup[nickname]['ownership']
                        self.players_df.at[idx, 'leverage_score'] = ownership_lookup[nickname]['leverage_score']
            
            # Calculate value score
            self.players_df['value_score'] = self.players_df['FPPG'] / (self.players_df['Salary'] / 1000)
            
            print(f"✅ Merged data for {len(self.players_df)} players")
            return True
            
        except Exception as e:
            print(f"❌ Error merging data: {e}")
            return False
    
    def identify_mini_stack_opportunities(self):
        """Find teams with good mini-stack potential (2-3 players)"""
        team_analysis = {}
        
        # Analyze each team for mini-stack potential
        for team in self.players_df['Team'].unique():
            team_players = self.players_df[self.players_df['Team'] == team].copy()
            
            if len(team_players) < 2:  # Need at least 2 players for mini-stack
                continue
            
            # Sort by value score
            team_players = team_players.sort_values('value_score', ascending=False)
            
            # Calculate mini-stack metrics
            top_2_proj = team_players.head(2)['FPPG'].sum()
            top_3_proj = team_players.head(3)['FPPG'].sum() if len(team_players) >= 3 else 0
            
            top_2_salary = team_players.head(2)['Salary'].sum()
            top_3_salary = team_players.head(3)['Salary'].sum() if len(team_players) >= 3 else 0
            
            top_2_ownership = team_players.head(2)['ownership_pct'].mean()
            top_3_ownership = team_players.head(3)['ownership_pct'].mean() if len(team_players) >= 3 else 0
            
            # Stack potential score (emphasis on value + low ownership)
            mini_2_score = (top_2_proj / (top_2_salary / 1000)) * (1 + (25 - top_2_ownership) / 25)
            mini_3_score = (top_3_proj / (top_3_salary / 1000)) * (1 + (25 - top_3_ownership) / 25) if top_3_proj > 0 else 0
            
            team_analysis[team] = {
                'mini_2': {
                    'players': team_players.head(2),
                    'projection': top_2_proj,
                    'salary': top_2_salary,
                    'ownership': top_2_ownership,
                    'score': mini_2_score
                },
                'mini_3': {
                    'players': team_players.head(3) if len(team_players) >= 3 else None,
                    'projection': top_3_proj,
                    'salary': top_3_salary,
                    'ownership': top_3_ownership,
                    'score': mini_3_score
                }
            }
        
        return team_analysis
    
    def build_multi_team_stacks(self, team_analysis):
        """Build tournament-winning multi-team stack combinations"""
        stack_combinations = []
        
        # Get top teams for mini-stacking (sorted by mini-stack score)
        teams_by_mini2 = sorted(team_analysis.items(), key=lambda x: x[1]['mini_2']['score'], reverse=True)
        teams_by_mini3 = sorted(team_analysis.items(), key=lambda x: x[1]['mini_3']['score'], reverse=True)
        
        print("\n🎯 MULTI-TEAM STACK ANALYSIS")
        print("=" * 50)
        
        # Configuration 1: Dual Mini-Stacks (3+3, 3+2, 2+3, 2+2)
        print("\n💎 DUAL MINI-STACKS (Tournament Winner Strategy)")
        dual_stacks = self._build_dual_mini_stacks(teams_by_mini2, teams_by_mini3, team_analysis)
        stack_combinations.extend(dual_stacks)
        
        # Configuration 2: Triple Mini-Stacks (2+2+2)  
        print("\n🔗 TRIPLE MINI-STACKS (Diversification Strategy)")
        triple_stacks = self._build_triple_mini_stacks(teams_by_mini2, team_analysis)
        stack_combinations.extend(triple_stacks)
        
        # Configuration 3: Primary + Secondary (4+2)
        print("\n⚡ PRIMARY + SECONDARY STACKS (Correlation Focus)")
        primary_secondary = self._build_primary_secondary_stacks(teams_by_mini3, teams_by_mini2, team_analysis)
        stack_combinations.extend(primary_secondary)
        
        return stack_combinations
    
    def _build_dual_mini_stacks(self, teams_by_mini2, teams_by_mini3, team_analysis):
        """Build dual mini-stacks like NYM(3) + CHC(3)"""
        dual_stacks = []
        
        # Try top combinations
        for i, (team1, _) in enumerate(teams_by_mini3[:8]):  # Top 8 teams
            for j, (team2, _) in enumerate(teams_by_mini3[:8]):
                if i >= j:  # Avoid duplicates
                    continue
                
                # Build different dual configurations
                configurations = [
                    ('mini_3', 'mini_3'),  # 3+3
                    ('mini_3', 'mini_2'),  # 3+2  
                    ('mini_2', 'mini_3'),  # 2+3
                    ('mini_2', 'mini_2')   # 2+2
                ]
                
                for config1, config2 in configurations:
                    if (team_analysis[team1][config1]['players'] is None or 
                        team_analysis[team2][config2]['players'] is None):
                        continue
                    
                    team1_players = team_analysis[team1][config1]['players']
                    team2_players = team_analysis[team2][config2]['players']
                    
                    total_proj = (team_analysis[team1][config1]['projection'] + 
                                 team_analysis[team2][config2]['projection'])
                    total_salary = (team_analysis[team1][config1]['salary'] + 
                                   team_analysis[team2][config2]['salary'])
                    avg_ownership = (team_analysis[team1][config1]['ownership'] + 
                                    team_analysis[team2][config2]['ownership']) / 2
                    
                    # Tournament score (high projection, low ownership, reasonable salary)
                    tournament_score = total_proj * (1 + (20 - avg_ownership) / 20) * (60000 / max(total_salary, 30000))
                    
                    dual_stacks.append({
                        'type': 'dual_mini',
                        'teams': f"{team1}({len(team1_players)}) + {team2}({len(team2_players)})",
                        'team1': team1,
                        'team2': team2,
                        'team1_players': team1_players,
                        'team2_players': team2_players,
                        'total_projection': total_proj,
                        'total_salary': total_salary,
                        'avg_ownership': avg_ownership,
                        'tournament_score': tournament_score,
                        'players_used': len(team1_players) + len(team2_players)
                    })
        
        # Sort by tournament score and show top options
        dual_stacks.sort(key=lambda x: x['tournament_score'], reverse=True)
        
        for i, stack in enumerate(dual_stacks[:5]):
            print(f"  {i+1}. {stack['teams']}: {stack['total_projection']:.1f} proj, "
                  f"${stack['total_salary']:,}, {stack['avg_ownership']:.1f}% own, "
                  f"Score: {stack['tournament_score']:.1f}")
        
        return dual_stacks[:10]  # Return top 10
    
    def _build_triple_mini_stacks(self, teams_by_mini2, team_analysis):
        """Build triple mini-stacks (2+2+2)"""
        triple_stacks = []
        
        # Try combinations of top teams for 2-player mini-stacks
        for combo in itertools.combinations(teams_by_mini2[:10], 3):
            team1, team2, team3 = [team for team, _ in combo]
            
            team1_players = team_analysis[team1]['mini_2']['players']
            team2_players = team_analysis[team2]['mini_2']['players'] 
            team3_players = team_analysis[team3]['mini_2']['players']
            
            total_proj = (team_analysis[team1]['mini_2']['projection'] +
                         team_analysis[team2]['mini_2']['projection'] +
                         team_analysis[team3]['mini_2']['projection'])
            total_salary = (team_analysis[team1]['mini_2']['salary'] +
                           team_analysis[team2]['mini_2']['salary'] +
                           team_analysis[team3]['mini_2']['salary'])
            avg_ownership = (team_analysis[team1]['mini_2']['ownership'] +
                            team_analysis[team2]['mini_2']['ownership'] +
                            team_analysis[team3]['mini_2']['ownership']) / 3
            
            # Diversification score (rewards low ownership and balanced projection)
            diversification_score = total_proj * (1 + (18 - avg_ownership) / 18) * (60000 / max(total_salary, 36000))
            
            triple_stacks.append({
                'type': 'triple_mini',
                'teams': f"{team1}(2) + {team2}(2) + {team3}(2)",
                'team1': team1,
                'team2': team2,
                'team3': team3,
                'team1_players': team1_players,
                'team2_players': team2_players,
                'team3_players': team3_players,
                'total_projection': total_proj,
                'total_salary': total_salary,
                'avg_ownership': avg_ownership,
                'diversification_score': diversification_score,
                'players_used': 6
            })
        
        # Sort and show top options
        triple_stacks.sort(key=lambda x: x['diversification_score'], reverse=True)
        
        for i, stack in enumerate(triple_stacks[:5]):
            print(f"  {i+1}. {stack['teams']}: {stack['total_projection']:.1f} proj, "
                  f"${stack['total_salary']:,}, {stack['avg_ownership']:.1f}% own, "
                  f"Score: {stack['diversification_score']:.1f}")
        
        return triple_stacks[:8]  # Return top 8
    
    def _build_primary_secondary_stacks(self, teams_by_mini3, teams_by_mini2, team_analysis):
        """Build primary + secondary stacks (4+2)"""
        primary_secondary = []
        
        # Find teams with good 4-player potential
        for team in self.players_df['Team'].unique():
            team_players = self.players_df[self.players_df['Team'] == team].copy()
            if len(team_players) < 4:
                continue
            
            team_players = team_players.sort_values('value_score', ascending=False)
            top_4 = team_players.head(4)
            
            primary_proj = top_4['FPPG'].sum()
            primary_salary = top_4['Salary'].sum()
            primary_ownership = top_4['ownership_pct'].mean()
            
            # Pair with top mini-2 stacks from other teams
            for secondary_team, _ in teams_by_mini2[:8]:
                if secondary_team == team:
                    continue
                
                secondary_data = team_analysis[secondary_team]['mini_2']
                
                total_proj = primary_proj + secondary_data['projection']
                total_salary = primary_salary + secondary_data['salary']
                avg_ownership = (primary_ownership + secondary_data['ownership']) / 2
                
                # Correlation score (rewards high ceiling)
                correlation_score = total_proj * (1 + (22 - avg_ownership) / 22) * (60000 / max(total_salary, 40000))
                
                primary_secondary.append({
                    'type': 'primary_secondary',
                    'teams': f"{team}(4) + {secondary_team}(2)",
                    'primary_team': team,
                    'secondary_team': secondary_team,
                    'primary_players': top_4,
                    'secondary_players': secondary_data['players'],
                    'total_projection': total_proj,
                    'total_salary': total_salary,
                    'avg_ownership': avg_ownership,
                    'correlation_score': correlation_score,
                    'players_used': 6
                })
        
        # Sort and show top options
        primary_secondary.sort(key=lambda x: x['correlation_score'], reverse=True)
        
        for i, stack in enumerate(primary_secondary[:5]):
            print(f"  {i+1}. {stack['teams']}: {stack['total_projection']:.1f} proj, "
                  f"${stack['total_salary']:,}, {stack['avg_ownership']:.1f}% own, "
                  f"Score: {stack['correlation_score']:.1f}")
        
        return primary_secondary[:8]  # Return top 8
    
    def export_stack_recommendations(self, stack_combinations):
        """Export top multi-team stack recommendations"""
        try:
            # Combine all stacks and sort by best score
            all_stacks = []
            
            for stack in stack_combinations:
                score_key = 'tournament_score' if 'tournament_score' in stack else \
                           'diversification_score' if 'diversification_score' in stack else 'correlation_score'
                
                all_stacks.append({
                    'type': stack['type'],
                    'teams': stack['teams'],
                    'total_projection': stack['total_projection'],
                    'total_salary': stack['total_salary'],
                    'avg_ownership': stack['avg_ownership'],
                    'score': stack[score_key],
                    'players_used': stack['players_used']
                })
            
            # Sort by score
            all_stacks.sort(key=lambda x: x['score'], reverse=True)
            
            # Create export DataFrame
            export_df = pd.DataFrame(all_stacks)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{self.data_dir}/multi_team_stacks_{timestamp}.csv"
            export_df.to_csv(output_file, index=False)
            
            print(f"\n💾 Multi-team stacks exported: {output_file}")
            print(f"   Top recommendations ready for lineup building!")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return None
    
    def run_analysis(self):
        """Run complete multi-team stack analysis"""
        print("🚀 MULTI-TEAM STACK OPTIMIZER")
        print("Tournament-winning strategy: Multiple mini-stacks instead of single team focus")
        print("=" * 70)
        
        # Load and prepare data
        if not self.load_slate_data():
            return
        
        if not self.merge_player_data():
            return
        
        # Analyze mini-stack opportunities
        team_analysis = self.identify_mini_stack_opportunities()
        
        # Build multi-team combinations
        stack_combinations = self.build_multi_team_stacks(team_analysis)
        
        # Export recommendations
        output_file = self.export_stack_recommendations(stack_combinations)
        
        print(f"\n✅ Analysis complete! Found {len(stack_combinations)} multi-team stack options")
        print("\n🎯 KEY INSIGHTS:")
        print("• Dual mini-stacks (3+3, 3+2, 2+3) for tournament upside")
        print("• Triple mini-stacks (2+2+2) for diversification")
        print("• Primary+Secondary (4+2) for correlation plays")
        print("• Focus on low ownership combinations for GPP edge")

if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    optimizer = MultiTeamStackOptimizer()
    optimizer.run_analysis()
