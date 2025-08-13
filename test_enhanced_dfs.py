#!/usr/bin/env python3
"""
Enhanced DFS Test Script
=======================

Quick test to validate the enhanced DFS simulation system works correctly.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dfs_game_simulator import DFSSimulationEngine, BaseballSimulator
from enhance_dfs_projections import DFSDataIntegrator
from enhanced_lineup_optimizer import EnhancedLineupOptimizer

def create_mock_data():
    """Create mock data for testing"""
    
    # Create mock FanDuel slate
    mock_slate = pd.DataFrame({
        'Id': range(1, 21),
        'First Name': ['Mike', 'John', 'Steve', 'Dave', 'Chris', 'Matt', 'Ryan', 'Jake', 'Tom', 'Alex'] * 2,
        'Last Name': ['Smith', 'Jones', 'Davis', 'Wilson', 'Brown', 'Taylor', 'Clark', 'White', 'Hall', 'Young'] * 2,
        'Position': ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'OF', 'C', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'OF', 'C'],
        'Team': ['NYY'] * 10 + ['BOS'] * 10,
        'Salary': np.random.randint(4000, 12000, 20),
        'FPPG': np.random.uniform(6, 16, 20)
    })
    
    # Save mock data
    os.makedirs("../data", exist_ok=True)
    mock_slate.to_csv("../data/fd_slate_today.csv", index=False)
    
    # Create mock projected scores
    mock_projections = pd.DataFrame({
        'player_id': range(1, 21),
        'name': [f"{row['First Name']} {row['Last Name']}" for _, row in mock_slate.iterrows()],
        'position': mock_slate['Position'],
        'team': mock_slate['Team'],
        'salary': mock_slate['Salary'],
        'mean_fppg': mock_slate['FPPG'],
        'floor_fppg': mock_slate['FPPG'] * 0.6,
        'ceiling_fppg': mock_slate['FPPG'] * 1.5,
        'value_mean': mock_slate['FPPG'] / (mock_slate['Salary'] / 1000)
    })
    
    mock_projections.to_csv("../data/dfs_projections_for_optimizer.csv", index=False)
    
    print("✅ Created mock data files")

def test_baseball_simulator():
    """Test the core baseball simulator"""
    
    print("🔧 Testing Baseball Simulator...")
    
    simulator = BaseballSimulator()
    
    # Create mock lineups
    away_lineup = [
        {'player_id': '1', 'name': 'Player 1', 'position': 'OF', 
         'strikeout_rate': 0.25, 'walk_rate': 0.10, 'home_run_rate': 0.03}
        for i in range(9)
    ]
    
    home_lineup = [
        {'player_id': str(i+10), 'name': f'Player {i+10}', 'position': 'OF',
         'strikeout_rate': 0.20, 'walk_rate': 0.08, 'home_run_rate': 0.025}
        for i in range(9)
    ]
    
    away_pitcher = {'pitcher_k_rate': 0.28, 'pitcher_bb_rate': 0.09}
    home_pitcher = {'pitcher_k_rate': 0.24, 'pitcher_bb_rate': 0.08}
    
    # Run single game simulation
    try:
        results = simulator.simulate_full_game(away_lineup, home_lineup, away_pitcher, home_pitcher)
        
        total_fppg = sum(player.calculate_fppg() for player in results.values())
        print(f"   ✅ Game simulation successful")
        print(f"   📊 Total FPPG generated: {total_fppg:.1f}")
        print(f"   👥 Players simulated: {len(results)}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Game simulation failed: {e}")
        return False

def test_data_integration():
    """Test the data integration layer"""
    
    print("🔧 Testing Data Integration...")
    
    try:
        integrator = DFSDataIntegrator("../data")
        slate_data = integrator.load_todays_slate()
        
        if slate_data and slate_data.get('games'):
            print(f"   ✅ Data integration successful")
            print(f"   🎮 Games loaded: {len(slate_data['games'])}")
            print(f"   👥 Players loaded: {len(slate_data['players'])}")
            return True
        else:
            print("   ❌ No slate data loaded")
            return False
            
    except Exception as e:
        print(f"   ❌ Data integration failed: {e}")
        return False

def test_lineup_optimizer():
    """Test the lineup optimizer"""
    
    print("🔧 Testing Lineup Optimizer...")
    
    try:
        optimizer = EnhancedLineupOptimizer("../data/dfs_projections_for_optimizer.csv")
        df = optimizer.load_projections()
        
        if df.empty:
            print("   ❌ No projection data loaded")
            return False
        
        # Test single lineup optimization
        lineup = optimizer.optimize_lineup(df, contest_type='cash')
        
        if lineup and 'players' in lineup:
            print(f"   ✅ Lineup optimization successful")
            print(f"   👥 Players in lineup: {len(lineup['players'])}")
            print(f"   💰 Total salary: ${lineup['total_salary']:,}")
            print(f"   📊 Projected points: {lineup['projected_points']:.1f}")
            return True
        else:
            print("   ❌ Lineup optimization failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Lineup optimizer failed: {e}")
        return False

def run_mini_simulation():
    """Run a mini version of the full simulation"""
    
    print("🔧 Testing Mini Simulation Pipeline...")
    
    try:
        integrator = DFSDataIntegrator("../data")
        
        # Run with very few simulations for speed
        projections = integrator.run_enhanced_projections(n_simulations=10)
        
        if not projections.empty:
            print(f"   ✅ Mini simulation successful")
            print(f"   📊 Enhanced projections for {len(projections)} players")
            print(f"   🎯 Average projected FPPG: {projections['mean_fppg'].mean():.2f}")
            return True
        else:
            print("   ❌ Mini simulation failed - no projections")
            return False
            
    except Exception as e:
        print(f"   ❌ Mini simulation failed: {e}")
        return False

def main():
    """Run all tests"""
    
    print("🚀 ENHANCED DFS SYSTEM TEST")
    print("=" * 50)
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Create test data
    create_mock_data()
    
    tests = [
        ("Baseball Simulator", test_baseball_simulator),
        ("Data Integration", test_data_integration),
        ("Lineup Optimizer", test_lineup_optimizer),
        ("Mini Simulation", run_mini_simulation)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}")
        print("-" * 30)
        results[test_name] = test_func()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Enhanced DFS system is ready to use.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the errors above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
