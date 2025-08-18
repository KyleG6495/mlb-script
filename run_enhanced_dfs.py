#!/usr/bin/env python3
"""
Enhanced DFS Pipeline Runner
===========================

Comprehensive runner that executes the complete enhanced DFS pipeline:
1. Load existing player projections
2. Run game state simulations
3. Generate enhanced projections with floor/ceiling
4. Optimize lineups for different contest types
5. Output results and recommendations
"""

import sys
import os
import logging
from datetime import datetime
import pandas as pd

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhance_dfs_projections import DFSDataIntegrator
from optimize_simplified_dfs_lineups import SimplifiedDFSOptimizer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('../data/dfs_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EnhancedDFSPipeline:
    """Complete enhanced DFS pipeline orchestrator"""
    
    def __init__(self, data_dir: str = "../data"):
        self.data_dir = data_dir
        self.start_time = datetime.now()
        
    def run_complete_pipeline(self, n_simulations: int = 1000):
        """Execute the complete enhanced DFS pipeline"""
        
        logger.info("START: Starting Enhanced DFS Pipeline")
        logger.info("="*60)
        
        try:
            # Step 1: Generate enhanced projections
            success = self.run_simulations(n_simulations)
            if not success:
                logger.error("Failed to generate enhanced projections")
                return False
            
            # Step 2: Optimize lineups
            success = self.optimize_lineups()
            if not success:
                logger.error("Failed to optimize lineups")
                return False
            
            # Step 3: Generate final reports
            self.generate_final_reports()
            
            # Step 4: Show completion summary
            self.show_completion_summary()
            
            logger.info("SUCCESS: Enhanced DFS Pipeline completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline failed with error: {e}")
            return False
    
    def run_simulations(self, n_simulations: int) -> bool:
        """Run game state simulations and generate enhanced projections"""
        
        logger.info(f"DATA: Step 1: Running {n_simulations} game simulations...")
        
        try:
            # Initialize simulation integrator
            integrator = DFSDataIntegrator(self.data_dir)
            
            # Run enhanced projections
            projections = integrator.run_enhanced_projections(n_simulations)
            
            if projections.empty:
                logger.error("No projections generated")
                return False
            
            logger.info(f"SUCCESS: Generated enhanced projections for {len(projections)} players")
            return True
            
        except Exception as e:
            logger.error(f"Simulation step failed: {e}")
            return False
    
    def optimize_lineups(self) -> bool:
        """Optimize lineups using enhanced projections"""
        
        logger.info("TARGET: Step 2: Optimizing lineups...")
        
        try:
            # Initialize optimizer
            optimizer = SimplifiedDFSOptimizer()
            
            # Load the enhanced projections
            projections_file = os.path.join(self.data_dir, "dfs_projections_for_optimizer.csv")
            df = pd.read_csv(projections_file)
            logger.info(f"Loaded {len(df)} enhanced projections")
            
            # Generate lineups using your existing optimizer
            logger.info("MONEY: Generating diverse lineups...")
            lineups = optimizer.generate_multiple_lineups(df, n_lineups=15)
            
            if lineups:
                logger.info(f"SUCCESS: Generated {len(lineups)} optimized lineups")
                
                # Save lineups to the standard format
                self._save_optimized_lineups(lineups)
                
                # Analyze lineup distribution
                optimizer.analyze_lineup_distribution(lineups)
                
                return True
            else:
                logger.error("Failed to generate lineups")
                return False
            
        except Exception as e:
            logger.error(f"Lineup optimization failed: {e}")
            return False
    
    def _save_optimized_lineups(self, lineups):
        """Convert and save lineups in standard format"""
        try:
            all_lineups = []
            for i, lineup_result in enumerate(lineups):
                for j, player in enumerate(lineup_result['lineup']):
                    all_lineups.append({
                        'lineup_id': i + 1,
                        'contest_type': lineup_result.get('objective', 'balanced'),
                        'strategy_description': self._get_strategy_description(lineup_result.get('objective', 'balanced')),
                        'slot': j + 1,
                        'player_id': '',  # Not available in simplified optimizer
                        'name': player['name'],
                        'position': player['position'],
                        'primary_position': player['position'],
                        'team': player['team'],
                        'salary': player['salary'],
                        'ml_projected_fppg': player['projected_fppg'],
                        'ceiling_fppg': player['ceiling'],
                        'floor_fppg': player['floor'],
                        'value_score': player.get('salary_efficiency', 0),
                        'lineup_total_salary': lineup_result['total_salary'],
                        'lineup_total_projection': lineup_result['total_fppg'],
                        'lineup_total_ceiling': sum(p['ceiling'] for p in lineup_result['lineup']),
                        'lineup_total_floor': sum(p['floor'] for p in lineup_result['lineup'])
                    })
            
            # Save to CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(self.data_dir, f"enhanced_ml_dfs_lineups_{timestamp}.csv")
            
            df_lineups = pd.DataFrame(all_lineups)
            df_lineups.to_csv(output_file, index=False)
            
            logger.info(f" Saved {len(lineups)} lineups to {os.path.basename(output_file)}")
            
        except Exception as e:
            logger.error(f"Failed to save lineups: {e}")
    
    def _get_strategy_description(self, objective):
        """Get strategy description for objective"""
        descriptions = {
            'floor': 'High-floor lineups for cash games',
            'balanced': 'Balanced upside for small tournaments', 
            'ceiling': 'High-ceiling lineups for large tournaments'
        }
        return descriptions.get(objective, 'Enhanced DFS lineup')
    
    def generate_final_reports(self):
        """Generate comprehensive final reports"""
        
        logger.info("INFO: Step 3: Generating final reports...")
        
        try:
            # Load enhanced projections
            proj_files = [f for f in os.listdir(self.data_dir) 
                         if f.startswith('enhanced_dfs_projections_')]
            
            if not proj_files:
                logger.warning("No enhanced projection files found")
                return
            
            # Use most recent file
            latest_proj_file = max(proj_files)
            projections = pd.read_csv(os.path.join(self.data_dir, latest_proj_file))
            
            # Generate summary report
            self.create_summary_report(projections)
            
            # Generate position-specific reports
            self.create_position_reports(projections)
            
            logger.info("SUCCESS: Final reports generated")
            
        except Exception as e:
            logger.error(f"Report generation failed: {e}")
    
    def create_summary_report(self, projections: pd.DataFrame):
        """Create comprehensive summary report"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.data_dir, f"dfs_summary_report_{timestamp}.txt")
        
        with open(report_file, 'w') as f:
            f.write("ENHANCED DFS ANALYSIS REPORT\n")
            f.write("="*50 + "\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Players Analyzed: {len(projections)}\n\n")
            
            # Overall statistics
            f.write("PROJECTION SUMMARY:\n")
            f.write("-"*30 + "\n")
            f.write(f"Average Projected FPPG: {projections['mean_fppg'].mean():.2f}\n")
            f.write(f"Highest Ceiling: {projections['ceiling_fppg'].max():.2f}\n")
            f.write(f"Safest Floor: {projections['floor_fppg'].max():.2f}\n\n")
            
            # Position breakdown
            f.write("POSITION BREAKDOWN:\n")
            f.write("-"*30 + "\n")
            pos_stats = projections.groupby('position').agg({
                'mean_fppg': ['count', 'mean', 'max'],
                'ceiling_fppg': 'max',
                'floor_fppg': 'max'
            }).round(2)
            f.write(pos_stats.to_string() + "\n\n")
            
            # Top recommendations by category
            f.write("TOP RECOMMENDATIONS:\n")
            f.write("-"*30 + "\n")
            
            # Top value plays
            if 'value_mean' in projections.columns:
                f.write("Top 5 Value Plays:\n")
                top_value = projections.nlargest(5, 'value_mean')[['name', 'position', 'mean_fppg', 'value_mean']]
                f.write(top_value.to_string(index=False) + "\n\n")
            
            # Top ceiling plays
            f.write("Top 5 Ceiling Plays:\n")
            top_ceiling = projections.nlargest(5, 'ceiling_fppg')[['name', 'position', 'ceiling_fppg']]
            f.write(top_ceiling.to_string(index=False) + "\n\n")
            
            # Top floor plays
            f.write("Top 5 Floor Plays:\n")
            top_floor = projections.nlargest(5, 'floor_fppg')[['name', 'position', 'floor_fppg']]
            f.write(top_floor.to_string(index=False) + "\n\n")
        
        logger.info(f"Summary report saved to {report_file}")
    
    def create_position_reports(self, projections: pd.DataFrame):
        """Create detailed reports by position"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for position in projections['position'].unique():
            pos_data = projections[projections['position'] == position].copy()
            pos_data = pos_data.sort_values('mean_fppg', ascending=False)
            
            report_file = os.path.join(self.data_dir, f"dfs_position_{position}_{timestamp}.csv")
            pos_data.to_csv(report_file, index=False)
        
        logger.info("Position-specific reports generated")
    
    def show_completion_summary(self):
        """Show final completion summary"""
        
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "="*70)
        print("COMPLETE: ENHANCED DFS PIPELINE COMPLETED SUCCESSFULLY!")
        print("="*70)
        print(f"  Total Runtime: {duration}")
        print(f" Output Directory: {os.path.abspath(self.data_dir)}")
        print()
        print("DATA: GENERATED FILES:")
        print("-" * 30)
        
        # List generated files
        recent_files = []
        cutoff_time = self.start_time
        
        for file in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, file)
            if os.path.getmtime(file_path) > cutoff_time.timestamp():
                recent_files.append(file)
        
        for file in sorted(recent_files):
            if any(keyword in file for keyword in ['enhanced', 'lineup', 'dfs_summary', 'dfs_position']):
                print(f"   SUCCESS: {file}")
        
        print()
        print("TARGET: NEXT STEPS:")
        print("-" * 30)
        print("   1. Review generated lineup files")
        print("   2. Upload lineups to FanDuel")
        print("   3. Monitor performance for model improvement")
        print("   4. Run backtest analysis after games complete")
        print()
        print("TIP: TIP: Check the summary report for detailed insights!")
        print("="*70)

def main():
    """Main execution function"""
    
    # Configuration
    N_SIMULATIONS = 1000  # Adjust based on computational resources
    
    print("START: ENHANCED DFS PIPELINE")
    print("=" * 50)
    print(f"Simulations: {N_SIMULATIONS}")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Initialize and run pipeline
    pipeline = EnhancedDFSPipeline()
    success = pipeline.run_complete_pipeline(N_SIMULATIONS)
    
    if not success:
        print("\nERROR: Pipeline failed. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
