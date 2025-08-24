#!/usr/bin/env python3
"""
UNIFIED MLB DECISION ENGINE
Integrates ALL data sources for cohesive recommendations:
- Stack analysis (vegas, pitcher, weather multipliers)
- Umpire analysis (strike zone, pace)
- Weather data (wind, temperature, humidity)
- Park factors
- Ownership projections
- Injury reports
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedMLBDecisionEngine:
    def __init__(self):
        self.data_sources = {
            'stack_analysis': None,
            'weather_data': None,
            'umpire_data': None,
            'ownership_data': None,
            'slate_data': None,
            'injury_data': None
        }
        self.unified_recommendations = {}
        
    def load_all_data_sources(self):
        """Load and validate all data sources"""
        logger.info("🔄 LOADING ALL DATA SOURCES FOR UNIFIED ANALYSIS")
        logger.info("=" * 60)
        
        # 1. Load stack analysis (core recommendations)
        self.load_stack_analysis()
        
        # 2. Load umpire data
        self.load_umpire_data()
        
        # 3. Load weather data
        self.load_weather_data()
        
        # 4. Load ownership projections
        self.load_ownership_data()
        
        # 5. Load current slate
        self.load_slate_data()
        
        # 6. Load injury reports
        self.load_injury_data()
        
        logger.info(f"✅ DATA INTEGRATION COMPLETE")
        return self.validate_data_completeness()
    
    def load_stack_analysis(self):
        """Load latest stack analysis with vegas/pitcher/weather multipliers"""
        try:
            data_dir = "../data"
            stack_files = [f for f in os.listdir(data_dir) if 'team_stack_analysis' in f and f.endswith('.csv')]
            
            if stack_files:
                latest_stack = max([os.path.join(data_dir, f) for f in stack_files], key=os.path.getmtime)
                self.data_sources['stack_analysis'] = pd.read_csv(latest_stack)
                logger.info(f"✅ Stack Analysis: {os.path.basename(latest_stack)} ({len(self.data_sources['stack_analysis'])} teams)")
            else:
                logger.warning("⚠️ No stack analysis found - run ADVANCED_STACK_OPTIMIZER.py first")
                
        except Exception as e:
            logger.error(f"❌ Error loading stack analysis: {e}")
    
    def load_umpire_data(self):
        """Load or generate umpire analysis for today's games"""
        try:
            # Try to load existing umpire data
            umpire_files = [f for f in os.listdir("../data") if 'umpire' in f.lower() and f.endswith('.csv')]
            
            if umpire_files:
                latest_umpire = max([os.path.join("../data", f) for f in umpire_files], key=os.path.getmtime)
                self.data_sources['umpire_data'] = pd.read_csv(latest_umpire)
                logger.info(f"✅ Umpire Data: {os.path.basename(latest_umpire)}")
            else:
                # Generate basic umpire analysis
                logger.info("📊 Generating basic umpire analysis...")
                self.generate_basic_umpire_analysis()
                
        except Exception as e:
            logger.error(f"❌ Error loading umpire data: {e}")
            self.generate_basic_umpire_analysis()
    
    def generate_basic_umpire_analysis(self):
        """Generate basic umpire multipliers based on known patterns"""
        # Basic umpire impact database
        umpire_impacts = {
            'Angel Hernandez': {'multiplier': 0.85, 'reason': 'Inconsistent strike zone favors variance'},
            'Joe West': {'multiplier': 0.90, 'reason': 'Pitcher-friendly zone'},
            'CB Bucknor': {'multiplier': 0.88, 'reason': 'Wide zone helps pitchers'},
            'Ron Kulpa': {'multiplier': 1.05, 'reason': 'Hitter-friendly calls'},
            'Pat Hoberg': {'multiplier': 1.02, 'reason': 'Consistent, slight hitter edge'},
            # Default for unknown umpires
            'DEFAULT': {'multiplier': 1.0, 'reason': 'No significant bias'}
        }
        
        # Create dummy umpire data - in real implementation, scrape from rotowire/ESPN
        games = ['BAL@HOU', 'STL@ARI', 'WSH@PHI', 'NYY@COL', 'LAD@MIL']
        umpire_data = []
        
        for game in games:
            umpire_name = 'DEFAULT'  # Would be scraped from rotowire
            impact = umpire_impacts.get(umpire_name, umpire_impacts['DEFAULT'])
            
            umpire_data.append({
                'game': game,
                'umpire': umpire_name,
                'scoring_multiplier': impact['multiplier'],
                'recommendation': 'NEUTRAL' if impact['multiplier'] == 1.0 else ('AVOID' if impact['multiplier'] < 0.95 else 'TARGET'),
                'reason': impact['reason']
            })
        
        self.data_sources['umpire_data'] = pd.DataFrame(umpire_data)
        logger.info(f"📋 Generated basic umpire analysis for {len(umpire_data)} games")
    
    def load_weather_data(self):
        """Load weather data with scoring impacts"""
        try:
            weather_files = [f for f in os.listdir("../data") if 'weather' in f.lower() and f.endswith('.csv')]
            
            if weather_files:
                latest_weather = max([os.path.join("../data", f) for f in weather_files], key=os.path.getmtime)
                self.data_sources['weather_data'] = pd.read_csv(latest_weather)
                logger.info(f"✅ Weather Data: {os.path.basename(latest_weather)}")
            else:
                logger.warning("⚠️ No weather data found")
                
        except Exception as e:
            logger.error(f"❌ Error loading weather data: {e}")
    
    def load_ownership_data(self):
        """Load ownership projections"""
        try:
            data_dir = "../data"
            ownership_files = [f for f in os.listdir(data_dir) if 'ownership' in f.lower() and f.endswith('.csv')]
            
            if ownership_files:
                latest_ownership = max([os.path.join(data_dir, f) for f in ownership_files], key=os.path.getmtime)
                self.data_sources['ownership_data'] = pd.read_csv(latest_ownership)
                logger.info(f"✅ Ownership Data: {os.path.basename(latest_ownership)}")
            else:
                logger.warning("⚠️ No ownership data found")
                
        except Exception as e:
            logger.error(f"❌ Error loading ownership data: {e}")
    
    def load_slate_data(self):
        """Load current slate data"""
        try:
            # Prefer clean slate (injuries removed)
            slate_paths = [
                "../fd_current_slate/fd_slate_today_clean.csv",
                "../fd_current_slate/fd_slate_today.csv"
            ]
            
            for path in slate_paths:
                if os.path.exists(path):
                    self.data_sources['slate_data'] = pd.read_csv(path)
                    clean_indicator = " (clean)" if "clean" in path else ""
                    logger.info(f"✅ Slate Data: {os.path.basename(path)}{clean_indicator} ({len(self.data_sources['slate_data'])} players)")
                    break
            else:
                logger.error("❌ No slate data found")
                
        except Exception as e:
            logger.error(f"❌ Error loading slate data: {e}")
    
    def load_injury_data(self):
        """Load injury reports"""
        try:
            injury_files = [f for f in os.listdir("../data") if 'injur' in f.lower() and f.endswith('.csv')]
            
            if injury_files:
                latest_injury = max([os.path.join("../data", f) for f in injury_files], key=os.path.getmtime)
                self.data_sources['injury_data'] = pd.read_csv(latest_injury)
                logger.info(f"✅ Injury Data: {os.path.basename(latest_injury)}")
            else:
                logger.warning("⚠️ No injury data found")
                
        except Exception as e:
            logger.error(f"❌ Error loading injury data: {e}")
    
    def validate_data_completeness(self):
        """Check which data sources are available"""
        available = sum(1 for source in self.data_sources.values() if source is not None)
        total = len(self.data_sources)
        
        logger.info(f"📊 DATA COMPLETENESS: {available}/{total} sources loaded")
        
        for source_name, data in self.data_sources.items():
            status = "✅" if data is not None else "❌"
            logger.info(f"   {status} {source_name}")
        
        return available >= 3  # Minimum viable data
    
    def generate_unified_recommendations(self):
        """Generate unified recommendations considering ALL factors"""
        logger.info("\n🧠 GENERATING UNIFIED RECOMMENDATIONS")
        logger.info("=" * 50)
        
        if self.data_sources['stack_analysis'] is None:
            logger.error("❌ Cannot generate recommendations without stack analysis")
            return {}
        
        unified_teams = []
        
        for _, stack in self.data_sources['stack_analysis'].iterrows():
            team = stack['team']
            
            # Start with base stack score
            base_score = stack.get('stack_value_score', 0)
            
            # Apply additional factors
            unified_score = base_score
            warnings = []
            boosts = []
            
            # 1. Umpire impact
            umpire_mult = self.get_umpire_multiplier(team)
            unified_score *= umpire_mult
            if umpire_mult < 0.95:
                warnings.append(f"Umpire concern ({umpire_mult:.2f}x)")
            elif umpire_mult > 1.05:
                boosts.append(f"Umpire boost ({umpire_mult:.2f}x)")
            
            # 2. Weather impact (already in stack analysis, but double-check)
            weather_mult = stack.get('weather_multiplier', 1.0)
            if weather_mult < 0.95:
                warnings.append(f"Weather concern ({weather_mult:.2f}x)")
            elif weather_mult > 1.05:
                boosts.append(f"Weather boost ({weather_mult:.2f}x)")
            
            # 3. Ownership considerations
            ownership_mult = self.get_ownership_multiplier(team)
            if ownership_mult < 0.9:
                warnings.append(f"High ownership ({ownership_mult:.2f}x)")
            elif ownership_mult > 1.1:
                boosts.append(f"Low ownership edge ({ownership_mult:.2f}x)")
            
            # 4. Injury impact
            injury_mult = self.get_injury_multiplier(team)
            unified_score *= injury_mult
            if injury_mult < 0.95:
                warnings.append(f"Key injuries ({injury_mult:.2f}x)")
            
            # Generate final recommendation
            if unified_score >= base_score * 1.1:
                recommendation = "ELITE TARGET"
            elif unified_score >= base_score * 1.05:
                recommendation = "GOOD PLAY"
            elif unified_score <= base_score * 0.9:
                recommendation = "AVOID"
            elif warnings:
                recommendation = "PROCEED WITH CAUTION"
            else:
                recommendation = "NEUTRAL"
            
            unified_teams.append({
                'team': team,
                'base_score': base_score,
                'unified_score': unified_score,
                'recommendation': recommendation,
                'score_change': f"{((unified_score/base_score - 1) * 100):+.1f}%",
                'boosts': ' | '.join(boosts) if boosts else 'None',
                'warnings': ' | '.join(warnings) if warnings else 'None',
                'opposing_pitcher': stack.get('opposing_pitcher', 'Unknown'),
                'game_total': stack.get('team_total', 0),
                'final_rank': 0  # Will be set after sorting
            })
        
        # Sort by unified score and assign final ranks
        unified_teams.sort(key=lambda x: x['unified_score'], reverse=True)
        for i, team in enumerate(unified_teams):
            team['final_rank'] = i + 1
        
        self.unified_recommendations = {
            'teams': unified_teams,
            'top_plays': [t for t in unified_teams if t['recommendation'] in ['ELITE TARGET', 'GOOD PLAY']],
            'avoid_games': [t for t in unified_teams if t['recommendation'] == 'AVOID'],
            'generated_at': datetime.now().isoformat()
        }
        
        return self.unified_recommendations
    
    def get_umpire_multiplier(self, team):
        """Get umpire multiplier for team's game"""
        if self.data_sources['umpire_data'] is None:
            return 1.0
        
        # Find team's game in umpire data
        umpire_df = self.data_sources['umpire_data']
        team_games = umpire_df[umpire_df['game'].str.contains(team, case=False)]
        
        if not team_games.empty:
            return team_games.iloc[0]['scoring_multiplier']
        
        return 1.0  # Default if not found
    
    def get_ownership_multiplier(self, team):
        """Calculate ownership multiplier (lower = more owned = worse for GPP)"""
        if self.data_sources['ownership_data'] is None:
            return 1.0
        
        ownership_df = self.data_sources['ownership_data']
        if 'team' in ownership_df.columns and 'ownership' in ownership_df.columns:
            team_ownership = ownership_df[ownership_df['team'] == team]
            if not team_ownership.empty:
                avg_ownership = team_ownership['ownership'].mean()
                # Convert ownership % to multiplier (high ownership = penalty)
                if avg_ownership > 20:
                    return 0.85  # Heavy penalty for high ownership
                elif avg_ownership > 15:
                    return 0.90  # Moderate penalty
                elif avg_ownership < 5:
                    return 1.15  # Bonus for very low ownership
                elif avg_ownership < 10:
                    return 1.10  # Moderate bonus
        
        return 1.0  # Neutral if no data
    
    def get_injury_multiplier(self, team):
        """Calculate injury impact multiplier"""
        if self.data_sources['injury_data'] is None:
            return 1.0
        
        # Check for key injuries affecting team
        injury_df = self.data_sources['injury_data']
        if 'team' in injury_df.columns:
            team_injuries = injury_df[injury_df['team'] == team]
            if not team_injuries.empty:
                # Simple implementation - reduce score for any injuries
                return 0.95
        
        return 1.0  # No injury impact
    
    def save_unified_recommendations(self):
        """Save unified recommendations for dashboard consumption"""
        if not self.unified_recommendations:
            logger.warning("No unified recommendations to save")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save detailed analysis
        output_file = f"../data/unified_recommendations_{timestamp}.json"
        with open(output_file, 'w') as f:
            json.dump(self.unified_recommendations, f, indent=2)
        
        # Save CSV for easy dashboard integration
        teams_df = pd.DataFrame(self.unified_recommendations['teams'])
        csv_file = f"../data/unified_team_analysis_{timestamp}.csv"
        teams_df.to_csv(csv_file, index=False)
        
        logger.info(f"💾 Unified recommendations saved:")
        logger.info(f"   JSON: {os.path.basename(output_file)}")
        logger.info(f"   CSV: {os.path.basename(csv_file)}")
        
        return output_file, csv_file
    
    def print_recommendation_summary(self):
        """Print summary of unified recommendations"""
        if not self.unified_recommendations:
            logger.warning("No recommendations available")
            return
        
        teams = self.unified_recommendations['teams']
        
        print(f"\n🎯 UNIFIED MLB RECOMMENDATIONS")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        print("🏆 TOP PLAYS:")
        for team in self.unified_recommendations['top_plays'][:3]:
            print(f"  {team['final_rank']}. {team['team']} vs {team['opposing_pitcher']}")
            print(f"     Score: {team['base_score']:.2f} → {team['unified_score']:.2f} ({team['score_change']})")
            print(f"     {team['recommendation']}: {team['boosts'] if team['boosts'] != 'None' else 'Solid fundamentals'}")
            print()
        
        avoid_teams = self.unified_recommendations['avoid_games']
        if avoid_teams:
            print("❌ AVOID:")
            for team in avoid_teams:
                print(f"  {team['team']}: {team['warnings']}")
            print()
        
        print("📊 FULL RANKINGS:")
        for team in teams:
            status_icon = "🎯" if team['recommendation'] in ['ELITE TARGET', 'GOOD PLAY'] else "⚠️" if team['recommendation'] == 'AVOID' else "➖"
            print(f"  {status_icon} {team['final_rank']}. {team['team']}: {team['unified_score']:.2f} ({team['recommendation']})")

def main():
    """Run unified analysis"""
    engine = UnifiedMLBDecisionEngine()
    
    # Load all data sources
    if engine.load_all_data_sources():
        # Generate unified recommendations
        recommendations = engine.generate_unified_recommendations()
        
        if recommendations:
            # Print summary
            engine.print_recommendation_summary()
            
            # Save for dashboard
            engine.save_unified_recommendations()
            
            print(f"\n✅ UNIFIED ANALYSIS COMPLETE")
            print("Your dashboard will now show integrated recommendations!")
        else:
            print("❌ Failed to generate recommendations")
    else:
        print("❌ Insufficient data sources for analysis")

if __name__ == "__main__":
    main()
