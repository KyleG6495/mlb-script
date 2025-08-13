#!/usr/bin/env python3
"""
🎯 ELITE MLB SYSTEM LAUNCHER
Quick launcher for the Elite MLB Orchestrator
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ELITE_MLB_ORCHESTRATOR import EliteMLBOrchestrator, EliteSystemConfig

async def main():
    print("🎯 LAUNCHING ELITE MLB SYSTEM")
    print("=" * 50)
    
    # Create elite configuration
    config = EliteSystemConfig(
        tournament_bankroll=1000.0,
        prop_bankroll=500.0,
        max_entries=150,
        risk_tolerance="aggressive"
    )
    
    # Initialize orchestrator
    orchestrator = EliteMLBOrchestrator(config)
    
    # Execute elite pipeline
    results = await orchestrator.run_elite_pipeline()
    
    print("\n🎯 ELITE SYSTEM EXECUTION COMPLETE")
    print(f"⏱️ Total Time: {results['execution_time']:.2f} seconds")
    print("📊 Check the elite report for detailed results")
    
    return results

if __name__ == "__main__":
    asyncio.run(main())
