#!/usr/bin/env python3
"""
VISUAL DFS SYSTEM FLOWCHART
Creates a simple diagram showing how the Elite DFS System works
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, ConnectionPatch
import numpy as np

def create_dfs_flowchart():
    """Create a visual flowchart of the Elite DFS System"""
    
    # Create figure and axis
    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Define colors
    colors = {
        'input': '#E3F2FD',      # Light Blue
        'process': '#C8E6C9',    # Light Green  
        'output': '#FFF3E0',     # Light Orange
        'alert': '#FFEBEE',      # Light Red
        'success': '#E8F5E8'     # Success Green
    }
    
    # Title
    ax.text(5, 9.5, 'START: ELITE DFS SYSTEM WORKFLOW', 
           fontsize=20, fontweight='bold', ha='center',
           bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue'))
    
    # Step 1: Data Input
    step1 = FancyBboxPatch((0.5, 8), 2, 0.8, 
                          boxstyle="round,pad=0.1", 
                          facecolor=colors['input'], 
                          edgecolor='black')
    ax.add_patch(step1)
    ax.text(1.5, 8.4, 'DATA: DATA INPUT\nProjections + FanDuel', 
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Step 2: Ownership Projections
    step2 = FancyBboxPatch((4, 8), 2, 0.8,
                          boxstyle="round,pad=0.1",
                          facecolor=colors['process'],
                          edgecolor='black')
    ax.add_patch(step2)
    ax.text(5, 8.4, ' OWNERSHIP\nPROJECTIONS\n0.5%-50% Range',
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Step 3: Elite Lineups
    step3 = FancyBboxPatch((7.5, 8), 2, 0.8,
                          boxstyle="round,pad=0.1",
                          facecolor=colors['output'],
                          edgecolor='black')
    ax.add_patch(step3)
    ax.text(8.5, 8.4, 'LINEUP: ELITE LINEUPS\n5.1% Avg Ownership\n20+ Lineups',
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Step 4: Upload to FanDuel
    step4 = FancyBboxPatch((1.5, 6.5), 2, 0.8,
                          boxstyle="round,pad=0.1",
                          facecolor=colors['input'],
                          edgecolor='black')
    ax.add_patch(step4)
    ax.text(2.5, 6.9, ' UPLOAD TO\nFANDUEL\nLineup Submission',
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Step 5: Live Monitoring
    step5 = FancyBboxPatch((6, 6.5), 2, 0.8,
                          boxstyle="round,pad=0.1",
                          facecolor=colors['process'],
                          edgecolor='black')
    ax.add_patch(step5)
    ax.text(7, 6.9, ' LIVE MONITORING\nRotoWire + MLB API\n24/7 Watching',
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Alert System
    alert1 = FancyBboxPatch((0.5, 4.5), 1.8, 1.2,
                           boxstyle="round,pad=0.1",
                           facecolor=colors['alert'],
                           edgecolor='red', linewidth=2)
    ax.add_patch(alert1)
    ax.text(1.4, 5.1, ' EMERGENCY\nSWAP\nPlayer Scratched\nAuto Replace',
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    alert2 = FancyBboxPatch((3, 4.5), 1.8, 1.2,
                           boxstyle="round,pad=0.1",
                           facecolor=colors['alert'],
                           edgecolor='orange', linewidth=2)
    ax.add_patch(alert2)
    ax.text(3.9, 5.1, 'PROGRESS: CHALK ALERT\nOwnership Rising\nConsider Fade',
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    alert3 = FancyBboxPatch((5.5, 4.5), 1.8, 1.2,
                           boxstyle="round,pad=0.1",
                           facecolor=colors['alert'],
                           edgecolor='green', linewidth=2)
    ax.add_patch(alert3)
    ax.text(6.4, 5.1, ' LEVERAGE\nOPPORTUNITY\nLow Ownership\nHigh Upside',
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    alert4 = FancyBboxPatch((8, 4.5), 1.8, 1.2,
                           boxstyle="round,pad=0.1",
                           facecolor=colors['alert'],
                           edgecolor='blue', linewidth=2)
    ax.add_patch(alert4)
    ax.text(8.9, 5.1, 'SWAP: PRE-LOCK\nOPTIMIZATION\nFinal Checks\nRecommendations',
           ha='center', va='center', fontsize=9, fontweight='bold')
    
    # Final Results
    results = FancyBboxPatch((3.5, 2.5), 3, 1.2,
                            boxstyle="round,pad=0.1",
                            facecolor=colors['success'],
                            edgecolor='green', linewidth=3)
    ax.add_patch(results)
    ax.text(5, 3.1, 'COMPLETE: TOURNAMENT SUCCESS\n3-4x Lower Ownership\nHigher Ceiling Potential\nCompetitive Advantage',
           ha='center', va='center', fontsize=11, fontweight='bold')
    
    # Draw arrows
    arrows = [
        # Horizontal flow
        ((2.5, 8.4), (4, 8.4)),
        ((6, 8.4), (7.5, 8.4)),
        
        # Down from lineups to upload
        ((8.5, 8), (2.5, 7.3)),
        
        # From upload to monitoring
        ((3.5, 6.9), (6, 6.9)),
        
        # From monitoring to alerts
        ((7, 6.5), (1.4, 5.7)),
        ((7, 6.5), (3.9, 5.7)),
        ((7, 6.5), (6.4, 5.7)),
        ((7, 6.5), (8.9, 5.7)),
        
        # From alerts to results
        ((1.4, 4.5), (5, 3.7)),
        ((3.9, 4.5), (5, 3.7)),
        ((6.4, 4.5), (5, 3.7)),
        ((8.9, 4.5), (5, 3.7))
    ]
    
    for start, end in arrows:
        arrow = ConnectionPatch(start, end, "data", "data",
                              arrowstyle="->", shrinkA=5, shrinkB=5,
                              mutation_scale=20, fc="black", lw=2)
        ax.add_patch(arrow)
    
    # Add timeline
    ax.text(0.5, 1.5, ' TIMELINE:', fontsize=12, fontweight='bold')
    ax.text(0.5, 1.2, ' Morning: Build projections & lineups', fontsize=10)
    ax.text(0.5, 0.9, ' Afternoon: Upload to FanDuel, start monitoring', fontsize=10)
    ax.text(0.5, 0.6, ' Pre-Game: Intensive monitoring & late swaps', fontsize=10)
    ax.text(0.5, 0.3, ' Lock Time: Final optimization & recommendations', fontsize=10)
    
    # Add competitive advantage box
    advantage = FancyBboxPatch((7, 0.2), 2.8, 1.8,
                              boxstyle="round,pad=0.1",
                              facecolor='lightyellow',
                              edgecolor='gold', linewidth=2)
    ax.add_patch(advantage)
    ax.text(8.4, 1.1, 'LINEUP: YOUR EDGE\n\n 5.1% vs 15-20%\n  ownership\n Real-time alerts\n Pro automation\n Advanced analytics',
           ha='center', va='center', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('../data/DFS_System_Flowchart.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(" Visual flowchart created!")
    print(" Saved as: data/DFS_System_Flowchart.png")

if __name__ == "__main__":
    create_dfs_flowchart()
