import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import pandas as pd
import numpy as np
import threading
import time
from datetime import datetime, timedelta
import os
import json
import traceback

class UserFriendlyEliteDFSDashboard:
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
            'blue': '#007bff',
            'green': '#28a745',
            'red': '#dc3545'
        }
        
        # Real data storage
        self.ownership_data = {}
        self.stack_data = []
        self.opportunities_data = []
        self.lineups_data = []
        self.simple_recommendations = {}
        
        # Debug info
        self.debug_info = []
        
        # Monitoring
        self.monitoring = True
        self.update_interval = 5000  # 5 seconds
        
        self.setup_gui()
        self.start_monitoring()
        
    def setup_gui(self):
        """Initialize the user-friendly GUI"""
        self.root = tk.Tk()
        self.root.title("🏆 Elite DFS Dashboard - User Friendly Edition")
        self.root.geometry("1400x900")
        self.root.configure(bg=self.colors['bg'])
        
        # Header with help button
        header_frame = tk.Frame(self.root, bg=self.colors['card'], height=80)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, text="🏆 Elite DFS Dashboard", 
                              bg=self.colors['card'], fg=self.colors['accent'],
                              font=('Arial', 20, 'bold'))
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Help button
        help_btn = tk.Button(header_frame, text="❓ How to Use", 
                           bg=self.colors['blue'], fg='white',
                           font=('Arial', 12, 'bold'),
                           command=self.show_help)
        help_btn.pack(side=tk.RIGHT, padx=(0, 20), pady=20)
        
        self.status_label = tk.Label(header_frame, text="🔴 Loading...", 
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
        
        self.create_simple_plays_tab()
        self.create_tournament_strategy_tab()
        self.create_cash_game_tab()
        self.create_ownership_analysis_tab()
        self.create_ready_lineups_tab()
        self.create_live_monitor_tab()
        
    def show_help(self):
        """Show help dialog"""
        help_text = """
🎯 QUICK START GUIDE:

1️⃣ SIMPLE PLAYS TAB:
   • Green = Good tournament plays
   • Yellow = Decent cash game plays  
   • Red = Avoid (too popular)

2️⃣ TOURNAMENT STRATEGY:
   • Use low ownership players
   • Stack 3-4 players from same team
   • Aim for <15% total ownership

3️⃣ CASH GAMES:
   • Use high floor players
   • Ownership 15-30% is fine
   • Focus on consistency

4️⃣ READY LINEUPS:
   • Copy and paste lineups
   • Low ownership% = better for tournaments
   • High projections = better for cash

💡 KEY RULE: 
Lower ownership + High projection = 💰
        """
        
        messagebox.showinfo("🏆 How to Use Dashboard", help_text)
        
    def create_simple_plays_tab(self):
        """Simplified recommendations with color coding"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🎯 Simple Plays")
        
        # Header with explanation
        header_text = tk.Label(tab, 
                              text="🎯 SIMPLIFIED PLAYER RECOMMENDATIONS\n" +
                                   "🟢 Green = Tournament Gold | 🟡 Yellow = Cash Game Safe | 🔴 Red = Avoid",
                              bg=self.colors['bg'], fg=self.colors['text'],
                              font=('Arial', 14, 'bold'),
                              justify=tk.CENTER)
        header_text.pack(pady=10)
        
        # Three columns for different play types
        columns_frame = tk.Frame(tab, bg=self.colors['bg'])
        columns_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tournament plays (Green)
        tournament_frame = tk.LabelFrame(columns_frame, text="🟢 TOURNAMENT PLAYS (Low Ownership)",
                                        fg=self.colors['success'], bg=self.colors['card'],
                                        font=('Arial', 12, 'bold'))
        tournament_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.tournament_text = scrolledtext.ScrolledText(tournament_frame,
                                                        bg=self.colors['bg'],
                                                        fg=self.colors['success'],
                                                        font=('Consolas', 10),
                                                        height=20)
        self.tournament_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Cash game plays (Yellow)
        cash_frame = tk.LabelFrame(columns_frame, text="🟡 CASH GAME PLAYS (Safe Floor)",
                                  fg=self.colors['warning'], bg=self.colors['card'],
                                  font=('Arial', 12, 'bold'))
        cash_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self.cash_text = scrolledtext.ScrolledText(cash_frame,
                                                  bg=self.colors['bg'],
                                                  fg=self.colors['warning'],
                                                  font=('Consolas', 10),
                                                  height=20)
        self.cash_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Avoid plays (Red)
        avoid_frame = tk.LabelFrame(columns_frame, text="🔴 AVOID PLAYS (High Ownership)",
                                   fg=self.colors['danger'], bg=self.colors['card'],
                                   font=('Arial', 12, 'bold'))
        avoid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.avoid_text = scrolledtext.ScrolledText(avoid_frame,
                                                   bg=self.colors['bg'],
                                                   fg=self.colors['danger'],
                                                   font=('Consolas', 10),
                                                   height=20)
        self.avoid_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def create_tournament_strategy_tab(self):
        """Tournament-specific strategy"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="🏆 Tournament Strategy")
        
        # Strategy explanation
        strategy_text = tk.Label(tab, 
                                text="🏆 TOURNAMENT STRATEGY: Be Different to Win Big!",
                                bg=self.colors['bg'], fg=self.colors['accent'],
                                font=('Arial', 16, 'bold'))
        strategy_text.pack(pady=10)
        
        # Strategy content
        self.tournament_strategy_text = scrolledtext.ScrolledText(tab,
                                                                 bg=self.colors['bg'],
                                                                 fg=self.colors['text'],
                                                                 font=('Consolas', 11),
                                                                 wrap=tk.WORD)
        self.tournament_strategy_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_cash_game_tab(self):
        """Cash game strategy"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="💰 Cash Games")
        
        # Cash game explanation
        cash_text = tk.Label(tab, 
                            text="💰 CASH GAMES: Consistency Wins!",
                            bg=self.colors['bg'], fg=self.colors['success'],
                            font=('Arial', 16, 'bold'))
        cash_text.pack(pady=10)
        
        self.cash_strategy_text = scrolledtext.ScrolledText(tab,
                                                           bg=self.colors['bg'],
                                                           fg=self.colors['text'],
                                                           font=('Consolas', 11),
                                                           wrap=tk.WORD)
        self.cash_strategy_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_ownership_analysis_tab(self):
        """Detailed ownership with explanations"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📊 Ownership Analysis")
        
        # Explanation
        explain_text = tk.Label(tab, 
                               text="📊 OWNERSHIP ANALYSIS: Understanding the Numbers",
                               bg=self.colors['bg'], fg=self.colors['blue'],
                               font=('Arial', 16, 'bold'))
        explain_text.pack(pady=10)
        
        # Ownership table with explanations
        self.ownership_analysis_text = scrolledtext.ScrolledText(tab,
                                                                bg=self.colors['bg'],
                                                                fg=self.colors['text'],
                                                                font=('Consolas', 10),
                                                                wrap=tk.WORD)
        self.ownership_analysis_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def create_ready_lineups_tab(self):
        """Copy-paste ready lineups"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📋 Ready Lineups")
        
        # Instructions
        instruct_text = tk.Label(tab, 
                                text="📋 READY-TO-USE LINEUPS: Copy & Paste into DraftKings/FanDuel",
                                bg=self.colors['bg'], fg=self.colors['accent'],
                                font=('Arial', 16, 'bold'))
        instruct_text.pack(pady=10)
        
        # Lineup display with copy buttons
        lineups_frame = tk.Frame(tab, bg=self.colors['bg'])
        lineups_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tournament lineup
        tournament_lineup_frame = tk.LabelFrame(lineups_frame, text="🏆 Best Tournament Lineup",
                                               fg=self.colors['success'], bg=self.colors['card'],
                                               font=('Arial', 12, 'bold'))
        tournament_lineup_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 5))
        
        self.tournament_lineup_text = scrolledtext.ScrolledText(tournament_lineup_frame,
                                                               bg=self.colors['bg'],
                                                               fg=self.colors['text'],
                                                               font=('Consolas', 11),
                                                               height=8)
        self.tournament_lineup_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Cash game lineup
        cash_lineup_frame = tk.LabelFrame(lineups_frame, text="💰 Best Cash Game Lineup",
                                         fg=self.colors['warning'], bg=self.colors['card'],
                                         font=('Arial', 12, 'bold'))
        cash_lineup_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.cash_lineup_text = scrolledtext.ScrolledText(cash_lineup_frame,
                                                         bg=self.colors['bg'],
                                                         fg=self.colors['text'],
                                                         font=('Consolas', 11),
                                                         height=8)
        self.cash_lineup_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
    def create_live_monitor_tab(self):
        """Live monitoring and alerts"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📡 Live Monitor")
        
        # Status indicators
        status_frame = tk.Frame(tab, bg=self.colors['bg'])
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.data_status = tk.Label(status_frame, text="📊 Data: Loading...", 
                                   bg=self.colors['card'], fg=self.colors['warning'],
                                   font=('Arial', 12), relief=tk.RAISED, bd=2)
        self.data_status.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.update_status = tk.Label(status_frame, text="🔄 Updates: Every 5 sec", 
                                     bg=self.colors['card'], fg=self.colors['blue'],
                                     font=('Arial', 12), relief=tk.RAISED, bd=2)
        self.update_status.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        self.alert_status = tk.Label(status_frame, text="🚨 Alerts: Active", 
                                    bg=self.colors['card'], fg=self.colors['success'],
                                    font=('Arial', 12), relief=tk.RAISED, bd=2)
        self.alert_status.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.X, expand=True)
        
        # Live feed
        self.live_monitor_text = scrolledtext.ScrolledText(tab,
                                                          bg=self.colors['bg'],
                                                          fg=self.colors['text'],
                                                          font=('Consolas', 10),
                                                          wrap=tk.WORD)
        self.live_monitor_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
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
                self.debug_log("Loading data for user-friendly display...")
                self.load_real_ownership_data()
                self.load_real_stack_data()
                self.load_real_lineup_data()
                self.check_submitted_lineups()  # Add late swap monitoring
                self.generate_simple_recommendations()
                self.debug_log("User-friendly data ready")
                time.sleep(5)
            except Exception as e:
                self.debug_log(f"Monitor error: {str(e)}")
                time.sleep(10)
                
    def check_submitted_lineups(self):
        """Check submitted lineups for late swap issues"""
        try:
            # Load submitted lineups
            lineup_path = "../data/FANDUEL_READY_ELITE_LINEUPS_20250815.csv"
            if not os.path.exists(lineup_path):
                return
                
            df = pd.read_csv(lineup_path)
            
            # Extract all players
            submitted_players = []
            for _, lineup in df.iterrows():
                for col in df.columns:
                    if col != 'Nickname' and pd.notna(lineup[col]):
                        submitted_players.append(lineup[col])
            
            # Check for known issues
            alerts = []
            for player in set(submitted_players):
                if "Rob Refsnyder" in player:
                    alerts.append(f"🚨 CRITICAL: {player} NOT STARTING - Swap immediately!")
                elif "Hurston Waldrep" in player:
                    alerts.append(f"✅ CONFIRMED: {player} starting vs TEX")
            
            # Update live monitor with alerts
            if alerts:
                timestamp = datetime.now().strftime("%H:%M:%S")
                for alert in alerts:
                    self.debug_log(f"LATE SWAP: {alert}")
                    
        except Exception as e:
            self.debug_log(f"Late swap check error: {str(e)}")
                
    def debug_log(self, message):
        """Add debug message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.debug_info.append(f"[{timestamp}] {message}")
        if len(self.debug_info) > 50:
            self.debug_info = self.debug_info[-50:]
            
    def load_real_ownership_data(self):
        """Load actual ownership projections"""
        try:
            data_dir = "../data"
            ownership_file = "advanced_ownership_projections_20250815_133716.csv"
            path = os.path.join(data_dir, ownership_file)
            
            if os.path.exists(path):
                df = pd.read_csv(path)
                self.ownership_data = {
                    'players': df.to_dict('records'),
                    'total_players': len(df)
                }
                self.debug_log(f"Loaded {len(df)} players for analysis")
                
        except Exception as e:
            self.debug_log(f"Ownership error: {str(e)}")
            
    def load_real_stack_data(self):
        """Load stack data"""
        try:
            data_dir = "../data"
            proj_file = "enhanced_projections_20250815_133709.csv"
            proj_path = os.path.join(data_dir, proj_file)
            
            if os.path.exists(proj_path):
                df = pd.read_csv(proj_path)
                hitters = df[df['Position'] != 'P'].copy()
                
                # Generate team stacks
                team_stacks = []
                for team in hitters['Team'].value_counts().head(10).index:
                    team_players = hitters[hitters['Team'] == team]
                    if len(team_players) >= 3:
                        top_players = team_players.nlargest(4, 'enhanced_fppg')
                        total_proj = top_players['enhanced_fppg'].sum()
                        total_sal = top_players['Salary'].sum()
                        
                        team_stacks.append({
                            'team': team,
                            'projection': total_proj,
                            'salary': total_sal,
                            'players': top_players['Nickname'].tolist()
                        })
                        
                self.stack_data = sorted(team_stacks, key=lambda x: x['projection'], reverse=True)[:8]
                
        except Exception as e:
            self.debug_log(f"Stack error: {str(e)}")
            
    def load_real_lineup_data(self):
        """Load lineup data"""
        try:
            data_dir = "../data"
            lineup_file = "elite_tournament_lineups_20250815_133721.csv"
            path = os.path.join(data_dir, lineup_file)
            
            if os.path.exists(path):
                df = pd.read_csv(path)
                self.lineups_data = df.head(10).to_dict('records')
                
        except Exception as e:
            self.debug_log(f"Lineup error: {str(e)}")
            
    def generate_simple_recommendations(self):
        """Generate simplified recommendations"""
        if not self.ownership_data or 'players' not in self.ownership_data:
            return
            
        players = self.ownership_data['players']
        
        # Tournament plays (low ownership, high projection)
        tournament_plays = []
        cash_plays = []
        avoid_plays = []
        
        for player in players:
            ownership = float(player.get('ownership', 0))
            if ownership <= 1:  # Convert to percentage
                ownership *= 100
                
            projection = float(player.get('projection', 0))
            salary = int(player.get('salary', 0))
            
            if ownership < 10 and projection > 8:  # Low ownership, decent projection
                tournament_plays.append(player)
            elif 10 <= ownership <= 25 and projection > 10:  # Medium ownership, good projection
                cash_plays.append(player)
            elif ownership > 30:  # High ownership
                avoid_plays.append(player)
                
        self.simple_recommendations = {
            'tournament': sorted(tournament_plays, key=lambda x: float(x.get('projection', 0)), reverse=True)[:15],
            'cash': sorted(cash_plays, key=lambda x: float(x.get('projection', 0)), reverse=True)[:15],
            'avoid': sorted(avoid_plays, key=lambda x: float(x.get('ownership', 0)), reverse=True)[:15]
        }
        
    def update_gui(self):
        """Update all GUI elements"""
        try:
            self.update_simple_plays()
            self.update_tournament_strategy()
            self.update_cash_strategy()
            self.update_ownership_analysis()
            self.update_ready_lineups()
            self.update_live_monitor()
            
            # Update status
            if self.ownership_data and self.stack_data:
                self.status_label.config(text="🟢 Live Data Active", fg=self.colors['success'])
                self.data_status.config(text="📊 Data: ✅ Loaded", fg=self.colors['success'])
            else:
                self.status_label.config(text="🟡 Loading...", fg=self.colors['warning'])
            
        except Exception as e:
            self.debug_log(f"GUI update error: {str(e)}")
        
        self.root.after(self.update_interval, self.update_gui)
        
    def update_simple_plays(self):
        """Update simple plays tab"""
        if not self.simple_recommendations:
            return
            
        # Tournament plays
        self.tournament_text.delete(1.0, tk.END)
        tournament_content = "🟢 TOURNAMENT GOLD (Low Ownership):\n"
        tournament_content += "=" * 45 + "\n\n"
        
        for i, player in enumerate(self.simple_recommendations['tournament'][:10], 1):
            ownership = float(player.get('ownership', 0))
            if ownership <= 1:
                ownership *= 100
            tournament_content += f"{i:2d}. {player.get('player_name', 'Unknown')}\n"
            tournament_content += f"    💰 ${player.get('salary', 0):,} | 📊 {player.get('projection', 0):.1f} pts | 👥 {ownership:.1f}%\n"
            tournament_content += f"    🎯 {player.get('position', 'N/A')} - {player.get('team', 'N/A')}\n\n"
            
        self.tournament_text.insert(tk.END, tournament_content)
        
        # Cash plays
        self.cash_text.delete(1.0, tk.END)
        cash_content = "🟡 CASH GAME SAFE (Good Floor):\n"
        cash_content += "=" * 45 + "\n\n"
        
        for i, player in enumerate(self.simple_recommendations['cash'][:10], 1):
            ownership = float(player.get('ownership', 0))
            if ownership <= 1:
                ownership *= 100
            cash_content += f"{i:2d}. {player.get('player_name', 'Unknown')}\n"
            cash_content += f"    💰 ${player.get('salary', 0):,} | 📊 {player.get('projection', 0):.1f} pts | 👥 {ownership:.1f}%\n"
            cash_content += f"    🎯 {player.get('position', 'N/A')} - {player.get('team', 'N/A')}\n\n"
            
        self.cash_text.insert(tk.END, cash_content)
        
        # Avoid plays
        self.avoid_text.delete(1.0, tk.END)
        avoid_content = "🔴 AVOID (Too Popular):\n"
        avoid_content += "=" * 45 + "\n\n"
        
        for i, player in enumerate(self.simple_recommendations['avoid'][:10], 1):
            ownership = float(player.get('ownership', 0))
            if ownership <= 1:
                ownership *= 100
            avoid_content += f"{i:2d}. {player.get('player_name', 'Unknown')}\n"
            avoid_content += f"    💰 ${player.get('salary', 0):,} | 📊 {player.get('projection', 0):.1f} pts | 👥 {ownership:.1f}%\n"
            avoid_content += f"    ⚠️ Too popular for tournaments\n\n"
            
        self.avoid_text.insert(tk.END, avoid_content)
        
    def update_tournament_strategy(self):
        """Update tournament strategy"""
        self.tournament_strategy_text.delete(1.0, tk.END)
        
        content = f"""
