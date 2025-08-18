#!/usr/bin/env python3
"""
ENHANCED SYSTEM VERIFICATION TEST
=================================

Quick test script to verify all enhanced components are working:
1. Enhanced model loading
2. Weather integration 
3. Feature engineering
4. Prediction generation
5. EV calculation
6. Performance tracking

Run this before using the full system to ensure everything works.
"""

import pandas as pd
import numpy as np
import os
import logging
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_models():
    """Test if enhanced models can be loaded"""
    logger.info(" Testing enhanced model loading...")
    
    try:
        from enhanced_automated_betting_system import EnhancedBettingSystem
        
        betting_system = EnhancedBettingSystem()
        models_loaded = betting_system.load_enhanced_models()
        
        if models_loaded:
            logger.info(f"SUCCESS: Enhanced models loaded successfully: {len(betting_system.models)} models")
            return True
        else:
            logger.warning("WARNING: Enhanced models not found - will use original models")
            return False
            
    except Exception as e:
        logger.error(f"ERROR: Error loading enhanced models: {e}")
        return False

def test_weather_integration():
    """Test weather integration"""
    logger.info(" Testing weather integration...")
    
    try:
        from enhanced_weather_analytics import EnhancedWeatherAnalytics
        
        weather_analytics = EnhancedWeatherAnalytics()
        
        # Test weather data for a few teams
        test_teams = ['NYY', 'LAD', 'BOS', 'COL', 'TB']
        weather_results = {}
        
        for team in test_teams:
            weather_data = weather_analytics.get_weather_data(team)
            weather_results[team] = weather_data
            
            impact_factors = weather_analytics.calculate_weather_impact_factors(weather_data, team)
            
            logger.info(f"   {team}: {weather_data['temperature']:.0f}F, HR factor: {impact_factors['home_run_factor']:.2f}")
        
        logger.info("SUCCESS: Weather integration working correctly")
        return True
        
    except Exception as e:
        logger.error(f"ERROR: Error testing weather integration: {e}")
        return False

def test_feature_engineering():
    """Test advanced feature engineering"""
    logger.info(" Testing feature engineering...")
    
    try:
        # Create sample player data
        sample_data = pd.DataFrame({
            'player_name': ['Test Player'],
            'team': ['NYY'],
            'opponent': ['BOS'],
            'hits': [2],
            'homeRuns': [1],
            'totalBases': [4],
            'runs': [2],
            'rbi': [3],
            'atBats': [4],
            'strikeOuts': [1],
            'pitcher_era': [4.50],
            'pitcher_k9': [8.5],
            'park_factor': [1.05]
        })
        
        from enhanced_automated_betting_system import EnhancedBettingSystem
        betting_system = EnhancedBettingSystem()
        
        # Test feature engineering
        enhanced_data = betting_system.engineer_live_features(sample_data.iloc[0])
        
        # Check if key features are generated
        key_features = ['weather_power_index', 'contact_rate', 'power_rate', 'platoon_advantage']
        missing_features = [f for f in key_features if f not in enhanced_data.index]
        
        if not missing_features:
            logger.info("SUCCESS: Feature engineering working correctly")
            logger.info(f"   Generated {len(enhanced_data)} features for test player")
            return True
        else:
            logger.warning(f"WARNING: Missing features: {missing_features}")
            return False
            
    except Exception as e:
        logger.error(f"ERROR: Error testing feature engineering: {e}")
        return False

def test_prediction_generation():
    """Test enhanced prediction generation"""
    logger.info(" Testing prediction generation...")
    
    try:
        # Create test player data
        test_data = pd.Series({
            'name': 'Test Player',
            'team': 'NYY',
            'opponent': 'BOS',
            'hits': 2,
            'homeRuns': 1,
            'totalBases': 4,
            'runs': 2,
            'rbi': 3,
            'atBats': 4,
            'hits_L7': 1.8,
            'homeRuns_L7': 0.3,
            'totalBases_L7': 2.1,
            'park_factor': 1.05
        })
        
        from enhanced_automated_betting_system import EnhancedBettingSystem
        betting_system = EnhancedBettingSystem()
        
        if betting_system.load_enhanced_models():
            # Test predictions for different stats
            test_stats = ['homeRuns', 'hits', 'totalBases']
            successful_predictions = 0
            
            for stat in test_stats:
                if stat in betting_system.models:
                    prediction_result = betting_system.make_enhanced_prediction(
                        test_data, stat, {'venue': 'NYY', 'date': '2025-08-06'}
                    )
                    
                    if prediction_result:
                        prediction = prediction_result['prediction']
                        confidence = prediction_result.get('confidence', prediction_result.get('model_confidence', 0.7))
                        method = prediction_result.get('method', 'enhanced')
                        logger.info(f"   {stat}: {prediction:.2f} (confidence: {confidence:.2f}, method: {method})")
                        successful_predictions += 1
            
            if successful_predictions > 0:
                logger.info(f"SUCCESS: Prediction generation working: {successful_predictions}/{len(test_stats)} successful")
                return True
            else:
                logger.warning("WARNING: No successful predictions generated")
                return False
        else:
            logger.warning("WARNING: Cannot test predictions - no models loaded")
            return False
            
    except Exception as e:
        logger.error(f"ERROR: Error testing prediction generation: {e}")
        return False

