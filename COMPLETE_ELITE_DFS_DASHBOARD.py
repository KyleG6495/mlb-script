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
try:
    from file_finder_utils import safe_read_csv
except ImportError:
    # Fallback if file_finder_utils not available
    import pandas as pd
    def safe_read_csv(file_path, **kwargs):
        try:
            return pd.read_csv(file_path, **kwargs)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return None

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
        self.lineups_data = {
            'teams': {},
            'pitchers': {},
            'status': {},
            'last_updated': '---'
        }
        self.scores_data = {
            'games': [],
            'last_updated': '---',
            'live_count': 0,
            'final_count': 0
        }
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
                       foreground='#000000', padding=[12, 8])
        
        self.create_ownership_tab()
        self.create_stacks_tab()
        self.create_lineups_tab()
        self.create_scores_tab()
        self.create_weather_tab()
        self.create_advanced_tab()
        self.create_lineup_selector_tab()
        self.create_integrated_workflow_tab()
        self.create_championship_tab()
        self.create_gpp_stacking_tab()
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
        
        # Ownership Validation Section
        validation_frame = tk.LabelFrame(tab, text="🎯 Ownership Validation & Accuracy Tracking",
                                       bg=self.colors['bg'], fg=self.colors['text'],
                                       font=('Arial', 12, 'bold'))
        validation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Input frame for actual ownership
        input_frame = tk.Frame(validation_frame, bg=self.colors['bg'])
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Date selection
        tk.Label(input_frame, text="Contest Date:", bg=self.colors['bg'], fg=self.colors['text'], font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.contest_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.contest_date_entry = tk.Entry(input_frame, textvariable=self.contest_date_var, width=12)
        self.contest_date_entry.pack(side=tk.LEFT, padx=5)
        
        # Contest info
        tk.Label(input_frame, text="Contest:", bg=self.colors['bg'], fg=self.colors['text'], font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        self.contest_name_var = tk.StringVar()
        self.contest_name_entry = tk.Entry(input_frame, textvariable=self.contest_name_var, width=20)
        self.contest_name_entry.pack(side=tk.LEFT, padx=5)
        
        # Import actual ownership button
        import_btn = tk.Button(input_frame, text="📊 Import Actual Ownership", 
                              command=self.import_actual_ownership,
                              bg=self.colors['accent'], fg=self.colors['text'],
                              font=('Arial', 10, 'bold'), relief='flat')
        import_btn.pack(side=tk.LEFT, padx=10)
        
        # View accuracy report button
        accuracy_btn = tk.Button(input_frame, text="📈 View Accuracy Report", 
                               command=self.show_accuracy_report,
                               bg=self.colors['blue'], fg=self.colors['text'],
                               font=('Arial', 10, 'bold'), relief='flat')
        accuracy_btn.pack(side=tk.LEFT, padx=5)
        
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
        
        self.best_stack_metric = self.create_metric_card(stack_metrics_frame, "Best 4-Man Stack", "0", "Projected Points", 0)
        self.value_stack_metric = self.create_metric_card(stack_metrics_frame, "Value Stack", "0", "Price/Point Ratio", 1)
        self.contrarian_stack_metric = self.create_metric_card(stack_metrics_frame, "Contrarian Stack", "0", "Low Ownership", 2)
        self.weather_stack_metric = self.create_metric_card(stack_metrics_frame, "Weather Boost", "0", "Conditions Edge", 3)
        
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
        
        # Add double-click event to show stacked lineups
        self.stack_tree.bind('<Double-1>', self.on_stack_double_click)
        
        self.stack_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar_stack.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_lineups_tab(self):
        """Team Lineups with Confirmation Status"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📋 Team Lineups")
        
        # Header with lineup status metrics
        header_frame = tk.Frame(tab, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.confirmed_lineups_metric = self.create_metric_card(header_frame, "Confirmed", "0", "Lineups Set", 0)
        self.expected_lineups_metric = self.create_metric_card(header_frame, "Expected", "0", "Lineups Projected", 1)
        self.coverage_metric = self.create_metric_card(header_frame, "Coverage", "0%", "Teams with Data", 2)
        self.last_updated_metric = self.create_metric_card(header_frame, "Last Updated", "---", "Rotowire Sync", 3)
        
        # Refresh button
        controls_frame = tk.Frame(tab, bg=self.colors['bg'])
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        refresh_btn = tk.Button(controls_frame, text="� Refresh Lineups", 
                               command=self.refresh_lineups_data,
                               bg=self.colors['accent'], fg=self.colors['text'],
                               font=('Arial', 12, 'bold'), relief='flat')
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Store reference to button for state updates
        self.refresh_lineups_btn = refresh_btn
        
        # Status indicator for refresh
        self.lineups_status_label = tk.Label(controls_frame,
                                           text="Click refresh to update lineup status",
                                           font=('Arial', 10),
                                           fg=self.colors['subtext'],
                                           bg=self.colors['bg'])
        self.lineups_status_label.pack(side=tk.LEFT, padx=10)
        
        # Main content area with scrollable frame
        canvas = tk.Canvas(tab, bg=self.colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        self.lineups_content_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        # Configure scrolling
        self.lineups_content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.lineups_content_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack scrollable elements
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y", pady=10)

    def create_scores_tab(self):
        """Live Game Scores & Updates"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="⚾ Live Scores")
        
        # Header with game status metrics
        header_frame = tk.Frame(tab, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.games_today_metric = self.create_metric_card(header_frame, "Games Today", "0", "On Tonight's Slate", 0)
        self.games_live_metric = self.create_metric_card(header_frame, "Live Games", "0", "Currently Playing", 1)
        self.games_final_metric = self.create_metric_card(header_frame, "Final Games", "0", "Completed", 2)
        self.last_score_update_metric = self.create_metric_card(header_frame, "Last Updated", "---", "Score Refresh", 3)
        
        # Refresh button
        controls_frame = tk.Frame(tab, bg=self.colors['bg'])
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.refresh_scores_btn = tk.Button(controls_frame, text="🔄 Refresh Scores", 
                               command=self.refresh_scores_data,
                               bg=self.colors['accent'], fg=self.colors['text'],
                               font=('Arial', 12, 'bold'), relief='flat')
        self.refresh_scores_btn.pack(side=tk.LEFT, padx=5)
        
        # Status indicator for scores refresh
        self.scores_status_label = tk.Label(controls_frame,
                                          text="Click refresh to get live scores",
                                          font=('Arial', 10),
                                          fg=self.colors['subtext'],
                                          bg=self.colors['bg'])
        self.scores_status_label.pack(side=tk.LEFT, padx=10)
        
        # Scores display area
        scores_frame = tk.Frame(tab, bg=self.colors['bg'])
        scores_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create Treeview for scores
        columns = ('Game', 'Status', 'Inning', 'Away Team', 'Away Score', 'Home Team', 'Home Score', 'Updated')
        self.scores_tree = ttk.Treeview(scores_frame, columns=columns, show='headings', height=8)
        
        # Configure columns
        self.scores_tree.heading('Game', text='Game')
        self.scores_tree.heading('Status', text='Status')
        self.scores_tree.heading('Inning', text='Inning')
        self.scores_tree.heading('Away Team', text='Away Team')
        self.scores_tree.heading('Away Score', text='Score')
        self.scores_tree.heading('Home Team', text='Home Team')
        self.scores_tree.heading('Home Score', text='Score')
        self.scores_tree.heading('Updated', text='Last Updated')
        
        # Column widths
        self.scores_tree.column('Game', width=120)
        self.scores_tree.column('Status', width=80)
        self.scores_tree.column('Inning', width=60)
        self.scores_tree.column('Away Team', width=80)
        self.scores_tree.column('Away Score', width=50)
        self.scores_tree.column('Home Team', width=80)
        self.scores_tree.column('Home Score', width=50)
        self.scores_tree.column('Updated', width=80)
        
        # Add scrollbar for scores table
        scores_scrollbar = ttk.Scrollbar(scores_frame, orient=tk.VERTICAL, command=self.scores_tree.yview)
        self.scores_tree.configure(yscrollcommand=scores_scrollbar.set)
        
        # Pack scores table
        self.scores_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scores_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_weather_tab(self):
        """Enhanced Weather & Park Conditions"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🌤️ Weather & Parks")
        
        # Create scrollable frame
        canvas = tk.Canvas(tab, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        def on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        canvas.bind("<Configure>", on_canvas_configure)
        
        # Bind mouse wheel to canvas
        canvas.bind("<MouseWheel>", on_mousewheel)
        tab.bind("<MouseWheel>", on_mousewheel)
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Enhanced title with refresh
        header_frame = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        header_frame.pack(fill='x', padx=20, pady=10)
        
        title_label = tk.Label(header_frame, text="🌤️ Live Weather & Stadium Analysis", 
                              font=("Arial", 18, "bold"), 
                              bg=self.colors['bg'], fg=self.colors['text'])
        title_label.pack(side='left')
        
        self.refresh_btn = tk.Button(header_frame, text="🔄 Refresh Weather", 
                               command=self.refresh_weather,
                               bg=self.colors['accent'], fg='white', 
                               font=('Arial', 10, 'bold'))
        self.refresh_btn.pack(side='right')
        
        # Weather summary cards
        summary_frame = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        summary_frame.pack(fill='x', padx=20, pady=(0, 20))
        
        self.wind_games_metric = self.create_metric_card(summary_frame, "🌪️ Wind Advantage", "0", "Games with Wind Out", 0)
        self.hot_games_metric = self.create_metric_card(summary_frame, "🔥 Hot Weather", "0", "Games >85°F", 1)
        self.dome_games_metric = self.create_metric_card(summary_frame, "🏟️ Dome Games", "0", "Controlled Environment", 2)
        self.weather_score_metric = self.create_metric_card(summary_frame, "⭐ Best Weather", "TBD", "Highest Scoring Potential", 3)
        
        # Detailed weather breakdown
        details_frame = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        details_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        details_title = tk.Label(details_frame, text="📊 Detailed Game-by-Game Weather Analysis", 
                                font=("Arial", 14, "bold"), 
                                bg=self.colors['bg'], fg=self.colors['text'])
        details_title.pack(pady=(0, 15))
        
        # Enhanced weather table
        table_frame = tk.Frame(details_frame, bg=self.colors['bg'])
        table_frame.pack(fill='both', expand=True)
        
        columns = ('Game', 'Stadium', 'Temp', 'Humidity', 'Wind', 'Direction', 'Conditions', 'Park Factor', 'DFS Impact', 'Weather Score')
        self.weather_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=8)
        
        # Enhanced column widths and headings
        column_config = {
            'Game': {'width': 100, 'text': '🏟️ Matchup'},
            'Stadium': {'width': 120, 'text': '🏟️ Stadium'},
            'Temp': {'width': 70, 'text': '🌡️ Temp'},
            'Humidity': {'width': 80, 'text': '💧 Humidity'},
            'Wind': {'width': 80, 'text': '💨 Wind Speed'},
            'Direction': {'width': 80, 'text': '🧭 Direction'},
            'Conditions': {'width': 100, 'text': '☀️ Conditions'},
            'Park Factor': {'width': 90, 'text': '⚾ Park Factor'},
            'DFS Impact': {'width': 150, 'text': '🎯 DFS Impact'},
            'Weather Score': {'width': 100, 'text': '⭐ Weather Score'}
        }
        
        for col in columns:
            config = column_config[col]
            self.weather_tree.heading(col, text=config['text'])
            self.weather_tree.column(col, width=config['width'], anchor=tk.CENTER)
        
        # Add scrollbar for table
        scrollbar_weather = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.weather_tree.yview)
        self.weather_tree.configure(yscrollcommand=scrollbar_weather.set)
        
        self.weather_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_weather.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Weather insights section
        insights_frame = tk.Frame(scrollable_frame, bg=self.colors['bg'])
        insights_frame.pack(fill='x', padx=20, pady=15)
        
        insights_title = tk.Label(insights_frame, text="🎯 Key Weather Insights for DFS", 
                                 font=("Arial", 14, "bold"), 
                                 bg=self.colors['bg'], fg=self.colors['text'])
        insights_title.pack(pady=(0, 10))
        
        self.insights_text = tk.Text(insights_frame, height=5, bg=self.colors['card'], 
                                    fg=self.colors['text'], font=('Arial', 11),
                                    wrap=tk.WORD, relief='flat', bd=0)
        self.insights_text.pack(fill='x', pady=5)
        
        # Park factors legend - Make it more prominent
        legend_frame = tk.Frame(scrollable_frame, bg=self.colors['bg'], relief='raised', bd=2)
        legend_frame.pack(fill='x', padx=20, pady=15)
        
        legend_title = tk.Label(legend_frame, text="📚 Stadium Park Factor Legend", 
                               font=("Arial", 13, "bold"), 
                               bg=self.colors['bg'], fg=self.colors['accent'])
        legend_title.pack(pady=10)
        
        # Make legend more readable with better formatting
        legend_content_frame = tk.Frame(legend_frame, bg=self.colors['card'], relief='sunken', bd=1)
        legend_content_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        legend_items = [
            "🏟️ Hitter Friendly (1.05+): Yankee Stadium, Fenway Park - Shorter dimensions favor offense",
            "⚾ Neutral Parks (0.95-1.05): Most stadiums - Balanced hitting/pitching conditions", 
            "🥎 Pitcher Friendly (<0.95): Petco Park, Oracle Park - Larger dimensions help pitchers",
            "🏠 Dome Stadiums: Minute Maid Park (HOU) - Climate controlled conditions",
            "⚾ Special Venue: Steinbrenner Field (TB) - Outdoor spring training facility, weather matters"
        ]
        
        for item in legend_items:
            item_label = tk.Label(legend_content_frame, text=f"• {item}", 
                                 font=('Arial', 10), bg=self.colors['card'], 
                                 fg=self.colors['text'], anchor='w', justify='left')
            item_label.pack(fill='x', padx=10, pady=3)
        
        # Add some bottom padding to ensure scrolling works
        bottom_spacer = tk.Frame(scrollable_frame, bg=self.colors['bg'], height=30)
        bottom_spacer.pack(fill='x')
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
    def refresh_weather(self):
        """Refresh weather data and update display"""
        try:
            print("🔄 Refreshing weather data...")
            
            # Update button to show it's working
            if hasattr(self, 'refresh_btn'):
                self.refresh_btn.config(text="🔄 Refreshing...", state='disabled')
                self.refresh_btn.update()
            
            # Reload weather data from files
            self.load_weather_data()
            
            # Update the weather display
            if hasattr(self, 'update_weather_display'):
                self.update_weather_display()
            
            # Also update the main data to refresh everything
            if hasattr(self, 'update_all_data'):
                self.update_all_data()
            
            print("✅ Weather data refreshed successfully!")
            
        except Exception as e:
            print(f"❌ Error refreshing weather: {e}")
        finally:
            # Reset button state
            if hasattr(self, 'refresh_btn'):
                self.refresh_btn.config(text="🔄 Refresh Weather", state='normal')
    
    def create_advanced_tab(self):
        """Advanced Stack Optimization with all edge techniques"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🚀 Advanced Edge")
        
        # Header with refresh button
        header_frame = tk.Frame(tab, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(header_frame, 
                              text="🚀 ELITE ADVANCED STACK OPTIMIZER",
                              font=('Arial', 16, 'bold'),
                              bg=self.colors['bg'],
                              fg=self.colors['accent'])
        title_label.pack(side=tk.LEFT)
        
        self.advanced_refresh_btn = tk.Button(header_frame,
                                            text="⚡ Run Advanced Analysis",
                                            command=self.refresh_advanced_analysis,
                                            bg=self.colors['accent'],
                                            fg=self.colors['bg'],
                                            font=('Arial', 10, 'bold'),
                                            relief=tk.FLAT,
                                            padx=15,
                                            pady=5)
        self.advanced_refresh_btn.pack(side=tk.RIGHT)
        
        # Create scrollable frame
        canvas = tk.Canvas(tab, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        def on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(e):
            canvas.itemconfig(window, width=e.width)
        
        scrollable_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)
        
        window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content frame
        self.advanced_content_frame = scrollable_frame
        
        # Initial content
        initial_label = tk.Label(self.advanced_content_frame,
                               text="Click 'Run Advanced Analysis' to generate comprehensive edge analysis",
                               font=('Arial', 12),
                               bg=self.colors['bg'],
                               fg=self.colors['subtext'])
        initial_label.pack(pady=50)

    def refresh_advanced_analysis(self):
        """Run the advanced stack analysis"""
        # Update button state
        self.advanced_refresh_btn.config(text="⏳ Analyzing...", state='disabled')
        
        def run_analysis():
            try:
                # Clear existing content
                for widget in self.advanced_content_frame.winfo_children():
                    widget.destroy()
                
                # Add loading indicator
                loading_label = tk.Label(self.advanced_content_frame,
                                       text="🔍 Running Elite Advanced Analysis...",
                                       font=('Arial', 14, 'bold'),
                                       bg=self.colors['bg'],
                                       fg=self.colors['accent'])
                loading_label.pack(pady=20)
                
                # Import and run the advanced optimizer
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from ELITE_ADVANCED_STACK_OPTIMIZER import EliteAdvancedStackOptimizer
                    
                    optimizer = EliteAdvancedStackOptimizer()
                    results = optimizer.generate_advanced_stack_analysis()
                    
                    if results:
                        self.display_advanced_results(results)
                    else:
                        self.display_advanced_error("No slate data available - run data pipeline first")
                        
                except ImportError as e:
                    self.display_advanced_error(f"Advanced optimizer not available: {e}")
                except Exception as e:
                    self.display_advanced_error(f"Analysis error: {e}")
                    
            except Exception as e:
                self.display_advanced_error(f"Error running analysis: {e}")
            finally:
                # Reset button state
                self.advanced_refresh_btn.config(text="⚡ Run Advanced Analysis", state='normal')
        
        # Run in thread to avoid UI blocking
        thread = threading.Thread(target=run_analysis)
        thread.daemon = True
        thread.start()

    def display_advanced_results(self, results):
        """Display the advanced analysis results"""
        # Clear loading indicator
        for widget in self.advanced_content_frame.winfo_children():
            widget.destroy()
        
        # Umpire Analysis Section
        umpire_frame = tk.LabelFrame(self.advanced_content_frame,
                                   text="⚾ UMPIRE EDGE ANALYSIS",
                                   font=('Arial', 12, 'bold'),
                                   bg=self.colors['card'],
                                   fg=self.colors['accent'],
                                   padx=10,
                                   pady=10)
        umpire_frame.pack(fill=tk.X, padx=10, pady=5)
        
        if 'umpire_analysis' in results:
            for game, data in results['umpire_analysis'].items():
                rec_color = self.colors['success'] if data['recommendation'] == 'TARGET' else \
                           self.colors['danger'] if data['recommendation'] == 'AVOID' else \
                           self.colors['warning'] if data['recommendation'] == 'TOURNAMENT_UPSIDE' else \
                           self.colors['text']
                
                game_label = tk.Label(umpire_frame,
                                    text=f"{game}: {data['umpire']} ({data['recommendation']})",
                                    font=('Arial', 10, 'bold'),
                                    bg=self.colors['card'],
                                    fg=rec_color)
                game_label.pack(anchor=tk.W)
                
                impact_label = tk.Label(umpire_frame,
                                      text=f"   Impact Factor: {data['impact_factor']:.2f}x scoring",
                                      font=('Arial', 9),
                                      bg=self.colors['card'],
                                      fg=self.colors['subtext'])
                impact_label.pack(anchor=tk.W)
        
        # Leverage Analysis Section
        leverage_frame = tk.LabelFrame(self.advanced_content_frame,
                                     text="📊 ELITE LEVERAGE PLAYS",
                                     font=('Arial', 12, 'bold'),
                                     bg=self.colors['card'],
                                     fg=self.colors['accent'],
                                     padx=10,
                                     pady=10)
        leverage_frame.pack(fill=tk.X, padx=10, pady=5)
        
        if 'leverage_scores' in results:
            # Load clean slate to filter out injured players
            clean_slate_players = set()
            try:
                clean_slate_path = "../fd_current_slate/fd_slate_today_clean.csv"
                if not os.path.exists(clean_slate_path):
                    clean_slate_path = "../fd_current_slate/fd_slate_today.csv"
                clean_slate_df = safe_read_csv(clean_slate_path)
                if clean_slate_df is not None and 'Nickname' in clean_slate_df.columns:
                    clean_slate_players = set(clean_slate_df['Nickname'].unique())
                    print(f"🧹 Filtering leverage plays to {len(clean_slate_players)} active players")
            except Exception as e:
                print(f"⚠️ Could not load clean slate for filtering: {e}")
            
            # Sort by leverage score and filter to clean slate players only
            sorted_leverage = sorted(results['leverage_scores'].items(), 
                                   key=lambda x: x[1]['leverage_score'], 
                                   reverse=True)
            
            # Filter to only players in clean slate (no injured players)
            filtered_leverage = [(player, data) for player, data in sorted_leverage 
                               if not clean_slate_players or player in clean_slate_players]
            
            for i, (player, data) in enumerate(filtered_leverage[:10]):
                if data['recommendation'] in ['ELITE_LEVERAGE', 'GOOD_LEVERAGE']:
                    rec_color = self.colors['success'] if data['recommendation'] == 'ELITE_LEVERAGE' else self.colors['warning']
                    
                    player_label = tk.Label(leverage_frame,
                                          text=f"🎯 {player}: {data['leverage_score']:.1f} leverage",
                                          font=('Arial', 10, 'bold'),
                                          bg=self.colors['card'],
                                          fg=rec_color)
                    player_label.pack(anchor=tk.W)
                    
                    details_label = tk.Label(leverage_frame,
                                           text=f"   Ceiling: {data['ceiling']} | Ownership: {data['predicted_ownership']:.1f}%",
                                           font=('Arial', 9),
                                           bg=self.colors['card'],
                                           fg=self.colors['subtext'])
                    details_label.pack(anchor=tk.W)
        
        # Correlation Analysis Section
        correlation_frame = tk.LabelFrame(self.advanced_content_frame,
                                        text="🔗 STACK CORRELATION ANALYSIS",
                                        font=('Arial', 12, 'bold'),
                                        bg=self.colors['card'],
                                        fg=self.colors['accent'],
                                        padx=10,
                                        pady=10)
        correlation_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Multi-Team Stack Button (NEW! - HIGHLY VISIBLE)
        multi_stack_button = tk.Button(correlation_frame,
                                     text="🎯 ANALYZE MULTI-TEAM STACKS (Tournament Strategy)",
                                     font=('Arial', 12, 'bold'),
                                     bg='#FF6B35',  # Bright orange
                                     fg='white',
                                     command=self.run_multi_team_stacks,
                                     pady=8,
                                     relief='raised',
                                     bd=3)
        multi_stack_button.pack(fill=tk.X, pady=(5, 10))
        
        # Complete Lineup Builder Button (NEW!)
        lineup_builder_button = tk.Button(correlation_frame,
                                         text="🏆 BUILD COMPLETE FANDUEL LINEUPS (All-in-One)",
                                         font=('Arial', 12, 'bold'),
                                         bg='#28A745',  # Green
                                         fg='white',
                                         command=self.run_complete_lineup_workflow,
                                         pady=8,
                                         relief='raised',
                                         bd=3)
        lineup_builder_button.pack(fill=tk.X, pady=(5, 15))
        
        # Add explanation text
        explanation_label = tk.Label(correlation_frame,
                                   text="⚡ NEW: Complete workflow from multi-team stacks to FanDuel-ready lineups",
                                   font=('Arial', 10, 'italic'),
                                   bg=self.colors['card'],
                                   fg='#28A745')
        explanation_label.pack(anchor=tk.W, pady=(0, 10))
        
        if 'correlations' in results:
            # Sort by stack potential
            sorted_correlations = sorted(results['correlations'].items(),
                                       key=lambda x: x[1]['stack_potential'],
                                       reverse=True)
            
            for team, data in sorted_correlations[:8]:
                potential_color = self.colors['success'] if data['stack_potential'] >= 7 else \
                                self.colors['warning'] if data['stack_potential'] >= 5 else \
                                self.colors['text']
                
                team_label = tk.Label(correlation_frame,
                                    text=f"🔥 {team}: {data['stack_potential']}/10 stack potential",
                                    font=('Arial', 10, 'bold'),
                                    bg=self.colors['card'],
                                    fg=potential_color)
                team_label.pack(anchor=tk.W)
                
                players_label = tk.Label(correlation_frame,
                                       text=f"   Available Players: {data['players_available']}",
                                       font=('Arial', 9),
                                       bg=self.colors['card'],
                                       fg=self.colors['subtext'])
                players_label.pack(anchor=tk.W)
        
        # Summary Section
        summary_frame = tk.LabelFrame(self.advanced_content_frame,
                                    text="💡 KEY INSIGHTS & RECOMMENDATIONS",
                                    font=('Arial', 12, 'bold'),
                                    bg=self.colors['card'],
                                    fg=self.colors['accent'],
                                    padx=10,
                                    pady=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        insights = [
            "🎯 Use Multi-Team Stacks for tournament upside (NYM + CHC strategy)",
            "🎯 Focus on high leverage plays (3.0+ leverage score)",
            "⚾ Target games with favorable umpire matchups",
            "🔗 Stack teams with 7+ correlation potential",
            "💎 Look for contrarian opportunities in tournament play",
            "📊 Combine multiple edge factors for maximum impact"
        ]
        
        for insight in insights:
            insight_label = tk.Label(summary_frame,
                                   text=insight,
                                   font=('Arial', 10),
                                   bg=self.colors['card'],
                                   fg=self.colors['text'])
            insight_label.pack(anchor=tk.W, pady=2)

    def display_advanced_error(self, error_message):
        """Display error message in advanced tab"""
        # Clear existing content
        for widget in self.advanced_content_frame.winfo_children():
            widget.destroy()
        
        error_label = tk.Label(self.advanced_content_frame,
                             text=f"❌ {error_message}",
                             font=('Arial', 12),
                             bg=self.colors['bg'],
                             fg=self.colors['danger'])
        error_label.pack(pady=20)
        
        suggestion_label = tk.Label(self.advanced_content_frame,
                                  text="💡 Run the data pipeline first to generate slate data",
                                  font=('Arial', 10),
                                  bg=self.colors['bg'],
                                  fg=self.colors['subtext'])
        suggestion_label.pack(pady=10)
    
    def create_lineup_selector_tab(self):
        """Lineup Selection for Contest Types"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🎯 Lineup Selector")
        
        # Header with selection button
        header_frame = tk.Frame(tab, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(header_frame, 
                              text="🎯 ELITE LINEUP SELECTOR",
                              font=('Arial', 16, 'bold'),
                              bg=self.colors['bg'],
                              fg=self.colors['accent'])
        title_label.pack(side=tk.LEFT)
        
        # Button frame for multiple buttons
        button_frame = tk.Frame(header_frame, bg=self.colors['bg'])
        button_frame.pack(side=tk.RIGHT)
        
        self.refresh_files_btn = tk.Button(button_frame,
                                          text="🔄 Refresh Files",
                                          command=self.refresh_files_only,
                                          bg=self.colors['blue'],
                                          fg='white',
                                          font=('Arial', 10, 'bold'),
                                          relief=tk.FLAT,
                                          padx=15,
                                          pady=5)
        self.refresh_files_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        self.export_btn = tk.Button(button_frame,
                                  text="📁 Export CSV Files",
                                  command=self.export_lineup_files,
                                  bg=self.colors['success'],
                                  fg='white',
                                  font=('Arial', 10, 'bold'),
                                  relief=tk.FLAT,
                                  padx=15,
                                  pady=5)
        self.export_btn.pack(side=tk.RIGHT, padx=(0, 10))
        
        self.selector_btn = tk.Button(button_frame,
                                    text="🎯 Select Optimal Lineups",
                                    command=self.run_lineup_selection,
                                    bg=self.colors['accent'],
                                    fg=self.colors['bg'],
                                    font=('Arial', 10, 'bold'),
                                    relief=tk.FLAT,
                                    padx=15,
                                    pady=5)
        self.selector_btn.pack(side=tk.RIGHT)
        
        # Create scrollable frame
        canvas = tk.Canvas(tab, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        def on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(e):
            canvas.itemconfig(window, width=e.width)
        
        scrollable_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)
        
        window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Content frame
        self.selector_content_frame = scrollable_frame
        
        # Initial content
        initial_label = tk.Label(self.selector_content_frame,
                               text="Click 'Select Optimal Lineups' to analyze your generated lineups\nfor different contest types",
                               font=('Arial', 12),
                               bg=self.colors['bg'],
                               fg=self.colors['subtext'],
                               justify=tk.CENTER)
        initial_label.pack(pady=50)

    def run_lineup_selection(self):
        """Run the lineup selection analysis"""
        # Update button state
        self.selector_btn.config(text="⏳ Analyzing Lineups...", state='disabled')
        
        def run_selection():
            try:
                # Clear existing content
                for widget in self.selector_content_frame.winfo_children():
                    widget.destroy()
                
                # Add loading indicator
                loading_label = tk.Label(self.selector_content_frame,
                                       text="🔍 Analyzing Generated Lineups...",
                                       font=('Arial', 14, 'bold'),
                                       bg=self.colors['bg'],
                                       fg=self.colors['accent'])
                loading_label.pack(pady=20)
                
                # Import and run the lineup selector
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                    from ELITE_LINEUP_SELECTOR import EliteLineupSelector
                    
                    selector = EliteLineupSelector()
                    selections = selector.select_optimal_lineups(max_lineups_per_contest=5)
                    
                    if selections:
                        self.display_lineup_selections(selections)
                    else:
                        self.display_selector_error("No lineups found - generate lineups first")
                        
                except ImportError as e:
                    self.display_selector_error(f"Lineup selector not available: {e}")
                except Exception as e:
                    self.display_selector_error(f"Selection error: {e}")
                    
            except Exception as e:
                self.display_selector_error(f"Error running selection: {e}")
            finally:
                # Reset button state
                self.selector_btn.config(text="🎯 Select Optimal Lineups", state='normal')
        
        # Run in thread to avoid UI blocking
        thread = threading.Thread(target=run_selection)
        thread.daemon = True
        thread.start()

    def display_lineup_selections(self, selections):
        """Display the lineup selection results"""
        # Clear loading indicator
        for widget in self.selector_content_frame.winfo_children():
            widget.destroy()
        
        contest_types = {
            'cash_games': {'title': '💰 CASH GAMES (50/50s, Double-ups)', 'color': self.colors['success']},
            'small_tournaments': {'title': '🎯 SMALL TOURNAMENTS (Single Entry)', 'color': self.colors['warning']},
            'large_tournaments': {'title': '🚀 LARGE TOURNAMENTS (Milly Maker)', 'color': self.colors['blue']}
        }
        
        for contest_type, lineups in selections.items():
            if contest_type in contest_types:
                # Contest type section
                type_frame = tk.LabelFrame(self.selector_content_frame,
                                         text=contest_types[contest_type]['title'],
                                         font=('Arial', 12, 'bold'),
                                         bg=self.colors['card'],
                                         fg=contest_types[contest_type]['color'],
                                         padx=10,
                                         pady=10)
                type_frame.pack(fill=tk.X, padx=10, pady=5)
                
                if lineups:
                    for i, lineup in enumerate(lineups[:3], 1):
                        char = lineup['characteristics']
                        suit_score = char['contest_suitability'][contest_type]
                        
                        # Determine rating
                        if suit_score >= 80:
                            rating = "🔥 ELITE"
                            rating_color = self.colors['success']
                        elif suit_score >= 65:
                            rating = "⭐ GREAT"
                            rating_color = self.colors['warning']
                        elif suit_score >= 50:
                            rating = "📊 GOOD"
                            rating_color = self.colors['blue']
                        else:
                            rating = "⚠️ OKAY"
                            rating_color = self.colors['subtext']
                        
                        # Lineup frame
                        lineup_frame = tk.Frame(type_frame, bg=self.colors['card'])
                        lineup_frame.pack(fill=tk.X, pady=2)
                        
                        # Lineup header
                        header_text = f"{rating} #{i} {lineup['lineup_id']}"
                        header_label = tk.Label(lineup_frame,
                                              text=header_text,
                                              font=('Arial', 11, 'bold'),
                                              bg=self.colors['card'],
                                              fg=rating_color)
                        header_label.pack(anchor=tk.W)
                        
                        # Lineup details
                        details_text = f"   Suitability: {suit_score}% | Ceiling: {char['ceiling_score']} | Floor: {char['floor_score']}"
                        details_label = tk.Label(lineup_frame,
                                               text=details_text,
                                               font=('Arial', 9),
                                               bg=self.colors['card'],
                                               fg=self.colors['subtext'])
                        details_label.pack(anchor=tk.W)
                        
                        # Strategy details
                        strategy_text = f"   Strategy: {char['stack_type']} | Chalk: {char['chalk_percentage']}% | Leverage: {char['leverage_score']:.1f}"
                        strategy_label = tk.Label(lineup_frame,
                                                text=strategy_text,
                                                font=('Arial', 9),
                                                bg=self.colors['card'],
                                                fg=self.colors['subtext'])
                        strategy_label.pack(anchor=tk.W)
                else:
                    no_lineups_label = tk.Label(type_frame,
                                              text="No suitable lineups found for this contest type",
                                              font=('Arial', 10),
                                              bg=self.colors['card'],
                                              fg=self.colors['subtext'])
                    no_lineups_label.pack()
        
        # Summary recommendations
        summary_frame = tk.LabelFrame(self.selector_content_frame,
                                    text="💡 CONTEST ENTRY STRATEGY",
                                    font=('Arial', 12, 'bold'),
                                    bg=self.colors['card'],
                                    fg=self.colors['accent'],
                                    padx=10,
                                    pady=10)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        recommendations = [
            "💰 Cash Games: Focus on high floor, low variance lineups",
            "🎯 Small Tournaments: Balance ceiling with moderate ownership",
            "🚀 Large Tournaments: Max ceiling, contrarian plays only",
            "📊 Use top-rated lineups for each specific contest type",
            "⚡ Avoid entering tournament lineups in cash games"
        ]
        
        for rec in recommendations:
            rec_label = tk.Label(summary_frame,
                               text=rec,
                               font=('Arial', 10),
                               bg=self.colors['card'],
                               fg=self.colors['text'])
            rec_label.pack(anchor=tk.W, pady=1)
            
        # Add exported files section
        self.add_exported_files_section()

    def display_selector_error(self, error_message):
        """Display error message in selector tab"""
        # Clear existing content
        for widget in self.selector_content_frame.winfo_children():
            widget.destroy()
        
        error_label = tk.Label(self.selector_content_frame,
                             text=f"❌ {error_message}",
                             font=('Arial', 12),
                             bg=self.colors['bg'],
                             fg=self.colors['danger'])
        error_label.pack(pady=20)
        
        suggestion_label = tk.Label(self.selector_content_frame,
                                  text="💡 Generate lineups first using your pipeline",
                                  font=('Arial', 10),
                                  bg=self.colors['bg'],
                                  fg=self.colors['subtext'])
        suggestion_label.pack(pady=10)
    
    def export_lineup_files(self):
        """Export recommended lineups as CSV files for contest entry"""
        # Update button state
        self.export_btn.config(text="⏳ Exporting...", state='disabled')
        
        def run_export():
            try:
                # Import and run the exporter
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                from EXPORT_SELECTED_LINEUPS import LineupExporter
                
                exporter = LineupExporter()
                recommendations = exporter.export_recommended_lineups()
                
                if recommendations:
                    # Show success message in debug tab
                    self.debug_text.insert(tk.END, f"\n✅ LINEUP EXPORT SUCCESSFUL - {datetime.now().strftime('%H:%M:%S')}\n")
                    self.debug_text.insert(tk.END, "=" * 50 + "\n")
                    
                    for contest_type, lineup_info in recommendations.items():
                        self.debug_text.insert(tk.END, f"{contest_type}:\n")
                        self.debug_text.insert(tk.END, f"  📁 Exported: RECOMMENDED_{contest_type.replace(' ', '_')}_{lineup_info['lineup_id']}_*.csv\n")
                        self.debug_text.insert(tk.END, f"  🎯 Lineup: {lineup_info['lineup_id']}\n")
                        self.debug_text.insert(tk.END, f"  🏆 Ceiling: {lineup_info['ceiling']}\n")
                        self.debug_text.insert(tk.END, f"  📈 Suitability: {lineup_info['suitability_score']:.1f}%\n\n")
                    
                    self.debug_text.insert(tk.END, f"📁 Files saved to: fd_current_slate folder\n")
                    self.debug_text.insert(tk.END, f"🎯 Ready for FanDuel upload!\n\n")
                    self.debug_text.see(tk.END)
                    
                    # Switch to debug tab to show results
                    self.notebook.select(7)  # Debug tab index
                    
                    # Refresh the files section
                    self.refresh_files_section()
                else:
                    self.debug_text.insert(tk.END, f"\n❌ EXPORT FAILED - {datetime.now().strftime('%H:%M:%S')}\n")
                    self.debug_text.insert(tk.END, "Run lineup selection first!\n\n")
                    self.debug_text.see(tk.END)
                    
            except Exception as e:
                self.debug_text.insert(tk.END, f"\n❌ EXPORT ERROR - {datetime.now().strftime('%H:%M:%S')}\n")
                self.debug_text.insert(tk.END, f"Error: {e}\n\n")
                self.debug_text.see(tk.END)
            finally:
                # Reset button state
                self.export_btn.config(text="📁 Export CSV Files", state='normal')
        
        # Run in thread to avoid UI blocking
        thread = threading.Thread(target=run_export)
        thread.daemon = True
        thread.start()
    
    def add_exported_files_section(self):
        """Add a section showing exported lineup files"""
        import os
        
        # Files section
        files_frame = tk.LabelFrame(self.selector_content_frame,
                                  text="📁 YOUR EXPORTED LINEUP FILES",
                                  font=('Arial', 12, 'bold'),
                                  bg=self.colors['card'],
                                  fg=self.colors['success'],
                                  padx=10,
                                  pady=10)
        files_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Check for exported files
        fd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fd_current_slate')
        
        try:
            if os.path.exists(fd_dir):
                recommended_files = [f for f in os.listdir(fd_dir) if f.startswith('RECOMMENDED_') and f.endswith('.csv')]
                
                if recommended_files:
                    # Sort files by type
                    cash_files = [f for f in recommended_files if 'cash_games' in f]
                    small_files = [f for f in recommended_files if 'small_tournaments' in f]
                    large_files = [f for f in recommended_files if 'large_tournaments' in f]
                    
                    file_types = [
                        ("💰 Cash Games", cash_files, self.colors['success']),
                        ("🎯 Small Tournaments", small_files, self.colors['warning']),
                        ("🚀 Large Tournaments", large_files, self.colors['blue'])
                    ]
                    
                    for type_name, files, color in file_types:
                        if files:
                            # Most recent file for this type
                            recent_file = sorted(files, reverse=True)[0]
                            
                            # Create file frame
                            file_frame = tk.Frame(files_frame, bg=self.colors['card'])
                            file_frame.pack(fill=tk.X, pady=2)
                            
                            # File type and name
                            type_label = tk.Label(file_frame,
                                                text=f"{type_name}:",
                                                font=('Arial', 10, 'bold'),
                                                bg=self.colors['card'],
                                                fg=color)
                            type_label.pack(anchor=tk.W)
                            
                            file_label = tk.Label(file_frame,
                                                 text=f"   📄 {recent_file}",
                                                 font=('Arial', 9),
                                                 bg=self.colors['card'],
                                                 fg=self.colors['text'])
                            file_label.pack(anchor=tk.W)
                            
                            # Buttons frame
                            btn_frame = tk.Frame(file_frame, bg=self.colors['card'])
                            btn_frame.pack(anchor=tk.W, padx=20, pady=2)
                            
                            # View button
                            view_btn = tk.Button(btn_frame,
                                               text="👁️ View",
                                               command=lambda f=recent_file: self.view_lineup_file(f),
                                               bg=self.colors['blue'],
                                               fg='white',
                                               font=('Arial', 8),
                                               relief=tk.FLAT,
                                               padx=10,
                                               pady=2)
                            view_btn.pack(side=tk.LEFT, padx=(0, 5))
                            
                            # Open folder button
                            folder_btn = tk.Button(btn_frame,
                                                 text="📁 Open Folder",
                                                 command=lambda: self.open_fd_folder(),
                                                 bg=self.colors['accent'],
                                                 fg=self.colors['bg'],
                                                 font=('Arial', 8),
                                                 relief=tk.FLAT,
                                                 padx=10,
                                                 pady=2)
                            folder_btn.pack(side=tk.LEFT)
                    
                    # Instructions
                    instr_frame = tk.Frame(files_frame, bg=self.colors['card'])
                    instr_frame.pack(fill=tk.X, pady=(10, 0))
                    
                    instr_label = tk.Label(instr_frame,
                                         text="📤 To upload to FanDuel: Go to contest → Upload Lineups → Select appropriate CSV file",
                                         font=('Arial', 9, 'italic'),
                                         bg=self.colors['card'],
                                         fg=self.colors['subtext'])
                    instr_label.pack()
                    
                else:
                    no_files_label = tk.Label(files_frame,
                                            text="No exported files found. Click 'Export CSV Files' first!",
                                            font=('Arial', 10),
                                            bg=self.colors['card'],
                                            fg=self.colors['subtext'])
                    no_files_label.pack()
            else:
                error_label = tk.Label(files_frame,
                                     text="fd_current_slate folder not found",
                                     font=('Arial', 10),
                                     bg=self.colors['card'],
                                     fg=self.colors['danger'])
                error_label.pack()
                
        except Exception as e:
            error_label = tk.Label(files_frame,
                                 text=f"Error checking files: {e}",
                                 font=('Arial', 10),
                                 bg=self.colors['card'],
                                 fg=self.colors['danger'])
            error_label.pack()
    
    def view_lineup_file(self, filename):
        """View lineup file contents in a popup"""
        import os
        import pandas as pd
        
        try:
            fd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fd_current_slate')
            filepath = os.path.join(fd_dir, filename)
            
            if os.path.exists(filepath):
                df = pd.read_csv(filepath)
                
                # Create popup window
                popup = tk.Toplevel(self.root)
                popup.title(f"📄 {filename}")
                popup.geometry("800x600")
                popup.configure(bg=self.colors['bg'])
                
                # Header
                header_label = tk.Label(popup,
                                      text=f"📄 Lineup Preview: {filename}",
                                      font=('Arial', 14, 'bold'),
                                      bg=self.colors['bg'],
                                      fg=self.colors['accent'])
                header_label.pack(pady=10)
                
                # Text widget for content
                text_widget = scrolledtext.ScrolledText(popup,
                                                      bg=self.colors['card'],
                                                      fg=self.colors['text'],
                                                      font=('Consolas', 10),
                                                      wrap=tk.WORD)
                text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
                
                # Insert DataFrame content
                text_widget.insert(tk.END, df.to_string(index=False))
                text_widget.config(state=tk.DISABLED)
                
                # Close button
                close_btn = tk.Button(popup,
                                    text="✖️ Close",
                                    command=popup.destroy,
                                    bg=self.colors['danger'],
                                    fg='white',
                                    font=('Arial', 10, 'bold'),
                                    relief=tk.FLAT,
                                    padx=20,
                                    pady=5)
                close_btn.pack(pady=10)
                
            else:
                self.debug_text.insert(tk.END, f"\n❌ File not found: {filename}\n")
                self.debug_text.see(tk.END)
                
        except Exception as e:
            self.debug_text.insert(tk.END, f"\n❌ Error viewing file: {e}\n")
            self.debug_text.see(tk.END)
    
    def open_fd_folder(self):
        """Open the fd_current_slate folder in file explorer"""
        import os
        import subprocess
        
        try:
            fd_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fd_current_slate')
            
            if os.path.exists(fd_dir):
                subprocess.run(['explorer', fd_dir], shell=True)
            else:
                self.debug_text.insert(tk.END, f"\n❌ Folder not found: {fd_dir}\n")
                self.debug_text.see(tk.END)
                
        except Exception as e:
            self.debug_text.insert(tk.END, f"\n❌ Error opening folder: {e}\n")
            self.debug_text.see(tk.END)
    
    def refresh_files_section(self):
        """Refresh the exported files section"""
        # Re-run lineup selection to refresh the display
        self.run_lineup_selection()
    
    def refresh_files_only(self):
        """Refresh just the files section without re-running analysis"""
        # Find and update just the files section if it exists
        for widget in self.selector_content_frame.winfo_children():
            if isinstance(widget, tk.LabelFrame) and "YOUR EXPORTED LINEUP FILES" in widget.cget('text'):
                widget.destroy()
                break
        
        self.add_exported_files_section()
        
    def create_integrated_workflow_tab(self):
        """Integrated Workflow - Connects all systems"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🔗 Integrated Workflow")
        
        # Header
        header_frame = tk.Frame(tab, bg=self.colors['card'], height=100)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🔗 INTEGRATED WORKFLOW", 
                              font=('Arial', 18, 'bold'), 
                              fg=self.colors['accent'], bg=self.colors['card'])
        title_label.pack(pady=10)
        
        subtitle_label = tk.Label(header_frame, 
                                 text="Connects: Stack Analysis → Umpire Data → Weather → Unified Lineups", 
                                 font=('Arial', 11), 
                                 fg=self.colors['subtext'], bg=self.colors['card'])
        subtitle_label.pack()
        
        # Main content area
        main_frame = tk.Frame(tab, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Left side - Workflow steps
        left_frame = tk.Frame(main_frame, bg=self.colors['card'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        steps_label = tk.Label(left_frame, text="📋 WORKFLOW STEPS", 
                              font=('Arial', 14, 'bold'), 
                              fg=self.colors['accent'], bg=self.colors['card'])
        steps_label.pack(pady=10)
        
        steps_text = """
1. 🔍 Generate Stack Analysis
   • Analyzes team offensive potential
   • Identifies pitcher matchups
   • Calculates team stack scores
   
2. 🧠 Run Integrated Analysis  
   • Combines stack data with umpire impacts
   • Applies weather factors
   • Considers ownership projections
   
3. 🎯 Generate Smart Lineups
   • Creates lineups using unified analysis
   • Avoids teams with bad umpire matchups
   • Boosts teams with favorable conditions
   
4. 📤 Convert to FanDuel Format
   • Prepares lineups for submission
   • Saves to fd_current_slate folder
        """
        
        steps_display = tk.Text(left_frame, wrap=tk.WORD, height=20,
                               font=('Arial', 10), fg=self.colors['text'], 
                               bg=self.colors['bg'], bd=0)
        steps_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        steps_display.insert('1.0', steps_text)
        steps_display.config(state=tk.DISABLED)
        
        # Right side - Controls and status
        right_frame = tk.Frame(main_frame, bg=self.colors['card'])
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        
        # Control buttons
        control_label = tk.Label(right_frame, text="⚡ CONTROLS", 
                                font=('Arial', 14, 'bold'), 
                                fg=self.colors['accent'], bg=self.colors['card'])
        control_label.pack(pady=10)
        
        # Run workflow button
        self.run_workflow_btn = tk.Button(right_frame,
                                         text="🚀 RUN COMPLETE\nINTEGRATED WORKFLOW",
                                         command=self.run_integrated_workflow_threaded,
                                         font=('Arial', 12, 'bold'),
                                         fg='white', bg=self.colors['success'],
                                         width=20, height=3)
        self.run_workflow_btn.pack(pady=10, padx=10)
        
        # Status display
        status_label = tk.Label(right_frame, text="📊 STATUS", 
                               font=('Arial', 12, 'bold'), 
                               fg=self.colors['accent'], bg=self.colors['card'])
        status_label.pack(pady=(20, 10))
        
        self.workflow_status = scrolledtext.ScrolledText(right_frame, 
                                                        width=30, height=15,
                                                        font=('Consolas', 9),
                                                        fg=self.colors['text'],
                                                        bg=self.colors['bg'])
        self.workflow_status.pack(padx=10, pady=10)
        
        # System integration status
        integration_label = tk.Label(right_frame, text="🔗 INTEGRATION STATUS", 
                                    font=('Arial', 12, 'bold'), 
                                    fg=self.colors['accent'], bg=self.colors['card'])
        integration_label.pack(pady=(20, 10))
        
        integration_text = """
✅ Stack Analysis Connected
✅ Umpire Data Connected  
✅ Weather Data Connected
✅ Ownership Data Connected
✅ Dashboard Integration Active
✅ Unified Decision Engine Ready

🎯 OLD PROBLEM:
❌ Systems operated in silos
❌ Umpire warnings ignored
❌ Poor DFS results

🚀 NEW SOLUTION:
✅ All data sources unified
✅ Angel Hernandez properly avoided
✅ Smart lineup generation
        """
        
        integration_display = tk.Text(right_frame, wrap=tk.WORD, height=12,
                                     font=('Arial', 9), fg=self.colors['text'], 
                                     bg=self.colors['bg'], bd=0)
        integration_display.pack(fill=tk.X, padx=10, pady=10)
        integration_display.insert('1.0', integration_text)
        integration_display.config(state=tk.DISABLED)
        
    def run_integrated_workflow_threaded(self):
        """Run integrated workflow in background thread"""
        def run_workflow():
            try:
                self.workflow_status.delete('1.0', tk.END)
                self.workflow_status.insert(tk.END, "🚀 Starting Integrated Workflow...\n\n")
                self.workflow_status.update()
                
                # Import and run the workflow
                import subprocess
                import sys
                
                script_path = "RUN_COMPLETE_INTEGRATED_WORKFLOW.py"
                
                self.workflow_status.insert(tk.END, f"📂 Running: {script_path}\n")
                self.workflow_status.update()
                
                # Run the workflow script
                result = subprocess.run([sys.executable, script_path], 
                                      capture_output=True, text=True, 
                                      cwd=os.path.dirname(os.path.abspath(__file__)))
                
                if result.returncode == 0:
                    self.workflow_status.insert(tk.END, "\n✅ WORKFLOW COMPLETED SUCCESSFULLY!\n\n")
                    self.workflow_status.insert(tk.END, "📋 OUTPUT:\n")
                    self.workflow_status.insert(tk.END, result.stdout)
                else:
                    self.workflow_status.insert(tk.END, "\n❌ WORKFLOW ERROR:\n")
                    self.workflow_status.insert(tk.END, result.stderr)
                
                self.workflow_status.insert(tk.END, "\n" + "="*50 + "\n")
                self.workflow_status.insert(tk.END, "🎯 Next Steps:\n")
                self.workflow_status.insert(tk.END, "1. Check Advanced Edge tab for umpire analysis\n")
                self.workflow_status.insert(tk.END, "2. Review generated lineups in Lineup Selector\n")
                self.workflow_status.insert(tk.END, "3. Upload FanDuel files from fd_current_slate\n")
                
            except Exception as e:
                self.workflow_status.insert(tk.END, f"\n❌ ERROR: {str(e)}\n")
                self.workflow_status.insert(tk.END, f"Traceback: {traceback.format_exc()}\n")
            
            # Re-enable button
            self.run_workflow_btn.config(state=tk.NORMAL, text="🚀 RUN COMPLETE\nINTEGRATED WORKFLOW")
            self.workflow_status.see(tk.END)
        
        # Disable button and start thread
        self.run_workflow_btn.config(state=tk.DISABLED, text="⏳ RUNNING...")
        thread = threading.Thread(target=run_workflow)
        thread.daemon = True
        thread.start()
        
    def create_championship_tab(self):
        """Championship Lineup Builder"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🏆 Championship")
        
        # Header
        header_frame = tk.Frame(tab, bg=self.colors['card'], height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🏆 Championship Lineup Builder",
                             bg=self.colors['card'], fg=self.colors['accent'],
                             font=('Arial', 16, 'bold'))
        title_label.pack(pady=15)
        
        # Description
        desc_frame = tk.Frame(tab, bg=self.colors['bg'])
        desc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        desc_text = ("Elite tournament optimization using ONLY confirmed starting pitchers\n"
                    "Realistic scoring expectations: 140-145 FPPG\n"
                    "Perfect for big GPP tournaments and championship events")
        
        desc_label = tk.Label(desc_frame, text=desc_text,
                            bg=self.colors['bg'], fg=self.colors['subtext'],
                            font=('Arial', 11), justify=tk.CENTER)
        desc_label.pack(pady=10)
        
        # Control buttons
        controls_frame = tk.Frame(tab, bg=self.colors['bg'])
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Single lineup button
        single_btn = tk.Button(controls_frame, text="🎯 Build Single Championship Lineup",
                             command=self.build_single_championship,
                             bg=self.colors['accent'], fg=self.colors['bg'],
                             font=('Arial', 12, 'bold'), relief=tk.FLAT,
                             padx=20, pady=10)
        single_btn.pack(side=tk.LEFT, padx=10)
        
        # Multiple lineups button
        multi_btn = tk.Button(controls_frame, text="📋 Build Multiple Championship Lineups",
                            command=self.build_multiple_championship,
                            bg=self.colors['blue'], fg=self.colors['text'],
                            font=('Arial', 12, 'bold'), relief=tk.FLAT,
                            padx=20, pady=10)
        multi_btn.pack(side=tk.LEFT, padx=10)
        
        # Results area
        results_frame = tk.LabelFrame(tab, text="Championship Lineup Results",
                                    fg=self.colors['text'], bg=self.colors['card'],
                                    font=('Arial', 14, 'bold'))
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollable results
        canvas = tk.Canvas(results_frame, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        def on_frame_configure(e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        def on_canvas_configure(e):
            canvas.itemconfig(window, width=e.width)
        
        scrollable_frame.bind('<Configure>', on_frame_configure)
        canvas.bind('<Configure>', on_canvas_configure)
        
        window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Store reference for updating
        self.championship_content_frame = scrollable_frame
        
        # Initial content
        initial_label = tk.Label(self.championship_content_frame,
                               text="🏆 Ready to build championship lineups!\n\nClick 'Single' for one optimal lineup\nClick 'Multiple' for 10+ diverse lineups",
                               font=('Arial', 12),
                               bg=self.colors['bg'],
                               fg=self.colors['subtext'],
                               justify=tk.CENTER)
        initial_label.pack(pady=50)
        
    def build_single_championship(self):
        """Build single championship lineup"""
        def run_single():
            try:
                # Clear existing content
                for widget in self.championship_content_frame.winfo_children():
                    widget.destroy()
                
                # Loading indicator
                loading_label = tk.Label(self.championship_content_frame,
                                       text="🔍 Building Single Championship Lineup...",
                                       font=('Arial', 14, 'bold'),
                                       bg=self.colors['bg'],
                                       fg=self.colors['accent'])
                loading_label.pack(pady=20)
                self.root.update()
                
                # Import and run championship builder
                import subprocess
                result = subprocess.run(['python', 'CHAMPIONSHIP_LINEUP_BUILDER.py'], 
                                      capture_output=True, text=True, cwd='.')
                
                # Clear loading
                loading_label.destroy()
                
                if result.returncode == 0:
                    success_label = tk.Label(self.championship_content_frame,
                                           text="✅ Championship Lineup Built Successfully!",
                                           font=('Arial', 14, 'bold'),
                                           bg=self.colors['bg'],
                                           fg=self.colors['success'])
                    success_label.pack(pady=10)
                    
                    # Show output
                    output_text = scrolledtext.ScrolledText(self.championship_content_frame,
                                                          height=15, width=80,
                                                          bg=self.colors['card'],
                                                          fg=self.colors['text'])
                    output_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
                    output_text.insert(tk.END, result.stdout)
                    
                    # Check for output files
                    self.check_championship_files()
                    
                else:
                    error_label = tk.Label(self.championship_content_frame,
                                         text="❌ Error building championship lineup",
                                         font=('Arial', 14, 'bold'),
                                         bg=self.colors['bg'],
                                         fg=self.colors['danger'])
                    error_label.pack(pady=10)
                    
                    error_text = scrolledtext.ScrolledText(self.championship_content_frame,
                                                         height=10, width=80,
                                                         bg=self.colors['card'],
                                                         fg=self.colors['danger'])
                    error_text.pack(pady=10, padx=10, fill=tk.X)
                    error_text.insert(tk.END, result.stderr)
                    
            except Exception as e:
                # Clear loading
                for widget in self.championship_content_frame.winfo_children():
                    widget.destroy()
                    
                error_label = tk.Label(self.championship_content_frame,
                                     text=f"❌ Error: {str(e)}",
                                     font=('Arial', 12),
                                     bg=self.colors['bg'],
                                     fg=self.colors['danger'])
                error_label.pack(pady=20)
        
        # Run in thread to avoid blocking UI
        threading.Thread(target=run_single, daemon=True).start()
        
    def build_multiple_championship(self):
        """Build multiple championship lineups"""
        def run_multiple():
            try:
                # Clear existing content
                for widget in self.championship_content_frame.winfo_children():
                    widget.destroy()
                
                # Loading indicator
                loading_label = tk.Label(self.championship_content_frame,
                                       text="🔍 Building Multiple Championship Lineups...",
                                       font=('Arial', 14, 'bold'),
                                       bg=self.colors['bg'],
                                       fg=self.colors['accent'])
                loading_label.pack(pady=20)
                self.root.update()
                
                # Import and run multiple championship builder
                import subprocess
                result = subprocess.run(['python', 'MULTIPLE_CHAMPIONSHIP_BUILDER.py'], 
                                      capture_output=True, text=True, cwd='.')
                
                # Clear loading
                loading_label.destroy()
                
                if result.returncode == 0:
                    success_label = tk.Label(self.championship_content_frame,
                                           text="✅ Multiple Championship Lineups Built Successfully!",
                                           font=('Arial', 14, 'bold'),
                                           bg=self.colors['bg'],
                                           fg=self.colors['success'])
                    success_label.pack(pady=10)
                    
                    # Show output
                    output_text = scrolledtext.ScrolledText(self.championship_content_frame,
                                                          height=15, width=80,
                                                          bg=self.colors['card'],
                                                          fg=self.colors['text'])
                    output_text.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
                    output_text.insert(tk.END, result.stdout)
                    
                    # Check for output files
                    self.check_championship_files()
                    
                else:
                    error_label = tk.Label(self.championship_content_frame,
                                         text="❌ Error building multiple championship lineups",
                                         font=('Arial', 14, 'bold'),
                                         bg=self.colors['bg'],
                                         fg=self.colors['danger'])
                    error_label.pack(pady=10)
                    
                    error_text = scrolledtext.ScrolledText(self.championship_content_frame,
                                                         height=10, width=80,
                                                         bg=self.colors['card'],
                                                         fg=self.colors['danger'])
                    error_text.pack(pady=10, padx=10, fill=tk.X)
                    error_text.insert(tk.END, result.stderr)
                    
            except Exception as e:
                # Clear loading
                for widget in self.championship_content_frame.winfo_children():
                    widget.destroy()
                    
                error_label = tk.Label(self.championship_content_frame,
                                     text=f"❌ Error: {str(e)}",
                                     font=('Arial', 12),
                                     bg=self.colors['bg'],
                                     fg=self.colors['danger'])
                error_label.pack(pady=20)
        
        # Run in thread to avoid blocking UI
        threading.Thread(target=run_multiple, daemon=True).start()
        
    def check_championship_files(self):
        """Check for championship output files and display them"""
        try:
            import os
            import glob
            
            # Look for championship files
            file_patterns = [
                '../fd_current_slate/CHAMPIONSHIP_SUBMISSION_*.csv',
                '../fd_current_slate/MULTIPLE_CHAMPIONSHIP_LINEUPS_*.csv',
                '../fd_current_slate/CHAMPIONSHIP_FANDUEL_SUBMISSION_*.csv'
            ]
            
            found_files = []
            for pattern in file_patterns:
                found_files.extend(glob.glob(pattern))
            
            if found_files:
                files_frame = tk.Frame(self.championship_content_frame, bg=self.colors['bg'])
                files_frame.pack(fill=tk.X, pady=10)
                
                files_label = tk.Label(files_frame,
                                     text="📁 Championship Files Created:",
                                     font=('Arial', 12, 'bold'),
                                     bg=self.colors['bg'],
                                     fg=self.colors['accent'])
                files_label.pack(anchor=tk.W)
                
                for file_path in sorted(found_files):
                    file_name = os.path.basename(file_path)
                    file_btn = tk.Button(files_frame,
                                       text=f"📄 {file_name}",
                                       command=lambda f=file_path: self.open_file_location(f),
                                       bg=self.colors['card'],
                                       fg=self.colors['text'],
                                       relief=tk.FLAT,
                                       anchor=tk.W)
                    file_btn.pack(fill=tk.X, pady=2)
                    
        except Exception as e:
            print(f"Error checking championship files: {e}")
            
    def open_file_location(self, file_path):
        """Open file location in explorer"""
        try:
            import os
            import subprocess
            abs_path = os.path.abspath(file_path)
            subprocess.run(['explorer', '/select,', abs_path])
        except Exception as e:
            print(f"Error opening file location: {e}")
        
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
        
    def create_gpp_stacking_tab(self):
        """GPP Stacking Strategy Tab"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🚀 GPP Stacks")
        
        # Header
        header_frame = tk.Frame(tab, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(header_frame, text="🏆 Elite GPP Stacking Strategy", 
                              bg=self.colors['bg'], fg=self.colors['accent'], 
                              font=('Arial', 18, 'bold'))
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(header_frame, text="Low-owned, high-projection stacks for large GPP tournaments", 
                                 bg=self.colors['bg'], fg=self.colors['subtext'], 
                                 font=('Arial', 11))
        subtitle_label.pack(anchor='w', pady=(5, 0))
        
        # Control buttons
        controls_frame = tk.Frame(tab, bg=self.colors['bg'])
        controls_frame.pack(fill=tk.X, padx=10, pady=10)
        
        analyze_btn = tk.Button(controls_frame, text="🔄 Run GPP Analysis", 
                               command=self.run_gpp_analysis,
                               bg=self.colors['accent'], fg='black', 
                               font=('Arial', 11, 'bold'), 
                               relief='flat', padx=20, pady=8)
        analyze_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        refresh_btn = tk.Button(controls_frame, text="↻ Refresh Data", 
                               command=self.refresh_gpp_data,
                               bg=self.colors['blue'], fg='white', 
                               font=('Arial', 11), 
                               relief='flat', padx=20, pady=8)
        refresh_btn.pack(side=tk.LEFT)
        
        # Status label
        self.gpp_status_label = tk.Label(controls_frame, text="Ready to analyze", 
                                        bg=self.colors['bg'], fg=self.colors['subtext'], 
                                        font=('Arial', 10))
        self.gpp_status_label.pack(side=tk.RIGHT)
        
        # Results frame
        results_frame = tk.Frame(tab, bg=self.colors['bg'])
        results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Elite stacks frame
        elite_frame = tk.LabelFrame(results_frame, text="🚀 Elite Stacks (40-50% of lineups)", 
                                   bg=self.colors['bg'], fg=self.colors['accent'], 
                                   font=('Arial', 12, 'bold'))
        elite_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.elite_stacks_text = scrolledtext.ScrolledText(elite_frame, height=6,
                                                          bg=self.colors['card'], 
                                                          fg=self.colors['text'],
                                                          font=('Consolas', 10),
                                                          wrap=tk.WORD)
        self.elite_stacks_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Good stacks frame
        good_frame = tk.LabelFrame(results_frame, text="✅ Good Stacks (20-30% of lineups)", 
                                  bg=self.colors['bg'], fg=self.colors['success'], 
                                  font=('Arial', 12, 'bold'))
        good_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.good_stacks_text = scrolledtext.ScrolledText(good_frame, height=4,
                                                         bg=self.colors['card'], 
                                                         fg=self.colors['text'],
                                                         font=('Consolas', 10),
                                                         wrap=tk.WORD)
        self.good_stacks_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Weather frame
        weather_frame = tk.LabelFrame(results_frame, text="🌡️ Weather Advantages", 
                                     bg=self.colors['bg'], fg=self.colors['warning'], 
                                     font=('Arial', 12, 'bold'))
        weather_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.weather_stacks_text = scrolledtext.ScrolledText(weather_frame, height=3,
                                                            bg=self.colors['card'], 
                                                            fg=self.colors['text'],
                                                            font=('Consolas', 10),
                                                            wrap=tk.WORD)
        self.weather_stacks_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Implementation strategy frame
        strategy_frame = tk.LabelFrame(results_frame, text="💡 Implementation Strategy", 
                                      bg=self.colors['bg'], fg=self.colors['blue'], 
                                      font=('Arial', 12, 'bold'))
        strategy_frame.pack(fill=tk.BOTH, expand=True)
        
        self.strategy_text = scrolledtext.ScrolledText(strategy_frame,
                                                      bg=self.colors['card'], 
                                                      fg=self.colors['text'],
                                                      font=('Consolas', 10),
                                                      wrap=tk.WORD)
        self.strategy_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def run_gpp_analysis(self):
        """Run GPP stacking analysis in separate thread"""
        def analysis_thread():
            try:
                self.gpp_status_label.config(text="🔄 Running analysis...", fg=self.colors['warning'])
                
                # Import and run the GPP analysis
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.abspath(__file__)))
                
                from ENHANCED_GPP_STACKING_STRATEGY_FIXED import GPPStackingStrategy
                
                analyzer = GPPStackingStrategy()
                results = analyzer.run_analysis()
                
                if results:
                    self.display_gpp_results(results)
                    self.gpp_status_label.config(text="✅ Analysis complete", fg=self.colors['success'])
                else:
                    self.gpp_status_label.config(text="❌ Analysis failed", fg=self.colors['danger'])
                    
            except Exception as e:
                self.gpp_status_label.config(text=f"❌ Error: {str(e)[:50]}...", fg=self.colors['danger'])
                print(f"GPP Analysis error: {e}")
                traceback.print_exc()
        
        # Run in thread to prevent UI blocking
        thread = threading.Thread(target=analysis_thread)
        thread.daemon = True
        thread.start()
        
    def display_gpp_results(self, results):
        """Display GPP analysis results"""
        all_stacks = results.get('all_stacks', [])
        weather_advantages = results.get('weather_advantages', [])
        
        # Clear existing text
        self.elite_stacks_text.delete(1.0, tk.END)
        self.good_stacks_text.delete(1.0, tk.END)
        self.weather_stacks_text.delete(1.0, tk.END)
        self.strategy_text.delete(1.0, tk.END)
        
        # Elite stacks (top tier)
        elite_stacks = [s for s in all_stacks if "ELITE" in s.get('gpp_rating', '')]
        if elite_stacks:
            elite_text = "🚀 PRIMARY TARGETS (Use in 40-50% of lineups):\n\n"
            for i, stack in enumerate(elite_stacks[:5], 1):
                elite_text += f"{i}. {stack['team']}: {stack['projected_points']:.1f} pts, {stack['ownership']:.1f}% owned\n"
                elite_text += f"   Score: {stack.get('stack_score', 0):.0f} | Value Ratio: {stack.get('value_ratio', 0):.1f}\n\n"
        else:
            elite_text = "⚠️ No elite stacks found. Look for teams with:\n"
            elite_text += "• High projections (100+ points)\n"
            elite_text += "• Low ownership (<5%)\n"
            elite_text += "• Weather advantages\n"
        
        self.elite_stacks_text.insert(tk.END, elite_text)
        
        # Good stacks (second tier)
        excellent_stacks = [s for s in all_stacks if "EXCELLENT" in s.get('gpp_rating', '')]
        if excellent_stacks:
            good_text = "⭐ SECONDARY TARGETS (Use in 20-30% of lineups):\n\n"
            for i, stack in enumerate(excellent_stacks[:3], 1):
                good_text += f"{i}. {stack['team']}: {stack['projected_points']:.1f} pts, {stack['ownership']:.1f}% owned\n"
                good_text += f"   Score: {stack.get('stack_score', 0):.0f} | Value Ratio: {stack.get('value_ratio', 0):.1f}\n\n"
        else:
            good_text = "💡 Consider teams with 95-100 point projections and <8% ownership"
        
        self.good_stacks_text.insert(tk.END, good_text)
        
        # Weather advantages
        if weather_advantages:
            weather_text = "🌡️ WEATHER BOOST OPPORTUNITIES:\n\n"
            for advantage in weather_advantages[:3]:
                teams_str = ", ".join(advantage.get('teams', ['Unknown']))
                weather_text += f"🔥 {teams_str}: {advantage.get('temp', 'N/A')} | {advantage.get('wind', 'N/A')}\n"
                weather_text += f"   Boost Score: {advantage.get('boost', 0)}/4\n\n"
        else:
            weather_text = "🌤️ No significant weather advantages found today"
        
        self.weather_stacks_text.insert(tk.END, weather_text)
        
        # Implementation strategy
        strategy_text = "💡 LINEUP CONSTRUCTION STRATEGY:\n\n"
        
        if elite_stacks:
            primary = elite_stacks[0]
            strategy_text += f"🎯 PRIMARY FOCUS: {primary['team']}\n"
            strategy_text += f"   • Use in 40-50% of lineups\n"
            strategy_text += f"   • 4-5 player stacks\n"
            strategy_text += f"   • {primary['projected_points']:.1f} points, {primary['ownership']:.1f}% owned\n\n"
            
            if len(elite_stacks) > 1:
                secondary = elite_stacks[1]
                strategy_text += f"⚡ SECONDARY FOCUS: {secondary['team']}\n"
                strategy_text += f"   • Use in 20-30% of lineups\n"
                strategy_text += f"   • {secondary['projected_points']:.1f} points, {secondary['ownership']:.1f}% owned\n\n"
        
        strategy_text += "📊 TOURNAMENT GUIDELINES:\n"
        strategy_text += "• Target total lineup ownership <15%\n"
        strategy_text += "• Use 4-5 player stacks for primary teams\n"
        strategy_text += "• Consider 2-3 player mini-stacks for diversification\n"
        strategy_text += "• Leverage weather advantages when available\n"
        strategy_text += "• Focus on contrarian plays in large GPPs\n\n"
        
        strategy_text += f"📈 ANALYSIS DATE: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        strategy_text += f"🎯 TEAMS ANALYZED: {len(all_stacks)} teams playing today"
        
        self.strategy_text.insert(tk.END, strategy_text)
        
    def on_stack_double_click(self, event):
        """Handle double-click on stack to show stacked lineups"""
        selection = self.stack_tree.selection()
        if not selection:
            return
        
        item = self.stack_tree.item(selection[0])
        team_raw = item['values'][1]  # Team is in column 1
        
        # Extract team code from "NYM Stack" -> "NYM"
        team = team_raw.replace(' Stack', '').strip()
        
        print(f"Looking for stacked lineups for {team}...")
        self.show_stacked_lineups(team)
    
    def show_stacked_lineups(self, team):
        """Display stacked lineups for the selected team"""
        try:
            # Look for stacked lineup files
            fd_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate"
            lineup_files = []
            
            # Search for recent stacked lineup files, prioritizing individual player format
            if os.path.exists(fd_dir):
                for file in os.listdir(fd_dir):
                    if ('STACKED_LINEUPS' in file or 'PRIORITY_STACKED' in file) and file.endswith('.csv') and 'FD_FORMAT' not in file:
                        lineup_files.append(os.path.join(fd_dir, file))
                
                # If no individual format files, look for FD format and integrated files
                if not lineup_files:
                    for file in os.listdir(fd_dir):
                        if ('STACKED_LINEUPS' in file or 'PRIORITY_STACKED' in file or 'Integrated_Lineups' in file) and file.endswith('.csv'):
                            lineup_files.append(os.path.join(fd_dir, file))
            
            if not lineup_files:
                self.show_message("No Stacked Lineups Found", 
                                f"No stacked lineups found for {team}.\n\nRun the stacking optimizer first:\npython RUN_COMPLETE_INTEGRATED_WORKFLOW.py")
                return
            
            # Get most recent stacked lineup file
            lineup_files.sort(key=os.path.getmtime, reverse=True)
            lineup_file = lineup_files[0]
            
            # Load lineup data
            lineup_df = safe_read_csv(lineup_file)
            if lineup_df is None:
                self.show_message("Error", f"Could not read lineup file: {lineup_file}")
                return
            
            # Check if it's FanDuel format (has position columns)
            fd_positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'Util']
            is_fd_format = any(col in lineup_df.columns for col in fd_positions)
            
            if is_fd_format:
                # For FanDuel format, filter lineups that contain players from the target team
                team_lineups = self.filter_fd_lineups_by_team(lineup_df, team)
                if team_lineups.empty:
                    self.show_message("No Team Lineups", 
                                    f"No lineups found containing {team} players in {os.path.basename(lineup_file)}.\n\nThis may be because {team} players are not heavily stacked in the integrated lineups.")
                    return
                print(f"Found {len(team_lineups)} lineups containing {team} players")
            else:
                # For individual player format, filter by team or target team
                team_lineups = pd.DataFrame()
                
                # Try Target_Team first (for stacked lineups)
                if 'Target_Team' in lineup_df.columns:
                    team_lineups = lineup_df[lineup_df['Target_Team'] == team]
                    print(f"Filtering by Target_Team: {team}")
                elif 'Team' in lineup_df.columns:
                    team_lineups = lineup_df[lineup_df['Team'] == team]
                    print(f"Filtering by Team: {team}")
                else:
                    # If no team column, show all data
                    team_lineups = lineup_df
                
                if team_lineups.empty:
                    available_teams = []
                    if 'Target_Team' in lineup_df.columns:
                        available_teams = lineup_df['Target_Team'].unique()
                    elif 'Team' in lineup_df.columns:
                        available_teams = lineup_df['Team'].unique()
                        
                    self.show_message("No Team Lineups", 
                                    f"No lineups found for {team} in {os.path.basename(lineup_file)}.\n\nAvailable teams: {list(available_teams)}")
                    return
                    
                print(f"Found {len(team_lineups)} {team} players in lineups")
            
            # Create popup window to display stacked lineups
            self.create_lineup_popup(team, team_lineups, lineup_file)
            
        except Exception as e:
            self.show_message("Error", f"Error loading stacked lineups: {str(e)}\n\nDetails: {type(e).__name__}")
    
    def filter_fd_lineups_by_team(self, lineup_df, target_team):
        """Filter FanDuel format lineups to only show those containing players from target team"""
        try:
            # Load player slate to get team mappings
            slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today_clean.csv"
            if not os.path.exists(slate_file):
                slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
            
            if os.path.exists(slate_file):
                slate_df = safe_read_csv(slate_file)
                if slate_df is not None and 'Team' in slate_df.columns:
                    # Create player-to-team mapping
                    player_teams = {}
                    for _, player in slate_df.iterrows():
                        name_cols = ['Nickname', 'Name', 'Player', 'First Name', 'Last Name']
                        player_name = None
                        for col in name_cols:
                            if col in player and str(player[col]).strip():
                                player_name = str(player[col]).strip()
                                break
                        
                        if player_name and 'Team' in player:
                            player_teams[player_name] = player.get('Team', '')
                    
                    # Filter lineups that contain at least 2 players from target team (stack threshold)
                    filtered_lineups = []
                    position_cols = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF ', 'OF  ', 'Util']
                    
                    for _, lineup in lineup_df.iterrows():
                        team_player_count = 0
                        for pos_col in position_cols:
                            if pos_col in lineup:
                                player = str(lineup[pos_col]).strip()
                                if player and player != 'nan':
                                    # Check if player is from target team
                                    player_team = player_teams.get(player, '')
                                    if player_team == target_team:
                                        team_player_count += 1
                        
                        # Include lineup if it has 2+ players from target team (stack)
                        if team_player_count >= 2:
                            filtered_lineups.append(lineup)
                    
                    if filtered_lineups:
                        return pd.DataFrame(filtered_lineups)
            
            # If we can't filter properly, return empty DataFrame
            return pd.DataFrame()
            
        except Exception as e:
            print(f"Error filtering lineups by team: {e}")
            return pd.DataFrame()
    
    def export_team_to_fanduel(self, team, lineups_df):
        """Export team stack lineups to FanDuel CSV format"""
        try:
            # Load the FD slate to get player IDs and details
            slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today_clean.csv"
            if not os.path.exists(slate_file):
                slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
            
            if not os.path.exists(slate_file):
                self.show_message("Error", "Cannot find FanDuel slate file to export lineups.")
                return
                
            slate_df = safe_read_csv(slate_file)
            if slate_df is None:
                self.show_message("Error", "Cannot read FanDuel slate file.")
                return
            
            # Create player name to ID mapping from FD slate
            player_mapping = {}
            for _, player in slate_df.iterrows():
                nickname = player.get('Nickname', '')
                player_id = player.get('Id', '')
                if nickname and player_id:
                    player_mapping[nickname] = player_id
            
            # Filter lineups to only include lineups that contain the selected team
            # First, find which lineups contain players from the selected team
            team_lineups = set(lineups_df[lineups_df['Team'] == team]['Lineup_Number'].unique())
            
            if not team_lineups:
                self.show_message("Error", f"No lineups found containing {team} players.")
                return
            
            # Group by lineup number and create FanDuel format
            lineup_rows = []
            lineups_by_number = lineups_df.groupby('Lineup_Number')
            
            for lineup_num, lineup_players in lineups_by_number:
                # Only process lineups that contain the selected team
                if lineup_num not in team_lineups:
                    continue
                    
                # Initialize lineup row with FanDuel format - using correct column names
                lineup_row = {
                    'entry_id': f'3556{lineup_num:06d}',  # Generate entry ID
                    'contest_id': '119721-276198390',     # Example contest ID
                    'contest_name': f'{team} Stack Lineup {lineup_num}',
                    'entry_fee': '5',
                    'P': '', 'C/1B': '', '2B': '', '3B': '', 'SS': '', 
                    'OF': '', 'OF2': '', 'OF3': '', 'UTIL': ''
                }
                
                # Track OF positions filled
                of_count = 0
                
                for _, player in lineup_players.iterrows():
                    nickname = player.get('Nickname', player.get('Player', ''))
                    position = player.get('Position', '')
                    
                    # Get FanDuel player ID
                    player_id = player_mapping.get(nickname, '')
                    if not player_id:
                        print(f"Warning: Could not find FanDuel ID for {nickname}, using placeholder")
                        player_id = f"119721-{hash(nickname) % 1000000}"  # Generate placeholder ID
                    
                    # Use ID:PlayerName format like in your example
                    player_entry = f"{player_id}:{nickname}"
                    
                    # Map player to FanDuel position with fallback to UTIL
                    placed = False
                    
                    if position == 'P' and lineup_row['P'] == '':
                        lineup_row['P'] = player_entry
                        placed = True
                    elif position in ['C', '1B'] and lineup_row['C/1B'] == '':
                        lineup_row['C/1B'] = player_entry
                        placed = True
                    elif position == '2B' and lineup_row['2B'] == '':
                        lineup_row['2B'] = player_entry
                        placed = True
                    elif position == '3B' and lineup_row['3B'] == '':
                        lineup_row['3B'] = player_entry
                        placed = True
                    elif position == 'SS' and lineup_row['SS'] == '':
                        lineup_row['SS'] = player_entry
                        placed = True
                    elif position == 'OF' and of_count < 3:
                        if lineup_row['OF'] == '':
                            lineup_row['OF'] = player_entry
                            of_count += 1
                            placed = True
                        elif lineup_row['OF2'] == '':
                            lineup_row['OF2'] = player_entry
                            of_count += 1
                            placed = True
                        elif lineup_row['OF3'] == '':
                            lineup_row['OF3'] = player_entry
                            of_count += 1
                            placed = True
                    
                    # If not placed in primary position, try UTIL
                    if not placed and lineup_row['UTIL'] == '':
                        lineup_row['UTIL'] = player_entry
                        placed = True
                    
                    # If still not placed, try to fill any empty position
                    if not placed:
                        for pos in ['C/1B', '2B', '3B', 'SS', 'UTIL']:
                            if lineup_row[pos] == '':
                                lineup_row[pos] = player_entry
                                placed = True
                                break
                    
                    if placed:
                        print(f"  Placed {nickname} ({position}) in lineup {lineup_num}")
                    else:
                        print(f"  WARNING: Could not place {nickname} ({position}) in lineup {lineup_num}")
                
                # Debug: Show what we have before checking completeness
                print(f"Lineup {lineup_num} contents: {lineup_row}")
                
                # Only add complete lineups - be more lenient (require 8+ positions)
                required_positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
                filled_positions = sum(1 for pos in required_positions if lineup_row[pos] != '')
                print(f"Lineup {lineup_num}: {filled_positions}/9 filled positions")
                if filled_positions >= 8:  # More lenient - allow 8+ instead of requiring all 9
                    lineup_rows.append(lineup_row)
                    print(f"  ✓ Added lineup {lineup_num} to export")
                else:
                    print(f"  ✗ Skipped lineup {lineup_num} - not enough players")
            
            # Create DataFrame in FanDuel format
            if not lineup_rows:
                print(f"Found {len(lineup_rows)} complete lineups for {team}")
                self.show_message("Error", f"No complete {team} lineups found to export.\nFound {len(team_lineups)} lineups containing {team} players.")
                return
            
            # Convert to proper FanDuel format with correct OF column handling
            fd_rows = []
            for row in lineup_rows:
                fd_row = [
                    row['entry_id'],
                    row['contest_id'], 
                    row['contest_name'],
                    row['entry_fee'],
                    row['P'],
                    row['C/1B'],
                    row['2B'],
                    row['3B'],
                    row['SS'],
                    row['OF'],
                    row['OF2'],  # This will be the second OF column
                    row['OF3'],  # This will be the third OF column
                    row['UTIL']
                ]
                fd_rows.append(fd_row)
            
            # Create DataFrame with proper column names (multiple OF columns)
            fd_columns = ['entry_id', 'contest_id', 'contest_name', 'entry_fee', 'P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
            export_df = pd.DataFrame(fd_rows, columns=fd_columns)
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(os.path.dirname(__file__), "..", "fd_current_slate", f"{team}_STACK_FD_LINEUPS_{timestamp}.csv")
            export_df.to_csv(output_file, index=False)
            
            self.show_message("Export Successful", 
                            f"Exported {len(export_df)} {team} stack lineups to:\n{os.path.basename(output_file)}\n\nFanDuel-ready format!")
            
        except Exception as e:
            self.show_message("Export Error", f"Error exporting to FanDuel format: {str(e)}")
    
    def create_lineup_popup(self, team, lineups_df, source_file):
        """Create popup window showing stacked lineups for a team"""
        popup = tk.Toplevel(self.root)
        popup.title(f"🔥 {team} Stacked Lineups")
        popup.geometry("1000x700")
        popup.configure(bg=self.colors['bg'])
        
        # Header
        header_frame = tk.Frame(popup, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        title_label = tk.Label(header_frame, text=f"🔥 {team} Stack Lineups", 
                              font=('Arial', 16, 'bold'), 
                              fg=self.colors['accent'], bg=self.colors['bg'])
        title_label.pack(side=tk.LEFT)
        
        source_label = tk.Label(header_frame, text=f"Source: {os.path.basename(source_file)}", 
                               font=('Arial', 10), 
                               fg=self.colors['subtext'], bg=self.colors['bg'])
        source_label.pack(side=tk.RIGHT)
        
        # Check if this is FanDuel lineup format (position columns) or individual player format
        fd_positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'Util']
        is_fd_format = any(col in lineups_df.columns for col in fd_positions)
        
        # Lineup display
        lineup_frame = tk.LabelFrame(popup, text=f"{team} Complete Lineups",
                                    fg=self.colors['text'], bg=self.colors['card'],
                                    font=('Arial', 12, 'bold'))
        lineup_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if is_fd_format:
            # FanDuel lineup format - show complete lineups
            lineup_columns = ('Lineup', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3', 'Util')
            lineup_tree = ttk.Treeview(lineup_frame, columns=lineup_columns, show='headings', height=15)
            
            for col in lineup_columns:
                lineup_tree.heading(col, text=col)
                if col == 'Lineup':
                    lineup_tree.column(col, width=150, anchor=tk.W)
                else:
                    lineup_tree.column(col, width=90, anchor=tk.CENTER)
            
            # Process FanDuel lineup data
            for idx, lineup in lineups_df.iterrows():
                lineup_name = lineup.get('Lineup', f'Lineup_{idx+1}')
                
                # Extract player names from position columns, handling different OF column names
                players = []
                position_mapping = {
                    'C': lineup.get('C', ''),
                    '1B': lineup.get('1B', ''),
                    '2B': lineup.get('2B', ''),
                    '3B': lineup.get('3B', ''),
                    'SS': lineup.get('SS', ''),
                    'OF1': lineup.get('OF', ''),
                    'OF2': lineup.get('OF ', ''),
                    'OF3': lineup.get('OF  ', ''),
                    'Util': lineup.get('Util', '')
                }
                
                values = [lineup_name] + [str(pos_player).strip() for pos_player in position_mapping.values()]
                lineup_tree.insert('', 'end', values=values)
        else:
            # Individual player format
            lineup_columns = ('Player', 'Team', 'Position', 'Salary', 'Projection', 'Lineup')
            lineup_tree = ttk.Treeview(lineup_frame, columns=lineup_columns, show='headings', height=20)
            
            for col in lineup_columns:
                lineup_tree.heading(col, text=col)
                if col == 'Player':
                    lineup_tree.column(col, width=180, anchor=tk.W)
                elif col == 'Team':
                    lineup_tree.column(col, width=60, anchor=tk.CENTER)
                elif col == 'Position':
                    lineup_tree.column(col, width=80, anchor=tk.CENTER)
                elif col == 'Salary':
                    lineup_tree.column(col, width=90, anchor=tk.CENTER)
                elif col == 'Projection':
                    lineup_tree.column(col, width=90, anchor=tk.CENTER)
                elif col == 'Lineup':
                    lineup_tree.column(col, width=80, anchor=tk.CENTER)
            
            # Add data to treeview
            for _, player in lineups_df.iterrows():
                values = (
                    player.get('Nickname', player.get('Player', 'Unknown')),
                    player.get('Team', 'N/A'),  # Added team info
                    player.get('Position', 'Unknown'),
                    f"${player.get('Salary', 0):,}",
                    f"{player.get('Projected_FPPG', player.get('FPPG', 0)):.1f}",
                    player.get('Lineup_Number', player.get('Lineup', 1))
                )
                lineup_tree.insert('', 'end', values=values)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(lineup_frame, orient=tk.VERTICAL, command=lineup_tree.yview)
        lineup_tree.configure(yscrollcommand=scrollbar.set)
        
        lineup_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Summary
        summary_text = f"📊 {len(lineups_df)} lineups found for {team}"
        summary_label = tk.Label(popup, text=summary_text,
                               font=('Arial', 10), 
                               fg=self.colors['subtext'], bg=self.colors['bg'])
        summary_label.pack(pady=5)
        
        # Buttons frame
        buttons_frame = tk.Frame(popup, bg=self.colors['bg'])
        buttons_frame.pack(pady=10)
        
        # Export to FanDuel button
        export_btn = tk.Button(buttons_frame, text="📁 Export to FanDuel CSV", 
                              command=lambda: self.export_team_to_fanduel(team, lineups_df),
                              bg=self.colors['accent'], fg=self.colors['text'],
                              font=('Arial', 12, 'bold'), relief='flat')
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = tk.Button(buttons_frame, text="Close", command=popup.destroy,
                             bg=self.colors['danger'], fg=self.colors['text'],
                             font=('Arial', 12, 'bold'), relief='flat')
        close_btn.pack(side=tk.LEFT, padx=5)
    
    def show_message(self, title, message):
        """Show a message popup"""
        popup = tk.Toplevel(self.root)
        popup.title(title)
        popup.geometry("400x200")
        popup.configure(bg=self.colors['bg'])
        
        label = tk.Label(popup, text=message, font=('Arial', 12), 
                        fg=self.colors['text'], bg=self.colors['bg'], 
                        wraplength=350, justify=tk.LEFT)
        label.pack(expand=True, padx=20, pady=20)
        
        ok_btn = tk.Button(popup, text="OK", command=popup.destroy,
                          bg=self.colors['accent'], fg=self.colors['text'],
                          font=('Arial', 12, 'bold'), relief='flat')
        ok_btn.pack(pady=10)

    def refresh_gpp_data(self):
        """Refresh data for GPP analysis"""
        self.gpp_status_label.config(text="🔄 Refreshing data...", fg=self.colors['warning'])
        
        # Clear existing results
        self.elite_stacks_text.delete(1.0, tk.END)
        self.good_stacks_text.delete(1.0, tk.END)
        self.weather_stacks_text.delete(1.0, tk.END)
        self.strategy_text.delete(1.0, tk.END)
        
        # Add placeholder text
        self.elite_stacks_text.insert(tk.END, "Click 'Run GPP Analysis' to generate elite stack recommendations...")
        self.good_stacks_text.insert(tk.END, "Secondary stack targets will appear here...")
        self.weather_stacks_text.insert(tk.END, "Weather-based opportunities will be shown here...")
        self.strategy_text.insert(tk.END, "Implementation strategy will be displayed here...")
        
        self.gpp_status_label.config(text="Ready to analyze", fg=self.colors['subtext'])
        
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
            
            print("📋 Loading lineup data...")
            self.load_lineup_data()
            
            print("⚾ Loading scores data...")
            self.load_scores_data()
            
            print("🌤️ Loading weather data...")
            self.load_weather_data()
            
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
                            # Calculate dynamic thresholds based on actual data distribution
                            chalk_threshold = df[ownership_col].quantile(0.90)  # Top 10% ownership
                            contrarian_threshold = df[ownership_col].quantile(0.10)  # Bottom 10% ownership
                            
                            chalk_plays = len(df[df[ownership_col] > chalk_threshold])
                            contrarian_targets = len(df[df[ownership_col] < contrarian_threshold])
                        
                        if leverage_col:
                            # Calculate dynamic threshold for high-leverage plays
                            leverage_threshold = df[leverage_col].quantile(0.75)  # Top 25% leverage
                            value_plays = len(df[df[leverage_col] > leverage_threshold])
                        
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
        """Load pre-calculated stack analysis and add ownership data from ownership projections"""
        try:
            data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
            stack_files = []
            
            if os.path.exists(data_dir):
                for file in os.listdir(data_dir):
                    if 'team_stack_analysis' in file.lower() and file.endswith('.csv'):
                        stack_files.append(os.path.join(data_dir, file))
                
                if stack_files:
                    # Get most recent stack analysis file
                    stack_files.sort(key=os.path.getmtime, reverse=True)
                    stack_file = stack_files[0]
                    
                    print(f"⚡ Loading pre-calculated stacks from: {os.path.basename(stack_file)}")
                    stack_df = safe_read_csv(stack_file)
                    
                    # Also load ownership data to calculate team ownership
                    ownership_data = {}
                    ownership_files = []
                    for file in os.listdir(data_dir):
                        if 'ownership_projections' in file.lower() and file.endswith('.csv'):
                            ownership_files.append(os.path.join(data_dir, file))
                    
                    if ownership_files:
                        ownership_files.sort(key=os.path.getmtime, reverse=True)
                        ownership_file = ownership_files[0]
                        print(f"📊 Loading ownership data from: {os.path.basename(ownership_file)}")
                        ownership_df = safe_read_csv(ownership_file)
                        
                        if ownership_df is not None and 'team' in ownership_df.columns and 'ownership' in ownership_df.columns:
                            # Calculate average ownership by team (top 4 hitters)
                            for team in ownership_df['team'].unique():
                                team_players = ownership_df[ownership_df['team'] == team]
                                if 'projection' in team_players.columns:
                                    # Get top 4 hitters by projection for stack ownership
                                    top_hitters = team_players.nlargest(4, 'projection')
                                    avg_ownership = top_hitters['ownership'].mean() * 100  # Convert to percentage
                                    ownership_data[team] = avg_ownership
                    
                    if stack_df is not None and len(stack_df) > 0:
                        # Get today's slate teams to filter stack data
                        slate_teams = set()
                        # Use clean slate data (injured players removed)
                        slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today_clean.csv"
                        if not os.path.exists(slate_file):
                            # Fallback to original if clean doesn't exist
                            slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
                        if os.path.exists(slate_file):
                            slate_df = safe_read_csv(slate_file)
                            if slate_df is not None and 'team' in slate_df.columns:
                                slate_teams = set(slate_df['team'].unique())
                            elif slate_df is not None and 'Game' in slate_df.columns:
                                # Extract teams from Game column (e.g., "BOS@NYY" -> BOS, NYY)
                                for game in slate_df['Game'].unique():
                                    if '@' in game:
                                        away, home = game.split('@')
                                        slate_teams.add(away.strip())
                                        slate_teams.add(home.strip())
                        
                        if slate_teams:
                            print(f"🎯 Filtering stacks to {len(slate_teams)} teams on tonight's slate: {sorted(slate_teams)}")
                        
                        self.stack_data = []
                        rank = 1
                        for i, row in enumerate(stack_df.iterrows()):
                            _, row_data = row
                            team = row_data.get('team', '')
                            
                            # Only include teams that are actually playing tonight
                            if slate_teams and team not in slate_teams:
                                print(f"⏭️ Skipping {team} - not on tonight's slate")
                                continue
                            
                            stack_info = {
                                'rank': rank,
                                'team': team,
                                'projection': row_data.get('full_stack_fppg', 0),
                                'salary': row_data.get('full_stack_salary', 0),
                                'ownership': ownership_data.get(team, 0),  # Use calculated ownership or 0
                                'value': row_data.get('stack_value_score', 0),
                                'weather_mult': row_data.get('weather_multiplier', 1.0),
                                'vegas_mult': row_data.get('vegas_multiplier', 1.0),
                                'pitcher_mult': row_data.get('pitcher_multiplier', 1.0),
                                'opposing_pitcher': row_data.get('opposing_pitcher', 'Unknown'),
                                'difficulty': row_data.get('difficulty', 'AVERAGE'),
                                'players': f"Hitter Park | {team} Stack"
                            }
                            self.stack_data.append(stack_info)
                            rank += 1
                        
                        print(f"✅ Loaded {len(self.stack_data)} team stacks filtered to tonight's slate")
                        if slate_teams:
                            missing_teams = slate_teams - {stack['team'] for stack in self.stack_data}
                            if missing_teams:
                                print(f"⚠️ Teams on slate but missing from stack analysis: {sorted(missing_teams)}")
                        return
            
            # No current stack analysis found
            print("⚠️ No current stack analysis found - run ADVANCED_STACK_OPTIMIZER.py first")
            self.stack_data = []
            
        except Exception as e:
            print(f"❌ Error loading stack data: {e}")
            self.stack_data = []
    
    def load_lineup_data(self):
        """Load team lineup data from Rotowire extraction"""
        try:
            # Check for temp lineup data file created by Rotowire script
            lineup_file = "temp_lineup_data.json"
            pitcher_file = "temp_pitcher_data.json"
            
            lineups = {}
            pitchers = {}
            
            # Load lineup data
            if os.path.exists(lineup_file):
                with open(lineup_file, 'r') as f:
                    lineup_data = json.load(f)
                print(f"📋 Loaded lineup data: {len(lineup_data)} player assignments")
                
                # Organize by team
                for key, batting_order in lineup_data.items():
                    if '_' in key:
                        team, player = key.split('_', 1)
                        if team not in lineups:
                            lineups[team] = []
                        lineups[team].append({
                            'player': player,
                            'batting_order': batting_order
                        })
                
                # Sort lineups by batting order
                for team in lineups:
                    lineups[team].sort(key=lambda x: x['batting_order'])
            
            # Load pitcher data
            if os.path.exists(pitcher_file):
                with open(pitcher_file, 'r') as f:
                    pitchers = json.load(f)
                print(f"⚾ Loaded pitcher data: {len(pitchers)} starting pitchers")
            
            # Load FD slate to get confirmation status (use clean data)
            slate_df = None
            try:
                # Try clean slate first (injured players removed)
                slate_path = "../fd_current_slate/fd_slate_today_clean.csv"
                if not os.path.exists(slate_path):
                    slate_path = "../fd_current_slate/fd_slate_today.csv"
                slate_df = safe_read_csv(slate_path)
                if slate_df is not None:
                    clean_indicator = "clean" if "clean" in slate_path else "original"
                    print(f"📊 Loaded FD slate ({clean_indicator}): {len(slate_df)} players")
            except Exception as e:
                print(f"⚠️ Could not load FD slate: {e}")
            
            # Determine lineup status (confirmed vs expected)
            lineup_status = self.determine_lineup_status(lineups, slate_df)
            
            self.lineups_data = {
                'teams': lineups,
                'pitchers': pitchers,
                'status': lineup_status,
                'last_updated': datetime.now().strftime("%I:%M %p")
            }
            
            print(f"✅ Loaded lineups for {len(lineups)} teams")
            return len(lineups) > 0
            
        except Exception as e:
            print(f"❌ Error loading lineup data: {e}")
            self.lineups_data = {
                'teams': {},
                'pitchers': {},
                'status': {},
                'last_updated': 'Error'
            }
            return False
    
    def determine_lineup_status(self, lineups, slate_df):
        """Determine if lineups are confirmed or expected based on FD slate batting orders"""
        status = {}
        
        if slate_df is None:
            # If no slate data, assume all are expected
            for team in lineups:
                status[team] = 'expected'
            return status
        
        for team in lineups:
            # Check if batting orders in our lineup match FD slate
            confirmed_count = 0
            total_lineup_players = len(lineups[team])
            
            team_slate = slate_df[slate_df['Team'] == team]
            if len(team_slate) > 0:
                for lineup_player in lineups[team]:
                    rotowire_name = lineup_player['player']
                    expected_order = lineup_player['batting_order']
                    
                    # Try to match player in slate with more flexible matching
                    for _, slate_row in team_slate.iterrows():
                        slate_first = str(slate_row['First Name']).strip()
                        slate_last = str(slate_row['Last Name']).strip()
                        slate_full = f"{slate_first} {slate_last}"
                        slate_order = slate_row.get('Batting Order', 0)
                        
                        # Multiple matching strategies
                        name_match = False
                        
                        # Strategy 1: Full name contains check
                        if (rotowire_name.lower() in slate_full.lower() or 
                            slate_full.lower() in rotowire_name.lower()):
                            name_match = True
                        
                        # Strategy 2: Last name exact match + first name initial
                        elif slate_last.lower() in rotowire_name.lower():
                            # Check if first initial matches
                            if len(slate_first) > 0 and slate_first[0].lower() in rotowire_name.lower():
                                name_match = True
                        
                        # Strategy 3: Split and check parts
                        rotowire_parts = rotowire_name.replace('.', '').split()
                        slate_parts = slate_full.split()
                        
                        if len(rotowire_parts) >= 2 and len(slate_parts) >= 2:
                            # Check if last names match and first name/initial match
                            if (rotowire_parts[-1].lower() == slate_parts[-1].lower() and
                                (rotowire_parts[0][0].lower() == slate_parts[0][0].lower() or
                                 rotowire_parts[0].lower() == slate_parts[0].lower())):
                                name_match = True
                        
                        # If name matches and batting order matches
                        if name_match and slate_order == expected_order and slate_order > 0:
                            confirmed_count += 1
                            break
                
                # Consider confirmed if >60% of batting orders match (lowered threshold)
                if total_lineup_players > 0:
                    match_percentage = confirmed_count / total_lineup_players
                    if match_percentage > 0.6:
                        status[team] = 'confirmed'
                    else:
                        status[team] = 'expected'
                else:
                    status[team] = 'expected'
            else:
                status[team] = 'expected'
        
        return status
    
    def refresh_lineups_data(self):
        """Refresh lineup data by running Rotowire script and reloading"""
        def run_refresh():
            try:
                # Update button state to show refreshing
                self.refresh_lineups_btn.config(text="⏳ Refreshing...", state="disabled")
                self.lineups_status_label.config(text="🔄 Fetching latest lineups from Rotowire...", 
                                                fg=self.colors['warning'])
                
                # Run Rotowire script
                import subprocess
                result = subprocess.run(
                    ["python", "fetch_rotowire_lineups_enhanced.py"],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                
                if result.returncode == 0:
                    # Reload lineup data
                    if self.load_lineup_data():
                        self.update_lineup_display()
                        
                        # Show success status
                        confirmed_count = sum(1 for s in self.lineups_data.get('status', {}).values() if s == 'confirmed')
                        total_teams = len(self.lineups_data.get('teams', {}))
                        
                        self.lineups_status_label.config(
                            text=f"✅ Refreshed! {confirmed_count}/{total_teams} lineups confirmed",
                            fg=self.colors['success']
                        )
                        self.update_status("✅ Lineups refreshed successfully!")
                    else:
                        self.lineups_status_label.config(
                            text="⚠️ Refresh completed but no lineup data found",
                            fg=self.colors['warning']
                        )
                        self.update_status("⚠️ Refresh completed but no lineup data found")
                else:
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    self.lineups_status_label.config(
                        text=f"❌ Refresh failed: {error_msg[:50]}...",
                        fg=self.colors['danger']
                    )
                    self.update_status(f"❌ Refresh failed: {error_msg}")
                    
            except Exception as e:
                self.lineups_status_label.config(
                    text=f"❌ Error: {str(e)[:50]}...",
                    fg=self.colors['danger']
                )
                self.update_status(f"❌ Error refreshing lineups: {e}")
            finally:
                # Re-enable button
                self.refresh_lineups_btn.config(text="🔄 Refresh Lineups", state="normal")
        
        # Run in background thread
        threading.Thread(target=run_refresh, daemon=True).start()

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
    
    def load_scores_data(self):
        """Load live game scores data"""
        try:
            scores_file = "live_scores_today.json"
            
            if os.path.exists(scores_file):
                with open(scores_file, 'r') as f:
                    scores_data = json.load(f)
                
                games = scores_data.get('games', [])
                print(f"⚾ Loaded live scores: {len(games)} games")
                
                # Calculate stats
                live_count = len([g for g in games if g.get('status_code') in ['I', 'IR']])
                final_count = len([g for g in games if g.get('status_code') == 'F'])
                slate_games = [g for g in games if g.get('on_slate', False)]
                
                self.scores_data = {
                    'games': games,
                    'slate_games': slate_games,
                    'last_updated': scores_data.get('last_updated', '---'),
                    'live_count': live_count,
                    'final_count': final_count,
                    'total_games': len(games)
                }
                
                print(f"📊 Scores summary: {len(slate_games)} slate games, {live_count} live, {final_count} final")
                
                # Update metric cards
                self.update_scores_metrics()
                
                return True
            else:
                print("⚠️ No scores file found - run fetch_live_scores.py first")
                self.scores_data = {
                    'games': [],
                    'slate_games': [],
                    'last_updated': '---',
                    'live_count': 0,
                    'final_count': 0,
                    'total_games': 0
                }
                
                # Update metric cards with empty data
                self.update_scores_metrics()
                
                return False
                
        except Exception as e:
            print(f"❌ Error loading scores data: {e}")
            self.scores_data = {
                'games': [],
                'slate_games': [],
                'last_updated': 'Error',
                'live_count': 0,
                'final_count': 0,
                'total_games': 0
            }
            
            # Update metric cards with error state
            self.update_scores_metrics()
            
            return False
    
    def update_scores_metrics(self):
        """Update the scores metric cards"""
        try:
            if hasattr(self, 'scores_data') and self.scores_data:
                # Update Games Today metric
                slate_count = len(self.scores_data.get('slate_games', []))
                if hasattr(self, 'games_today_metric'):
                    self.games_today_metric.config(text=str(slate_count))
                
                # Update Live Games metric
                live_count = self.scores_data.get('live_count', 0)
                if hasattr(self, 'games_live_metric'):
                    self.games_live_metric.config(text=str(live_count))
                
                # Update Final Games metric
                final_count = self.scores_data.get('final_count', 0)
                if hasattr(self, 'games_final_metric'):
                    self.games_final_metric.config(text=str(final_count))
                
                # Update Last Updated metric
                last_updated = self.scores_data.get('last_updated', '---')
                if hasattr(self, 'last_score_update_metric'):
                    # Format timestamp if it's a full timestamp
                    try:
                        if 'T' in last_updated:
                            from datetime import datetime
                            dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                            formatted_time = dt.strftime('%I:%M %p')
                        else:
                            formatted_time = last_updated
                    except:
                        formatted_time = last_updated
                    
                    self.last_score_update_metric.config(text=formatted_time)
            else:
                # Set to default values if no data
                if hasattr(self, 'games_today_metric'):
                    self.games_today_metric.config(text="0")
                if hasattr(self, 'games_live_metric'):
                    self.games_live_metric.config(text="0")
                if hasattr(self, 'games_final_metric'):
                    self.games_final_metric.config(text="0")
                if hasattr(self, 'last_score_update_metric'):
                    self.last_score_update_metric.config(text="---")
                    
        except Exception as e:
            print(f"❌ Error updating scores metrics: {e}")
    
    def refresh_scores_data(self):
        """Refresh scores data by fetching latest from MLB API"""
        def run_refresh():
            try:
                # Update button state to show refreshing
                self.refresh_scores_btn.config(text="⏳ Refreshing...", state="disabled")
                self.scores_status_label.config(text="🔄 Fetching latest scores from MLB API...", 
                                               fg=self.colors['warning'])
                
                # Run live scores script
                import subprocess
                result = subprocess.run(
                    ["python", "fetch_live_scores.py"],
                    capture_output=True,
                    text=True,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                
                if result.returncode == 0:
                    # Reload scores data
                    if self.load_scores_data():
                        self.update_scores_display()
                        
                        # Show success status
                        live_count = self.scores_data.get('live_count', 0)
                        slate_count = len(self.scores_data.get('slate_games', []))
                        
                        self.scores_status_label.config(
                            text=f"✅ Updated! {slate_count} slate games, {live_count} live",
                            fg=self.colors['success']
                        )
                        self.update_status("✅ Scores refreshed successfully!")
                    else:
                        self.scores_status_label.config(
                            text="⚠️ Refresh completed but no score data found",
                            fg=self.colors['warning']
                        )
                        self.update_status("⚠️ Refresh completed but no score data found")
                else:
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    self.scores_status_label.config(
                        text=f"❌ Refresh failed: API error",
                        fg=self.colors['danger']
                    )
                    self.update_status(f"❌ Score refresh failed: {error_msg}")
                    
            except Exception as e:
                self.scores_status_label.config(
                    text=f"❌ Error: {str(e)[:50]}...",
                    fg=self.colors['danger']
                )
                self.update_status(f"❌ Error refreshing scores: {e}")
            finally:
                # Re-enable button
                self.refresh_scores_btn.config(text="🔄 Refresh Scores", state="normal")
        
        # Run in background thread
        threading.Thread(target=run_refresh, daemon=True).start()
    
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
    
    def load_weather_data(self):
        """Load current weather conditions for today's slate games"""
        try:
            # First load the actual slate to get the games (use clean data)
            slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today_clean.csv"
            if not os.path.exists(slate_file):
                slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
            data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
            weather_file = os.path.join(data_dir, 'weather_today.csv')
            
            slate_games = []
            if os.path.exists(slate_file):
                slate_df = safe_read_csv(slate_file)
                if slate_df is not None and 'Game' in slate_df.columns:
                    # Get unique games from slate and extract home teams
                    unique_games = slate_df['Game'].unique()
                    for game in unique_games:
                        if '@' in game:
                            away_team, home_team = game.split('@')
                            slate_games.append({
                                'game': game,
                                'home_team': home_team.strip(),
                                'away_team': away_team.strip()
                            })
                    print(f"🎯 Found {len(slate_games)} games on tonight's slate")
            
            if os.path.exists(weather_file) and slate_games:
                weather_df = safe_read_csv(weather_file)
                
                if weather_df is not None and len(weather_df) > 0:
                    # Clean and process weather data for slate games only
                    weather_games = []
                    
                    # Create mapping for team abbreviations to match weather data
                    team_mappings = {
                        'NYY': ['NYY', 'Yankees', 'New York Yankees'],
                        'BAL': ['BAL', 'Orioles', 'Baltimore'],
                        'WSH': ['WSH', 'Nationals', 'Washington'],
                        'SD': ['SD', 'Padres', 'San Diego'],
                        'TB': ['TB', 'Rays', 'Tampa Bay'],
                        'BOS': ['BOS', 'Red Sox', 'Boston'],
                        'HOU': ['HOU', 'Astros', 'Houston'],
                        'NYM': ['NYM', 'Mets', 'New York Mets'],
                        'SF': ['SF', 'Giants', 'San Francisco'],
                        'STL': ['STL', 'Cardinals', 'St. Louis']
                    }
                    
                    for slate_game in slate_games:
                        home_team = slate_game['home_team']
                        game_matchup = slate_game['game']
                        
                        # Find weather data for this home team
                        weather_row = None
                        
                        # Try exact match first
                        if 'home_team' in weather_df.columns:
                            exact_match = weather_df[weather_df['home_team'] == home_team]
                            if len(exact_match) > 0:
                                weather_row = exact_match.iloc[0]
                        
                        # Try game column match
                        if weather_row is None and 'game' in weather_df.columns:
                            game_match = weather_df[weather_df['game'] == game_matchup]
                            if len(game_match) > 0:
                                weather_row = game_match.iloc[0]
                        
                        # Try fuzzy matching with team mappings
                        if weather_row is None:
                            possible_names = team_mappings.get(home_team, [home_team])
                            for col in weather_df.columns:
                                if any(name.lower() in str(weather_df[col].values).lower() for name in possible_names):
                                    for _, row in weather_df.iterrows():
                                        if any(name.lower() in str(row[col]).lower() for name in possible_names):
                                            weather_row = row
                                            break
                                if weather_row is not None:
                                    break
                        
                        # Use weather data if found, otherwise create placeholder
                        if weather_row is not None:
                            temp = weather_row.get('temperature', 75)
                            humidity = weather_row.get('humidity', 50)
                            wind_speed = weather_row.get('wind_speed', 5)
                            wind_deg = weather_row.get('wind_deg', 0)
                            condition = weather_row.get('condition', 'Unknown')
                        else:
                            # Default values for games without weather data
                            temp = 75
                            humidity = 50
                            wind_speed = 5
                            wind_deg = 0
                            condition = 'No Data'
                        
                        # Determine DFS impact
                        impact_factors = []
                        if temp > 85:
                            impact_factors.append("🔥Hot")
                        elif temp < 60:
                            impact_factors.append("❄️Cold")
                        
                        if wind_speed > 10:
                            # Wind direction impact
                            if 90 <= wind_deg <= 270:  # Wind blowing out
                                impact_factors.append("💨Out")
                            else:
                                impact_factors.append("💨In")
                        
                        if humidity < 40:
                            impact_factors.append("🌵Dry")
                        elif humidity > 80:
                            impact_factors.append("💧Humid")
                        
                        # Check for dome stadiums (always controlled conditions) - Updated for 2025
                        dome_teams = ['HOU']  # Only Minute Maid Park now (TB plays outdoors at Steinbrenner Field)
                        if home_team in dome_teams:
                            impact_factors = ["🏟️Dome"]
                            condition = "Controlled"
                            temp = 72
                            humidity = 50
                            wind_speed = 0
                        
                        if 'clear' in condition.lower() or 'sunny' in condition.lower():
                            impact_factors.append("☀️Clear")
                        elif 'rain' in condition.lower() or 'storm' in condition.lower():
                            impact_factors.append("🌧️Rain")
                        
                        dfs_impact = " ".join(impact_factors) if impact_factors else "Neutral"
                        
                        weather_game = {
                            'game': game_matchup,
                            'home_team': home_team,
                            'temperature': f"{temp:.0f}°F",
                            'humidity': f"{humidity:.0f}%",
                            'wind_speed': f"{wind_speed:.0f} mph",
                            'wind_direction': f"{wind_deg:.0f}°",
                            'condition': condition,
                            'dfs_impact': dfs_impact,
                            'temp_numeric': temp,
                            'wind_numeric': wind_speed,
                            'wind_deg_numeric': wind_deg
                        }
                        weather_games.append(weather_game)
                    
                    self.weather_data = weather_games
                    print(f"🌤️ Loaded weather for {len(weather_games)} slate games")
                else:
                    print("⚠️ Weather file is empty")
                    self.weather_data = []
            else:
                if not slate_games:
                    print("⚠️ No games found in slate file")
                else:
                    print("⚠️ Weather file not found")
                self.weather_data = []
                
        except Exception as e:
            print(f"❌ Error loading weather data: {e}")
            self.weather_data = []
            
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
                
                # Calculate dynamic thresholds for tier classification
                players_data = self.ownership_data.get('players', [])
                if players_data:
                    ownerships = [p.get('ownership', p.get('projected_ownership', p.get('own_proj', 0))) for p in players_data]
                    leverages = []
                    for p in players_data:
                        lev = 0
                        for col in ['leverage', 'leverage_score']:
                            if col in p:
                                lev = p[col]
                                break
                        leverages.append(lev)
                    
                    import numpy as np
                    chalk_threshold = np.percentile([o for o in ownerships if o > 0], 90) if any(o > 0 for o in ownerships) else 1.0
                    contrarian_threshold = np.percentile([o for o in ownerships if o > 0], 10) if any(o > 0 for o in ownerships) else 0.0
                    leverage_threshold = np.percentile([l for l in leverages if l > 0], 75) if any(l > 0 for l in leverages) else 1.0
                else:
                    chalk_threshold = 1.0  # Impossible threshold if no data
                    contrarian_threshold = 0.0  # No threshold if no data
                    leverage_threshold = 1.0  # Impossible threshold if no data
                
                for i, player in enumerate(self.ownership_data.get('players', [])):  # Show all players
                    values = []
                    values.append(player.get('player_name', player.get('Player', 'Unknown')))
                    values.append(player.get('position', player.get('Position', 'N/A')))
                    values.append(player.get('team', player.get('Team', 'N/A')))
                    values.append(f"${player.get('salary', player.get('Salary', 0)):,}")
                    values.append(f"{player.get('projection', player.get('Projection', 0)):.1f}")
                    
                    # Ownership - use actual data from file
                    ownership = player.get('ownership', player.get('projected_ownership', player.get('own_proj', 0)))
                    values.append(f"{ownership*100:.1f}%" if ownership else "0.0%")
                    
                    # Leverage
                    leverage = 0
                    for col in ['leverage', 'leverage_score']:
                        if col in player:
                            leverage = player[col]
                            break
                    values.append(f"{leverage:.2f}" if leverage else "0.00")
                    
                    # Tier - use dynamic thresholds
                    if ownership > chalk_threshold:
                        tier = "Chalk"
                    elif ownership < contrarian_threshold:
                        tier = "Contrarian"
                    elif leverage > leverage_threshold:
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
                    
                    # Find best weather boost
                    weather_stack = max(self.stack_data, key=lambda x: x.get('weather_mult', 1.0))
                    weather_multiplier = weather_stack.get('weather_mult', 1.0)
                    if weather_multiplier > 1.0:
                        boost_pct = f"+{round((weather_multiplier - 1) * 100)}%"
                        self.weather_stack_metric.config(text=f"{weather_stack['team']} {boost_pct}")
                    else:
                        self.weather_stack_metric.config(text="No Boost")
            
            # Update lineup data
            self.update_lineup_display()
            
            # Update scores data
            self.update_scores_display()
            
            # Update weather data
            if self.weather_data:
                # Clear existing weather data
                for item in self.weather_tree.get_children():
                    self.weather_tree.delete(item)
                
                # Populate weather table
                wind_games = 0
                hot_games = 0
                dome_games = 0
                best_conditions_game = ""
                best_score = 0
                
                for game in self.weather_data:
                    values = [
                        game['game'],
                        game['home_team'],
                        game['temperature'],
                        game['humidity'],
                        game['wind_speed'],
                        game['wind_direction'],
                        game['condition'],
                        game['dfs_impact']
                    ]
                    self.weather_tree.insert('', 'end', values=values)
                    
                    # Calculate summary metrics
                    temp = game['temp_numeric']
                    wind = game['wind_numeric']
                    wind_deg = game['wind_deg_numeric']
                    
                    if wind > 10 and 90 <= wind_deg <= 270:  # Wind blowing out
                        wind_games += 1
                    
                    if temp > 85:
                        hot_games += 1
                    
                    # Calculate best conditions score (temp 70-85, low wind in, clear skies)
                    conditions_score = 0
                    if 70 <= temp <= 85:
                        conditions_score += 3
                    if wind < 10:
                        conditions_score += 2
                    elif wind > 10 and 90 <= wind_deg <= 270:
                        conditions_score += 1  # Wind out is good too
                    if 'clear' in game['condition'].lower() or 'sunny' in game['condition'].lower():
                        conditions_score += 2
                    
                    if conditions_score > best_score:
                        best_score = conditions_score
                        best_conditions_game = game['home_team']
                
                # Update weather summary metrics
                self.wind_games_metric.config(text=str(wind_games))
                self.hot_games_metric.config(text=str(hot_games))
                self.dome_games_metric.config(text=str(dome_games))
                self.weather_score_metric.config(text=best_conditions_game if best_conditions_game else "TBD")
                
                # Update enhanced weather display
                self.update_weather_display()
            
            # Update debug info
            self.update_debug_text()
            
        except Exception as e:
            print(f"GUI update error: {e}")
            
    def update_weather_display(self):
        """Update enhanced weather display with detailed analysis"""
        try:
            if not hasattr(self, 'weather_tree') or not self.weather_data:
                return
                
            # Clear existing weather data
            for item in self.weather_tree.get_children():
                self.weather_tree.delete(item)
            
            # Stadium park factors (based on actual MLB data)
            park_factors = {
                'NYY': 1.05,  # Yankee Stadium - short right field
                'BAL': 1.02,  # Camden Yards - hitter friendly
                'WSH': 0.98,  # Nationals Park - neutral to slight pitcher
                'SD': 0.95,   # Petco Park - pitcher friendly
                'TB': 1.00,   # Tropicana Field - dome, neutral
                'BOS': 1.08,  # Fenway Park - Green Monster
                'HOU': 1.03,  # Minute Maid Park - short left field
                'NYM': 0.97,  # Citi Field - pitcher friendly
                'SF': 0.92,   # Oracle Park - very pitcher friendly
                'STL': 1.01   # Busch Stadium - neutral
            }
            
            insights = []
            wind_out_games = []
            hot_weather_games = []
            best_weather_games = []
            
            for game in self.weather_data:
                home_team = game['home_team']
                temp = game['temp_numeric']
                wind = game['wind_numeric']
                wind_deg = game['wind_deg_numeric']
                
                # Get park factor
                park_factor = park_factors.get(home_team, 1.00)
                
                # Calculate comprehensive weather score
                weather_score = 5.0  # Base score
                
                # Temperature impact
                if 75 <= temp <= 85:
                    weather_score += 2  # Ideal hitting temperature
                    temp_impact = "Perfect"
                elif temp > 85:
                    weather_score += 1  # Hot helps ball carry
                    temp_impact = "Hot+"
                    hot_weather_games.append(game['game'])
                elif temp < 65:
                    weather_score -= 1  # Cold air is denser
                    temp_impact = "Cold-"
                else:
                    temp_impact = "Good"
                
                # Wind impact
                if wind > 15:
                    if 90 <= wind_deg <= 270:  # Blowing out
                        weather_score += 3
                        wind_impact = "Strong Out++"
                        wind_out_games.append(game['game'])
                    else:  # Blowing in
                        weather_score -= 2
                        wind_impact = "Strong In--"
                elif wind > 10:
                    if 90 <= wind_deg <= 270:
                        weather_score += 2
                        wind_impact = "Out+"
                        wind_out_games.append(game['game'])
                    else:
                        weather_score -= 1
                        wind_impact = "In-"
                elif wind < 5:
                    weather_score += 0.5
                    wind_impact = "Calm"
                else:
                    wind_impact = "Light"
                
                # Condition impact
                condition = game['condition'].lower()
                if 'clear' in condition or 'sunny' in condition:
                    weather_score += 1
                    condition_impact = "Clear"
                elif 'cloud' in condition:
                    condition_impact = "Cloudy"
                elif 'rain' in condition or 'storm' in condition:
                    weather_score -= 2
                    condition_impact = "Rain Risk"
                else:
                    condition_impact = "Unknown"
                
                # Dome override - Updated for 2025 season
                if home_team == 'TB':
                    # TB now plays at George M. Steinbrenner Field (outdoor) due to Tropicana Field hurricane damage
                    weather_score = weather_score  # Keep calculated weather score, no dome override
                    condition_impact = condition_impact  # Keep actual weather conditions
                    # Don't override wind/temp since it's now outdoor
                elif home_team == 'HOU' and 'retractable' not in condition.lower():
                    # HOU still has retractable roof at Minute Maid Park
                    weather_score = 6.0  # Controlled conditions
                    condition_impact = "Dome"
                    wind_impact = "None"
                    temp_impact = "Controlled"
                
                # Park factor integration
                combined_score = weather_score * park_factor
                
                # DFS impact summary
                impact_parts = []
                if temp_impact != "Good":
                    impact_parts.append(temp_impact)
                if wind_impact != "Light":
                    impact_parts.append(wind_impact)
                if condition_impact != "Clear":
                    impact_parts.append(condition_impact)
                
                if combined_score >= 7.5:
                    impact_parts.append("🔥Elite")
                    best_weather_games.append(game['game'])
                elif combined_score >= 6.5:
                    impact_parts.append("⭐Excellent")
                    best_weather_games.append(game['game'])
                elif combined_score >= 5.5:
                    impact_parts.append("✅Good")
                elif combined_score < 4.5:
                    impact_parts.append("❌Avoid")
                
                dfs_impact_enhanced = " | ".join(impact_parts) if impact_parts else "Neutral"
                
                # Stadium name mapping - Updated for 2025 season
                stadium_names = {
                    'NYY': 'Yankee Stadium',
                    'BAL': 'Camden Yards', 
                    'WSH': 'Nationals Park',
                    'SD': 'Petco Park',
                    'TB': 'Steinbrenner Field',  # Temporary home due to Tropicana Field hurricane damage
                    'BOS': 'Fenway Park',
                    'HOU': 'Minute Maid Park',
                    'NYM': 'Citi Field',
                    'SF': 'Oracle Park',
                    'STL': 'Busch Stadium'
                }
                
                stadium_name = stadium_names.get(home_team, f"{home_team} Stadium")
                
                # Insert enhanced row data
                values = [
                    game['game'],
                    stadium_name,
                    game['temperature'],
                    game['humidity'],
                    game['wind_speed'],
                    f"{wind_deg}° {self.get_wind_direction(wind_deg)}",
                    game['condition'],
                    f"{park_factor:.2f}",
                    dfs_impact_enhanced,
                    f"{combined_score:.1f}/10"
                ]
                
                # Color coding for weather score
                if combined_score >= 7.5:
                    self.weather_tree.insert('', 'end', values=values, tags=('excellent',))
                elif combined_score >= 6.5:
                    self.weather_tree.insert('', 'end', values=values, tags=('good',))
                elif combined_score < 4.5:
                    self.weather_tree.insert('', 'end', values=values, tags=('poor',))
                else:
                    self.weather_tree.insert('', 'end', values=values)
            
            # Configure row colors
            self.weather_tree.tag_configure('excellent', background='#E8F5E8')
            self.weather_tree.tag_configure('good', background='#FFF8E1')
            self.weather_tree.tag_configure('poor', background='#FFEBEE')
            
            # Generate insights
            if wind_out_games:
                insights.append(f"🌪️ WIND ADVANTAGE: {', '.join(wind_out_games)} have favorable wind conditions for offense")
            
            if hot_weather_games:
                insights.append(f"🔥 HOT WEATHER BOOST: {', '.join(hot_weather_games)} benefit from hot air helping ball carry")
            
            if best_weather_games:
                insights.append(f"⭐ PREMIUM CONDITIONS: {', '.join(best_weather_games)} have elite weather for high-scoring games")
            
            # Park-specific insights
            hitter_parks = [game['game'] for game in self.weather_data if park_factors.get(game['home_team'], 1.0) > 1.05]
            if hitter_parks:
                insights.append(f"🏟️ HITTER-FRIENDLY PARKS: {', '.join(hitter_parks)} have park factors favoring offense")
            
            dome_games = [game['game'] for game in self.weather_data if game['home_team'] in ['HOU']]  # Updated: TB now outdoor
            if dome_games:
                insights.append(f"🏠 CONTROLLED ENVIRONMENT: {', '.join(dome_games)} played in climate-controlled domes")
            
            # Special note for TB's temporary venue
            tb_games = [game['game'] for game in self.weather_data if game['home_team'] == 'TB']
            if tb_games:
                insights.append(f"⚾ OUTDOOR VENUE: {', '.join(tb_games)} at Steinbrenner Field (TB's temporary home due to Tropicana Field damage)")
            
            if not insights:
                insights = ["✅ Neutral weather conditions across all games today"]
            
            # Update summary metric cards with actual counts
            try:
                wind_count = len(wind_out_games)
                hot_count = len(hot_weather_games) 
                dome_count = len(dome_games)
                best_game = best_weather_games[0].split('@')[1] if best_weather_games else "TBD"
                
                # Update the metric cards
                if hasattr(self, 'wind_games_metric'):
                    # Find the value label in the metric card and update it
                    for widget in self.wind_games_metric.winfo_children():
                        if isinstance(widget, tk.Label) and widget.cget('font')[2] == 'bold' and widget.cget('font')[1] == 24:
                            widget.config(text=str(wind_count))
                            break
                            
                if hasattr(self, 'hot_games_metric'):
                    for widget in self.hot_games_metric.winfo_children():
                        if isinstance(widget, tk.Label) and widget.cget('font')[2] == 'bold' and widget.cget('font')[1] == 24:
                            widget.config(text=str(hot_count))
                            break
                            
                if hasattr(self, 'dome_games_metric'):
                    for widget in self.dome_games_metric.winfo_children():
                        if isinstance(widget, tk.Label) and widget.cget('font')[2] == 'bold' and widget.cget('font')[1] == 24:
                            widget.config(text=str(dome_count))
                            break
                            
                if hasattr(self, 'weather_score_metric'):
                    for widget in self.weather_score_metric.winfo_children():
                        if isinstance(widget, tk.Label) and widget.cget('font')[2] == 'bold' and widget.cget('font')[1] == 24:
                            widget.config(text=best_game)
                            break
                            
            except Exception as card_error:
                print(f"Error updating metric cards: {card_error}")
            
            # Update insights text
            if hasattr(self, 'insights_text'):
                self.insights_text.delete(1.0, tk.END)
                insights_content = "\n• ".join([""] + insights)
                self.insights_text.insert(1.0, insights_content)
                self.insights_text.config(state=tk.DISABLED)
                
        except Exception as e:
            print(f"Weather display update error: {e}")
    
    def get_wind_direction(self, degrees):
        """Convert wind degrees to compass direction"""
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        index = round(degrees / 22.5) % 16
        return directions[index]
            
    def update_lineup_display(self):
        """Update lineup display with team lineups and confirmation status"""
        try:
            if not self.lineups_data or not self.lineups_data.get('teams'):
                # Clear existing content
                for widget in self.lineups_content_frame.winfo_children():
                    widget.destroy()
                
                # Show no data message
                no_data_label = tk.Label(self.lineups_content_frame,
                                       text="⚠️ No lineup data available\\nRun 'Refresh Lineups' to fetch from Rotowire",
                                       font=('Arial', 14),
                                       fg=self.colors['subtext'],
                                       bg=self.colors['bg'],
                                       justify=tk.CENTER)
                no_data_label.pack(pady=50)
                return
            
            teams = self.lineups_data['teams']
            pitchers = self.lineups_data.get('pitchers', {})
            status = self.lineups_data.get('status', {})
            
            # Update metrics
            confirmed_count = sum(1 for s in status.values() if s == 'confirmed')
            expected_count = sum(1 for s in status.values() if s == 'expected')
            total_teams = len(teams)
            coverage_pct = int((total_teams / 10) * 100) if total_teams > 0 else 0
            
            self.confirmed_lineups_metric.config(text=str(confirmed_count))
            self.expected_lineups_metric.config(text=str(expected_count))
            self.coverage_metric.config(text=f"{coverage_pct}%")
            self.last_updated_metric.config(text=self.lineups_data.get('last_updated', '---'))
            
            # Update status label
            if hasattr(self, 'lineups_status_label'):
                if confirmed_count == total_teams and total_teams > 0:
                    self.lineups_status_label.config(
                        text=f"✅ All {total_teams} lineups confirmed!",
                        fg=self.colors['success']
                    )
                elif confirmed_count > 0:
                    self.lineups_status_label.config(
                        text=f"⚡ {confirmed_count}/{total_teams} lineups confirmed",
                        fg=self.colors['warning']
                    )
                else:
                    self.lineups_status_label.config(
                        text=f"⏳ All {total_teams} lineups are expected/projected",
                        fg=self.colors['subtext']
                    )
            
            # Clear existing content
            for widget in self.lineups_content_frame.winfo_children():
                widget.destroy()
            
            # Create team lineup cards
            teams_per_row = 2
            current_row = 0
            current_col = 0
            
            for team in sorted(teams.keys()):
                lineup = teams[team]
                team_status = status.get(team, 'expected')
                
                # Create row frame if needed
                if current_col == 0:
                    row_frame = tk.Frame(self.lineups_content_frame, bg=self.colors['bg'])
                    row_frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Create team card
                team_frame = tk.Frame(row_frame, bg=self.colors['card'], relief='solid', bd=1)
                team_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
                
                # Team header
                header_color = self.colors['success'] if team_status == 'confirmed' else self.colors['warning']
                status_icon = "✅" if team_status == 'confirmed' else "⏳"
                status_text = "CONFIRMED" if team_status == 'confirmed' else "EXPECTED"
                
                header_frame = tk.Frame(team_frame, bg=header_color)
                header_frame.pack(fill=tk.X, pady=2)
                
                team_label = tk.Label(header_frame,
                                    text=f"{status_icon} {team} - {status_text}",
                                    font=('Arial', 12, 'bold'),
                                    fg=self.colors['text'],
                                    bg=header_color)
                team_label.pack(pady=5)
                
                # Starting pitcher info
                pitcher_info = None
                for pitcher_name, pitcher_data in pitchers.items():
                    # Simple name matching - could be improved
                    if any(part.lower() in pitcher_name.lower() for part in [team.lower()]):
                        pitcher_info = pitcher_data
                        break
                
                if pitcher_info:
                    pitcher_frame = tk.Frame(team_frame, bg=self.colors['card'])
                    pitcher_frame.pack(fill=tk.X, padx=5, pady=2)
                    
                    pitcher_label = tk.Label(pitcher_frame,
                                           text=f"⚾ SP: {list(pitchers.keys())[0] if pitchers else 'Unknown'} ({pitcher_info.get('handedness', '?')}) {pitcher_info.get('era', '?.??')} ERA",
                                           font=('Arial', 9),
                                           fg=self.colors['subtext'],
                                           bg=self.colors['card'])
                    pitcher_label.pack()
                
                # Lineup display
                lineup_frame = tk.Frame(team_frame, bg=self.colors['card'])
                lineup_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                
                for player in lineup[:9]:  # Show top 9 only
                    order = player['batting_order']
                    name = player['player']
                    
                    player_label = tk.Label(lineup_frame,
                                          text=f"{order}. {name}",
                                          font=('Consolas', 9),
                                          fg=self.colors['text'],
                                          bg=self.colors['card'],
                                          anchor='w')
                    player_label.pack(fill=tk.X, pady=1)
                
                # Move to next position
                current_col += 1
                if current_col >= teams_per_row:
                    current_col = 0
                    current_row += 1
                    
        except Exception as e:
            print(f"❌ Error updating lineup display: {e}")
            # Show error message
            for widget in self.lineups_content_frame.winfo_children():
                widget.destroy()
            
            error_label = tk.Label(self.lineups_content_frame,
                                 text=f"⚠️ Error loading lineups:\\n{str(e)}",
                                 font=('Arial', 12),
                                 fg=self.colors['danger'],
                                 bg=self.colors['bg'],
                                 justify=tk.CENTER)
            error_label.pack(pady=20)
    
    def update_scores_display(self):
        """Update scores display with live game data"""
        try:
            # Clear existing items
            for item in self.scores_tree.get_children():
                self.scores_tree.delete(item)
            
            if not self.scores_data or 'games' not in self.scores_data:
                # Show no data message  
                self.scores_tree.insert('', tk.END, values=(
                    'No game data available', '', '', '', '', '', '', 'Click refresh to load scores'
                ))
                return
            
            games = self.scores_data['games']
            if not games:
                self.scores_tree.insert('', tk.END, values=(
                    'No games found', '', '', '', '', '', '', 'Check if games are scheduled today'
                ))
                return
            
            # Add game data to tree
            for game in games:
                game_id = game.get('game_pk', 'Unknown')
                status = game.get('status', 'Unknown')
                inning = game.get('inning', '')
                
                # Get individual team data
                away_team = game.get('away_team', 'Unknown')
                home_team = game.get('home_team', 'Unknown')
                away_score = game.get('away_score', '')
                home_score = game.get('home_score', '')
                
                # Format scores - show empty if not available
                away_score_display = str(away_score) if away_score != '' else ''
                home_score_display = str(home_score) if home_score != '' else ''
                
                # Format last updated
                updated = game.get('last_updated', 'Unknown')
                if updated != 'Unknown':
                    try:
                        # Convert to readable format if needed
                        from datetime import datetime
                        if 'T' in updated:
                            dt = datetime.fromisoformat(updated.replace('Z', '+00:00'))
                            updated = dt.strftime('%I:%M %p')
                    except:
                        pass
                
                # Add to tree with all 8 columns
                self.scores_tree.insert('', tk.END, values=(
                    f"Game {game_id}", status, inning, away_team, away_score_display, home_team, home_score_display, updated
                ))
            
            # Update summary stats
            slate_count = len(self.scores_data.get('slate_games', []))
            live_count = self.scores_data.get('live_count', 0)
            final_count = self.scores_data.get('final_count', 0)
            
            self.scores_status_label.config(
                text=f"📊 {slate_count} slate games • {live_count} live • {final_count} final",
                fg=self.colors['text']
            )
            
        except Exception as e:
            print(f"❌ Error updating scores display: {e}")
            # Show error in tree
            for item in self.scores_tree.get_children():
                self.scores_tree.delete(item)
            self.scores_tree.insert('', tk.END, values=(
                'Error loading scores', str(e), '', '', '', '', '', 'Try refreshing'
            ))

    def update_debug_text(self):
        """Update debug information"""
        try:
            self.debug_text.delete(1.0, tk.END)
            content = f"🔧 DEBUG INFORMATION\\n\\n"
            content += f"Data Loaded: {'✅ Yes' if self.data_loaded else '❌ No'}\\n"
            content += f"Ownership Players: {len(self.ownership_data.get('players', []))}\\n"
            content += f"Stack Teams: {len(self.stack_data)}\\n"
            content += f"Lineup Teams: {len(self.lineups_data.get('teams', {}))}\\n\\n"
            
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
    
    def update_status(self, message):
        """Update the main status label"""
        try:
            if hasattr(self, 'status_label'):
                # Determine color based on message content
                if "✅" in message or "success" in message.lower():
                    color = self.colors['success']
                elif "⚠️" in message or "warning" in message.lower():
                    color = self.colors['warning']
                elif "❌" in message or "error" in message.lower() or "failed" in message.lower():
                    color = self.colors['danger']
                else:
                    color = self.colors['text']
                
                self.status_label.config(text=message, fg=color)
                
                # Also log to debug
                self.debug_log(message)
        except Exception as e:
            print(f"❌ Error updating status: {e}")
            
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
    
    def import_actual_ownership(self):
        """Import actual ownership data from FanDuel contest results"""
        try:
            from tkinter import filedialog, messagebox
            
            # Let user select actual ownership file
            file_path = filedialog.askopenfilename(
                title="Select Actual Ownership Data",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir="../data"
            )
            
            if not file_path:
                return
            
            # Create input dialog for actual ownership data
            self.create_ownership_input_dialog(file_path)
            
        except Exception as e:
            self.show_message("Import Error", f"Error importing ownership data: {str(e)}")
    
    def create_ownership_input_dialog(self, file_path=None):
        """Create dialog for inputting actual ownership percentages"""
        dialog = tk.Toplevel(self.root)
        dialog.title("📊 Input Actual Ownership Data")
        dialog.geometry("800x600")
        dialog.configure(bg=self.colors['bg'])
        
        # Header
        header = tk.Label(dialog, text="Input Actual Ownership from FanDuel Contest",
                         bg=self.colors['bg'], fg=self.colors['text'],
                         font=('Arial', 16, 'bold'))
        header.pack(pady=10)
        
        # Instructions
        instructions = tk.Label(dialog, 
                               text="Enter the actual ownership % for each player from your FanDuel contest results.\nLeave blank for players not in the contest.",
                               bg=self.colors['bg'], fg=self.colors['text'],
                               font=('Arial', 10))
        instructions.pack(pady=5)
        
        # Scrollable frame
        canvas = tk.Canvas(dialog, bg=self.colors['bg'])
        scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Load current projections
        proj_file = self.find_latest_ownership_file()
        if proj_file:
            proj_df = safe_read_csv(proj_file)
            if proj_df is not None:
                self.ownership_entries = {}
                
                # Create input fields for each player
                for idx, row in proj_df.iterrows():
                    player_frame = tk.Frame(scrollable_frame, bg=self.colors['card'], relief='solid', bd=1)
                    player_frame.pack(fill=tk.X, padx=10, pady=2)
                    
                    # Player info
                    player_info = f"{row['player_name']} ({row['position']}, {row['team']}) - Proj: {row['ownership']*100:.1f}%"
                    tk.Label(player_frame, text=player_info, bg=self.colors['card'], fg=self.colors['text'],
                            font=('Arial', 10), anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
                    
                    # Actual ownership input
                    tk.Label(player_frame, text="Actual %:", bg=self.colors['card'], fg=self.colors['text'],
                            font=('Arial', 10)).pack(side=tk.RIGHT, padx=5)
                    
                    entry_var = tk.StringVar()
                    entry = tk.Entry(player_frame, textvariable=entry_var, width=8)
                    entry.pack(side=tk.RIGHT, padx=5)
                    
                    self.ownership_entries[row['player_name']] = entry_var
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        button_frame = tk.Frame(dialog, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=10)
        
        save_btn = tk.Button(button_frame, text="💾 Save Actual Ownership", 
                            command=lambda: self.save_actual_ownership(dialog),
                            bg=self.colors['success'], fg=self.colors['text'],
                            font=('Arial', 12, 'bold'), relief='flat')
        save_btn.pack(side=tk.LEFT, padx=10)
        
        cancel_btn = tk.Button(button_frame, text="Cancel", command=dialog.destroy,
                              bg=self.colors['danger'], fg=self.colors['text'],
                              font=('Arial', 12, 'bold'), relief='flat')
        cancel_btn.pack(side=tk.RIGHT, padx=10)
    
    def save_actual_ownership(self, dialog):
        """Save actual ownership data and calculate accuracy"""
        try:
            contest_date = self.contest_date_var.get()
            contest_name = self.contest_name_var.get()
            
            if not contest_date or not contest_name:
                self.show_message("Error", "Please enter contest date and name.")
                return
            
            # Collect actual ownership data
            actual_data = []
            for player_name, entry_var in self.ownership_entries.items():
                actual_ownership = entry_var.get().strip()
                if actual_ownership:
                    try:
                        actual_pct = float(actual_ownership)
                        actual_data.append({
                            'player_name': player_name,
                            'actual_ownership': actual_pct / 100 if actual_pct > 1 else actual_pct,
                            'contest_date': contest_date,
                            'contest_name': contest_name
                        })
                    except ValueError:
                        continue
            
            if not actual_data:
                self.show_message("Error", "No valid ownership data entered.")
                return
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"../data/actual_ownership_{contest_date.replace('-', '')}_{timestamp}.csv"
            
            actual_df = pd.DataFrame(actual_data)
            actual_df.to_csv(output_file, index=False)
            
            # Calculate and save accuracy metrics
            self.calculate_ownership_accuracy(contest_date, actual_df)
            
            self.show_message("Success", f"Actual ownership saved!\nFile: {output_file}\nAccuracy analysis completed.")
            dialog.destroy()
            
        except Exception as e:
            self.show_message("Save Error", f"Error saving actual ownership: {str(e)}")
    
    def calculate_ownership_accuracy(self, contest_date, actual_df):
        """Calculate accuracy metrics comparing projected vs actual ownership"""
        try:
            # Load corresponding projections
            proj_file = self.find_latest_ownership_file()
            if not proj_file:
                return
            
            proj_df = safe_read_csv(proj_file)
            if proj_df is None:
                return
            
            # Merge projected and actual
            merged = proj_df.merge(actual_df, on='player_name', how='inner')
            
            if merged.empty:
                return
            
            # Calculate accuracy metrics
            merged['projected_pct'] = merged['ownership'] * 100
            merged['actual_pct'] = merged['actual_ownership'] * 100
            merged['abs_error'] = abs(merged['projected_pct'] - merged['actual_pct'])
            merged['error_pct'] = merged['abs_error'] / merged['actual_pct'] * 100
            
            # Overall metrics
            mae = merged['abs_error'].mean()  # Mean Absolute Error
            rmse = np.sqrt((merged['abs_error'] ** 2).mean())  # Root Mean Square Error
            mape = merged['error_pct'].mean()  # Mean Absolute Percentage Error
            
            # Chalk accuracy (players >25% projected)
            chalk_players = merged[merged['projected_pct'] >= 25]
            chalk_accuracy = len(chalk_players[chalk_players['actual_pct'] >= 20]) / len(chalk_players) * 100 if len(chalk_players) > 0 else 0
            
            # Contrarian accuracy (players <8% projected)
            contrarian_players = merged[merged['projected_pct'] <= 8]
            contrarian_accuracy = len(contrarian_players[contrarian_players['actual_pct'] <= 12]) / len(contrarian_players) * 100 if len(contrarian_players) > 0 else 0
            
            # Save accuracy report
            accuracy_data = {
                'contest_date': contest_date,
                'contest_name': merged['contest_name'].iloc[0] if 'contest_name' in merged.columns else 'Unknown',
                'players_analyzed': len(merged),
                'mae': mae,
                'rmse': rmse,
                'mape': mape,
                'chalk_accuracy': chalk_accuracy,
                'contrarian_accuracy': contrarian_accuracy,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Append to accuracy tracking file
            accuracy_file = "../data/ownership_accuracy_tracking.csv"
            accuracy_df = pd.DataFrame([accuracy_data])
            
            if os.path.exists(accuracy_file):
                existing_df = safe_read_csv(accuracy_file)
                if existing_df is not None:
                    accuracy_df = pd.concat([existing_df, accuracy_df], ignore_index=True)
            
            accuracy_df.to_csv(accuracy_file, index=False)
            
            # Save detailed comparison
            comparison_file = f"../data/ownership_comparison_{contest_date.replace('-', '')}_{datetime.now().strftime('%H%M%S')}.csv"
            merged.to_csv(comparison_file, index=False)
            
        except Exception as e:
            print(f"Error calculating accuracy: {e}")
    
    def show_accuracy_report(self):
        """Show ownership projection accuracy report"""
        try:
            accuracy_file = "../data/ownership_accuracy_tracking.csv"
            if not os.path.exists(accuracy_file):
                self.show_message("No Data", "No accuracy data available yet.\nImport actual ownership data first.")
                return
            
            accuracy_df = safe_read_csv(accuracy_file)
            if accuracy_df is None or accuracy_df.empty:
                self.show_message("No Data", "No accuracy data available.")
                return
            
            # Create accuracy report window
            report_window = tk.Toplevel(self.root)
            report_window.title("📈 Ownership Projection Accuracy Report")
            report_window.geometry("900x600")
            report_window.configure(bg=self.colors['bg'])
            
            # Header
            header = tk.Label(report_window, text="Ownership Projection Accuracy Analysis",
                             bg=self.colors['bg'], fg=self.colors['text'],
                             font=('Arial', 16, 'bold'))
            header.pack(pady=10)
            
            # Summary metrics
            latest = accuracy_df.iloc[-1] if len(accuracy_df) > 0 else None
            avg_mae = accuracy_df['mae'].mean()
            avg_chalk_acc = accuracy_df['chalk_accuracy'].mean()
            avg_contrarian_acc = accuracy_df['contrarian_accuracy'].mean()
            
            # Format latest contest data
            latest_date = latest['contest_date'] if latest else 'N/A'
            latest_mae = f"{latest['mae']:.1f}%" if latest else 'N/A'
            latest_players = latest['players_analyzed'] if latest else 'N/A'
            latest_chalk = f"{latest['chalk_accuracy']:.1f}%" if latest else 'N/A'
            latest_contrarian = f"{latest['contrarian_accuracy']:.1f}%" if latest else 'N/A'
            
            summary_frame = tk.Frame(report_window, bg=self.colors['card'], relief='solid', bd=2)
            summary_frame.pack(fill=tk.X, padx=20, pady=10)
            
            summary_text = f"""
📊 OVERALL ACCURACY METRICS:
• Average Error: {avg_mae:.1f} percentage points
• Chalk Prediction Accuracy: {avg_chalk_acc:.1f}% (>25% projected players)
• Contrarian Accuracy: {avg_contrarian_acc:.1f}% (<8% projected players)
• Total Contests Analyzed: {len(accuracy_df)}

🎯 LATEST CONTEST ({latest_date}):
• Mean Absolute Error: {latest_mae}
• Players Analyzed: {latest_players}
• Chalk Accuracy: {latest_chalk}
• Contrarian Accuracy: {latest_contrarian}
            """
            
            summary_label = tk.Label(summary_frame, text=summary_text,
                                   bg=self.colors['card'], fg=self.colors['text'],
                                   font=('Arial', 10), justify=tk.LEFT)
            summary_label.pack(padx=10, pady=10)
            
            # Historical data table
            table_frame = tk.LabelFrame(report_window, text="📈 Historical Accuracy Data",
                                       bg=self.colors['bg'], fg=self.colors['text'],
                                       font=('Arial', 12, 'bold'))
            table_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            
            columns = ('Date', 'Contest', 'Players', 'MAE', 'Chalk Acc%', 'Contrarian Acc%')
            tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
            
            for col in columns:
                tree.heading(col, text=col)
                tree.column(col, width=120, anchor=tk.CENTER)
            
            # Populate data
            for _, row in accuracy_df.iterrows():
                tree.insert('', 'end', values=(
                    row['contest_date'],
                    row['contest_name'][:20] + '...' if len(str(row['contest_name'])) > 20 else row['contest_name'],
                    row['players_analyzed'],
                    f"{row['mae']:.1f}",
                    f"{row['chalk_accuracy']:.1f}%",
                    f"{row['contrarian_accuracy']:.1f}%"
                ))
            
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
        except Exception as e:
            self.show_message("Report Error", f"Error generating accuracy report: {str(e)}")
    
    def run_multi_team_stacks(self):
        """Run multi-team stack analysis (tournament-winning strategy)"""
        try:
            # Create new window for multi-team stack results
            stack_window = tk.Toplevel(self.root)
            stack_window.title("🎯 Multi-Team Stack Analysis")
            stack_window.geometry("1000x700")
            stack_window.configure(bg=self.colors['bg'])
            
            # Header
            header_frame = tk.Frame(stack_window, bg=self.colors['bg'])
            header_frame.pack(fill=tk.X, padx=10, pady=10)
            
            title_label = tk.Label(header_frame,
                                 text="🎯 MULTI-TEAM STACK ANALYSIS",
                                 font=('Arial', 16, 'bold'),
                                 bg=self.colors['bg'],
                                 fg=self.colors['accent'])
            title_label.pack()
            
            subtitle_label = tk.Label(header_frame,
                                    text="Tournament-winning strategy: Multiple mini-stacks like NYM(3) + CHC(3)",
                                    font=('Arial', 12),
                                    bg=self.colors['bg'],
                                    fg=self.colors['text'])
            subtitle_label.pack()
            
            # Loading indicator
            loading_label = tk.Label(stack_window,
                                   text="🔍 Analyzing multi-team stack combinations...",
                                   font=('Arial', 14),
                                   bg=self.colors['bg'],
                                   fg=self.colors['accent'])
            loading_label.pack(pady=20)
            
            # Progress frame
            progress_frame = tk.Frame(stack_window, bg=self.colors['bg'])
            progress_frame.pack(pady=10)
            
            def run_analysis():
                try:
                    # Import multi-team stack optimizer
                    import sys
                    sys.path.append('.')
                    from MULTI_TEAM_STACK_OPTIMIZER import MultiTeamStackOptimizer
                    
                    # Update progress
                    loading_label.config(text="📊 Loading slate data...")
                    stack_window.update()
                    
                    optimizer = MultiTeamStackOptimizer()
                    
                    # Load data
                    if not optimizer.load_slate_data():
                        loading_label.config(text="❌ Could not load slate data", fg=self.colors['error'])
                        return
                    
                    loading_label.config(text="🔗 Merging player data...")
                    stack_window.update()
                    
                    if not optimizer.merge_player_data():
                        loading_label.config(text="❌ Could not merge player data", fg=self.colors['error'])
                        return
                    
                    loading_label.config(text="🎯 Identifying mini-stack opportunities...")
                    stack_window.update()
                    
                    # Analyze mini-stack opportunities
                    team_analysis = optimizer.identify_mini_stack_opportunities()
                    
                    loading_label.config(text="💎 Building multi-team combinations...")
                    stack_window.update()
                    
                    # Build multi-team combinations
                    stack_combinations = optimizer.build_multi_team_stacks(team_analysis)
                    
                    # Clear loading
                    loading_label.destroy()
                    
                    # Create scrollable results frame
                    canvas = tk.Canvas(stack_window, bg=self.colors['bg'])
                    scrollbar = tk.Scrollbar(stack_window, orient="vertical", command=canvas.yview)
                    scrollable_frame = tk.Frame(canvas, bg=self.colors['bg'])
                    
                    scrollable_frame.bind(
                        "<Configure>",
                        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
                    )
                    
                    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                    canvas.configure(yscrollcommand=scrollbar.set)
                    
                    # Pack canvas and scrollbar
                    canvas.pack(side="left", fill="both", expand=True, padx=10)
                    scrollbar.pack(side="right", fill="y")
                    
                    # Display results
                    self.display_multi_team_results(scrollable_frame, stack_combinations)
                    
                    # Buttons frame
                    buttons_frame = tk.Frame(header_frame, bg=self.colors['bg'])
                    buttons_frame.pack(side=tk.RIGHT, padx=10)
                    
                    # Build Lineups button (NEW!)
                    lineup_btn = tk.Button(buttons_frame,
                                         text="🎯 BUILD LINEUPS",
                                         font=('Arial', 10, 'bold'),
                                         bg='#FF6B35',  # Bright orange
                                         fg='white',
                                         command=lambda: self.build_lineups_from_stacks(stack_combinations))
                    lineup_btn.pack(side=tk.LEFT, padx=(0, 5))
                    
                    # Export button
                    export_btn = tk.Button(buttons_frame,
                                         text="📊 Export Results",
                                         font=('Arial', 10, 'bold'),
                                         bg=self.colors['success'],
                                         fg='white',
                                         command=lambda: self.export_multi_stacks(stack_combinations))
                    export_btn.pack(side=tk.LEFT, padx=5)
                    
                except Exception as e:
                    loading_label.config(text=f"❌ Analysis error: {str(e)}", fg=self.colors['error'])
                    import traceback
                    traceback.print_exc()
            
            # Run analysis in thread to prevent GUI freezing
            import threading
            analysis_thread = threading.Thread(target=run_analysis)
            analysis_thread.daemon = True
            analysis_thread.start()
            
        except Exception as e:
            self.show_message("Multi-Team Stack Error", f"Error: {str(e)}")
    
    def display_multi_team_results(self, parent_frame, stack_combinations):
        """Display multi-team stack results in organized sections"""
        try:
            # Separate by stack type
            dual_stacks = [s for s in stack_combinations if s['type'] == 'dual_mini']
            triple_stacks = [s for s in stack_combinations if s['type'] == 'triple_mini']
            primary_secondary = [s for s in stack_combinations if s['type'] == 'primary_secondary']
            
            # Dual Mini-Stacks Section
            if dual_stacks:
                dual_frame = tk.LabelFrame(parent_frame,
                                         text="💎 DUAL MINI-STACKS (Tournament Winner Strategy)",
                                         font=('Arial', 12, 'bold'),
                                         bg=self.colors['card'],
                                         fg=self.colors['accent'],
                                         padx=10,
                                         pady=10)
                dual_frame.pack(fill=tk.X, padx=10, pady=5)
                
                description_label = tk.Label(dual_frame,
                                            text="2-3 players from multiple teams (e.g., NYM(3) + CHC(3))",
                                            font=('Arial', 10),
                                            bg=self.colors['card'],
                                            fg=self.colors['subtext'])
                description_label.pack(anchor=tk.W)
                
                for i, stack in enumerate(dual_stacks[:5]):
                    score = stack.get('tournament_score', 0)
                    
                    stack_label = tk.Label(dual_frame,
                                         text=f"{i+1}. {stack['teams']}: {stack['total_projection']:.1f} proj, "
                                              f"${stack['total_salary']:,}, {stack['avg_ownership']:.1f}% own, "
                                              f"Score: {score:.1f}",
                                         font=('Arial', 10),
                                         bg=self.colors['card'],
                                         fg=self.colors['text'])
                    stack_label.pack(anchor=tk.W, pady=2)
            
            # Triple Mini-Stacks Section
            if triple_stacks:
                triple_frame = tk.LabelFrame(parent_frame,
                                           text="🔗 TRIPLE MINI-STACKS (Diversification Strategy)",
                                           font=('Arial', 12, 'bold'),
                                           bg=self.colors['card'],
                                           fg=self.colors['accent'],
                                           padx=10,
                                           pady=10)
                triple_frame.pack(fill=tk.X, padx=10, pady=5)
                
                description_label = tk.Label(triple_frame,
                                            text="2 players from 3 different teams for maximum diversification",
                                            font=('Arial', 10),
                                            bg=self.colors['card'],
                                            fg=self.colors['subtext'])
                description_label.pack(anchor=tk.W)
                
                for i, stack in enumerate(triple_stacks[:5]):
                    score = stack.get('diversification_score', 0)
                    
                    stack_label = tk.Label(triple_frame,
                                         text=f"{i+1}. {stack['teams']}: {stack['total_projection']:.1f} proj, "
                                              f"${stack['total_salary']:,}, {stack['avg_ownership']:.1f}% own, "
                                              f"Score: {score:.1f}",
                                         font=('Arial', 10),
                                         bg=self.colors['card'],
                                         fg=self.colors['text'])
                    stack_label.pack(anchor=tk.W, pady=2)
            
            # Primary + Secondary Section
            if primary_secondary:
                primary_frame = tk.LabelFrame(parent_frame,
                                            text="⚡ PRIMARY + SECONDARY STACKS (Correlation Focus)",
                                            font=('Arial', 12, 'bold'),
                                            bg=self.colors['card'],
                                            fg=self.colors['accent'],
                                            padx=10,
                                            pady=10)
                primary_frame.pack(fill=tk.X, padx=10, pady=5)
                
                description_label = tk.Label(primary_frame,
                                            text="4 players from primary team + 2 from secondary team",
                                            font=('Arial', 10),
                                            bg=self.colors['card'],
                                            fg=self.colors['subtext'])
                description_label.pack(anchor=tk.W)
                
                for i, stack in enumerate(primary_secondary[:5]):
                    score = stack.get('correlation_score', 0)
                    
                    stack_label = tk.Label(primary_frame,
                                         text=f"{i+1}. {stack['teams']}: {stack['total_projection']:.1f} proj, "
                                              f"${stack['total_salary']:,}, {stack['avg_ownership']:.1f}% own, "
                                              f"Score: {score:.1f}",
                                         font=('Arial', 10),
                                         bg=self.colors['card'],
                                         fg=self.colors['text'])
                    stack_label.pack(anchor=tk.W, pady=2)
            
            # Summary insights
            summary_frame = tk.LabelFrame(parent_frame,
                                        text="💡 KEY INSIGHTS",
                                        font=('Arial', 12, 'bold'),
                                        bg=self.colors['card'],
                                        fg=self.colors['accent'],
                                        padx=10,
                                        pady=10)
            summary_frame.pack(fill=tk.X, padx=10, pady=5)
            
            insights = [
                "🎯 Dual mini-stacks offer tournament upside with lower ownership",
                "🔗 Triple mini-stacks provide excellent diversification",
                "⚡ Primary+Secondary maximizes correlation leverage",
                "💎 Focus on stacks with <20% combined ownership",
                "🏆 Tournament winners often use multi-team strategies"
            ]
            
            for insight in insights:
                insight_label = tk.Label(summary_frame,
                                       text=insight,
                                       font=('Arial', 10),
                                       bg=self.colors['card'],
                                       fg=self.colors['text'])
                insight_label.pack(anchor=tk.W, pady=2)
                
        except Exception as e:
            error_label = tk.Label(parent_frame,
                                 text=f"❌ Display error: {str(e)}",
                                 font=('Arial', 12),
                                 bg=self.colors['bg'],
                                 fg=self.colors['error'])
            error_label.pack(pady=20)
    
    def run_complete_lineup_workflow(self):
        """Complete workflow: Multi-team stacks → Complete lineups → FanDuel export"""
        try:
            # Create workflow window
            workflow_window = tk.Toplevel(self.root)
            workflow_window.title("🏆 Complete FanDuel Lineup Builder")
            workflow_window.geometry("800x600")
            workflow_window.configure(bg=self.colors['bg'])
            
            # Header
            header_frame = tk.Frame(workflow_window, bg=self.colors['bg'])
            header_frame.pack(fill=tk.X, padx=10, pady=10)
            
            title_label = tk.Label(header_frame,
                                 text="🏆 COMPLETE FANDUEL LINEUP BUILDER",
                                 font=('Arial', 16, 'bold'),
                                 bg=self.colors['bg'],
                                 fg=self.colors['accent'])
            title_label.pack()
            
            subtitle_label = tk.Label(header_frame,
                                    text="All-in-One: Multi-team stacks → Complete lineups → FanDuel export",
                                    font=('Arial', 12),
                                    bg=self.colors['bg'],
                                    fg=self.colors['text'])
            subtitle_label.pack()
            
            # Progress area
            progress_frame = tk.Frame(workflow_window, bg=self.colors['bg'])
            progress_frame.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Status label
            status_label = tk.Label(progress_frame,
                                  text="🚀 Ready to build tournament-winning lineups...",
                                  font=('Arial', 14, 'bold'),
                                  bg=self.colors['bg'],
                                  fg=self.colors['accent'])
            status_label.pack(pady=10)
            
            # Progress text area
            progress_text = tk.Text(progress_frame, 
                                  width=90, 
                                  height=25,
                                  bg=self.colors['card'],
                                  fg=self.colors['text'],
                                  font=('Courier', 10))
            progress_text.pack(fill='both', expand=True, pady=10)
            
            # Scrollbar for text
            scrollbar = tk.Scrollbar(progress_text)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            progress_text.config(yscrollcommand=scrollbar.set)
            scrollbar.config(command=progress_text.yview)
            
            def run_complete_workflow():
                try:
                    progress_text.insert(tk.END, "🏆 COMPLETE FANDUEL LINEUP BUILDER\n")
                    progress_text.insert(tk.END, "=" * 60 + "\n\n")
                    
                    # Step 1: Multi-team stack analysis
                    status_label.config(text="Step 1/3: Analyzing multi-team stacks...")
                    progress_text.insert(tk.END, "🎯 STEP 1: MULTI-TEAM STACK ANALYSIS\n")
                    progress_text.insert(tk.END, "-" * 40 + "\n")
                    workflow_window.update()
                    
                    import sys
                    sys.path.append('.')
                    from MULTI_TEAM_STACK_OPTIMIZER import MultiTeamStackOptimizer
                    
                    optimizer = MultiTeamStackOptimizer()
                    
                    if not optimizer.load_slate_data():
                        raise Exception("Failed to load slate data")
                    
                    progress_text.insert(tk.END, "✅ Loaded FD slate data\n")
                    progress_text.see(tk.END)
                    workflow_window.update()
                    
                    if not optimizer.merge_player_data():
                        raise Exception("Failed to merge player data")
                    
                    progress_text.insert(tk.END, "✅ Merged ownership projections\n")
                    progress_text.see(tk.END)
                    workflow_window.update()
                    
                    # Analyze stacks
                    team_analysis = optimizer.identify_mini_stack_opportunities()
                    stack_combinations = optimizer.build_multi_team_stacks(team_analysis)
                    
                    progress_text.insert(tk.END, f"✅ Found {len(stack_combinations)} multi-team stack combinations\n")
                    progress_text.insert(tk.END, "   • Dual mini-stacks (3+3, 3+2, 2+3)\n")
                    progress_text.insert(tk.END, "   • Triple mini-stacks (2+2+2)\n")
                    progress_text.insert(tk.END, "   • Primary+Secondary (4+2)\n\n")
                    progress_text.see(tk.END)
                    workflow_window.update()
                    
                    # Step 2: Build complete lineups
                    status_label.config(text="Step 2/3: Building complete 9-player lineups...")
                    progress_text.insert(tk.END, "🎯 STEP 2: BUILDING COMPLETE LINEUPS\n")
                    progress_text.insert(tk.END, "-" * 40 + "\n")
                    workflow_window.update()
                    
                    from MULTI_TEAM_LINEUP_BUILDER import MultiTeamLineupBuilder
                    
                    builder = MultiTeamLineupBuilder()
                    
                    if not builder.load_player_data():
                        raise Exception("Failed to load player data for lineup building")
                    
                    progress_text.insert(tk.END, "✅ Loaded player data for lineup building\n")
                    progress_text.see(tk.END)
                    workflow_window.update()
                    
                    lineups = builder.build_lineups_from_stacks(max_lineups=20)
                    
                    if not lineups:
                        raise Exception("No lineups generated")
                    
                    progress_text.insert(tk.END, f"✅ Built {len(lineups)} complete 9-player lineups\n")
                    
                    # Show lineup summary
                    avg_proj = sum(l['total_projection'] for l in lineups) / len(lineups)
                    avg_own = sum(l['avg_ownership'] for l in lineups) / len(lineups)
                    best_lev = max(l['leverage_score'] for l in lineups)
                    
                    progress_text.insert(tk.END, f"   • Average projection: {avg_proj:.1f}\n")
                    progress_text.insert(tk.END, f"   • Average ownership: {avg_own:.1f}%\n")
                    progress_text.insert(tk.END, f"   • Best leverage: {best_lev:.1f}\n\n")
                    progress_text.see(tk.END)
                    workflow_window.update()
                    
                    # Step 3: Export for FanDuel
                    status_label.config(text="Step 3/3: Exporting FanDuel-ready file...")
                    progress_text.insert(tk.END, "🎯 STEP 3: FANDUEL EXPORT\n")
                    progress_text.insert(tk.END, "-" * 40 + "\n")
                    workflow_window.update()
                    
                    output_file = builder.export_lineups_for_fanduel(lineups)
                    
                    if output_file:
                        progress_text.insert(tk.END, f"✅ Exported lineups: {output_file}\n")
                        
                        # Fix headers to match FanDuel exactly
                        import pandas as pd
                        df = pd.read_csv(output_file)
                        df.columns = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
                        
                        final_file = output_file.replace('FD_READY', 'FANDUEL_UPLOAD')
                        df.to_csv(final_file, index=False)
                        
                        progress_text.insert(tk.END, f"✅ Final file: {final_file}\n")
                        progress_text.insert(tk.END, f"   Headers: P, C/1B, 2B, 3B, SS, OF, OF, OF, UTIL\n\n")
                        
                        # Success summary
                        progress_text.insert(tk.END, "🏆 WORKFLOW COMPLETE!\n")
                        progress_text.insert(tk.END, "=" * 60 + "\n")
                        progress_text.insert(tk.END, f"✅ {len(lineups)} tournament-ready lineups created\n")
                        progress_text.insert(tk.END, "✅ Multi-team stacking strategy implemented\n")
                        progress_text.insert(tk.END, "✅ Low ownership combinations selected\n")
                        progress_text.insert(tk.END, "✅ FanDuel upload format ready\n\n")
                        progress_text.insert(tk.END, "🎯 READY TO UPLOAD TO FANDUEL!\n")
                        progress_text.insert(tk.END, f"📁 File: {final_file}\n")
                        
                        status_label.config(text="✅ Complete! FanDuel lineups ready for upload", fg=self.colors['success'])
                        
                        # Add file copy button
                        copy_frame = tk.Frame(header_frame, bg=self.colors['bg'])
                        copy_frame.pack(pady=10)
                        
                        copy_btn = tk.Button(copy_frame,
                                           text="📋 Copy File Path",
                                           font=('Arial', 10, 'bold'),
                                           bg=self.colors['accent'],
                                           fg='white',
                                           command=lambda: self.copy_to_clipboard(final_file))
                        copy_btn.pack(side=tk.LEFT, padx=5)
                        
                        open_btn = tk.Button(copy_frame,
                                           text="📁 Open File Location",
                                           font=('Arial', 10, 'bold'),
                                           bg=self.colors['success'],
                                           fg='white',
                                           command=lambda: self.open_file_location(final_file))
                        open_btn.pack(side=tk.LEFT, padx=5)
                        
                    else:
                        progress_text.insert(tk.END, "❌ Failed to export lineups\n")
                        status_label.config(text="❌ Export failed", fg=self.colors['error'])
                    
                    progress_text.see(tk.END)
                    
                except Exception as e:
                    status_label.config(text=f"❌ Workflow error: {str(e)}", fg=self.colors['error'])
                    progress_text.insert(tk.END, f"\n❌ Error: {str(e)}\n")
                    import traceback
                    traceback.print_exc()
            
            # Start button
            start_btn = tk.Button(header_frame,
                                text="🚀 START COMPLETE WORKFLOW",
                                font=('Arial', 12, 'bold'),
                                bg='#28A745',
                                fg='white',
                                command=lambda: [start_btn.config(state='disabled'), 
                                               self.run_in_thread(run_complete_workflow)])
            start_btn.pack(pady=10)
            
        except Exception as e:
            self.show_message("Workflow Error", f"Error: {str(e)}")
    
    def open_file_location(self, file_path):
        """Open file location in Windows Explorer"""
        try:
            import os
            import subprocess
            
            # Get directory containing the file
            directory = os.path.dirname(os.path.abspath(file_path))
            
            # Open in Windows Explorer
            subprocess.run(['explorer', directory])
            
        except Exception as e:
            self.show_message("Open Error", f"Could not open file location: {str(e)}")
    
    def run_in_thread(self, func):
        """Run function in a separate thread"""
        import threading
        thread = threading.Thread(target=func)
        thread.daemon = True
        thread.start()
    
    def build_lineups_from_stacks(self, stack_combinations):
        """Build complete FanDuel lineups from multi-team stacks"""
        try:
            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("🎯 Building Lineups")
            progress_window.geometry("600x400")
            progress_window.configure(bg=self.colors['bg'])
            
            # Header
            header_label = tk.Label(progress_window,
                                  text="🎯 BUILDING FANDUEL LINEUPS",
                                  font=('Arial', 16, 'bold'),
                                  bg=self.colors['bg'],
                                  fg=self.colors['accent'])
            header_label.pack(pady=10)
            
            # Status label
            status_label = tk.Label(progress_window,
                                  text="🔄 Initializing lineup builder...",
                                  font=('Arial', 12),
                                  bg=self.colors['bg'],
                                  fg=self.colors['text'])
            status_label.pack(pady=10)
            
            # Progress text area
            progress_text = tk.Text(progress_window, 
                                  width=70, 
                                  height=15,
                                  bg=self.colors['card'],
                                  fg=self.colors['text'],
                                  font=('Courier', 10))
            progress_text.pack(padx=10, pady=10, fill='both', expand=True)
            
            def run_builder():
                try:
                    # Import and run lineup builder
                    import sys
                    sys.path.append('.')
                    from MULTI_TEAM_LINEUP_BUILDER import MultiTeamLineupBuilder
                    
                    status_label.config(text="📊 Loading player data...")
                    progress_window.update()
                    
                    builder = MultiTeamLineupBuilder()
                    
                    # Load player data
                    if not builder.load_player_data():
                        status_label.config(text="❌ Failed to load player data", fg=self.colors['error'])
                        return
                    
                    progress_text.insert(tk.END, "✅ Loaded player data with projections and ownership\n")
                    progress_text.see(tk.END)
                    progress_window.update()
                    
                    status_label.config(text="🎯 Building lineups from stacks...")
                    progress_window.update()
                    
                    # Build lineups from stacks (use top 15 stacks)
                    lineups = builder.build_lineups_from_stacks(max_lineups=15)
                    
                    if not lineups:
                        status_label.config(text="❌ No lineups generated", fg=self.colors['error'])
                        progress_text.insert(tk.END, "❌ No lineups could be generated from stacks\n")
                        return
                    
                    progress_text.insert(tk.END, f"✅ Generated {len(lineups)} complete lineups\n")
                    progress_text.see(tk.END)
                    progress_window.update()
                    
                    status_label.config(text="📁 Exporting to FanDuel format...")
                    progress_window.update()
                    
                    # Export for FanDuel
                    output_file = builder.export_lineups_for_fanduel(lineups)
                    
                    if output_file:
                        progress_text.insert(tk.END, f"💾 Exported to: {output_file}\n")
                        progress_text.insert(tk.END, f"🎯 {len(lineups)} lineups ready for FanDuel upload!\n\n")
                        
                        # Show summary
                        progress_text.insert(tk.END, "📊 LINEUP SUMMARY:\n")
                        progress_text.insert(tk.END, f"   Generated: {len(lineups)} lineups\n")
                        avg_proj = sum(l['total_projection'] for l in lineups) / len(lineups)
                        progress_text.insert(tk.END, f"   Avg Projection: {avg_proj:.1f}\n")
                        avg_own = sum(l['avg_ownership'] for l in lineups) / len(lineups)
                        progress_text.insert(tk.END, f"   Avg Ownership: {avg_own:.1f}%\n")
                        best_lev = max(l['leverage_score'] for l in lineups)
                        progress_text.insert(tk.END, f"   Best Leverage: {best_lev:.1f}\n\n")
                        
                        progress_text.insert(tk.END, "🏆 Lineups use tournament-winning multi-team strategies!\n")
                        
                        status_label.config(text="✅ Lineups ready for FanDuel upload!", fg=self.colors['success'])
                        
                        # Add copy file path button
                        copy_btn = tk.Button(progress_window,
                                           text="📋 Copy File Path",
                                           font=('Arial', 10, 'bold'),
                                           bg=self.colors['accent'],
                                           fg='white',
                                           command=lambda: self.copy_to_clipboard(output_file))
                        copy_btn.pack(pady=10)
                        
                    else:
                        progress_text.insert(tk.END, "❌ Failed to export lineups\n")
                        status_label.config(text="❌ Export failed", fg=self.colors['error'])
                    
                    progress_text.see(tk.END)
                    
                except Exception as e:
                    status_label.config(text=f"❌ Lineup building error: {str(e)}", fg=self.colors['error'])
                    progress_text.insert(tk.END, f"\n❌ Error: {str(e)}\n")
                    import traceback
                    traceback.print_exc()
            
            # Run in thread
            import threading
            builder_thread = threading.Thread(target=run_builder)
            builder_thread.daemon = True
            builder_thread.start()
            
        except Exception as e:
            self.show_message("Lineup Builder Error", f"Error: {str(e)}")
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.show_message("Copied", f"File path copied to clipboard:\n{text}")
        except Exception as e:
            self.show_message("Copy Error", f"Could not copy to clipboard: {str(e)}")
    
    def export_multi_stacks(self, stack_combinations):
        """Export multi-team stack combinations to CSV"""
        try:
            # Create export DataFrame
            all_stacks = []
            for stack in stack_combinations:
                score_key = 'tournament_score' if 'tournament_score' in stack else \
                           'diversification_score' if 'diversification_score' in stack else 'correlation_score'
                
                all_stacks.append({
                    'Stack_Type': stack['type'],
                    'Teams': stack['teams'],
                    'Total_Projection': round(stack['total_projection'], 1),
                    'Total_Salary': stack['total_salary'],
                    'Avg_Ownership': round(stack['avg_ownership'], 1),
                    'Score': round(stack[score_key], 1),
                    'Players_Used': stack['players_used']
                })
            
            # Sort by score
            all_stacks.sort(key=lambda x: x['Score'], reverse=True)
            
            # Create DataFrame and export
            export_df = pd.DataFrame(all_stacks)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"../data/multi_team_stacks_{timestamp}.csv"
            export_df.to_csv(output_file, index=False)
            
            self.show_message("Export Success", f"Multi-team stacks exported to:\n{output_file}")
            
        except Exception as e:
            self.show_message("Export Error", f"Error exporting stacks: {str(e)}")
    
    def find_latest_ownership_file(self):
        """Find the most recent ownership projections file"""
        try:
            data_dir = "../data"
            ownership_files = [f for f in os.listdir(data_dir) if f.startswith("advanced_ownership_projections_")]
            if ownership_files:
                ownership_files.sort(reverse=True)
                return os.path.join(data_dir, ownership_files[0])
        except:
            pass
        return None
            
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