🏆 TOURNAMENT STRATEGY GUIDE - {datetime.now().strftime('%H:%M:%S')}
═══════════════════════════════════════════════════════════════

🎯 THE GOLDEN RULE:
Be different from the crowd to win big money!

📊 OPTIMAL TOURNAMENT BUILD:
─────────────────────────────────────────────────────────────
1. Pick 1-2 players from GREEN list (low ownership studs)
2. Build a 4-man stack from same team (when they score, you win big)
3. Fill remaining spots with more GREEN players
4. AVOID RED players (everyone has them)

🔥 TOP TEAM STACKS RIGHT NOW:
─────────────────────────────────────────────────────────────
"""
        
        for i, stack in enumerate(self.stack_data[:5], 1):
            content += f"{i}. {stack.get('team', 'Unknown')} - {stack.get('projection', 0):.1f} projected points\n"
            content += f"   Players: {', '.join(stack.get('players', []))}\n"
            content += f"   Cost: ${stack.get('salary', 0):,}\n\n"
            
        content += """
💡 TOURNAMENT TIPS:
─────────────────────────────────────────────────────────────
• Target 8-15% total lineup ownership
• Use players under 10% ownership when possible  
• Stack teams playing in high-scoring games
• Pay up for low-owned superstars
• Take calculated risks on bench players

