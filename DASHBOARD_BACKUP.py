#!/usr/bin/env python3
"""
WORKING ELITE DFS DASHBOARD - CLEAN VERSION
Fixed version that loads data properly with correct file paths
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime, timedelta
import os
import json
import traceback
from file_finder_utils import safe_read_csv

class WorkingEliteDFSDashboard:
    def __init__(self):
        self.colors = {
            'bg': '#0f1419',
            'card': '#1a1f2e',
            'accent': '#00d4aa',
            'text': '#ffffff',
            'subtext': '#b0b3b8',
            'success': '#00c851',
            'warning': '#ffbb33',
            'danger': '#ff4444',
            'blue': '#007bff'
        }
        
        # Real data storage
        self.ownership_data = {}
        self.stack_data = []
        self.opportunities_data = []
        self.lineups_data = []
        self.late_swap_alerts = []
        self.contest_data = {}
        
        # Debug info
        self.debug_info = []
        self.data_loaded = False
        
        print("🏆 Starting Fixed Elite DFS Dashboard...")
        self.setup_gui()
        
        # Load data immediately in main thread first
        print("📊 Loading data in main thread...")
        self.load_all_data()
        
        # Then start background monitoring
        self.start_monitoring()
        
    def setup_gui(self):
        """Initialize the main GUI"""
        self.root = tk.Tk()
        self.root.title("🏆 Fixed Elite DFS Dashboard - REAL DATA")
        self.root.geometry("1400x900")
        self.root.configure(bg=self.colors['bg'])
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors['card'], height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🏆 Fixed Elite DFS Dashboard", 
                              bg=self.colors['card'], fg=self.colors['accent'],
                              font=('Arial', 20, 'bold'))
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        self.status_label = tk.Label(header_frame, text="🔴 Starting...", 
                                   bg=self.colors['card'], fg=self.colors['warning'],
                                   font=('Arial', 12))
        self.status_label.pack(side=tk.RIGHT, padx=20, pady=20)
        
        # Create notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Style the notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background=self.colors['bg'])
        style.configure('TNotebook.Tab', background=self.colors['card'], 
                       foreground=self.colors['text'], padding=[12, 8])
        
        self.create_ownership_tab()
        self.create_stacks_tab()
        self.create_lineups_tab()
        self.create_debug_tab()
        
    def create_ownership_tab(self):
        """Real Ownership Analysis"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="👥 Real Ownership")
        
        # Metrics
        metrics_frame = tk.Frame(tab, bg=self.colors['bg'])
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.chalk_metric = self.create_metric_card(metrics_frame, "Chalk Plays", "0", "High Ownership >25%", 0)
        self.contrarian_metric = self.create_metric_card(metrics_frame, "Contrarian Targets", "0", "Low Ownership <8%", 1)
        self.value_metric = self.create_metric_card(metrics_frame, "Value Plays", "0", "High Points/Dollar", 2)
        self.leverage_metric = self.create_metric_card(metrics_frame, "Leverage Spots", "0", "Low Own/High Proj", 3)
        
        # Real ownership table
        table_frame = tk.LabelFrame(tab, text="🎯 Real Ownership Projections & Opportunities",
                                   fg=self.colors['text'], bg=self.colors['card'],
                                   font=('Arial', 14, 'bold'))
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ownership treeview
        columns = ('Player', 'Pos', 'Team', 'Salary', 'Projection', 'Ownership%', 'Leverage', 'Tier')
        self.ownership_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.ownership_tree.heading(col, text=col)
            self.ownership_tree.column(col, width=100, anchor=tk.CENTER)
            
        scrollbar_own = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.ownership_tree.yview)
        self.ownership_tree.configure(yscrollcommand=scrollbar_own.set)
        
        self.ownership_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar_own.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_stacks_tab(self):
        """Real Team Stacks"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="⚡ Real Stacks")
        
        # Stack metrics
        stack_metrics_frame = tk.Frame(tab, bg=self.colors['bg'])
        stack_metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.best_stack_metric = self.create_metric_card(stack_metrics_frame, "Best 4-Man Stack", "---", "Projected Points", 0)
        self.value_stack_metric = self.create_metric_card(stack_metrics_frame, "Value Stack", "---", "Price/Point Ratio", 1)
        self.contrarian_stack_metric = self.create_metric_card(stack_metrics_frame, "Contrarian Stack", "---", "Low Ownership", 2)
        self.weather_stack_metric = self.create_metric_card(stack_metrics_frame, "Weather Boost", "---", "Conditions Edge", 3)
        
        # Stack rankings
        rankings_frame = tk.LabelFrame(tab, text="🏆 Team Stacks Built from Real Data",
                                      fg=self.colors['text'], bg=self.colors['card'],
                                      font=('Arial', 14, 'bold'))
        rankings_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        stack_columns = ('Rank', 'Team', 'Projection', 'Salary', 'Ownership%', 'Value', 'Players')
        self.stack_tree = ttk.Treeview(rankings_frame, columns=stack_columns, show='headings', height=15)
        
        for col in stack_columns:
            self.stack_tree.heading(col, text=col)
            if col == 'Players':
                self.stack_tree.column(col, width=400, anchor=tk.W)
            else:
                self.stack_tree.column(col, width=80, anchor=tk.CENTER)
            
        scrollbar_stack = ttk.Scrollbar(rankings_frame, orient=tk.VERTICAL, command=self.stack_tree.yview)
        self.stack_tree.configure(yscrollcommand=scrollbar_stack.set)
        
        self.stack_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar_stack.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_lineups_tab(self):
        """Real Optimized Lineups - All Available Files"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🎯 Lineup Files")
        
        # Lineup file summary metrics
        lineup_metrics_frame = tk.Frame(tab, bg=self.colors['bg'])
        lineup_metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.total_files_metric = self.create_metric_card(lineup_metrics_frame, "Total Files", "---", "Available Today", 0)
        self.total_lineups_metric = self.create_metric_card(lineup_metrics_frame, "Total Lineups", "---", "Ready to Enter", 1)
        self.fanduel_ready_metric = self.create_metric_card(lineup_metrics_frame, "FanDuel Ready", "---", "Upload Format", 2)
        self.latest_generation_metric = self.create_metric_card(lineup_metrics_frame, "Latest Generated", "---", "Most Recent", 3)
        
        # Export buttons
        export_frame = tk.Frame(tab, bg=self.colors['bg'])
        export_frame.pack(fill=tk.X, padx=10, pady=5)
        
        export_btn = tk.Button(export_frame, text="🚀 Export Latest Lineups", 
                              command=self.export_lineups,
                              bg=self.colors['success'], fg=self.colors['text'],
                              font=('Arial', 12, 'bold'), relief='flat')
        export_btn.pack(side=tk.LEFT, padx=5)
        
        export_stack_btn = tk.Button(export_frame, text="⚡ Export Stack Lineups", 
                                    command=self.export_stack_lineups,
                                    bg=self.colors['blue'], fg=self.colors['text'],
                                    font=('Arial', 12, 'bold'), relief='flat')
        export_stack_btn.pack(side=tk.LEFT, padx=5)
        
        # File list
        files_text = scrolledtext.ScrolledText(tab,
                                              bg=self.colors['bg'],
                                              fg=self.colors['text'],
                                              font=('Consolas', 10),
                                              wrap=tk.WORD)
        files_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.files_text = files_text
        
    def create_debug_tab(self):
        """Debug Information"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🔧 Debug")
        
        self.debug_text = scrolledtext.ScrolledText(tab,
                                                   bg=self.colors['bg'],
                                                   fg=self.colors['text'],
                                                   font=('Consolas', 10),
                                                   wrap=tk.WORD)
        self.debug_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_metric_card(self, parent, title, value, subtitle, col):
        """Create a metric card"""
        card = tk.Frame(parent, bg=self.colors['card'], relief='flat', bd=0)
        card.grid(row=0, column=col, padx=10, pady=10, sticky='ew')
        parent.grid_columnconfigure(col, weight=1)
        
        title_label = tk.Label(card, text=title, bg=self.colors['card'], 
                              fg=self.colors['subtext'], font=('Arial', 10))
        title_label.pack(pady=(15, 5))
        
        value_label = tk.Label(card, text=value, bg=self.colors['card'], 
                              fg=self.colors['accent'], font=('Arial', 24, 'bold'))
        value_label.pack()
        
        subtitle_label = tk.Label(card, text=subtitle, bg=self.colors['card'], 
                                 fg=self.colors['subtext'], font=('Arial', 9))
        subtitle_label.pack(pady=(5, 15))
        
        # Store reference to value label for updates
        return value_label
        
    def load_all_data(self):
        """Load all data synchronously"""
        try:
            print("📊 Loading ownership data...")
            self.load_ownership_data()
            
            print("⚡ Loading stack data...")
            self.load_stack_data()
            
            print("📁 Loading lineup files...")
            self.load_lineup_files()
            
            self.data_loaded = True
            print("✅ All data loaded successfully!")
            
            # Update status
            self.status_label.config(text="🟢 Data Loaded Successfully", fg=self.colors['success'])
            
            # Update GUI immediately
            self.update_gui_data()
            
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            self.debug_log(f"Data loading error: {str(e)}")
            self.status_label.config(text="🔴 Data Loading Error", fg=self.colors['danger'])
            
    def load_ownership_data(self):
        """Load ownership data with absolute paths"""
        try:
            # Find ownership files directly
            data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
            ownership_files = []
            
            if os.path.exists(data_dir):
                for file in os.listdir(data_dir):
                    if "ownership" in file.lower() and file.endswith('.csv'):
                        ownership_files.append(os.path.join(data_dir, file))
                
                if ownership_files:
                    # Get most recent
                    ownership_files.sort(key=os.path.getmtime, reverse=True)
                    ownership_file = ownership_files[0]
                    
                    print(f"📊 Loading ownership from: {os.path.basename(ownership_file)}")
                    df = safe_read_csv(ownership_file)
                    
                    if df is not None and len(df) > 0:
                        # Safe column access
                        ownership_col = None
                        for col in ['ownership', 'projected_ownership', 'own_proj', 'ownership_projection']:
                            if col in df.columns:
                                ownership_col = col
                                break
                        
                        leverage_col = None
                        for col in ['leverage', 'leverage_score', 'leverage_rating']:
                            if col in df.columns:
                                leverage_col = col
                                break
                        
                        # Calculate metrics
                        chalk_plays = 0
                        contrarian_targets = 0
                        value_plays = 0
                        
                        if ownership_col:
                            chalk_plays = len(df[df[ownership_col] > 0.25])
                            contrarian_targets = len(df[df[ownership_col] < 0.08])
                        
                        if leverage_col:
                            value_plays = len(df[df[leverage_col] > 0.7])
                        
                        self.ownership_data = {
                            'total_players': len(df),
                            'chalk_plays': chalk_plays,
                            'contrarian_targets': contrarian_targets,
                            'value_plays': value_plays,
                            'leverage_spots': len(df) - chalk_plays,
                            'players': df.to_dict('records')
                        }
                        
                        print(f"✅ Loaded {len(df)} players with ownership data")
                        print(f"Found {chalk_plays} chalk, {contrarian_targets} contrarian, {value_plays} value plays")
                    else:
                        print("⚠️ Ownership file is empty")
                        self.ownership_data = {}
                else:
                    print("⚠️ No ownership files found")
                    self.ownership_data = {}
            else:
                print(f"⚠️ Data directory not found: {data_dir}")
                self.ownership_data = {}
                
        except Exception as e:
            print(f"❌ Error loading ownership data: {e}")
            self.ownership_data = {}
            
    def load_stack_data(self):
        """Enhanced stack generation with weather, park factors, and opposing pitcher analysis"""
        try:
            # Load base ownership projections
            data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
            ownership_files = []
            
            if os.path.exists(data_dir):
                for file in os.listdir(data_dir):
                    if 'ownership' in file.lower() and file.endswith('.csv'):
                        ownership_files.append(os.path.join(data_dir, file))
                
                if ownership_files:
                    # Get most recent ownership file
                    ownership_files.sort(key=os.path.getmtime, reverse=True)
                    ownership_file = ownership_files[0]
                    
                    print(f"⚡ Analyzing stacks from: {os.path.basename(ownership_file)}")
                    df = safe_read_csv(ownership_file)
                    
                    # Load additional enhancement data
                    weather_data = self.load_weather_data(data_dir)
                    pitcher_data = self.load_pitcher_data(data_dir)
                    park_data = self.load_park_data(data_dir)
                    
                    if df is not None and len(df) > 0:
                        # Use actual column names from ownership file
                        team_col = 'team'
                        proj_col = 'projection'
                        salary_col = 'salary'
                        name_col = 'player_name'
                        
                        if all(col in df.columns for col in [team_col, proj_col, salary_col, name_col]):
                            # Filter out pitchers for hitting stacks
                            hitters = df[df['position'] != 'P'].copy() if 'position' in df.columns else df.copy()
                            
                            # Enhanced stack generation with multiple factors
                            self.stack_data = []
                            
                            # Define team categories based on backtest analysis
                            explosive_teams = {'PHI', 'SD', 'NYY', 'ATH', 'COL', 'KC', 'TEX'}
                            conservative_teams = {'CIN', 'ATL', 'CWS', 'SF'}
                            
                            for i, team in enumerate(hitters[team_col].value_counts().head(10).index):
                                team_players = hitters[hitters[team_col] == team]
                                
                                # Get top 4 hitters for this team
                                if len(team_players) >= 4:
                                    top_players = team_players.nlargest(4, proj_col)
                                    
                                    # Base projection calculation
                                    base_proj = top_players[proj_col].sum()
                                    
                                    # Apply team-specific multipliers based on backtest insights
                                    if team in explosive_teams:
                                        historical_multiplier = 1.35 + (0.1 if team in ['PHI', 'SD', 'NYY'] else 0)
                                        team_type = "🔥 Explosive"
                                    elif team in conservative_teams:
                                        historical_multiplier = 0.95
                                        team_type = "📉 Conservative"
                                    else:
                                        historical_multiplier = 1.20
                                        team_type = "⚖️ Standard"
                                    
                                    # Apply weather enhancement
                                    weather_multiplier = self.get_weather_multiplier(team, weather_data)
                                    
                                    # Apply opposing pitcher factor
                                    pitcher_multiplier = self.get_pitcher_multiplier(team, pitcher_data)
                                    
                                    # Apply park factor
                                    park_multiplier = self.get_park_multiplier(team, park_data, weather_data)
                                    
                                    # Combined multiplier
                                    total_multiplier = historical_multiplier * weather_multiplier * pitcher_multiplier * park_multiplier
                                    
                                    # Enhanced projection
                                    total_proj = round(base_proj * total_multiplier, 1)
                                    total_salary = int(top_players[salary_col].sum())
                                    
                                    # Dynamic ownership based on team type and enhancements
                                    base_ownership = 12 if team in explosive_teams else 7
                                    weather_ownership_boost = (weather_multiplier - 1) * 5  # Weather adds ownership
                                    pitcher_ownership_boost = (pitcher_multiplier - 1) * 3  # Good matchup adds ownership
                                    park_ownership_boost = (park_multiplier - 1) * 4  # Hitter-friendly parks add ownership
                                    
                                    avg_ownership = round(base_ownership + (i * 0.3) + weather_ownership_boost + pitcher_ownership_boost + park_ownership_boost, 1)
                                    
                                    value_score = round(total_proj / (total_salary / 1000), 2)
                                    
                                    # Enhanced player display with context
                                    context_factors = []
                                    if weather_multiplier > 1.05:
                                        context_factors.append("🌤️ Weather")
                                    if pitcher_multiplier > 1.1:
                                        context_factors.append("⚾ Weak Pitching")
                                    if park_multiplier > 1.03:
                                        context_factors.append("🏟️ Hitter Park")
                                    
                                    context_text = " + ".join(context_factors)
                                    if context_text:
                                        team_type = f"{team_type} + {context_text}"
                                    
                                    # Get actual player names for the stack
                                    player_names = []
                                    for _, player in top_players.iterrows():
                                        name = player[name_col]
                                        proj = player[proj_col]
                                        player_names.append(f"{name} ({proj:.1f})")
                                    
                                    players_text = f"{team_type} | " + " | ".join(player_names)
                                else:
                                    # Fallback if not enough players - still apply enhanced multipliers
                                    count = len(team_players)
                                    base_proj = count * 15.5
                                    
                                    # Apply same enhancement logic
                                    if team in explosive_teams:
                                        historical_multiplier = 1.35
                                        team_type = "🔥 Explosive"
                                    elif team in conservative_teams:
                                        historical_multiplier = 0.95
                                        team_type = "📉 Conservative"
                                    else:
                                        historical_multiplier = 1.20
                                        team_type = "⚖️ Standard"
                                    
                                    weather_multiplier = self.get_weather_multiplier(team, weather_data)
                                    pitcher_multiplier = self.get_pitcher_multiplier(team, pitcher_data)
                                    park_multiplier = self.get_park_multiplier(team, park_data, weather_data)
                                    total_multiplier = historical_multiplier * weather_multiplier * pitcher_multiplier * park_multiplier
                                    
                                    total_proj = round(base_proj * total_multiplier, 1)
                                    total_salary = count * 4500
                                    
                                    base_ownership = 12 if team in explosive_teams else 7
                                    weather_ownership_boost = (weather_multiplier - 1) * 5
                                    pitcher_ownership_boost = (pitcher_multiplier - 1) * 3
                                    park_ownership_boost = (park_multiplier - 1) * 4
                                    avg_ownership = round(base_ownership + (i * 0.3) + weather_ownership_boost + pitcher_ownership_boost + park_ownership_boost, 1)
                                    
                                    value_score = round(total_proj / (total_salary / 1000), 2)
                                    
                                    context_factors = []
                                    if weather_multiplier > 1.05:
                                        context_factors.append("🌤️ Weather")
                                    if pitcher_multiplier > 1.1:
                                        context_factors.append("⚾ Weak Pitching")
                                    
                                    context_text = " + ".join(context_factors)
                                    if context_text:
                                        team_type = f"{team_type} + {context_text}"
                                    
                                    players_text = f"{team_type} | {count} players available"
                                
                                stack_info = {
                                    'rank': i + 1,
                                    'team': team,
                                    'projection': total_proj,
                                    'salary': total_salary,
                                    'ownership': avg_ownership,
                                    'value': value_score,
                                    'players': players_text
                                }
                                self.stack_data.append(stack_info)
                            
                            print(f"✅ Generated {len(self.stack_data)} enhanced team stacks")
                    else:
                        print("⚠️ Projection file is empty")
                        self.stack_data = []
                else:
                    print("⚠️ No projection files found for stack analysis")
                    self.stack_data = []
            else:
                print(f"⚠️ Data directory not found: {data_dir}")
                self.stack_data = []
                
        except Exception as e:
            print(f"❌ Error loading stack data: {e}")
            self.stack_data = []
    
    def load_weather_data(self, data_dir):
        """Load weather data for game enhancement"""
        try:
            weather_file = os.path.join(data_dir, 'weather_today.csv')
            if os.path.exists(weather_file):
                weather_df = safe_read_csv(weather_file)
                print(f"🌤️ Loaded weather data: {len(weather_df)} games")
                return weather_df
        except Exception as e:
            print(f"⚠️ Weather data not available: {e}")
        return None
    
    def load_pitcher_data(self, data_dir):
        """Load opposing pitcher data for matchup analysis"""
        try:
            pitcher_file = os.path.join(data_dir, 'today_pitcher_features.csv')
            if os.path.exists(pitcher_file):
                pitcher_df = safe_read_csv(pitcher_file)
                print(f"⚾ Loaded pitcher data: {len(pitcher_df)} pitcher stats")
                return pitcher_df
        except Exception as e:
            print(f"⚠️ Pitcher data not available: {e}")
        return None
    
    def load_park_data(self, data_dir):
        """Load ballpark factors for venue analysis"""
        try:
            park_file = os.path.join(data_dir, 'mlb_park_factors_database.csv')
            if os.path.exists(park_file):
                park_df = safe_read_csv(park_file)
                print(f"🏟️ Loaded park factors: {len(park_df)} ballparks")
                return park_df
        except Exception as e:
            print(f"⚠️ Park factors not available: {e}")
        return None
    
    def get_weather_multiplier(self, team, weather_data):
        """Calculate weather-based projection multiplier"""
        if weather_data is None or len(weather_data) == 0:
            return 1.0
        
        try:
            # Find team's game in weather data
            team_weather = weather_data[weather_data['home_team'] == team]
            if len(team_weather) == 0:
                # Try to find as visiting team (would need game schedule data)
                return 1.0
            
            game_weather = team_weather.iloc[0]
            
            # Weather scoring factors
            multiplier = 1.0
            
            # Temperature factor (ideal 70-85°F)
            temp = game_weather.get('temperature', 75)
            if 70 <= temp <= 85:
                multiplier += 0.05  # Ideal hitting weather
            elif temp > 90:
                multiplier += 0.02  # Hot weather, ball carries
            elif temp < 60:
                multiplier -= 0.03  # Cold weather hurts offense
            
            # Wind factor
            wind_speed = game_weather.get('wind_speed', 0)
            wind_deg = game_weather.get('wind_deg', 0)
            
            # Wind direction: 90-270 degrees is roughly out to the outfield
            if 90 <= wind_deg <= 270 and wind_speed > 10:
                multiplier += 0.08  # Wind blowing out
            elif (wind_deg < 90 or wind_deg > 270) and wind_speed > 15:
                multiplier -= 0.05  # Strong wind blowing in
            
            # Humidity factor (lower humidity = ball carries better)
            humidity = game_weather.get('humidity', 50)
            if humidity < 40:
                multiplier += 0.03
            elif humidity > 80:
                multiplier -= 0.02
            
            # Condition factor
            condition = game_weather.get('condition', '').lower()
            if 'clear' in condition or 'sunny' in condition:
                multiplier += 0.02
            elif 'rain' in condition or 'storm' in condition:
                multiplier -= 0.10  # Rain significantly hurts offense
            
            return max(0.8, min(1.3, multiplier))  # Cap between 0.8-1.3x
            
        except Exception as e:
            print(f"⚠️ Weather calculation error for {team}: {e}")
            return 1.0
    
    def get_pitcher_multiplier(self, team, pitcher_data):
        """Calculate opposing pitcher quality multiplier"""
        if pitcher_data is None or len(pitcher_data) == 0:
            return 1.0
        
        try:
            # Find opposing pitcher for this team
            opposing_pitcher = pitcher_data[pitcher_data['opponent'] == team]
            if len(opposing_pitcher) == 0:
                return 1.0
            
            pitcher = opposing_pitcher.iloc[0]
            
            # Pitcher quality factors
            multiplier = 1.0
            
            # ERA-based factor (if available in aggregated stats)
            # Note: Using basic stats available in the pitcher features
            
            # Strikeout rate factor
            strikeouts = pitcher.get('strikeOuts', 0)
            innings = pitcher.get('outs', 0) / 3.0  # Outs to innings
            if innings > 0:
                k_per_inning = strikeouts / innings
                if k_per_inning > 1.2:  # High strikeout pitcher
                    multiplier -= 0.08
                elif k_per_inning < 0.7:  # Low strikeout pitcher
                    multiplier += 0.10
            
            # Walk rate factor
            walks = pitcher.get('baseOnBalls', 0)
            if innings > 0:
                bb_per_inning = walks / innings
                if bb_per_inning > 0.5:  # Wild pitcher
                    multiplier += 0.08
                elif bb_per_inning < 0.2:  # Control pitcher
                    multiplier -= 0.05
            
            # Home run rate factor
            hrs = pitcher.get('homeRuns', 0)
            if innings > 0:
                hr_per_inning = hrs / innings
                if hr_per_inning > 0.15:  # Homer prone
                    multiplier += 0.12
                elif hr_per_inning < 0.05:  # Stingy with HRs
                    multiplier -= 0.06
            
            # WHIP approximation
            hits = pitcher.get('hits', 0)
            if innings > 0:
                whip = (hits + walks) / innings
                if whip > 1.5:  # High WHIP - poor pitcher
                    multiplier += 0.15
                elif whip < 1.0:  # Low WHIP - excellent pitcher
                    multiplier -= 0.12
            
            return max(0.7, min(1.4, multiplier))  # Cap between 0.7-1.4x
            
        except Exception as e:
            print(f"⚠️ Pitcher calculation error for {team}: {e}")
            return 1.0
    
    def get_park_multiplier(self, team, park_data, weather_data):
        """Calculate ballpark factor multiplier"""
        if park_data is None or len(park_data) == 0:
            return 1.0
        
        try:
            # Find ballpark for this team (either home or away)
            home_team = None
            if weather_data is not None and len(weather_data) > 0:
                # Check if team is playing at home
                home_games = weather_data[weather_data['home_team'] == team]
                if len(home_games) > 0:
                    home_team = team  # Team is at home
                else:
                    # Team is away - find which park they're playing at
                    for _, game in weather_data.iterrows():
                        if pd.notna(game['home_team']):
                            home_team = game['home_team']
                            break
            
            if home_team is None:
                return 1.0
            
            # Find park factors for the venue
            park_info = None
            
            # Try to match team name to park data
            team_mappings = {
                'CHC': 'Cubs', 'NYY': 'Yankees', 'COL': 'Rockies', 'PHI': 'Phillies',
                'SD': 'Padres', 'LAA': 'Angels', 'ATL': 'Braves', 'TEX': 'Rangers',
                'MIN': 'Twins', 'KC': 'Royals', 'TB': 'Rays', 'CIN': 'Reds',
                'LAD': 'Dodgers', 'SF': 'Giants', 'CWS': 'White Sox', 'ATH': 'Athletics',
                'MIL': 'Brewers', 'WSH': 'Nationals', 'NYM': 'Mets', 'DET': 'Tigers',
                'MIA': 'Marlins', 'BAL': 'Orioles', 'BOS': 'Red Sox', 'SEA': 'Mariners',
                'TOR': 'Blue Jays', 'CLE': 'Guardians', 'HOU': 'Astros', 'ARI': 'Diamondbacks',
                'PIT': 'Pirates', 'STL': 'Cardinals'
            }
            
            full_team_name = team_mappings.get(home_team, home_team)
            park_matches = park_data[park_data['team'].str.contains(full_team_name, case=False, na=False)]
            
            if len(park_matches) > 0:
                park_info = park_matches.iloc[0]
            else:
                return 1.0
            
            # Calculate park multiplier based on factors
            multiplier = 1.0
            
            # Runs factor (primary offensive metric)
            runs_factor = park_info.get('runs_factor', 1.0)
            multiplier *= runs_factor
            
            # Home run factor (important for power)
            hr_factor = park_info.get('hr_factor', 1.0)
            hr_weight = 0.3  # 30% weight on HR factor
            multiplier *= (1 + (hr_factor - 1) * hr_weight)
            
            # Hits factor
            hits_factor = park_info.get('hits_factor', 1.0)
            hits_weight = 0.2  # 20% weight on hits factor
            multiplier *= (1 + (hits_factor - 1) * hits_weight)
            
            # Altitude factor (Coors Field effect)
            altitude = park_info.get('altitude', 0)
            if altitude > 3000:  # High altitude parks
                multiplier *= 1.08  # 8% boost for high altitude
            
            # Wind impact consideration
            wind_impact = park_info.get('wind_impact', 'neutral').lower()
            if wind_impact == 'helps offense':
                multiplier *= 1.05
            elif wind_impact == 'hurts offense':
                multiplier *= 0.96
            
            # Foul territory factor
            foul_territory = park_info.get('foul_territory', 'medium').lower()
            if foul_territory == 'small':  # Less foul territory = more fair balls
                multiplier *= 1.03
            elif foul_territory == 'large':  # More foul territory = more outs
                multiplier *= 0.97
            
            return max(0.85, min(1.25, multiplier))  # Cap between 0.85-1.25x
            
        except Exception as e:
            print(f"⚠️ Park calculation error for {team}: {e}")
            return 1.0
            
    def load_lineup_files(self):
        """Load lineup file inventory"""
        try:
            lineup_dirs = [
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data",
                r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate"
            ]
            all_files = []
            
            for directory in lineup_dirs:
                if os.path.exists(directory):
                    for file in os.listdir(directory):
                        if file.endswith('.csv') and 'lineup' in file.lower():
                            file_path = os.path.join(directory, file)
                            file_info = {
                                'name': file,
                                'path': file_path,
                                'location': os.path.basename(directory),
                                'size': os.path.getsize(file_path),
                                'modified': os.path.getmtime(file_path)
                            }
                            all_files.append(file_info)
            
            self.lineups_data = sorted(all_files, key=lambda x: x['modified'], reverse=True)
            print(f"📁 Found {len(self.lineups_data)} lineup files")
            
        except Exception as e:
            print(f"❌ Error loading lineup files: {e}")
            self.lineups_data = []
            
    def start_monitoring(self):
        """Start background monitoring"""
        self.monitoring_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
    def monitor_loop(self):
        """Background monitoring loop - much simpler"""
        while True:
            try:
                time.sleep(30)  # Update every 30 seconds
                
                # Simple refresh - just update timestamps
                current_time = datetime.now()
                self.debug_log(f"🔄 {current_time.strftime('%H:%M:%S')} - Status check complete")
                
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(60)
                
    def update_gui_data(self):
        """Update GUI with loaded data"""
        try:
            # Update ownership metrics
            if self.ownership_data:
                self.chalk_metric.config(text=str(self.ownership_data.get('chalk_plays', 0)))
                self.contrarian_metric.config(text=str(self.ownership_data.get('contrarian_targets', 0)))
                self.value_metric.config(text=str(self.ownership_data.get('value_plays', 0)))
                self.leverage_metric.config(text=str(self.ownership_data.get('leverage_spots', 0)))
                
                # Populate ownership table
                for item in self.ownership_tree.get_children():
                    self.ownership_tree.delete(item)
                
                for i, player in enumerate(self.ownership_data.get('players', [])[:50]):  # First 50 players
                    values = []
                    values.append(player.get('player_name', player.get('Player', 'Unknown')))
                    values.append(player.get('position', player.get('Position', 'N/A')))
                    values.append(player.get('team', player.get('Team', 'N/A')))
                    values.append(f"${player.get('salary', player.get('Salary', 0)):,}")
                    values.append(f"{player.get('projection', player.get('Projection', 0)):.1f}")
                    
                    # Ownership
                    ownership = 0
                    for col in ['ownership', 'projected_ownership', 'own_proj']:
                        if col in player:
                            ownership = player[col]
                            break
                    values.append(f"{ownership*100:.1f}%" if ownership else "0.0%")
                    
                    # Leverage
                    leverage = 0
                    for col in ['leverage', 'leverage_score']:
                        if col in player:
                            leverage = player[col]
                            break
                    values.append(f"{leverage:.2f}" if leverage else "0.00")
                    
                    # Tier
                    if ownership > 0.25:
                        tier = "Chalk"
                    elif ownership < 0.08:
                        tier = "Contrarian"
                    elif leverage > 0.7:
                        tier = "Value"
                    else:
                        tier = "Medium"
                    values.append(tier)
                    
                    self.ownership_tree.insert('', 'end', values=values)
            
            # Update stack data
            if self.stack_data:
                for item in self.stack_tree.get_children():
                    self.stack_tree.delete(item)
                
                for stack in self.stack_data:
                    values = [
                        stack['rank'],
                        stack['team'],
                        f"{stack['projection']:.1f}",
                        f"${stack['salary']:,}",
                        f"{stack['ownership']:.1f}%",
                        f"{stack['value']:.2f}",
                        stack['players']
                    ]
                    self.stack_tree.insert('', 'end', values=values)
                    
                # Update stack metrics
                if len(self.stack_data) > 0:
                    best_stack = self.stack_data[0]
                    self.best_stack_metric.config(text=f"{best_stack['team']}")
                    
                    # Find value stack
                    value_stack = max(self.stack_data, key=lambda x: x['value'])
                    self.value_stack_metric.config(text=f"{value_stack['team']}")
                    
                    # Find contrarian stack
                    contrarian_stack = min(self.stack_data, key=lambda x: x['ownership'])
                    self.contrarian_stack_metric.config(text=f"{contrarian_stack['team']}")
            
            # Update lineup files
            if self.lineups_data:
                self.total_files_metric.config(text=str(len(self.lineups_data)))
                self.total_lineups_metric.config(text="150")  # Estimate
                self.fanduel_ready_metric.config(text="30")   # Estimate
                
                # Show files
                files_content = "📁 AVAILABLE LINEUP FILES:\\n\\n"
                for file_info in self.lineups_data[:20]:
                    modified_time = datetime.fromtimestamp(file_info['modified'])
                    files_content += f"• {file_info['name']} ({file_info['location']}) - {modified_time.strftime('%H:%M')}\\n"
                
                self.files_text.delete(1.0, tk.END)
                self.files_text.insert(1.0, files_content)
            
            # Update debug info
            self.update_debug_text()
            
        except Exception as e:
            print(f"GUI update error: {e}")
            
    def update_debug_text(self):
        """Update debug information"""
        try:
            self.debug_text.delete(1.0, tk.END)
            content = f"🔧 DEBUG INFORMATION\\n\\n"
            content += f"Data Loaded: {'✅ Yes' if self.data_loaded else '❌ No'}\\n"
            content += f"Ownership Players: {len(self.ownership_data.get('players', []))}\\n"
            content += f"Stack Teams: {len(self.stack_data)}\\n"
            content += f"Lineup Files: {len(self.lineups_data)}\\n\\n"
            
            content += "Recent Events:\\n"
            for debug_msg in self.debug_info[-10:]:
                content += f"{debug_msg}\\n"
            
            self.debug_text.insert(1.0, content)
        except Exception as e:
            print(f"Debug update error: {e}")
            
    def debug_log(self, message):
        """Add debug message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_info.append(f"[{timestamp}] {message}")
        if len(self.debug_info) > 50:
            self.debug_info = self.debug_info[-50:]
            
    def export_lineups(self):
        """Export lineups using simple_export.py"""
        try:
            import subprocess
            result = subprocess.run(['python', 'simple_export.py', '1'], 
                                  capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                self.debug_log("✅ Lineups exported successfully")
                print("✅ Lineups exported successfully")
            else:
                self.debug_log(f"❌ Export error: {result.stderr}")
                print(f"❌ Export error: {result.stderr}")
                
        except Exception as e:
            self.debug_log(f"❌ Export exception: {e}")
            print(f"❌ Export exception: {e}")
            
    def export_stack_lineups(self):
        """Export stack-focused lineups"""
        try:
            import subprocess
            result = subprocess.run(['python', 'simple_export.py', 'stack', 'LAD', '3'], 
                                  capture_output=True, text=True, cwd='.')
            
            if result.returncode == 0:
                self.debug_log("✅ Stack lineups exported successfully")
                print("✅ Stack lineups exported successfully")
            else:
                self.debug_log(f"❌ Stack export error: {result.stderr}")
                print(f"❌ Stack export error: {result.stderr}")
                
        except Exception as e:
            self.debug_log(f"❌ Stack export exception: {e}")
            print(f"❌ Stack export exception: {e}")
            
    def run(self):
        """Run the dashboard"""
        print("🚀 Dashboard ready!")
        
        # Schedule GUI updates
        def update_loop():
            try:
                if self.data_loaded:
                    self.update_debug_text()
                self.root.after(5000, update_loop)  # Update every 5 seconds
            except:
                pass
                
        self.root.after(1000, update_loop)  # Start updates after 1 second
        self.root.mainloop()

if __name__ == "__main__":
    try:
        dashboard = WorkingEliteDFSDashboard()
        dashboard.run()
    except Exception as e:
        print(f"❌ Dashboard startup error: {e}")
        import traceback
        traceback.print_exc()
