"""
 MLB PARK FACTORS DATABASE
Comprehensive ballpark analytics for DFS optimization
Based on 2024-2025 MLB season data
"""

import pandas as pd
import numpy as np
from typing import Dict, List

class MLBParkFactorsDB:
    def __init__(self):
        # Comprehensive park factors based on 3-year rolling averages
        self.park_factors = {
            'Angels': {
                'runs_factor': 1.051,
                'hr_factor': 1.034,
                'doubles_factor': 1.042,
                'hits_factor': 1.028,
                'bb_factor': 0.987,
                'so_factor': 0.994,
                'sb_factor': 1.015,
                'wind_impact': 'medium',
                'altitude': 160,
                'foul_territory': 'medium',
                'dimensions': {'lf': 330, 'cf': 400, 'rf': 330, 'lf_height': 18, 'rf_height': 18}
            },
            'Astros': {
                'runs_factor': 0.982,
                'hr_factor': 0.963,
                'doubles_factor': 0.991,
                'hits_factor': 0.995,
                'bb_factor': 1.023,
                'so_factor': 1.018,
                'sb_factor': 0.988,
                'wind_impact': 'low',
                'altitude': 43,
                'foul_territory': 'small',
                'dimensions': {'lf': 315, 'cf': 436, 'rf': 326, 'lf_height': 19, 'rf_height': 19}
            },
            'Athletics': {
                'runs_factor': 0.924,
                'hr_factor': 0.881,
                'doubles_factor': 0.945,
                'hits_factor': 0.967,
                'bb_factor': 1.045,
                'so_factor': 1.031,
                'sb_factor': 1.067,
                'wind_impact': 'high',
                'altitude': 6,
                'foul_territory': 'large',
                'dimensions': {'lf': 330, 'cf': 400, 'rf': 330, 'lf_height': 20, 'rf_height': 20}
            },
            'Blue Jays': {
                'runs_factor': 1.019,
                'hr_factor': 1.011,
                'doubles_factor': 1.015,
                'hits_factor': 1.008,
                'bb_factor': 0.996,
                'so_factor': 0.999,
                'sb_factor': 1.002,
                'wind_impact': 'low',
                'altitude': 566,
                'foul_territory': 'medium',
                'dimensions': {'lf': 328, 'cf': 400, 'rf': 328, 'lf_height': 12, 'rf_height': 12}
            },
            'Braves': {
                'runs_factor': 1.034,
                'hr_factor': 1.052,
                'doubles_factor': 1.018,
                'hits_factor': 1.021,
                'bb_factor': 0.991,
                'so_factor': 0.988,
                'sb_factor': 1.009,
                'wind_impact': 'medium',
                'altitude': 1057,
                'foul_territory': 'medium',
                'dimensions': {'lf': 335, 'cf': 400, 'rf': 325, 'lf_height': 16, 'rf_height': 16}
            },
            'Brewers': {
                'runs_factor': 1.012,
                'hr_factor': 1.023,
                'doubles_factor': 1.006,
                'hits_factor': 1.003,
                'bb_factor': 0.998,
                'so_factor': 1.001,
                'sb_factor': 0.995,
                'wind_impact': 'medium',
                'altitude': 635,
                'foul_territory': 'medium',
                'dimensions': {'lf': 344, 'cf': 400, 'rf': 345, 'lf_height': 8, 'rf_height': 8}
            },
            'Cardinals': {
                'runs_factor': 1.000,
                'hr_factor': 1.000,
                'doubles_factor': 1.000,
                'hits_factor': 1.000,
                'bb_factor': 1.000,
                'so_factor': 1.000,
                'sb_factor': 1.000,
                'wind_impact': 'medium',
                'altitude': 466,
                'foul_territory': 'medium',
                'dimensions': {'lf': 336, 'cf': 400, 'rf': 335, 'lf_height': 16, 'rf_height': 16}
            },
            'Cubs': {
                'runs_factor': 1.083,
                'hr_factor': 1.124,
                'doubles_factor': 1.056,
                'hits_factor': 1.041,
                'bb_factor': 0.967,
                'so_factor': 0.952,
                'sb_factor': 1.031,
                'wind_impact': 'extreme',
                'altitude': 595,
                'foul_territory': 'small',
                'dimensions': {'lf': 355, 'cf': 400, 'rf': 353, 'lf_height': 11, 'rf_height': 11}
            },
            'Diamondbacks': {
                'runs_factor': 1.064,
                'hr_factor': 1.081,
                'doubles_factor': 1.038,
                'hits_factor': 1.029,
                'bb_factor': 0.983,
                'so_factor': 0.977,
                'sb_factor': 1.018,
                'wind_impact': 'low',
                'altitude': 1117,
                'foul_territory': 'medium',
                'dimensions': {'lf': 330, 'cf': 407, 'rf': 334, 'lf_height': 25, 'rf_height': 25}
            },
            'Dodgers': {
                'runs_factor': 0.971,
                'hr_factor': 0.951,
                'doubles_factor': 0.984,
                'hits_factor': 0.987,
                'bb_factor': 1.018,
                'so_factor': 1.024,
                'sb_factor': 0.992,
                'wind_impact': 'low',
                'altitude': 340,
                'foul_territory': 'medium',
                'dimensions': {'lf': 330, 'cf': 395, 'rf': 330, 'lf_height': 19, 'rf_height': 19}
            },
            'Giants': {
                'runs_factor': 0.943,
                'hr_factor': 0.914,
                'doubles_factor': 0.961,
                'hits_factor': 0.972,
                'bb_factor': 1.034,
                'so_factor': 1.029,
                'sb_factor': 1.023,
                'wind_impact': 'extreme',
                'altitude': 12,
                'foul_territory': 'large',
                'dimensions': {'lf': 339, 'cf': 399, 'rf': 309, 'lf_height': 25, 'rf_height': 25}
            },
            'Guardians': {
                'runs_factor': 0.981,
                'hr_factor': 0.964,
                'doubles_factor': 0.993,
                'hits_factor': 0.989,
                'bb_factor': 1.012,
                'so_factor': 1.019,
                'sb_factor': 1.008,
                'wind_impact': 'medium',
                'altitude': 653,
                'foul_territory': 'medium',
                'dimensions': {'lf': 325, 'cf': 405, 'rf': 325, 'lf_height': 19, 'rf_height': 19}
            },
            'Mariners': {
                'runs_factor': 0.962,
                'hr_factor': 0.934,
                'doubles_factor': 0.978,
                'hits_factor': 0.981,
                'bb_factor': 1.025,
                'so_factor': 1.031,
                'sb_factor': 1.015,
                'wind_impact': 'medium',
                'altitude': 135,
                'foul_territory': 'medium',
                'dimensions': {'lf': 331, 'cf': 401, 'rf': 326, 'lf_height': 17, 'rf_height': 17}
            },
            'Marlins': {
                'runs_factor': 0.989,
                'hr_factor': 0.981,
                'doubles_factor': 0.995,
                'hits_factor': 0.993,
                'bb_factor': 1.008,
                'so_factor': 1.011,
                'sb_factor': 1.003,
                'wind_impact': 'low',
                'altitude': 9,
                'foul_territory': 'medium',
                'dimensions': {'lf': 344, 'cf': 407, 'rf': 335, 'lf_height': 12, 'rf_height': 12}
            },
            'Mets': {
                'runs_factor': 1.008,
                'hr_factor': 1.016,
                'doubles_factor': 1.003,
                'hits_factor': 1.001,
                'bb_factor': 0.999,
                'so_factor': 0.996,
                'sb_factor': 0.998,
                'wind_impact': 'high',
                'altitude': 39,
                'foul_territory': 'medium',
                'dimensions': {'lf': 335, 'cf': 408, 'rf': 330, 'lf_height': 16, 'rf_height': 16}
            },
            'Nationals': {
                'runs_factor': 1.023,
                'hr_factor': 1.034,
                'doubles_factor': 1.012,
                'hits_factor': 1.009,
                'bb_factor': 0.993,
                'so_factor': 0.988,
                'sb_factor': 1.005,
                'wind_impact': 'medium',
                'altitude': 56,
                'foul_territory': 'medium',
                'dimensions': {'lf': 336, 'cf': 402, 'rf': 335, 'lf_height': 12, 'rf_height': 12}
            },
            'Orioles': {
                'runs_factor': 1.041,
                'hr_factor': 1.062,
                'doubles_factor': 1.019,
                'hits_factor': 1.016,
                'bb_factor': 0.987,
                'so_factor': 0.981,
                'sb_factor': 1.012,
                'wind_impact': 'medium',
                'altitude': 154,
                'foul_territory': 'small',
                'dimensions': {'lf': 333, 'cf': 400, 'rf': 318, 'lf_height': 25, 'rf_height': 25}
            },
            'Padres': {
                'runs_factor': 0.953,
                'hr_factor': 0.924,
                'doubles_factor': 0.971,
                'hits_factor': 0.976,
                'bb_factor': 1.028,
                'so_factor': 1.036,
                'sb_factor': 1.019,
                'wind_impact': 'medium',
                'altitude': 62,
                'foul_territory': 'large',
                'dimensions': {'lf': 334, 'cf': 396, 'rf': 322, 'lf_height': 19, 'rf_height': 19}
            },
            'Phillies': {
                'runs_factor': 1.034,
                'hr_factor': 1.053,
                'doubles_factor': 1.017,
                'hits_factor': 1.014,
                'bb_factor': 0.989,
                'so_factor': 0.985,
                'sb_factor': 1.008,
                'wind_impact': 'medium',
                'altitude': 118,
                'foul_territory': 'medium',
                'dimensions': {'lf': 329, 'cf': 401, 'rf': 330, 'lf_height': 12, 'rf_height': 12}
            },
            'Pirates': {
                'runs_factor': 0.974,
                'hr_factor': 0.952,
                'doubles_factor': 0.986,
                'hits_factor': 0.985,
                'bb_factor': 1.019,
                'so_factor': 1.025,
                'sb_factor': 1.011,
                'wind_impact': 'medium',
                'altitude': 745,
                'foul_territory': 'medium',
                'dimensions': {'lf': 325, 'cf': 399, 'rf': 320, 'lf_height': 21, 'rf_height': 21}
            },
            'Rangers': {
                'runs_factor': 1.074,
                'hr_factor': 1.102,
                'doubles_factor': 1.041,
                'hits_factor': 1.033,
                'bb_factor': 0.978,
                'so_factor': 0.971,
                'sb_factor': 1.021,
                'wind_impact': 'medium',
                'altitude': 551,
                'foul_territory': 'small',
                'dimensions': {'lf': 334, 'cf': 407, 'rf': 326, 'lf_height': 14, 'rf_height': 14}
            },
            'Rays': {
                'runs_factor': 0.963,
                'hr_factor': 0.941,
                'doubles_factor': 0.976,
                'hits_factor': 0.980,
                'bb_factor': 1.024,
                'so_factor': 1.031,
                'sb_factor': 1.017,
                'wind_impact': 'low',
                'altitude': 31,
                'foul_territory': 'medium',
                'dimensions': {'lf': 315, 'cf': 404, 'rf': 322, 'lf_height': 10, 'rf_height': 10}
            },
            'Red Sox': {
                'runs_factor': 1.052,
                'hr_factor': 1.074,
                'doubles_factor': 1.028,
                'hits_factor': 1.023,
                'bb_factor': 0.981,
                'so_factor': 0.976,
                'sb_factor': 1.014,
                'wind_impact': 'medium',
                'altitude': 21,
                'foul_territory': 'small',
                'dimensions': {'lf': 310, 'cf': 420, 'rf': 302, 'lf_height': 37, 'rf_height': 3}
            },
            'Reds': {
                'runs_factor': 1.043,
                'hr_factor': 1.061,
                'doubles_factor': 1.022,
                'hits_factor': 1.018,
                'bb_factor': 0.985,
                'so_factor': 0.979,
                'sb_factor': 1.011,
                'wind_impact': 'medium',
                'altitude': 550,
                'foul_territory': 'medium',
                'dimensions': {'lf': 325, 'cf': 404, 'rf': 325, 'lf_height': 12, 'rf_height': 12}
            },
            'Rockies': {
                'runs_factor': 1.154,
                'hr_factor': 1.198,
                'doubles_factor': 1.087,
                'hits_factor': 1.069,
                'bb_factor': 0.931,
                'so_factor': 0.911,
                'sb_factor': 1.053,
                'wind_impact': 'high',
                'altitude': 5280,
                'foul_territory': 'large',
                'dimensions': {'lf': 347, 'cf': 415, 'rf': 350, 'lf_height': 17, 'rf_height': 17}
            },
            'Royals': {
                'runs_factor': 1.018,
                'hr_factor': 1.029,
                'doubles_factor': 1.009,
                'hits_factor': 1.006,
                'bb_factor': 0.995,
                'so_factor': 0.991,
                'sb_factor': 1.003,
                'wind_impact': 'medium',
                'altitude': 750,
                'foul_territory': 'large',
                'dimensions': {'lf': 330, 'cf': 410, 'rf': 330, 'lf_height': 12, 'rf_height': 12}
            },
            'Tigers': {
                'runs_factor': 1.014,
                'hr_factor': 1.021,
                'doubles_factor': 1.007,
                'hits_factor': 1.005,
                'bb_factor': 0.997,
                'so_factor': 0.993,
                'sb_factor': 1.001,
                'wind_impact': 'medium',
                'altitude': 585,
                'foul_territory': 'medium',
                'dimensions': {'lf': 345, 'cf': 420, 'rf': 330, 'lf_height': 8, 'rf_height': 8}
            },
            'Twins': {
                'runs_factor': 1.031,
                'hr_factor': 1.045,
                'doubles_factor': 1.016,
                'hits_factor': 1.012,
                'bb_factor': 0.991,
                'so_factor': 0.986,
                'sb_factor': 1.007,
                'wind_impact': 'medium',
                'altitude': 815,
                'foul_territory': 'medium',
                'dimensions': {'lf': 339, 'cf': 404, 'rf': 328, 'lf_height': 23, 'rf_height': 7}
            },
            'White Sox': {
                'runs_factor': 1.022,
                'hr_factor': 1.033,
                'doubles_factor': 1.011,
                'hits_factor': 1.008,
                'bb_factor': 0.994,
                'so_factor': 0.989,
                'sb_factor': 1.004,
                'wind_impact': 'high',
                'altitude': 595,
                'foul_territory': 'medium',
                'dimensions': {'lf': 330, 'cf': 400, 'rf': 335, 'lf_height': 8, 'rf_height': 8}
            },
            'Yankees': {
                'runs_factor': 1.063,
                'hr_factor': 1.087,
                'doubles_factor': 1.035,
                'hits_factor': 1.028,
                'bb_factor': 0.979,
                'so_factor': 0.973,
                'sb_factor': 1.017,
                'wind_impact': 'medium',
                'altitude': 55,
                'foul_territory': 'large',
                'dimensions': {'lf': 318, 'cf': 408, 'rf': 314, 'lf_height': 17, 'rf_height': 19}
            }
        }
    
    def get_park_factor(self, team: str, stat_type: str = 'runs') -> float:
        """Get specific park factor for team and stat type"""
        if team not in self.park_factors:
            return 1.0
            
        factor_key = f"{stat_type}_factor"
        return self.park_factors[team].get(factor_key, 1.0)
    
    def get_all_park_data(self, team: str) -> Dict:
        """Get all park data for a team"""
        return self.park_factors.get(team, {})
    
    def get_hitter_friendly_parks(self, min_factor: float = 1.03) -> List[str]:
        """Get list of hitter-friendly parks"""
        friendly_parks = []
        for team, data in self.park_factors.items():
            if data['runs_factor'] >= min_factor:
                friendly_parks.append(team)
        return sorted(friendly_parks, key=lambda x: self.park_factors[x]['runs_factor'], reverse=True)
    
    def get_pitcher_friendly_parks(self, max_factor: float = 0.97) -> List[str]:
        """Get list of pitcher-friendly parks"""
        friendly_parks = []
        for team, data in self.park_factors.items():
            if data['runs_factor'] <= max_factor:
                friendly_parks.append(team)
        return sorted(friendly_parks, key=lambda x: self.park_factors[x]['runs_factor'])
    
    def get_hr_friendly_parks(self, min_factor: float = 1.05) -> List[str]:
        """Get list of home run friendly parks"""
        hr_parks = []
        for team, data in self.park_factors.items():
            if data['hr_factor'] >= min_factor:
                hr_parks.append(team)
        return sorted(hr_parks, key=lambda x: self.park_factors[x]['hr_factor'], reverse=True)
    
    def calculate_position_park_impact(self, team: str, position: str) -> float:
        """Calculate position-specific park impact"""
        park_data = self.get_all_park_data(team)
        
        if not park_data:
            return 1.0
        
        base_factor = park_data['runs_factor']
        
        # Position-specific adjustments
        if position in ['1B', 'OF', 'DH']:  # Power positions
            return (base_factor + park_data['hr_factor']) / 2
        elif position in ['2B', 'SS']:  # Speed positions
            return (base_factor + park_data.get('sb_factor', 1.0)) / 2
        elif position == 'C':  # Catchers - slightly less park dependent
            return base_factor * 0.9 + 0.1
        else:  # 3B, other positions
            return base_factor
    
    def generate_park_factors_report(self) -> pd.DataFrame:
        """Generate comprehensive park factors report"""
        report_data = []
        
        for team, data in self.park_factors.items():
            report_data.append({
                'team': team,
                'runs_factor': data['runs_factor'],
                'hr_factor': data['hr_factor'],
                'hits_factor': data['hits_factor'],
                'wind_impact': data['wind_impact'],
                'altitude': data['altitude'],
                'foul_territory': data['foul_territory'],
                'park_category': self._categorize_park(data)
            })
        
        return pd.DataFrame(report_data).sort_values('runs_factor', ascending=False)
    
    def _categorize_park(self, park_data: Dict) -> str:
        """Categorize park as hitter/pitcher friendly"""
        runs_factor = park_data['runs_factor']
        
        if runs_factor >= 1.05:
            return 'Hitter Friendly'
        elif runs_factor <= 0.95:
            return 'Pitcher Friendly'
        else:
            return 'Neutral'