🚀 WHAT WINS TOURNAMENTS:
─────────────────────────────────────────────────────────────
• Unique lineups (different from 90% of field)
• High ceiling players (can score 30+ points)
• Correlated scoring (stack teammates)
• Contrarian thinking (fade popular narratives)
"""
        
        self.tournament_strategy_text.insert(tk.END, content)
        
    def update_cash_strategy(self):
        """Update cash game strategy"""
        self.cash_strategy_text.delete(1.0, tk.END)
        
        content = f"""
💰 CASH GAME STRATEGY GUIDE - {datetime.now().strftime('%H:%M:%S')}
═══════════════════════════════════════════════════════════════

🎯 THE GOLDEN RULE:
Consistency over ceiling - just beat 50% of the field!

📊 OPTIMAL CASH BUILD:
─────────────────────────────────────────────────────────────
1. Focus on YELLOW players (consistent performers)
2. Use 15-30% ownership players (proven, but not too chalky)
3. Target high floor projections over ceiling
4. Avoid super risky low-owned players
5. Pay for safety at key positions

💪 CASH GAME PRIORITIES:
─────────────────────────────────────────────────────────────
"""
        
        if self.simple_recommendations.get('cash'):
            content += "🥇 TOP CASH PLAYS:\n"
            for i, player in enumerate(self.simple_recommendations['cash'][:8], 1):
                ownership = float(player.get('ownership', 0))
                if ownership <= 1:
                    ownership *= 100
                content += f"{i}. {player.get('player_name', 'Unknown')} ({player.get('position', 'N/A')})\n"
                content += f"   💰 ${player.get('salary', 0):,} | 📊 {player.get('projection', 0):.1f} pts | 👥 {ownership:.1f}%\n\n"
        
        content += """
