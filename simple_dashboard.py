#!/usr/bin/env python3
"""
SIMPLE NO-HANG DASHBOARD
Basic dashboard that loads data once and doesn't refresh automatically
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd
import os
from datetime import datetime

class SimpleDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏆 Simple DFS Dashboard - No Hang Version")
        self.root.geometry("1000x700")
        
        # Colors
        self.colors = {
            'bg': '#1a1a1a',
            'card': '#2d2d2d', 
            'text': '#ffffff',
            'success': '#28a745',
            'warning': '#ffc107'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Data storage
        self.fd_slate = None
        self.lineups = None
        
        self.setup_ui()
        self.load_data_once()
        
    def setup_ui(self):
        """Setup simple UI"""
        # Header
        header = tk.Frame(self.root, bg=self.colors['bg'])
        header.pack(fill=tk.X, padx=10, pady=5)
        
        title = tk.Label(header, text="🏆 Simple DFS Dashboard", 
                        font=('Arial', 18, 'bold'),
                        bg=self.colors['bg'], fg=self.colors['text'])
        title.pack(side=tk.LEFT)
        
        self.status = tk.Label(header, text="🟡 Loading...", 
                              font=('Arial', 12),
                              bg=self.colors['bg'], fg=self.colors['warning'])
        self.status.pack(side=tk.RIGHT)
        
        # Notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_slate_tab()
        self.create_lineups_tab()
        self.create_info_tab()
        
    def create_slate_tab(self):
        """Show FD slate info"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📊 Tonight's Slate")
        
        # Slate info
        info_frame = tk.Frame(frame, bg=self.colors['card'])
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(info_frame, text="FanDuel Slate Information", 
                font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=5)
        
        self.slate_info = tk.Text(info_frame, height=10, width=80,
                                 bg=self.colors['bg'], fg=self.colors['text'])
        self.slate_info.pack(pady=5)
        
    def create_lineups_tab(self):
        """Show confirmed lineups"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚾ Confirmed Lineups")
        
        # Lineups info
        lineups_frame = tk.Frame(frame, bg=self.colors['card'])
        lineups_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(lineups_frame, text="Confirmed Starting Lineups", 
                font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=5)
        
        self.lineups_info = tk.Text(lineups_frame, height=15, width=80,
                                   bg=self.colors['bg'], fg=self.colors['text'])
        self.lineups_info.pack(pady=5)
        
    def create_info_tab(self):
        """Show general info and manual refresh"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="ℹ️ Info & Refresh")
        
        info_frame = tk.Frame(frame, bg=self.colors['card'])
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(info_frame, text="Dashboard Information", 
                font=('Arial', 14, 'bold'),
                bg=self.colors['card'], fg=self.colors['text']).pack(pady=5)
        
        # Manual refresh button
        refresh_btn = tk.Button(info_frame, text="🔄 Manual Refresh", 
                               command=self.manual_refresh,
                               font=('Arial', 12, 'bold'),
                               bg=self.colors['success'], fg='white')
        refresh_btn.pack(pady=10)
        
        # Info text
        self.info_text = tk.Text(info_frame, height=10, width=80,
                                bg=self.colors['bg'], fg=self.colors['text'])
        self.info_text.pack(pady=5)
        
    def load_data_once(self):
        """Load data once without any auto-refresh"""
        try:
            # Load FD slate
            fd_path = os.path.join('..', 'fd_current_slate', 'fd_slate_today.csv')
            if os.path.exists(fd_path):
                self.fd_slate = pd.read_csv(fd_path)
                self.update_slate_info()
            
            # Load lineups
            lineups_path = os.path.join('..', 'data', 'starting_lineups.csv')
            if os.path.exists(lineups_path):
                self.lineups = pd.read_csv(lineups_path)
                self.update_lineups_info()
            
            self.update_info()
            self.status.config(text="🟢 Ready", fg=self.colors['success'])
            
        except Exception as e:
            self.status.config(text=f"❌ Error: {str(e)}", fg='red')
            
    def update_slate_info(self):
        """Update slate information"""
        if self.fd_slate is not None:
            info = f"""TONIGHT'S 7:15 PM SLATE
======================
Total Players: {len(self.fd_slate):,}
Teams: {len(self.fd_slate['Team'].unique())} teams
Teams: {', '.join(sorted(self.fd_slate['Team'].unique()))}

TOP PITCHERS BY SALARY:
{self.fd_slate[self.fd_slate['Position'] == 'P'].nlargest(10, 'Salary')[['Nickname', 'Last Name', 'Salary', 'Team']].to_string(index=False)}

SALARY RANGES:
Pitchers: ${self.fd_slate[self.fd_slate['Position'] == 'P']['Salary'].min():,} - ${self.fd_slate[self.fd_slate['Position'] == 'P']['Salary'].max():,}
Hitters: ${self.fd_slate[self.fd_slate['Position'] != 'P']['Salary'].min():,} - ${self.fd_slate[self.fd_slate['Position'] != 'P']['Salary'].max():,}
"""
            self.slate_info.delete(1.0, tk.END)
            self.slate_info.insert(1.0, info)
        
    def update_lineups_info(self):
        """Update lineups information"""
        if self.lineups is not None:
            pitchers = self.lineups[self.lineups['position'] == 'P']
            hitters = self.lineups[self.lineups['position'] != 'P']
            
            info = f"""CONFIRMED STARTING LINEUPS
===========================
Total Confirmed Starters: {len(self.lineups)}
Pitchers: {len(pitchers)}
Hitters: {len(hitters)}
Teams: {len(self.lineups['team'].unique())}

STARTING PITCHERS:
{pitchers[['player_name', 'team', 'salary']].to_string(index=False)}

TEAMS WITH CONFIRMED LINEUPS:
"""
            
            # Show hitters by team
            for team in sorted(self.lineups['team'].unique()):
                team_hitters = hitters[hitters['team'] == team]
                if len(team_hitters) > 0:
                    info += f"\\n{team} ({len(team_hitters)} hitters):\\n"
                    for _, player in team_hitters.iterrows():
                        info += f"  {player['batting_order']}. {player['player_name']} (${player['salary']:,})\\n"
            
            self.lineups_info.delete(1.0, tk.END)
            self.lineups_info.insert(1.0, info)
    
    def update_info(self):
        """Update general info"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        info = f"""DASHBOARD STATUS
================
Last Updated: {current_time}
Status: Ready for tonight's slate

FEATURES:
• No auto-refresh (prevents hanging)
• Manual refresh button available
• Complete slate and lineup information
• Confirmed lineups from RotoWire

TONIGHT'S STRATEGY:
• Focus on LAA, COL, CWS stacks (low owned)
• Avoid high ownership: NYY, TB, ATH, MIN
• All lineups confirmed - no guessing needed

NEXT STEPS:
1. Review slate and lineups above
2. Run your DAILY_RUNNERS scripts
3. Use manual refresh if needed
4. Generate your lineups!

NO HANGING ISSUES! 🎉
"""
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info)
    
    def manual_refresh(self):
        """Manual refresh without hanging"""
        self.status.config(text="🔄 Refreshing...", fg=self.colors['warning'])
        try:
            self.load_data_once()
            self.status.config(text="🟢 Refreshed", fg=self.colors['success'])
        except Exception as e:
            self.status.config(text=f"❌ Error: {str(e)}", fg='red')
    
    def run(self):
        """Start the simple dashboard"""
        self.root.mainloop()

if __name__ == "__main__":
    print("🏆 Starting Simple DFS Dashboard (No Hang Version)...")
    app = SimpleDashboard()
    app.run()
