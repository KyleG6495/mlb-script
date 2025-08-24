#!/usr/bin/env python3
"""
SIMPLIFIED ELITE DFS DASHBOARD - No background monitoring
"""

import tkinter as tk
from tkinter import ttk
import os
import glob
from datetime import datetime
from file_finder_utils import get_data_files, safe_read_csv

class SimplifiedEliteDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏆 Elite DFS Dashboard - Simplified")
        self.root.geometry("1200x800")
        
        # Colors
        self.colors = {
            'bg': '#1a1a1a',
            'card': '#2d2d2d', 
            'accent': '#00ff88',
            'text': '#ffffff',
            'subtext': '#888888'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Create notebook for tabs
        style = ttk.Style()
        style.theme_use('clam')
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create tabs
        self.create_lineup_files_tab()
        self.create_quick_summary_tab()
        
        # Load data once
        self.load_data()
        
    def create_lineup_files_tab(self):
        """Lineup files overview"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📁 Lineup Files")
        
        # Title
        title_label = tk.Label(tab, text="📁 Available Lineup Files", 
                              bg=self.colors['bg'], fg=self.colors['text'],
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # File tree
        file_columns = ('File Name', 'Location', 'Lineups', 'Type', 'Status')
        self.files_tree = ttk.Treeview(tab, columns=file_columns, show='headings', height=20)
        
        for col in file_columns:
            self.files_tree.heading(col, text=col)
        
        self.files_tree.column('File Name', width=350)
        self.files_tree.column('Location', width=120)
        self.files_tree.column('Lineups', width=80)
        self.files_tree.column('Type', width=150)
        self.files_tree.column('Status', width=100)
        
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Refresh button
        refresh_btn = tk.Button(tab, text="🔄 Refresh", command=self.load_data,
                               bg=self.colors['accent'], fg=self.colors['bg'])
        refresh_btn.pack(pady=5)
        
    def create_quick_summary_tab(self):
        """Quick data summary"""
        tab = tk.Frame(self.notebook, bg=self.colors['bg'])
        self.notebook.add(tab, text="📊 Quick Summary")
        
        # Summary text
        self.summary_text = tk.Text(tab, bg=self.colors['card'], fg=self.colors['text'],
                                   font=('Courier', 11), wrap=tk.WORD)
        self.summary_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
    def load_data(self):
        """Load lineup files and summary"""
        # Clear existing data
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        today = datetime.now().strftime("%Y%m%d")
        total_files = 0
        total_lineups = 0
        
        # Load lineup files
        base_path = os.path.dirname(os.path.dirname(__file__))
        
        # Data folder
        data_pattern = os.path.join(base_path, "data", f"*lineup*{today}*.csv")
        for file_path in glob.glob(data_pattern):
            try:
                file_name = os.path.basename(file_path)
                with open(file_path, 'r') as f:
                    line_count = sum(1 for line in f) - 1
                
                file_type = self.get_file_type(file_name)
                
                self.files_tree.insert('', 'end', values=(
                    file_name, 'data/', line_count, file_type, '✅ Ready'
                ))
                
                total_files += 1
                total_lineups += line_count
                
            except Exception as e:
                self.files_tree.insert('', 'end', values=(
                    file_name, 'data/', 'Error', 'Unknown', '❌ Error'
                ))
        
        # FD folder
        fd_pattern = os.path.join(base_path, "fd_current_slate", f"*{today}*.csv")
        for file_path in glob.glob(fd_pattern):
            try:
                file_name = os.path.basename(file_path)
                with open(file_path, 'r') as f:
                    line_count = sum(1 for line in f) - 1
                
                file_type = self.get_file_type(file_name)
                status = '🎯 FD Ready' if 'FD_Format' in file_name else '✅ Ready'
                
                self.files_tree.insert('', 'end', values=(
                    file_name, 'fd_slate/', line_count, file_type, status
                ))
                
                total_files += 1
                total_lineups += line_count
                
            except Exception as e:
                self.files_tree.insert('', 'end', values=(
                    file_name, 'fd_slate/', 'Error', 'Unknown', '❌ Error'
                ))
        
        # Update summary
        self.update_summary(total_files, total_lineups)
        
    def get_file_type(self, filename):
        """Get file type from name"""
        if "elite_tournament" in filename.lower():
            return "🏆 Elite Tournament"
        elif "enhanced_ml" in filename.lower():
            return "🤖 Enhanced ML"
        elif "fd_format" in filename.lower():
            return "📤 FanDuel Ready"
        else:
            return "📊 Standard"
    
    def update_summary(self, total_files, total_lineups):
        """Update summary tab"""
        self.summary_text.delete(1.0, tk.END)
        
        summary = f"""
🎯 LINEUP FILES SUMMARY - {datetime.now().strftime('%Y-%m-%d %H:%M')}
{'=' * 60}

📊 TOTALS:
   Files Available: {total_files}
   Total Lineups: {total_lineups}
   
📁 LOCATIONS:
   Main Data: c:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\
   FanDuel Ready: c:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\fd_current_slate\\

🎯 READY TO ENTER:
   ✅ All files are available for lineup entry
   🎯 Look for "FD Ready" status for direct upload
   📊 Elite Tournament files contain optimized stacks

💡 TIP: Use the "Lineup Files" tab to see detailed breakdown!
"""
        
        self.summary_text.insert(tk.END, summary)
    
    def run(self):
        """Start dashboard"""
        print("🏆 Simplified Elite Dashboard starting...")
        self.root.mainloop()

if __name__ == "__main__":
    dashboard = SimplifiedEliteDashboard()
    dashboard.run()