💡 CASH GAME TIPS:
─────────────────────────────────────────────────────────────
• Target 20-30% total lineup ownership
• Prioritize players with 12+ point floors
• Use proven veterans over rookies
• Avoid extremely low-owned punt plays
• Balance salary across all positions

✅ CASH GAME CHECKLIST:
─────────────────────────────────────────────────────────────
□ No player under 5% ownership
□ No player over 40% ownership  
□ Balanced salary distribution
□ High floor projections
□ Weather/injury concerns checked
"""
        
        self.cash_strategy_text.insert(tk.END, content)
        
    def update_ownership_analysis(self):
        """Update ownership analysis"""
        self.ownership_analysis_text.delete(1.0, tk.END)
        
        if not self.ownership_data or 'players' not in self.ownership_data:
            return
            
        content = f"""
📊 OWNERSHIP ANALYSIS - {datetime.now().strftime('%H:%M:%S')}
═══════════════════════════════════════════════════════════════

🎯 WHAT THE NUMBERS MEAN:
─────────────────────────────────────────────────────────────
Ownership %:
• 0-8%   = 🟢 Contrarian Gold (great for tournaments)
• 8-15%  = 🟡 Medium Owned (solid plays)  
• 15-25% = 🟠 Popular (good for cash, risky for GPP)
• 25%+   = 🔴 Chalk (avoid in tournaments)

