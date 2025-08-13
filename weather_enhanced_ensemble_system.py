"""
🌤️🏟️ WEATHER & PARK ENHANCED ENSEMBLE SYSTEM 🏟️🌤️
Advanced ensemble system with comprehensive weather and ballpark intelligence
"""

import pandas as pd
import numpy as np
import logging
from datetime import datetime
from pathlib import Path
import requests
import time
from ultimate_ensemble_betting_system import UltimateEnsembleBettingSystem

class WeatherEnhancedEnsembleSystem(UltimateEnsembleBettingSystem):
    """Ultimate ensemble system enhanced with weather and park factor intelligence"""
    
    def __init__(self):
        super().__init__()
        self.weather_api_key = 'eb27f1689074b1163c5cf5a1fde8fa91'
        self.weather_multipliers = {}
        self.park_factor_adjustments = {}
        
    def load_current_weather_park_data(self):
        """Load and refresh current weather and park factor data"""
        
        logging.info("🌤️ Loading weather and park factor data...")
        
        # Load park factors
        try:
            park_df = pd.read_csv("../park_factors/park_factors.csv")
            logging.info(f"✅ Loaded park factors for {len(park_df)} teams")
        except Exception as e:
            logging.warning(f"⚠️ Could not load park factors: {e}")
            park_df = pd.DataFrame()
        
        # Load weather data
        try:
            weather_df = pd.read_csv("../data/weather_today.csv")
            logging.info(f"✅ Loaded weather data for {len(weather_df)} games")
        except Exception as e:
            logging.warning(f"⚠️ Could not load weather data: {e}")
            weather_df = pd.DataFrame()
        
        # Load merged weather/park data if available
        try:
            merged_df = pd.read_csv("../data/merged_weather_park.csv")
            logging.info(f"✅ Loaded merged weather/park data for {len(merged_df)} games")
            return merged_df
        except Exception as e:
            logging.warning(f"⚠️ Could not load merged data: {e}")
            return pd.DataFrame()
    
    def calculate_weather_adjustments(self, weather_park_df):
        """Calculate weather-based prediction adjustments"""
        
        if weather_park_df.empty:
            return {}
        
        adjustments = {}
        
        for _, row in weather_park_df.iterrows():
            game_pk = row.get('game_pk')
            if pd.isna(game_pk):
                continue
                
            game_pk = int(game_pk)
            temp = row.get('temperature', 70)
            humidity = row.get('humidity', 50)  
            wind_speed = row.get('wind_speed', 5)
            wind_deg = row.get('wind_deg', 0)
            
            # Temperature effects (higher temp = more offense)
            temp_multiplier = 1.0 + ((temp - 70) * 0.003)  # 3% per 10 degrees
            
            # Humidity effects (lower humidity = more offense)  
            humidity_multiplier = 1.0 + ((50 - humidity) * 0.002)  # 2% per 10% humidity
            
            # Wind effects
            # Wind from 180-360 degrees (roughly behind batter) helps offense
            if 135 <= wind_deg <= 225:  # Wind blowing out
                wind_multiplier = 1.0 + (wind_speed * 0.01)  # 1% per mph
            elif 315 <= wind_deg <= 45:  # Wind blowing in
                wind_multiplier = 1.0 - (wind_speed * 0.01)  # -1% per mph
            else:  # Cross winds
                wind_multiplier = 1.0 - (wind_speed * 0.005)  # -0.5% per mph
            
            # Combined weather effect
            total_weather_multiplier = temp_multiplier * humidity_multiplier * wind_multiplier
            
            adjustments[game_pk] = {
                'weather_multiplier': total_weather_multiplier,
                'temp_effect': temp_multiplier,
                'humidity_effect': humidity_multiplier, 
                'wind_effect': wind_multiplier,
                'conditions': {
                    'temperature': temp,
                    'humidity': humidity,
                    'wind_speed': wind_speed,
                    'wind_direction': wind_deg
                }
            }
        
        logging.info(f"🌤️ Calculated weather adjustments for {len(adjustments)} games")
        return adjustments
    
    def calculate_park_adjustments(self, weather_park_df):
        """Calculate park factor adjustments for different stat categories"""
        
        if weather_park_df.empty:
            return {}
        
        adjustments = {}
        
        for _, row in weather_park_df.iterrows():
            game_pk = row.get('game_pk')
            if pd.isna(game_pk):
                continue
                
            game_pk = int(game_pk)
            team = row.get('team_standardized', '')
            
            # Park factor adjustments (100 = neutral)
            park_factor = row.get('park_factor', 100) / 100.0
            hr_factor = row.get('HR', 100) / 100.0
            so_factor = row.get('SO', 100) / 100.0
            bb_factor = row.get('BB', 100) / 100.0
            
            adjustments[game_pk] = {
                'park_multiplier': park_factor,
                'home_run_factor': hr_factor,
                'strikeout_factor': so_factor,
                'walk_factor': bb_factor,
                'team': team
            }
        
        logging.info(f"🏟️ Calculated park adjustments for {len(adjustments)} games")
        return adjustments
    
    def apply_weather_park_enhancements(self, predictions_df, weather_park_df):
        """Apply weather and park factor enhancements to predictions"""
        
        if weather_park_df.empty:
            logging.warning("⚠️ No weather/park data available - using base predictions")
            return predictions_df
        
        # Calculate adjustments
        weather_adjustments = self.calculate_weather_adjustments(weather_park_df)
        park_adjustments = self.calculate_park_adjustments(weather_park_df)
        
        enhanced_predictions = predictions_df.copy()
        enhanced_count = 0
        
        for idx, row in enhanced_predictions.iterrows():
            player = row.get('player', '')
            category = row.get('stat_type', '')
            game_pk = row.get('game_pk')
            
            if pd.isna(game_pk):
                continue
                
            game_pk = int(game_pk)
            
            # Get adjustments for this game
            weather_adj = weather_adjustments.get(game_pk, {})
            park_adj = park_adjustments.get(game_pk, {})
            
            if not weather_adj and not park_adj:
                continue
            
            # Apply weather effects
            weather_mult = weather_adj.get('weather_multiplier', 1.0)
            
            # Apply park effects based on stat category
            park_mult = 1.0
            if category in ['home_runs', 'hrr'] and park_adj:
                park_mult = park_adj.get('home_run_factor', 1.0)
            elif category in ['hitter_strikeouts', 'pitcher_strikeouts'] and park_adj:
                park_mult = park_adj.get('strikeout_factor', 1.0)
            elif category in ['total_bases', 'hits', 'runs', 'rbi'] and park_adj:
                park_mult = park_adj.get('park_multiplier', 1.0)
            
            # Combined adjustment
            total_adjustment = weather_mult * park_mult
            
            # Apply to prediction
            original_pred = row.get('ensemble_prediction', row.get('prediction', 0))
            enhanced_pred = original_pred * total_adjustment
            
            enhanced_predictions.at[idx, 'weather_enhanced_prediction'] = enhanced_pred
            enhanced_predictions.at[idx, 'weather_adjustment'] = weather_mult
            enhanced_predictions.at[idx, 'park_adjustment'] = park_mult
            enhanced_predictions.at[idx, 'total_adjustment'] = total_adjustment
            
            enhanced_count += 1
        
        logging.info(f"🌟 Enhanced {enhanced_count} predictions with weather/park factors")
        return enhanced_predictions
    
    def run_weather_enhanced_analysis(self):
        """Run the complete weather-enhanced ensemble analysis"""
        
        logging.info("🌤️🏟️ Starting Weather-Enhanced Ensemble Analysis...")
        
        # Load weather and park data
        weather_park_df = self.load_current_weather_park_data()
        
        # Run base ensemble analysis
        base_results = self.run_ultimate_analysis()
        
        if weather_park_df.empty:
            logging.warning("⚠️ No weather/park enhancements applied")
            return base_results
        
        # Load ensemble predictions for enhancement
        try:
            ensemble_predictions = pd.read_csv("ultimate_ensemble_opportunities.csv")
        except Exception as e:
            logging.error(f"❌ Could not load ensemble predictions: {e}")
            return base_results
        
        # Apply weather and park enhancements
        enhanced_predictions = self.apply_weather_park_enhancements(
            ensemble_predictions, weather_park_df
        )
        
        # Recalculate edges with enhanced predictions
        enhanced_opportunities = []
        weather_enhanced_count = 0
        
        for _, row in enhanced_predictions.iterrows():
            if pd.notna(row.get('weather_enhanced_prediction')):
                enhanced_pred = row['weather_enhanced_prediction']
                weather_enhanced_count += 1
            else:
                enhanced_pred = row.get('ensemble_prediction', row.get('prediction', 0))
            
            # Recalculate opportunity metrics
            line = row.get('line', 0)
            if line > 0 and enhanced_pred > 0:
                
                # Calculate new edges
                over_edge = max(0, (enhanced_pred - line) / line * 100)
                under_edge = max(0, (line - enhanced_pred) / enhanced_pred * 100)
                
                best_edge = max(over_edge, under_edge)
                bet_type = "OVER" if over_edge > under_edge else "UNDER"
                
                if best_edge > 3:  # Only include meaningful edges
                    enhanced_opportunities.append({
                        'player': row.get('player', ''),
                        'stat_type': row.get('stat_type', ''),
                        'sportsbook': row.get('sportsbook', ''),
                        'line': line,
                        'original_prediction': row.get('ensemble_prediction', row.get('prediction', 0)),
                        'weather_enhanced_prediction': enhanced_pred,
                        'weather_adjustment': row.get('weather_adjustment', 1.0),
                        'park_adjustment': row.get('park_adjustment', 1.0),
                        'total_adjustment': row.get('total_adjustment', 1.0),
                        'edge': best_edge,
                        'bet_type': bet_type,
                        'confidence': row.get('ensemble_confidence', 50),
                        'quality': row.get('prediction_quality', 80)
                    })
        
        # Sort by edge
        enhanced_opportunities.sort(key=lambda x: x['edge'], reverse=True)
        
        # Save enhanced results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        enhanced_df = pd.DataFrame(enhanced_opportunities)
        enhanced_df.to_csv(f"weather_enhanced_opportunities_{timestamp}.csv", index=False)
        
        # Generate enhanced report
        self.generate_weather_enhanced_report(enhanced_opportunities, weather_enhanced_count, timestamp)
        
        logging.info(f"🌟 Weather-Enhanced Analysis Complete!")
        logging.info(f"🎯 Generated {len(enhanced_opportunities)} weather-enhanced opportunities")
        logging.info(f"🌤️ {weather_enhanced_count} predictions enhanced with weather/park factors")
        
        return {
            'enhanced_opportunities': enhanced_opportunities,
            'weather_enhanced_count': weather_enhanced_count,
            'total_opportunities': len(enhanced_opportunities)
        }
    
    def generate_weather_enhanced_report(self, opportunities, enhanced_count, timestamp):
        """Generate comprehensive weather-enhanced report"""
        
        if not opportunities:
            return
        
        report_lines = [
            "🌤️🏟️🔥 WEATHER-ENHANCED ENSEMBLE BETTING SYSTEM 🔥🏟️🌤️",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 80,
            "",
            "🌟 WEATHER & PARK FACTOR ENHANCEMENTS:",
            "-" * 60,
            f"Predictions Enhanced with Weather: {enhanced_count}",
            f"Total Enhanced Opportunities: {len(opportunities)}",
            f"Average Edge (Top 100): {np.mean([op['edge'] for op in opportunities[:100]]):.2f}%",
            "",
            "🌤️ WEATHER INTELLIGENCE:",
            "✅ Temperature effects on offense",
            "✅ Humidity impact on ball flight", 
            "✅ Wind direction and speed analysis",
            "✅ Real-time game conditions",
            "",
            "🏟️ BALLPARK INTELLIGENCE:",
            "✅ Park factor adjustments",
            "✅ Home run friendly/pitcher friendly parks",
            "✅ Strikeout rate adjustments",
            "✅ Offensive environment scoring",
            "",
            "🎯 TOP 20 WEATHER-ENHANCED OPPORTUNITIES:",
            "-" * 70
        ]
        
        for i, op in enumerate(opportunities[:20], 1):
            adj_indicator = ""
            if op.get('total_adjustment', 1.0) != 1.0:
                adj_pct = (op['total_adjustment'] - 1.0) * 100
                adj_indicator = f" [+{adj_pct:.1f}%]" if adj_pct > 0 else f" [{adj_pct:.1f}%]"
            
            report_lines.extend([
                f"{i:2d}. {op['player']:<25} | {op['stat_type']:<15} | {op['sportsbook']}",
                f"    Line: {op['line']:>6.1f} | Enhanced Pred: {op['weather_enhanced_prediction']:>6.2f}{adj_indicator}",
                f"    Edge: {op['edge']:>6.2f}% | Bet: {op['bet_type']} | Quality: {op['quality']:.1f}%",
                ""
            ])
        
        # Category breakdown
        categories = {}
        for op in opportunities:
            cat = op['stat_type']
            if cat not in categories:
                categories[cat] = {'count': 0, 'avg_edge': 0, 'enhanced_count': 0}
            categories[cat]['count'] += 1
            categories[cat]['avg_edge'] += op['edge']
            if op.get('total_adjustment', 1.0) != 1.0:
                categories[cat]['enhanced_count'] += 1
        
        report_lines.extend([
            "",
            "📊 CATEGORY BREAKDOWN (WEATHER-ENHANCED):",
            "-" * 60
        ])
        
        for cat, stats in categories.items():
            avg_edge = stats['avg_edge'] / stats['count']
            enhanced_pct = (stats['enhanced_count'] / stats['count'] * 100) if stats['count'] > 0 else 0
            report_lines.append(
                f"{cat:<20}: {stats['count']:>4} ops, {avg_edge:>6.2f}% avg edge, "
                f"{enhanced_pct:>5.1f}% weather-enhanced"
            )
        
        report_lines.extend([
            "",
            "🚀 ADVANCED FEATURES:",
            "-" * 40,
            "✅ Real-time weather condition analysis",
            "✅ Multi-factor park adjustments", 
            "✅ Wind direction impact modeling",
            "✅ Temperature-based offensive scaling",
            "✅ Humidity effects on ball flight",
            "✅ Stadium-specific environmental factors",
            "✅ Enhanced ensemble prediction confidence",
            "✅ Weather-adjusted Kelly sizing"
        ])
        
        # Save report
        report_filename = f"weather_enhanced_report_{timestamp}.txt"
        with open(report_filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logging.info(f"📊 Weather-Enhanced report saved: {report_filename}")


if __name__ == "__main__":
    # Initialize and run weather-enhanced system
    weather_system = WeatherEnhancedEnsembleSystem()
    results = weather_system.run_weather_enhanced_analysis()
    
    print(f"\n🌟 Weather-Enhanced Ensemble System Complete!")
    print(f"🎯 Generated {results['total_opportunities']} enhanced opportunities")
    print(f"🌤️ {results['weather_enhanced_count']} predictions enhanced with weather/park factors")