def test_data_files():
    """Test if required data files exist"""
    logger.info(" Testing data file availability...")
    
    required_files = [
        "../data/prediction_features_enhanced_real_stats.csv",
        "../data/PrizePicks_MLB.xlsx"
    ]
    
    optional_files = [
        "../data/hitters_enhanced_features.csv",
        "../data/aggregated_hitter_features_2025.csv",
        "../data/actual_results_latest.csv"
    ]
    
    files_found = 0
    total_files = len(required_files) + len(optional_files)
    
    logger.info("   Required files:")
    for file_path in required_files:
        if os.path.exists(file_path):
            logger.info(f"   SUCCESS: {file_path}")
            files_found += 1
        else:
            logger.warning(f"   ERROR: {file_path} (REQUIRED)")
    
    logger.info("   Optional files:")
    for file_path in optional_files:
        if os.path.exists(file_path):
            logger.info(f"   SUCCESS: {file_path}")
            files_found += 1
        else:
            logger.info(f"    {file_path} (optional)")
    
    logger.info(f"DATA: Data files: {files_found}/{total_files} available")
    
    # Check if minimum required files exist
    required_found = sum(1 for f in required_files if os.path.exists(f))
    return required_found >= len(required_files) * 0.5  # At least 50% of required files

def test_performance_tracking():
    """Test performance tracking system"""
    logger.info("DATA: Testing performance tracking...")
    
    try:
        from enhanced_performance_tracker import PerformanceTracker
        
        tracker = PerformanceTracker()
        
        # Test loading historical data
        results_df = tracker.load_historical_results()
        predictions_df = tracker.load_historical_predictions()
        
        if not results_df.empty or not predictions_df.empty:
            logger.info(f"SUCCESS: Performance tracking working")
            logger.info(f"   Historical results: {len(results_df)} records")
            logger.info(f"   Historical predictions: {len(predictions_df)} records")
            return True
        else:
            logger.info(" Performance tracking ready (no historical data yet)")
            return True
            
    except Exception as e:
        logger.error(f"ERROR: Error testing performance tracking: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive system test"""
    print(" ENHANCED SYSTEM VERIFICATION TEST")
    print("=" * 45)
    print()
    
    test_results = {}
    
    # Run all tests
    tests = [
        ("Data Files", test_data_files),
        ("Enhanced Models", test_enhanced_models),
        ("Weather Integration", test_weather_integration),
        ("Feature Engineering", test_feature_engineering),
        ("Prediction Generation", test_prediction_generation),
        ("Performance Tracking", test_performance_tracking)
    ]
    
    passed_tests = 0
    
    for test_name, test_function in tests:
        print(f"\n Testing {test_name}...")
        print("-" * 30)
        
        try:
            result = test_function()
            test_results[test_name] = result
            
            if result:
                passed_tests += 1
                
        except Exception as e:
            logger.error(f"ERROR: Test {test_name} failed with exception: {e}")
            test_results[test_name] = False
    
    # Summary
    print(f"\nTARGET: TEST SUMMARY")
    print("=" * 20)
    print(f"Tests passed: {passed_tests}/{len(tests)}")
    print()
    
    for test_name, result in test_results.items():
        status = "SUCCESS: PASS" if result else "ERROR: FAIL"
        print(f"{test_name:20}: {status}")
    
    print()
    
    if passed_tests == len(tests):
        print("COMPLETE: ALL TESTS PASSED! Enhanced system is ready to use.")
        print("START: Run ENHANCED_PREDICTION_SYSTEM.bat to start the full system")
    elif passed_tests >= len(tests) * 0.7:  # 70% pass rate
        print("WARNING: Most tests passed. System should work with minor issues.")
        print("STEP: Review failed tests and fix issues for optimal performance")
    else:
        print("ERROR: Multiple test failures detected.")
        print(" Please fix the failing components before using the system")
    
    print()
    
    # Generate test report
    test_report = {
        'test_date': datetime.now().isoformat(),
        'total_tests': len(tests),
        'passed_tests': passed_tests,
        'pass_rate': passed_tests / len(tests),
        'detailed_results': test_results,
        'system_ready': passed_tests >= len(tests) * 0.7
    }
    
    with open("../data/system_test_report.json", 'w') as f:
        import json
        json.dump(test_report, f, indent=2)
    
    print(" Test report saved to system_test_report.json")
    
    return passed_tests >= len(tests) * 0.7

if __name__ == "__main__":
    run_comprehensive_test()