📈 CURRENT OWNERSHIP BREAKDOWN:
─────────────────────────────────────────────────────────────
"""
        
        players = self.ownership_data['players']
        
        # Categorize by ownership
        contrarian = len([p for p in players if float(p.get('ownership', 0)) * (100 if float(p.get('ownership', 0)) <= 1 else 1) < 8])
        medium = len([p for p in players if 8 <= float(p.get('ownership', 0)) * (100 if float(p.get('ownership', 0)) <= 1 else 1) < 15])
        popular = len([p for p in players if 15 <= float(p.get('ownership', 0)) * (100 if float(p.get('ownership', 0)) <= 1 else 1) < 25])
        chalk = len([p for p in players if float(p.get('ownership', 0)) * (100 if float(p.get('ownership', 0)) <= 1 else 1) >= 25])
        
        content += f"🟢 Contrarian Plays (0-8%):    {contrarian} players\n"
        content += f"🟡 Medium Owned (8-15%):      {medium} players\n"
        content += f"🟠 Popular (15-25%):          {popular} players\n"
        content += f"🔴 Chalk (25%+):              {chalk} players\n\n"
        
        content += "🔥 BEST LEVERAGE OPPORTUNITIES:\n"
        content += "─────────────────────────────────────────────────────────────\n"
        
        # Show top leverage plays
        leverage_plays = [p for p in players if float(p.get('leverage_score', 0)) > 0.7]
        for i, player in enumerate(sorted(leverage_plays, key=lambda x: float(x.get('leverage_score', 0)), reverse=True)[:10], 1):
            ownership = float(player.get('ownership', 0))
            if ownership <= 1:
                ownership *= 100
            content += f"{i:2d}. {player.get('player_name', 'Unknown')} ({player.get('position', 'N/A')})\n"
            content += f"    Leverage: {player.get('leverage_score', 0):.2f} | Own: {ownership:.1f}% | Proj: {player.get('projection', 0):.1f}\n\n"
        
        self.ownership_analysis_text.insert(tk.END, content)
        
    def update_ready_lineups(self):
        """Update ready lineups"""
        if not self.lineups_data:
            return
            
        # Tournament lineup
        self.tournament_lineup_text.delete(1.0, tk.END)
        
        if self.lineups_data:
            # Find lowest ownership lineup
            tournament_lineup = min(self.lineups_data, key=lambda x: float(x.get('Avg_Ownership', 100)))
            
            content = f"""
