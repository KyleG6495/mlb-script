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

class DebugEliteDFSDashboard:
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
        
        # Monitoring
        self.monitoring = True
        self.update_interval = 5000  # 5 seconds
        
        self.setup_gui()
        self.start_monitoring()
        
    def setup_gui(self):
        """Initialize the main GUI"""
        self.root = tk.Tk()
        self.root.title("🏆 Debug Elite DFS Dashboard - REAL DATA")
        self.root.geometry("1400x900")
        self.root.configure(bg=self.colors['bg'])
        
        # Header
        header_frame = tk.Frame(self.root, bg=self.colors['card'], height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🏆 Debug Elite DFS Dashboard", 
                              bg=self.colors['card'], fg=self.colors['accent'],
                              font=('Arial', 20, 'bold'))
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        self.status_label = tk.Label(header_frame, text="🔴 Loading Real Data...", 
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
        self.create_debug_tab()
        
    def create_ownership_tab(self):
        """Real Ownership Analysis"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="👥 Real Ownership")
        
        # Real ownership table
        table_frame = tk.LabelFrame(tab, text="🎯 Real Ownership Projections",
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
        
    def create_debug_tab(self):
        """Debug Information"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🐛 Debug")
        
        self.debug_text = scrolledtext.ScrolledText(tab,
                                                   bg=self.colors['bg'],
                                                   fg=self.colors['text'],
                                                   font=('Consolas', 10),
                                                   wrap=tk.WORD)
        self.debug_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def start_monitoring(self):
        """Start real-time monitoring"""
        self.monitoring_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        self.monitoring_thread.start()
        
        # Start GUI updates
        self.update_gui()
        
    def monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                self.debug_log("Starting data load cycle...")
                self.load_real_ownership_data()
                self.load_real_stack_data()
                self.debug_log("Data load cycle completed successfully")
                time.sleep(5)  # Update every 5 seconds
            except Exception as e:
                self.debug_log(f"Monitor error: {str(e)}")
                self.debug_log(f"Traceback: {traceback.format_exc()}")
                time.sleep(10)
                
    def debug_log(self, message):
        """Add debug message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_info.append(f"[{timestamp}] {message}")
        # Keep only last 100 messages
        if len(self.debug_info) > 100:
            self.debug_info = self.debug_info[-100:]
            
    def load_real_ownership_data(self):
        """Load actual ownership projections"""
        try:
            data_dir = "../data"
            ownership_file = "advanced_ownership_projections_20250815_133716.csv"
            path = os.path.join(data_dir, ownership_file)
            
            self.debug_log(f"Looking for ownership file: {path}")
            
            if os.path.exists(path):
                df = pd.read_csv(path)
                self.debug_log(f"Loaded ownership data: {len(df)} rows")
                self.debug_log(f"Columns: {list(df.columns)}")
                
                # Real ownership data
                self.ownership_data = {
                    'total_players': len(df),
                    'chalk_plays': len(df[df['ownership'] > 0.25]),
                    'contrarian_targets': len(df[df['ownership'] < 0.08]),
                    'value_plays': len(df[df['leverage_score'] > 0.7]),
                    'players': df.to_dict('records')
                }
                
                self.debug_log(f"Processed ownership data: {self.ownership_data['total_players']} players")
                
            else:
                self.debug_log(f"Ownership file not found: {path}")
                
        except Exception as e:
            self.debug_log(f"Ownership data error: {str(e)}")
            self.debug_log(f"Traceback: {traceback.format_exc()}")
            
    def load_real_stack_data(self):
        """Load/generate stack data from projections"""
        try:
            data_dir = "../data"
            proj_file = "enhanced_projections_20250815_133709.csv"
            ownership_file = "advanced_ownership_projections_20250815_133716.csv"
            proj_path = os.path.join(data_dir, proj_file)
            own_path = os.path.join(data_dir, ownership_file)
            
            self.debug_log(f"Looking for projection file: {proj_path}")
            
            if os.path.exists(proj_path):
                # Load projections
                df = pd.read_csv(proj_path)
                self.debug_log(f"Loaded projections: {len(df)} rows")
                self.debug_log(f"Columns: {list(df.columns)}")
                
                # Filter to hitters only
                hitters = df[df['Position'] != 'P'].copy()
                self.debug_log(f"Filtered to hitters: {len(hitters)} rows")
                
                if len(hitters) == 0:
                    self.debug_log("No hitters found!")
                    return
                
                # Load ownership data for matching
                ownership_dict = {}
                if os.path.exists(own_path):
                    own_df = pd.read_csv(own_path)
                    self.debug_log(f"Loaded ownership mapping: {len(own_df)} rows")
                    for _, row in own_df.iterrows():
                        ownership_dict[row['player_name']] = row['ownership']
                
                # Function to get ownership
                def get_ownership(name, salary, projection):
                    if name in ownership_dict:
                        own = ownership_dict[name]
                        return own * 100 if own <= 1 else own
                    # Estimate based on salary and projection
                    base_own = (salary / 1000) * 2.5
                    proj_factor = (projection / (salary / 1000)) * 5
                    return min(max(base_own + proj_factor, 1), 45)
                
                # Add ownership projections
                hitters['ownership_proj'] = hitters.apply(
                    lambda row: get_ownership(row['Nickname'], row['Salary'], row['enhanced_fppg']), 
                    axis=1
                )
                
                self.debug_log("Added ownership projections to hitters")
                
                # Group by team and create detailed stacks
                team_stacks = []
                teams_processed = 0
                
                for team in hitters['Team'].value_counts().head(15).index:
                    team_players = hitters[hitters['Team'] == team].copy()
                    teams_processed += 1
                    
                    self.debug_log(f"Processing team {team}: {len(team_players)} players")
                    
                    if len(team_players) >= 3:
                        # Sort by projection and take top 4
                        top_players = team_players.nlargest(4, 'enhanced_fppg')
                        
                        total_salary = int(top_players['Salary'].sum())
                        total_projection = round(top_players['enhanced_fppg'].sum(), 1)
                        avg_ownership = round(top_players['ownership_proj'].mean(), 1)
                        value_score = round(total_projection / (total_salary / 1000), 2)
                        
                        # Create player details list
                        players_detail = []
                        for _, player in top_players.iterrows():
                            players_detail.append(f"{player['Nickname']} (${player['Salary']:,})")
                        
                        stack_info = {
                            'team': team,
                            'projection': total_projection,
                            'salary': total_salary,
                            'ownership': avg_ownership,
                            'value': value_score,
                            'players_detail': players_detail
                        }
                        
                        team_stacks.append(stack_info)
                        self.debug_log(f"Created stack for {team}: ${total_salary:,}, {total_projection} proj")
                
                # Sort by projection and take top 10
                self.stack_data = sorted(team_stacks, key=lambda x: x['projection'], reverse=True)[:10]
                self.debug_log(f"Created {len(self.stack_data)} stacks from {teams_processed} teams")
                
            else:
                self.debug_log(f"Projection file not found: {proj_path}")
                
        except Exception as e:
            self.debug_log(f"Stack generation error: {str(e)}")
            self.debug_log(f"Traceback: {traceback.format_exc()}")
            
    def update_gui(self):
        """Update GUI with real data"""
        try:
            self.update_ownership_display()
            self.update_stacks_display()
            self.update_debug_display()
            
            # Update status
            if self.ownership_data and self.stack_data:
                self.status_label.config(text="🟢 Live - Real Data Active", fg=self.colors['success'])
            else:
                self.status_label.config(text="🟡 Loading Data...", fg=self.colors['warning'])
            
        except Exception as e:
            self.debug_log(f"GUI update error: {str(e)}")
        
        # Schedule next update
        self.root.after(self.update_interval, self.update_gui)
        
    def update_ownership_display(self):
        """Update ownership tab"""
        # Clear existing items
        for item in self.ownership_tree.get_children():
            self.ownership_tree.delete(item)
            
        # Populate table with real data
        if self.ownership_data and 'players' in self.ownership_data:
            for player in self.ownership_data['players'][:30]:
                ownership_pct = float(player.get('ownership', 0))
                if ownership_pct <= 1:
                    ownership_pct *= 100
                    
                self.ownership_tree.insert('', 'end', values=(
                    player.get('player_name', 'Unknown'),
                    player.get('position', 'N/A'),
                    player.get('team', 'N/A'),
                    f"${player.get('salary', 0):,}",
                    f"{player.get('projection', 0):.1f}",
                    f"{ownership_pct:.1f}%",
                    f"{player.get('leverage_score', 0):.2f}",
                    player.get('ownership_tier', 'Unknown')
                ))
                
    def update_stacks_display(self):
        """Update stacks tab with full metrics"""
        # Clear existing items
        for item in self.stack_tree.get_children():
            self.stack_tree.delete(item)
            
        # Populate with stack data
        for i, stack in enumerate(self.stack_data):
            players_str = ", ".join(stack.get('players_detail', []))
            
            self.stack_tree.insert('', 'end', values=(
                i + 1,
                stack.get('team', 'Unknown'),
                f"{stack.get('projection', 0):.1f}",
                f"${stack.get('salary', 0):,}",
                f"{stack.get('ownership', 0):.1f}%",
                f"{stack.get('value', 0):.2f}",
                players_str
            ))
            
    def update_debug_display(self):
        """Update debug tab"""
        self.debug_text.delete(1.0, tk.END)
        
        debug_content = "\n".join(self.debug_info[-50:])  # Show last 50 messages
        debug_content += f"\n\nCURRENT STATUS:\n"
        debug_content += f"Ownership data loaded: {bool(self.ownership_data)}\n"
        debug_content += f"Stack data loaded: {len(self.stack_data)} stacks\n"
        debug_content += f"Total players: {self.ownership_data.get('total_players', 0)}\n"
        
        self.debug_text.insert(tk.END, debug_content)
        self.debug_text.see(tk.END)
        
    def run(self):
        """Start the dashboard"""
        print("🏆 Starting Debug Elite DFS Dashboard...")
        print("📊 Loading actual ownership projections and optimizations")
        print("🎯 Real-time monitoring with debug information")
        
        self.root.mainloop()

if __name__ == "__main__":
    dashboard = DebugEliteDFSDashboard()
    dashboard.run()
