#!/usr/bin/env python3
"""
MULTI-TEAM LINEUP BUILDER
Takes multi-team stack combinations and builds complete 9-player FanDuel lineups
"""

import pandas as pd
import numpy as np
import itertools
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MultiTeamLineupBuilder:
    """
    Build complete FanDuel lineups from multi-team stack recommendations
    """
    
    def __init__(self):
        self.data_dir = "../data"
        self.slate_dir = "../fd_current_slate"
        self.salary_cap = 60000
        
        # FanDuel roster requirements
        self.positions = {
            'C': 1,
            '1B': 1, 
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'OF': 3,
            'UTIL': 1  # Any position
        }
        
        self.total_players = 9
    
    def load_player_data(self):
        """Load FD slate with projections and ownership"""
        try:
            import os
            
            # Load FD slate
            slate_file = f"{self.slate_dir}/fd_slate_today_clean.csv"
            if not os.path.exists(slate_file):
                slate_file = f"{self.slate_dir}/fd_slate_today.csv"
            
            self.players_df = pd.read_csv(slate_file)
            print(f"✅ Loaded {len(self.players_df)} players from FD slate")
            
            # Load ownership projections if available
            ownership_files = [f for f in os.listdir(self.data_dir) if f.startswith("advanced_ownership_projections_")]
            if ownership_files:
                ownership_files.sort(reverse=True)
                ownership_file = f"{self.data_dir}/{ownership_files[0]}"
                ownership_df = pd.read_csv(ownership_file)
                
                # Merge ownership data
                ownership_lookup = {}
                for _, row in ownership_df.iterrows():
                    player_name = row['player_name']
                    ownership_lookup[player_name] = {
                        'ownership': row['ownership'] * 100 if row['ownership'] < 1 else row['ownership'],
                        'leverage_score': row.get('leverage_score', 1.0)
                    }
                
                # Add ownership columns
                self.players_df['ownership_pct'] = 0.0
                self.players_df['leverage_score'] = 1.0
                
                for idx, row in self.players_df.iterrows():
                    nickname = row.get('Nickname', '')
                    if nickname in ownership_lookup:
                        self.players_df.at[idx, 'ownership_pct'] = ownership_lookup[nickname]['ownership']
                        self.players_df.at[idx, 'leverage_score'] = ownership_lookup[nickname]['leverage_score']
                
                print(f"✅ Merged ownership data from: {ownership_files[0]}")
            
            # Calculate value score
            self.players_df['value_score'] = self.players_df['FPPG'] / (self.players_df['Salary'] / 1000)
            
            # Parse positions (handle multi-position eligibility)
            self.players_df['positions_list'] = self.players_df['Position'].apply(lambda x: x.split('/') if '/' in str(x) else [str(x)])
            
            return True
            
        except Exception as e:
            print(f"❌ Error loading player data: {e}")
            return False
    
    def load_multi_team_stacks(self):
        """Load the latest multi-team stack recommendations"""
        try:
            import os
            
            # Find latest multi-team stack file
            stack_files = [f for f in os.listdir(self.data_dir) if f.startswith("multi_team_stacks_")]
            if not stack_files:
                print("❌ No multi-team stack files found. Run the analyzer first.")
                return []
            
            stack_files.sort(reverse=True)
            stack_file = f"{self.data_dir}/{stack_files[0]}"
            
            stack_df = pd.read_csv(stack_file)
            print(f"✅ Loaded {len(stack_df)} multi-team stack combinations from: {stack_files[0]}")
            
            return stack_df.to_dict('records')
            
        except Exception as e:
            print(f"❌ Error loading stack recommendations: {e}")
            return []
    
    def get_stack_players(self, stack_info):
        """Extract actual player objects from stack information"""
        try:
            stack_players = []
            teams = stack_info['Teams']
            
            # Parse team information (e.g., "NYM(3) + CHC(3)")
            if ' + ' in teams:
                team_parts = teams.split(' + ')
                for part in team_parts:
                    if '(' in part and ')' in part:
                        team = part.split('(')[0]
                        count = int(part.split('(')[1].split(')')[0])
                        
                        # Get top players from this team by value score
                        team_players = self.players_df[self.players_df['Team'] == team].copy()
                        team_players = team_players.sort_values('value_score', ascending=False)
                        
                        # Add top players from this team
                        stack_players.extend(team_players.head(count).to_dict('records'))
            
            return stack_players
            
        except Exception as e:
            print(f"❌ Error extracting stack players: {e}")
            return []
    
    def fill_remaining_positions(self, stack_players, target_salary=60000):
        """Fill remaining roster spots with best available players"""
        try:
            # Convert stack players to DataFrame for easier manipulation
            stack_df = pd.DataFrame(stack_players)
            used_player_ids = set(stack_df['Id'].tolist()) if not stack_df.empty else set()
            
            # Calculate remaining salary and positions needed
            used_salary = stack_df['Salary'].sum() if not stack_df.empty else 0
            remaining_salary = target_salary - used_salary
            
            # Track positions used
            positions_used = {'C': 0, '1B': 0, '2B': 0, '3B': 0, 'SS': 0, 'OF': 0, 'UTIL': 0}
            
            for player in stack_players:
                positions = player['positions_list']
                # Assign to most restrictive position first
                assigned = False
                for pos in ['C', '1B', '2B', '3B', 'SS']:
                    if pos in positions and positions_used[pos] < self.positions[pos]:
                        positions_used[pos] += 1
                        assigned = True
                        break
                
                if not assigned:
                    if 'OF' in positions and positions_used['OF'] < self.positions['OF']:
                        positions_used['OF'] += 1
                    else:
                        positions_used['UTIL'] += 1
            
            # Get available players (not in stack)
            available_players = self.players_df[~self.players_df['Id'].isin(used_player_ids)].copy()
            
            # Fill remaining positions
            remaining_players = []
            total_needed = sum(self.positions.values()) - len(stack_players)
            
            if total_needed > 0:
                # Sort by value score
                available_players = available_players.sort_values('value_score', ascending=False)
                
                # Filter by salary constraint
                affordable_players = available_players[available_players['Salary'] <= remaining_salary * 0.8]
                
                # Take top available players within budget
                for _, player in affordable_players.iterrows():
                    if len(remaining_players) >= total_needed:
                        break
                    
                    player_salary = player['Salary']
                    if used_salary + player_salary <= target_salary:
                        remaining_players.append(player.to_dict())
                        used_salary += player_salary
                        used_player_ids.add(player['Id'])
            
            return remaining_players, used_salary
            
        except Exception as e:
            print(f"❌ Error filling remaining positions: {e}")
            return [], 0
    
    def optimize_lineup(self, stack_players):
        """Build optimized lineup using stack as core"""
        try:
            # Get remaining players and total salary
            remaining_players, total_salary = self.fill_remaining_positions(stack_players)
            
            # Combine all players
            lineup_players = stack_players + remaining_players
            
            # Ensure we have exactly 9 players
            if len(lineup_players) < 9:
                # Need to add more players
                used_player_ids = set(p['Id'] for p in lineup_players)
                available_players = self.players_df[~self.players_df['Id'].isin(used_player_ids)].copy()
                available_players = available_players.sort_values('value_score', ascending=False)
                
                # Add players until we have 9
                current_salary = sum(p['Salary'] for p in lineup_players)
                for _, player in available_players.iterrows():
                    if len(lineup_players) >= 9:
                        break
                    if current_salary + player['Salary'] <= self.salary_cap:
                        lineup_players.append(player.to_dict())
                        current_salary += player['Salary']
            
            elif len(lineup_players) > 9:
                # Too many players, keep best 9 by value score
                lineup_players.sort(key=lambda x: x['value_score'], reverse=True)
                lineup_players = lineup_players[:9]
            
            # Recalculate final salary
            total_salary = sum(p['Salary'] for p in lineup_players)
            
            if len(lineup_players) != 9:
                print(f"⚠️ Warning: Lineup has {len(lineup_players)} players instead of 9")
                return None
            
            if total_salary > self.salary_cap:
                print(f"⚠️ Warning: Lineup salary ${total_salary:,} exceeds cap ${self.salary_cap:,}")
                return None
            
            # Calculate lineup metrics
            total_projection = sum(p['FPPG'] for p in lineup_players)
            avg_ownership = sum(p.get('ownership_pct', 0) for p in lineup_players) / len(lineup_players)
            
            # Leverage score (projection per dollar / ownership)
            leverage = (total_projection / (total_salary / 1000)) * (1 + (25 - avg_ownership) / 25)
            
            lineup_data = {
                'players': lineup_players,
                'total_projection': total_projection,
                'total_salary': total_salary,
                'avg_ownership': avg_ownership,
                'leverage_score': leverage,
                'salary_remaining': self.salary_cap - total_salary
            }
            
            return lineup_data
            
        except Exception as e:
            print(f"❌ Error optimizing lineup: {e}")
            return None
    
    def build_lineups_from_stacks(self, max_lineups=20):
        """Build complete lineups from top multi-team stacks with diversity"""
        lineups = []
        used_players_count = {}  # Track how often each player is used
        
        try:
            # Load multi-team stack recommendations
            stack_recommendations = self.load_multi_team_stacks()
            
            if not stack_recommendations:
                print("❌ No stack recommendations available")
                return []
            
            print(f"\n🔄 Building diverse lineups from top {min(max_lineups, len(stack_recommendations))} stacks...")
            
            for i, stack_info in enumerate(stack_recommendations[:max_lineups * 2]):  # Try more stacks for diversity
                if len(lineups) >= max_lineups:
                    break
                    
                print(f"  Processing stack {i+1}: {stack_info['Teams']}")
                
                # Get players for this stack
                stack_players = self.get_stack_players(stack_info)
                
                if len(stack_players) < 2:
                    print(f"    ⚠️ Insufficient players for stack {i+1}")
                    continue
                
                # Build complete lineup with diversity consideration
                lineup = self.optimize_lineup_with_diversity(stack_players, used_players_count, len(lineups))
                
                if lineup:
                    # Update player usage counts
                    for player in lineup['players']:
                        player_id = player['Id']
                        used_players_count[player_id] = used_players_count.get(player_id, 0) + 1
                    
                    lineup['stack_info'] = stack_info
                    lineup['lineup_id'] = len(lineups) + 1
                    lineups.append(lineup)
                    print(f"    ✅ Lineup {len(lineups)}: {lineup['total_projection']:.1f} proj, "
                          f"${lineup['total_salary']:,}, {lineup['avg_ownership']:.1f}% own")
                else:
                    print(f"    ❌ Failed to build lineup {i+1}")
            
            print(f"\n✅ Successfully built {len(lineups)} diverse lineups from multi-team stacks")
            
            # Show diversity metrics
            if lineups:
                all_players = set()
                for lineup in lineups:
                    for player in lineup['players']:
                        all_players.add(player['Id'])
                
                print(f"📊 Diversity metrics:")
                print(f"   Total unique players: {len(all_players)}")
                
                # Show most used players
                most_used = sorted(used_players_count.items(), key=lambda x: x[1], reverse=True)
                print(f"   Most used player appears in {most_used[0][1]}/{len(lineups)} lineups ({most_used[0][1]/len(lineups)*100:.1f}%)")
            
            return lineups
            
        except Exception as e:
            print(f"❌ Error building lineups: {e}")
            return []
    
    def optimize_lineup_with_diversity(self, stack_players, used_players_count, lineup_number):
        """Build optimized lineup with diversity consideration"""
        try:
            # Get remaining players and total salary
            remaining_players, total_salary = self.fill_remaining_positions_diverse(
                stack_players, used_players_count, lineup_number)
            
            # Combine all players
            lineup_players = stack_players + remaining_players
            
            # Ensure we have exactly 9 players
            if len(lineup_players) < 9:
                # Need to add more players with diversity consideration
                used_player_ids = set(p['Id'] for p in lineup_players)
                available_players = self.players_df[~self.players_df['Id'].isin(used_player_ids)].copy()
                
                # Sort by value score but penalize overused players
                def diversity_score(row):
                    base_score = row['value_score']
                    usage_penalty = used_players_count.get(row['Id'], 0) * 0.5  # Penalty for overuse
                    return base_score - usage_penalty
                
                available_players['diversity_score'] = available_players.apply(diversity_score, axis=1)
                available_players = available_players.sort_values('diversity_score', ascending=False)
                
                # Add players until we have 9
                current_salary = sum(p['Salary'] for p in lineup_players)
                for _, player in available_players.iterrows():
                    if len(lineup_players) >= 9:
                        break
                    if current_salary + player['Salary'] <= self.salary_cap:
                        lineup_players.append(player.to_dict())
                        current_salary += player['Salary']
            
            elif len(lineup_players) > 9:
                # Too many players, keep best 9 by diversity-adjusted value score
                def player_diversity_score(player):
                    base_score = player['value_score']
                    usage_penalty = used_players_count.get(player['Id'], 0) * 0.3
                    return base_score - usage_penalty
                
                lineup_players.sort(key=player_diversity_score, reverse=True)
                lineup_players = lineup_players[:9]
            
            # Recalculate final salary
            total_salary = sum(p['Salary'] for p in lineup_players)
            
            if len(lineup_players) != 9:
                print(f"⚠️ Warning: Lineup has {len(lineup_players)} players instead of 9")
                return None
            
            if total_salary > self.salary_cap:
                print(f"⚠️ Warning: Lineup salary ${total_salary:,} exceeds cap ${self.salary_cap:,}")
                return None
            
            # Calculate lineup metrics
            total_projection = sum(p['FPPG'] for p in lineup_players)
            avg_ownership = sum(p.get('ownership_pct', 0) for p in lineup_players) / len(lineup_players)
            
            # Leverage score (projection per dollar / ownership)
            leverage = (total_projection / (total_salary / 1000)) * (1 + (25 - avg_ownership) / 25)
            
            lineup_data = {
                'players': lineup_players,
                'total_projection': total_projection,
                'total_salary': total_salary,
                'avg_ownership': avg_ownership,
                'leverage_score': leverage,
                'salary_remaining': self.salary_cap - total_salary
            }
            
            return lineup_data
            
        except Exception as e:
            print(f"❌ Error optimizing lineup: {e}")
            return None
    
    def fill_remaining_positions_diverse(self, stack_players, used_players_count, lineup_number):
        """Fill remaining roster spots with diversity consideration"""
        try:
            # Convert stack players to DataFrame for easier manipulation
            stack_df = pd.DataFrame(stack_players)
            used_player_ids = set(stack_df['Id'].tolist()) if not stack_df.empty else set()
            
            # Calculate remaining salary and positions needed
            used_salary = stack_df['Salary'].sum() if not stack_df.empty else 0
            remaining_salary = self.salary_cap - used_salary
            
            # Get available players (not in stack)
            available_players = self.players_df[~self.players_df['Id'].isin(used_player_ids)].copy()
            
            # Fill remaining positions with diversity scoring
            remaining_players = []
            total_needed = 9 - len(stack_players)
            
            if total_needed > 0:
                # Sort by diversity-adjusted value score
                def diversity_value_score(row):
                    base_score = row['value_score']
                    # Penalize players that have been used too much
                    usage_count = used_players_count.get(row['Id'], 0)
                    # Progressive penalty: more penalty for each additional use
                    usage_penalty = usage_count * (0.3 + lineup_number * 0.05)
                    return base_score - usage_penalty
                
                available_players['diversity_value'] = available_players.apply(diversity_value_score, axis=1)
                available_players = available_players.sort_values('diversity_value', ascending=False)
                
                # Filter by salary constraint
                affordable_players = available_players[available_players['Salary'] <= remaining_salary * 0.9]
                
                # Take top available players within budget
                for _, player in affordable_players.iterrows():
                    if len(remaining_players) >= total_needed:
                        break
                    
                    player_salary = player['Salary']
                    if used_salary + player_salary <= self.salary_cap:
                        remaining_players.append(player.to_dict())
                        used_salary += player_salary
                        used_player_ids.add(player['Id'])
            
            return remaining_players, used_salary
            
        except Exception as e:
            print(f"❌ Error filling remaining positions: {e}")
            return [], 0
    
    def export_lineups_for_fanduel(self, lineups):
        """Export lineups in FanDuel upload format"""
        try:
            if not lineups:
                print("❌ No lineups to export")
                return None
            
            # Create FanDuel format DataFrame with proper column structure
            fd_data = []
            
            for lineup in lineups:
                players = lineup['players']
                
                if len(players) != 9:
                    print(f"⚠️ Skipping incomplete lineup {lineup['lineup_id']} - has {len(players)} players")
                    continue
                
                # Create lineup row with all 9 positions
                # FanDuel format: P, C/1B, 2B, 3B, SS, OF, OF, OF, UTIL
                lineup_row = []
                
                for i, player in enumerate(players):
                    player_entry = f"{player['Id']}:{player['Nickname']}"
                    lineup_row.append(player_entry)
                
                # Ensure we have exactly 9 players
                while len(lineup_row) < 9:
                    lineup_row.append("MISSING:PLAYER")
                
                fd_data.append(lineup_row)
            
            if not fd_data:
                print("❌ No valid lineups to export")
                return None
            
            # Create DataFrame with correct FanDuel column names (matching your lineups.csv)
            columns = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
            export_df = pd.DataFrame(fd_data, columns=columns)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"{self.data_dir}/multi_team_lineups_FD_READY_{timestamp}.csv"
            export_df.to_csv(output_file, index=False)
            
            print(f"\n💾 FanDuel-ready lineups exported: {output_file}")
            print(f"   {len(fd_data)} complete 9-player lineups with correct headers!")
            
            # Show sample lineup for verification
            if len(export_df) > 0:
                print(f"\n📋 Sample lineup verification:")
                sample = export_df.iloc[0]
                for pos in columns:
                    print(f"   {pos}: {sample[pos]}")
            
            return output_file
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def run_lineup_builder(self, max_lineups=15):
        """Run complete lineup building process"""
        print("🚀 MULTI-TEAM LINEUP BUILDER")
        print("Building complete FanDuel lineups from tournament-winning stack strategies")
        print("=" * 70)
        
        # Load player data
        if not self.load_player_data():
            return
        
        # Build lineups from stacks
        lineups = self.build_lineups_from_stacks(max_lineups)
        
        if not lineups:
            print("❌ No lineups generated")
            return
        
        # Export for FanDuel
        output_file = self.export_lineups_for_fanduel(lineups)
        
        # Show summary
        if lineups:
            print(f"\n📊 LINEUP SUMMARY:")
            print(f"   Generated: {len(lineups)} lineups")
            print(f"   Avg Projection: {sum(l['total_projection'] for l in lineups) / len(lineups):.1f}")
            print(f"   Avg Ownership: {sum(l['avg_ownership'] for l in lineups) / len(lineups):.1f}%")
            print(f"   Best Leverage: {max(l['leverage_score'] for l in lineups):.1f}")
            
            if output_file:
                print(f"\n🎯 Ready to upload to FanDuel: {output_file}")

if __name__ == "__main__":
    import os
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    builder = MultiTeamLineupBuilder()
    builder.run_lineup_builder()