🏆 TOURNAMENT LINEUP (Copy to DraftKings/FanDuel):
═══════════════════════════════════════════════════════════

💰 Total Salary: ${tournament_lineup.get('Total_Salary', 0):,}
📊 Projected Points: {tournament_lineup.get('Projected_Points', 0):.1f}
👥 Avg Ownership: {tournament_lineup.get('Avg_Ownership', 0):.1f}%
🎯 Leverage Score: {tournament_lineup.get('Leverage_Score', 0):.2f}

LINEUP:
───────────────────────────────────────────────────────────
P:  {tournament_lineup.get('P', 'N/A')}
C:  {tournament_lineup.get('C', 'N/A')}
1B: {tournament_lineup.get('1B', 'N/A')}
2B: {tournament_lineup.get('2B', 'N/A')}
3B: {tournament_lineup.get('3B', 'N/A')}
SS: {tournament_lineup.get('SS', 'N/A')}
OF: {tournament_lineup.get('OF1', 'N/A')}
OF: {tournament_lineup.get('OF2', 'N/A')}
OF: {tournament_lineup.get('OF3', 'N/A')}

🚀 Why This Lineup Wins:
• Low ownership = Different from field
• High leverage score = Tournament upside
• Stack team = Correlated scoring
"""
            
            self.tournament_lineup_text.insert(tk.END, content)
            
        # Cash lineup
        self.cash_lineup_text.delete(1.0, tk.END)
        
        if self.lineups_data:
            # Find highest projection lineup
            cash_lineup = max(self.lineups_data, key=lambda x: float(x.get('Projected_Points', 0)))
            
            content = f"""