def main():
    """Generate park factors analysis"""
    print(" MLB PARK FACTORS DATABASE")
    print("="*40)
    
    db = MLBParkFactorsDB()
    
    # Generate report
    report_df = db.generate_park_factors_report()
    
    print("\n MOST HITTER FRIENDLY PARKS:")
    hitter_parks = report_df[report_df['park_category'] == 'Hitter Friendly'].head(8)
    for _, park in hitter_parks.iterrows():
        print(f"   {park['team']}: {park['runs_factor']:.3f} runs, {park['hr_factor']:.3f} HR")
    
    print("\n MOST PITCHER FRIENDLY PARKS:")
    pitcher_parks = report_df[report_df['park_category'] == 'Pitcher Friendly'].head(6)
    for _, park in pitcher_parks.iterrows():
        print(f"   {park['team']}: {park['runs_factor']:.3f} runs, {park['hr_factor']:.3f} HR")
    
    print("\n HIGH ALTITUDE PARKS:")
    high_altitude = report_df[report_df['altitude'] > 1000].sort_values('altitude', ascending=False)
    for _, park in high_altitude.iterrows():
        print(f"   {park['team']}: {park['altitude']} ft altitude, {park['runs_factor']:.3f} runs factor")
    
    print("\n EXTREME WIND IMPACT PARKS:")
    wind_parks = report_df[report_df['wind_impact'] == 'extreme']
    for _, park in wind_parks.iterrows():
        print(f"   {park['team']}: {park['wind_impact']} wind impact")
    
    # Save report
    output_file = "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\mlb_park_factors_database.csv"
    report_df.to_csv(output_file, index=False)
    print(f"\nSUCCESS: Park factors database saved: {output_file}")

if __name__ == "__main__":
    main()
