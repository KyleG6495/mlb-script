import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd
import numpy as np
import os
import glob
from datetime import datetime
import traceback
from file_finder_utils import get_data_files, safe_read_csv

class WorkingDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Elite DFS Dashboard - WORKING VERSION")
        self.root.geometry("1800x1000")
        
        # Initialize data containers
        self.ownership_data = None
        self.stack_data = []
        self.fd_slate_data = pd.DataFrame()
        
        # Setup UI
        self.setup_ui()
        
        # Load data
        self.load_data()
        
    def setup_ui(self):
        """Setup the main UI"""
        # Status bar at top
        status_frame = tk.Frame(self.root, bg='#f0f0f0')
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(status_frame, text="🏆 Elite DFS Dashboard", 
                font=('Arial', 16, 'bold'), bg='#f0f0f0').pack(side=tk.LEFT)
        
        self.status_label = tk.Label(status_frame, text="● Live - Data Loaded", 
                                   font=('Arial', 12), fg='green', bg='#f0f0f0')
        self.status_label.pack(side=tk.RIGHT)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_ownership_tab()
        self.create_stacks_tab()
        self.create_debug_tab()
        
    def create_ownership_tab(self):
        """Create ownership tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="👥 Ownership")
        
        # Summary metrics
        summary_frame = tk.Frame(frame)
        summary_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(summary_frame, text="📊 OWNERSHIP SUMMARY", 
                font=('Arial', 14, 'bold')).pack(side=tk.LEFT)
        
        # Metrics row
        summary_row = tk.Frame(summary_frame)
        summary_row.pack(side=tk.RIGHT)
        
        tk.Label(summary_row, text="Total Players:", font=('Arial', 10)).pack(side=tk.LEFT)
        self.total_players = tk.Label(summary_row, text="0", font=('Arial', 14, 'bold'), fg='blue')
        self.total_players.pack(side=tk.LEFT, padx=5)
        
        tk.Label(summary_row, text="Chalk Plays (>25%):", font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        self.chalk_plays = tk.Label(summary_row, text="0", font=('Arial', 14, 'bold'), fg='red')
        self.chalk_plays.pack(side=tk.LEFT, padx=5)
        
        tk.Label(summary_row, text="Contrarian (<5%):", font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
        self.contrarian_targets = tk.Label(summary_row, text="0", font=('Arial', 14, 'bold'), fg='green')
        self.contrarian_targets.pack(side=tk.LEFT, padx=5)
        
    def create_stacks_tab(self):
        """Create stacks tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🎯 Stacks")
        
        # Header
        header = tk.Frame(frame)
        header.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(header, text="Team Stack Rankings", font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        
        # Stack table
        table_frame = tk.Frame(frame)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        columns = ('Rank', 'Team', 'Projection', 'Salary', 'Ownership', 'Value', 'GPP Rating', 'Top Players')
        self.stack_tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.stack_tree.heading(col, text=col)
            if col == 'Rank':
                self.stack_tree.column(col, width=50)
            elif col == 'Team':
                self.stack_tree.column(col, width=80)
            elif col == 'Top Players':
                self.stack_tree.column(col, width=300)
            else:
                self.stack_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.stack_tree.yview)
        self.stack_tree.configure(yscrollcommand=scrollbar.set)
        
        self.stack_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_debug_tab(self):
        """Create debug tab"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔧 Debug")
        
        tk.Label(frame, text="Debug Information", font=('Arial', 16, 'bold')).pack(pady=10)
        
        self.debug_text = scrolledtext.ScrolledText(frame, height=25, width=80, 
                                                   font=('Consolas', 10))
        self.debug_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Clear button
        tk.Button(frame, text="🗑️ Clear Debug", command=self.clear_debug).pack(pady=5)
        
    def debug_log(self, message):
        """Add debug message"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}\n"
            self.debug_text.insert(tk.END, formatted_message)
            self.debug_text.see(tk.END)
        except Exception as e:
            print(f"Debug log error: {e}")
        
    def clear_debug(self):
        """Clear debug text"""
        self.debug_text.delete(1.0, tk.END)
        
    def load_data(self):
        """Load all data"""
        self.debug_log("🚀 Starting data load...")
        
        # Load FanDuel slate data first (needed for validation)
        self.load_fd_slate_data()
        
        # Load ownership data
        self.load_ownership_data()
        
        # Load stack data (now using direct generation from FD slate)
        self.load_stack_data()
        
        # Update status
        if self.ownership_data and self.stack_data:
            self.status_label.config(text="● Live - Data Loaded", fg='green')
        else:
            self.status_label.config(text="● Partial Data", fg='orange')
            
        self.debug_log("✅ Data load complete")
        
    def load_fd_slate_data(self):
        """Load FanDuel slate data for validation"""
        try:
            slate_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'fd_current_slate')
            fd_file = os.path.join(slate_dir, 'fd_slate_today.csv')
            
            if os.path.exists(fd_file):
                self.fd_slate_data = pd.read_csv(fd_file)
                self.debug_log(f"✅ Loaded FanDuel slate: {len(self.fd_slate_data)} players")
            else:
                self.debug_log("❌ FD slate file not found")
                self.fd_slate_data = pd.DataFrame()
        except Exception as e:
            self.debug_log(f"❌ Error loading FD slate: {str(e)}")
            self.fd_slate_data = pd.DataFrame()
        
    def load_ownership_data(self):
        """Load ownership projections"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(script_dir), "data")
            today = datetime.now().strftime("%Y%m%d")
            
            # Look for today's ownership projections
            ownership_pattern = f"advanced_ownership_projections_{today}_*.csv"
            files = glob.glob(os.path.join(data_dir, ownership_pattern))
            
            if files:
                file_path = max(files, key=os.path.getmtime)  # Get most recent
                self.debug_log(f"Reading: {os.path.basename(file_path)}")
                df = safe_read_csv(file_path)
                
                if df is not None and len(df) > 0:
                    # Find the ownership column
                    ownership_col = None
                    for col in ['ownership', 'projected_ownership', 'own_proj', 'ownership_projection']:
                        if col in df.columns:
                            ownership_col = col
                            break
                    
                    if not ownership_col:
                        self.debug_log("❌ No ownership column found")
                        return
                    
                    self.ownership_data = {
                        'total_players': len(df),
                        'chalk_plays': len(df[df[ownership_col] > 0.25]),
                        'contrarian_targets': len(df[df[ownership_col] < 0.05]),  # Updated for real data range
                        'players': df.to_dict('records')
                    }
                    
                    # Update UI
                    self.total_players.config(text=str(self.ownership_data['total_players']))
                    self.chalk_plays.config(text=str(self.ownership_data['chalk_plays']))
                    self.contrarian_targets.config(text=str(self.ownership_data['contrarian_targets']))
                    
                    self.debug_log(f"✅ Loaded {len(df)} ownership projections")
                else:
                    self.debug_log("❌ Failed to load ownership data")
            else:
                self.debug_log("❌ No ownership projection files found")
                
        except Exception as e:
            self.debug_log(f"❌ Error loading ownership data: {str(e)}")
            
    def load_stack_data(self):
        """Generate stack data directly from today's FD slate and ownership projections"""
        try:
            self.debug_log("Loading stack data...")
            
            # Use FD slate to get actual teams playing today
            if not hasattr(self, 'fd_slate_data') or self.fd_slate_data.empty:
                self.debug_log("❌ No FD slate data available")
                return
                
            # Get teams actually in today's slate
            teams_in_slate = sorted(self.fd_slate_data['Team'].unique())
            self.debug_log(f"🎯 Generating stacks for {len(teams_in_slate)} teams in today's slate: {teams_in_slate}")
            
            # Generate team stacks using real data
            team_stacks = []
            
            for team in teams_in_slate:
                # Get team players from FD slate
                team_players = self.fd_slate_data[self.fd_slate_data['Team'] == team]
                hitters = team_players[team_players['Position'] != 'P']
                
                if len(hitters) < 4:  # Need at least 4 hitters for a stack
                    self.debug_log(f"⚠️ {team} has only {len(hitters)} hitters - skipping stack")
                    continue
                
                # Find projection and salary columns
                projection_col = None
                salary_col = None
                
                for col in team_players.columns:
                    if 'fppg' in col.lower() or 'projection' in col.lower():
                        projection_col = col
                    elif 'salary' in col.lower():
                        salary_col = col
                
                if not projection_col or not salary_col:
                    self.debug_log(f"⚠️ {team} missing projection or salary columns")
                    continue
                
                # Calculate stack metrics using top 4-5 hitters
                top_hitters = hitters.nlargest(5, projection_col)[:4]  # 4-stack
                
                avg_projection = top_hitters[projection_col].sum()
                avg_salary = top_hitters[salary_col].sum()
                
                # Calculate REAL team ownership from individual player projections
                team_ownership = self.calculate_team_ownership(team, f"{team} (4-stack)")
                
                stack_info = {
                    'team': team,
                    'projection': round(avg_projection, 1),
                    'salary': int(avg_salary),
                    'ownership': round(team_ownership, 1),
                    'value': round(avg_projection / (avg_salary / 1000), 2) if avg_salary > 0 else 0,
                    'players': f"{team} (4-stack) - Top hitters",
                    'players_with_own': f"{team} (4-stack) ({team_ownership:.1f}% avg)",
                    'lineup_count': 1  # Generated stack
                }
                team_stacks.append(stack_info)
                self.debug_log(f"📊 {team} stack: {len(top_hitters)} hitters, {team_ownership:.1f}% ownership, {avg_projection:.1f} projection")
            
            # Sort by projection
            self.stack_data = sorted(team_stacks, key=lambda x: x['projection'], reverse=True)
            self.debug_log(f"✅ Generated {len(self.stack_data)} team stacks from current slate")
            
            # Populate stack table with generated data
            for item in self.stack_tree.get_children():
                self.stack_tree.delete(item)
                
            for i, stack in enumerate(self.stack_data, 1):
                # Handle NaN projections
                projection = stack['projection']
                if pd.isna(projection):
                    proj_display = "TBD"
                    gpp_rating = "⏳ PENDING"
                else:
                    proj_display = f"{projection:.1f}"
                    # Calculate GPP rating based on REAL projection and ownership data
                    ownership = stack['ownership']
                    if projection > 105 and ownership < 3:
                        gpp_rating = "🚀 ELITE"
                    elif projection > 100 and ownership < 5:
                        gpp_rating = "✅ EXCELLENT"
                    elif projection > 95 and ownership < 8:
                        gpp_rating = "✅ GOOD"
                    elif ownership < 12:
                        gpp_rating = "⚠️ MODERATE"
                    else:
                        gpp_rating = "❌ HIGH OWNED"
                
                self.stack_tree.insert("", "end", values=(
                    i,
                    stack['team'],
                    proj_display,
                    f"${stack['salary']:,}",
                    f"{stack['ownership']:.1f}%",
                    f"{stack['value']:.2f}",
                    gpp_rating,
                    stack['players_with_own']
                ))
                
        except Exception as e:
            self.debug_log(f"❌ Error loading stack data: {str(e)}")
            import traceback
            self.debug_log(traceback.format_exc())

    def calculate_team_ownership(self, team, stack_description):
        """Calculate actual team ownership from individual player projections"""
        try:
            if not hasattr(self, 'ownership_data') or not self.ownership_data.get('players'):
                self.debug_log(f"⚠️ No ownership data available for {team}")
                return 1.0  # Very low fallback instead of 8.0
                
            # Get players for this team from ownership data
            team_players = [p for p in self.ownership_data['players'] if p.get('team', '').upper() == team.upper()]
            
            if not team_players:
                self.debug_log(f"⚠️ No players found for team {team}")
                return 1.0  # Very low fallback
            
            # Calculate average ownership for hitters (exclude pitchers)
            hitter_ownerships = []
            for player in team_players:
                position = player.get('position', '')
                ownership = player.get('ownership', 0)
                if position != 'P' and ownership > 0:  # Only hitters with ownership data
                    # Convert to percentage (ownership is in decimal format)
                    ownership_pct = ownership * 100
                    hitter_ownerships.append(ownership_pct)
            
            if hitter_ownerships:
                avg_ownership = sum(hitter_ownerships) / len(hitter_ownerships)
                # For 4-player stacks, ownership is typically 40-60% of individual average
                # This reflects the correlation between players
                stack_multiplier = 0.5  # 50% of individual average
                stack_ownership = avg_ownership * stack_multiplier
                
                self.debug_log(f"📊 {team} stack: {len(hitter_ownerships)} hitters, avg {avg_ownership:.1f}%, stack {stack_ownership:.1f}%")
                return max(stack_ownership, 0.5)  # Minimum 0.5% ownership
            else:
                self.debug_log(f"⚠️ No hitter ownership data for {team}")
                return 1.0  # Low fallback
                
        except Exception as e:
            self.debug_log(f"❌ Error calculating team ownership for {team}: {str(e)}")
            return 1.0

    def run(self):
        """Run the dashboard"""
        self.debug_log("🚀 Dashboard starting...")
        self.root.mainloop()


if __name__ == "__main__":
    print("🏆 Starting Working Elite DFS Dashboard...")
    
    dashboard = WorkingDashboard()
    dashboard.run()