💰 CASH GAME LINEUP (Copy to DraftKings/FanDuel):
═══════════════════════════════════════════════════════════

💰 Total Salary: ${cash_lineup.get('Total_Salary', 0):,}
📊 Projected Points: {cash_lineup.get('Projected_Points', 0):.1f}
👥 Avg Ownership: {cash_lineup.get('Avg_Ownership', 0):.1f}%
🏆 Floor Score: {cash_lineup.get('Floor_Score', 'N/A')}

LINEUP:
───────────────────────────────────────────────────────────
P:  {cash_lineup.get('P', 'N/A')}
C:  {cash_lineup.get('C', 'N/A')}
1B: {cash_lineup.get('1B', 'N/A')}
2B: {cash_lineup.get('2B', 'N/A')}
3B: {cash_lineup.get('3B', 'N/A')}
SS: {cash_lineup.get('SS', 'N/A')}
OF: {cash_lineup.get('OF1', 'N/A')}
OF: {cash_lineup.get('OF2', 'N/A')}
OF: {cash_lineup.get('OF3', 'N/A')}

✅ Why This Lineup Cashes:
• Highest projected points
• Safe ownership levels
• Consistent performers
• High floor projections
"""
            
            self.cash_lineup_text.insert(tk.END, content)
            
    def update_live_monitor(self):
        """Update live monitor"""
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Keep only last 30 lines
        content = self.live_monitor_text.get(1.0, tk.END)
        lines = content.split('\n')
        if len(lines) > 30:
            lines = lines[-30:]
            self.live_monitor_text.delete(1.0, tk.END)
            self.live_monitor_text.insert(tk.END, '\n'.join(lines))
        
        # Show critical late swap alerts first
        critical_alerts = [msg for msg in self.debug_info if "🚨 CRITICAL" in msg]
        if critical_alerts:
            for alert in critical_alerts[-3:]:  # Show last 3 critical alerts
                self.live_monitor_text.insert(tk.END, f"{alert}\n")
        
        # Add new status
        if self.ownership_data and self.stack_data:
            total_players = self.ownership_data.get('total_players', 0)
            tournament_plays = len(self.simple_recommendations.get('tournament', []))
            cash_plays = len(self.simple_recommendations.get('cash', []))
            
            status_line = f"[{current_time}] ✅ Data Updated - "
            status_line += f"{total_players} players analyzed, "
            status_line += f"{tournament_plays} tournament targets, "
            status_line += f"{cash_plays} cash plays, "
            status_line += f"{len(self.stack_data)} team stacks\n"
        else:
            status_line = f"[{current_time}] 🔄 Loading data...\n"
            
        self.live_monitor_text.insert(tk.END, status_line)
        self.live_monitor_text.see(tk.END)
        
    def run(self):
        """Start the dashboard"""
        print("🏆 Starting User-Friendly Elite DFS Dashboard...")
        print("📖 Simplified interface with color-coded recommendations")
        print("🎯 Click '❓ How to Use' button for quick help")
        
        self.root.mainloop()

if __name__ == "__main__":
    dashboard = UserFriendlyEliteDFSDashboard()
    dashboard.run()
