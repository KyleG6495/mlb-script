#!/usr/bin/env python3
"""
MONTE CARLO SIMULATION SYSTEM
============================
Run Monte Carlo simulations on tournament lineups to predict performance ranges.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from scipy import stats
warnings.filterwarnings('ignore')

class MonteCarloSimulationSystem:
    def __init__(self):
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.data_dir = Path(__file__).parent.parent / "data"
        
    def load_tournament_lineups(self):
        """Load all tournament lineup files for simulation"""
        print("🎲 MONTE CARLO SIMULATION SYSTEM")
        print("Running performance simulations on tournament lineups")
        print("="*80)
        
        # Find all tournament lineup files
        lineup_files = list(self.slate_dir.glob("*tournament_lineups*.csv")) + \
                      list(self.slate_dir.glob("*TOURNAMENT_PORTFOLIO*.csv")) + \
                      list(self.slate_dir.glob("*ML_ENHANCED*.csv"))
        
        print(f"📊 Found {len(lineup_files)} tournament files for simulation:")
        
        all_lineups = []
        for file in lineup_files:
            try:
                df = pd.read_csv(file)
                df['Source_File'] = file.name
                all_lineups.append(df)
                print(f"  ✅ {file.name}: {len(df)} lineups")
            except Exception as e:
                print(f"  ❌ Error loading {file.name}: {e}")
        
        if not all_lineups:
            print("❌ No tournament lineups found for simulation!")
            return None
        
        combined_df = pd.concat(all_lineups, ignore_index=True)
        print(f"\n📊 Total lineups for simulation: {len(combined_df)}")
        
        return combined_df
    
    def create_player_simulation_profiles(self):
        """Create simulation profiles for each player"""
        print(f"\n🎯 CREATING PLAYER SIMULATION PROFILES")
        
        # Load FanDuel slate for player data
        slate_file = self.slate_dir / "fd_slate_today.csv"
        slate = pd.read_csv(slate_file)
        
        # Create simulation profiles
        player_profiles = slate.copy()
        
        # Add variance based on position and salary
        player_profiles['floor_multiplier'] = np.where(
            player_profiles['Position'] == 'P',
            0.3,  # Pitchers more volatile
            0.4   # Hitters more consistent
        )
        
        player_profiles['ceiling_multiplier'] = np.where(
            player_profiles['Position'] == 'P',
            2.2,  # Pitchers higher ceiling
            2.5   # Hitters explosive potential
        )
        
        # Salary-based variance (higher salary = lower variance)
        salary_factor = (player_profiles['Salary'] / player_profiles['Salary'].max())
        player_profiles['variance_factor'] = 1.2 - (salary_factor * 0.4)  # 0.8 to 1.2 range
        
        # Calculate simulation parameters
        player_profiles['sim_floor'] = player_profiles['FPPG'] * player_profiles['floor_multiplier']
        player_profiles['sim_ceiling'] = player_profiles['FPPG'] * player_profiles['ceiling_multiplier']
        player_profiles['sim_std'] = (player_profiles['sim_ceiling'] - player_profiles['sim_floor']) / 4
        
        print(f"  ✅ Created simulation profiles for {len(player_profiles)} players")
        print(f"  📊 Variance range: {player_profiles['variance_factor'].min():.2f} - {player_profiles['variance_factor'].max():.2f}")
        
        return player_profiles
    
    def simulate_lineup_performance(self, lineup_row, player_profiles, num_simulations=1000):
        """Simulate performance for a single lineup"""
        
        # Extract player names from lineup
        player_positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
        lineup_players = []
        
        for pos in player_positions:
            if pos in lineup_row and pd.notna(lineup_row[pos]):
                player_name = lineup_row[pos]
                lineup_players.append(player_name)
        
        if len(lineup_players) != 9:
            return None  # Invalid lineup
        
        # Get player profiles for this lineup
        lineup_profiles = []
        for player_name in lineup_players:
            # Try to match player
            matches = player_profiles[
                (player_profiles['First Name'] + ' ' + player_profiles['Last Name']) == player_name
            ]
            
            if len(matches) > 0:
                lineup_profiles.append(matches.iloc[0])
            else:
                # Fallback: use average profile
                avg_profile = {
                    'FPPG': 10.0,
                    'sim_floor': 3.0,
                    'sim_ceiling': 25.0,
                    'sim_std': 5.5
                }
                lineup_profiles.append(avg_profile)
        
        if len(lineup_profiles) != 9:
            return None
        
        # Run Monte Carlo simulation
        simulation_results = []
        
        for _ in range(num_simulations):
            lineup_total = 0
            
            for profile in lineup_profiles:
                # Generate random performance using beta distribution
                # Beta distribution bounded by floor and ceiling
                alpha = 2.0  # Shape parameter
                beta = 2.0   # Shape parameter
                
                # Random value between 0 and 1
                random_pct = np.random.beta(alpha, beta)
                
                # Scale to player's range
                player_score = profile['sim_floor'] + random_pct * (profile['sim_ceiling'] - profile['sim_floor'])
                
                # Add some normal noise
                noise = np.random.normal(0, profile['sim_std'] * 0.3)
                player_score += noise
                
                # Ensure reasonable bounds
                player_score = max(0, min(player_score, profile['sim_ceiling'] * 1.2))
                
                lineup_total += player_score
            
            simulation_results.append(lineup_total)
        
        # Calculate simulation statistics
        sim_array = np.array(simulation_results)
        
        return {
            'mean_score': np.mean(sim_array),
            'median_score': np.median(sim_array),
            'std_score': np.std(sim_array),
            'min_score': np.min(sim_array),
            'max_score': np.max(sim_array),
            'percentile_10': np.percentile(sim_array, 10),
            'percentile_25': np.percentile(sim_array, 25),
            'percentile_75': np.percentile(sim_array, 75),
            'percentile_90': np.percentile(sim_array, 90),
            'prob_150_plus': np.mean(sim_array >= 150),
            'prob_200_plus': np.mean(sim_array >= 200),
            'prob_250_plus': np.mean(sim_array >= 250),
            'simulation_results': sim_array
        }
    
    def run_portfolio_simulation(self, lineups_df, player_profiles):
        """Run simulations on entire lineup portfolio"""
        print(f"\n🎲 RUNNING MONTE CARLO SIMULATIONS")
        print(f"Simulating {len(lineups_df)} lineups with 1000 iterations each...")
        
        simulation_results = []
        
        for idx, lineup in lineups_df.iterrows():
            print(f"  🎯 Simulating lineup {idx+1}/{len(lineups_df)}: {lineup.get('Lineup_ID', f'Lineup_{idx+1}')}")
            
            sim_result = self.simulate_lineup_performance(lineup, player_profiles, num_simulations=1000)
            
            if sim_result:
                # Add lineup metadata
                sim_result['lineup_id'] = lineup.get('Lineup_ID', f'Lineup_{idx+1}')
                sim_result['source_file'] = lineup.get('Source_File', 'Unknown')
                sim_result['original_projection'] = lineup.get('Projected_FPPG', lineup.get('ML_Projected_FPPG', 0))
                sim_result['original_ceiling'] = lineup.get('Ceiling_FPPG', lineup.get('ML_Ceiling_FPPG', 0))
                
                simulation_results.append(sim_result)
            else:
                print(f"    ❌ Failed to simulate lineup {idx+1}")
        
        print(f"  ✅ Simulation complete: {len(simulation_results)} successful simulations")
        
        return simulation_results
    
    def analyze_simulation_results(self, simulation_results):
        """Analyze and rank simulation results"""
        print(f"\n📊 ANALYZING SIMULATION RESULTS")
        
        # Convert to DataFrame for analysis
        sim_df = pd.DataFrame(simulation_results)
        
        # Calculate tournament competitiveness scores
        sim_df['tournament_score'] = (
            sim_df['prob_200_plus'] * 0.4 +      # 40% weight on 200+ probability
            sim_df['prob_250_plus'] * 0.3 +      # 30% weight on 250+ probability  
            sim_df['percentile_90'] * 0.002 +    # 20% weight on 90th percentile (scaled)
            sim_df['mean_score'] * 0.001         # 10% weight on mean score (scaled)
        )
        
        # Sort by tournament score
        sim_df = sim_df.sort_values('tournament_score', ascending=False)
        
        print(f"  🏆 SIMULATION ANALYSIS SUMMARY:")
        print(f"    📊 Lineups simulated: {len(sim_df)}")
        print(f"    🎯 Average mean score: {sim_df['mean_score'].mean():.1f} FPPG")
        print(f"    🚀 Average 90th percentile: {sim_df['percentile_90'].mean():.1f} FPPG")
        print(f"    ⭐ Average 200+ probability: {sim_df['prob_200_plus'].mean():.1%}")
        print(f"    👑 Average 250+ probability: {sim_df['prob_250_plus'].mean():.1%}")
        
        return sim_df
    
    def export_simulation_results(self, sim_df):
        """Export simulation results"""
        print(f"\n📄 EXPORTING SIMULATION RESULTS")
        
        # Create summary export
        export_columns = [
            'lineup_id', 'source_file', 'tournament_score',
            'mean_score', 'median_score', 'std_score',
            'percentile_10', 'percentile_25', 'percentile_75', 'percentile_90',
            'min_score', 'max_score',
            'prob_150_plus', 'prob_200_plus', 'prob_250_plus',
            'original_projection', 'original_ceiling'
        ]
        
        summary_df = sim_df[export_columns].copy()
        summary_df = summary_df.round(2)
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"MONTE_CARLO_SIMULATION_RESULTS_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        summary_df.to_csv(filepath, index=False)
        print(f"✅ Simulation results exported: {filename}")
        
        return summary_df, filepath
    
    def create_simulation_report(self, sim_df):
        """Create detailed simulation report"""
        print(f"\n📈 SIMULATION TOURNAMENT REPORT")
        print("="*60)
        
        # Overall portfolio performance
        print(f"🏆 PORTFOLIO SIMULATION SUMMARY:")
        print(f"  📊 Total lineups analyzed: {len(sim_df)}")
        print(f"  🎯 Mean score range: {sim_df['mean_score'].min():.1f} - {sim_df['mean_score'].max():.1f} FPPG")
        print(f"  🚀 90th percentile range: {sim_df['percentile_90'].min():.1f} - {sim_df['percentile_90'].max():.1f} FPPG")
        
        # Tournament probability analysis
        print(f"\n🎯 TOURNAMENT PROBABILITY ANALYSIS:")
        elite_lineups = len(sim_df[sim_df['prob_250_plus'] >= 0.05])  # 5%+ chance at 250+
        competitive_lineups = len(sim_df[sim_df['prob_200_plus'] >= 0.20])  # 20%+ chance at 200+
        
        print(f"  👑 Elite lineups (5%+ chance at 250+): {elite_lineups}/{len(sim_df)} ({elite_lineups/len(sim_df)*100:.1f}%)")
        print(f"  ⭐ Competitive lineups (20%+ chance at 200+): {competitive_lineups}/{len(sim_df)} ({competitive_lineups/len(sim_df)*100:.1f}%)")
        
        # Top performing lineups
        print(f"\n🌟 TOP 10 SIMULATED LINEUPS:")
        top_lineups = sim_df.head(10)
        
        for i, (_, lineup) in enumerate(top_lineups.iterrows(), 1):
            print(f"  {i:2d}. {lineup['lineup_id']} | Mean: {lineup['mean_score']:.1f} | 90th: {lineup['percentile_90']:.1f} | 200+: {lineup['prob_200_plus']:.1%} | 250+: {lineup['prob_250_plus']:.1%}")
        
        # Risk analysis
        print(f"\n⚡ RISK/REWARD ANALYSIS:")
        high_ceiling_lineups = sim_df[sim_df['percentile_90'] >= 250]
        consistent_lineups = sim_df[sim_df['std_score'] <= sim_df['std_score'].median()]
        
        print(f"  🚀 High ceiling lineups (90th ≥ 250): {len(high_ceiling_lineups)}")
        print(f"  📊 Consistent lineups (low variance): {len(consistent_lineups)}")
        
        # Source file performance
        print(f"\n📁 PERFORMANCE BY SOURCE:")
        source_performance = sim_df.groupby('source_file').agg({
            'tournament_score': 'mean',
            'prob_200_plus': 'mean',
            'prob_250_plus': 'mean',
            'mean_score': 'mean'
        }).round(3)
        
        for source, stats in source_performance.iterrows():
            print(f"  📊 {source[:30]:30} | Score: {stats['tournament_score']:.3f} | 200+: {stats['prob_200_plus']:.1%} | 250+: {stats['prob_250_plus']:.1%}")
        
        # Tournament readiness rating
        avg_200_prob = sim_df['prob_200_plus'].mean()
        avg_250_prob = sim_df['prob_250_plus'].mean()
        
        if avg_250_prob >= 0.05:
            rating = "LEGENDARY 👑"
        elif avg_200_prob >= 0.25:
            rating = "ELITE ⭐"
        elif avg_200_prob >= 0.15:
            rating = "STRONG 💪"
        else:
            rating = "GOOD ✅"
        
        print(f"\n🏆 SIMULATION-BASED TOURNAMENT RATING: {rating}")
        print(f"  📊 Average 200+ probability: {avg_200_prob:.1%}")
        print(f"  🚀 Average 250+ probability: {avg_250_prob:.1%}")
        
        return {
            'rating': rating,
            'avg_200_prob': avg_200_prob,
            'avg_250_prob': avg_250_prob,
            'elite_lineups': elite_lineups,
            'competitive_lineups': competitive_lineups
        }
    
    def run_complete_simulation(self):
        """Run complete Monte Carlo simulation system"""
        print("🎲 MONTE CARLO SIMULATION SYSTEM")
        print("Analyzing tournament lineup performance probabilities")
        print("="*80)
        
        try:
            # Load tournament lineups
            lineups_df = self.load_tournament_lineups()
            if lineups_df is None:
                return
            
            # Create player simulation profiles
            player_profiles = self.create_player_simulation_profiles()
            
            # Run portfolio simulation
            simulation_results = self.run_portfolio_simulation(lineups_df, player_profiles)
            
            if not simulation_results:
                print("❌ No simulation results generated")
                return
            
            # Analyze results
            sim_df = self.analyze_simulation_results(simulation_results)
            
            # Export results
            summary_df, filepath = self.export_simulation_results(sim_df)
            
            # Create report
            report_stats = self.create_simulation_report(sim_df)
            
            print(f"\n🎉 MONTE CARLO SIMULATION COMPLETE!")
            print(f"🎲 Analyzed {len(sim_df)} lineups with 1000 simulations each")
            print(f"🏆 Tournament Rating: {report_stats['rating']}")
            print(f"📊 Portfolio ready for simulation-guided decisions!")
            
            return filepath
            
        except Exception as e:
            print(f"Error in simulation system: {e}")
            import traceback
            traceback.print_exc()

def main():
    print("🎲 MONTE CARLO SIMULATION SYSTEM")
    print("Analyzing tournament lineup performance probabilities")
    print("="*80)
    
    sim_system = MonteCarloSimulationSystem()
    sim_system.run_complete_simulation()

if __name__ == "__main__":
    main()
