#!/usr/bin/env python3
"""
TEST DASHBOARD - Simple version to verify functionality
"""

import tkinter as tk
from tkinter import ttk
import os
import glob
from datetime import datetime

class TestDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎯 MLB Lineup Files Dashboard - TEST")
        self.root.geometry("800x600")
        
        # Create main frame
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="📁 Your Lineup Files", 
                              font=('Arial', 16, 'bold'))
        title_label.pack(pady=10)
        
        # File list
        self.file_listbox = tk.Listbox(main_frame, height=20, font=('Courier', 10))
        self.file_listbox.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Refresh button
        refresh_btn = tk.Button(main_frame, text="🔄 Refresh Files", 
                               command=self.load_files, bg='lightblue')
        refresh_btn.pack(pady=5)
        
        # Load files initially
        self.load_files()
        
    def load_files(self):
        """Load and display lineup files"""
        self.file_listbox.delete(0, tk.END)
        
        today = datetime.now().strftime("%Y%m%d")
        total_lineups = 0
        
        try:
            # Check data folder
            base_path = os.path.dirname(os.path.dirname(__file__))
            data_path = os.path.join(base_path, "data")
            pattern = os.path.join(data_path, f"*lineup*{today}*.csv")
            
            self.file_listbox.insert(tk.END, "=== DATA FOLDER ===")
            
            for file_path in glob.glob(pattern):
                try:
                    file_name = os.path.basename(file_path)
                    with open(file_path, 'r') as f:
                        line_count = sum(1 for line in f) - 1
                    
                    self.file_listbox.insert(tk.END, f"  {file_name}: {line_count} lineups")
                    total_lineups += line_count
                except Exception as e:
                    self.file_listbox.insert(tk.END, f"  Error reading {file_name}: {e}")
            
            # Check FD folder
            fd_path = os.path.join(base_path, "fd_current_slate")
            fd_pattern = os.path.join(fd_path, f"*{today}*.csv")
            
            self.file_listbox.insert(tk.END, "")
            self.file_listbox.insert(tk.END, "=== FD_CURRENT_SLATE FOLDER ===")
            
            for file_path in glob.glob(fd_pattern):
                try:
                    file_name = os.path.basename(file_path)
                    with open(file_path, 'r') as f:
                        line_count = sum(1 for line in f) - 1
                    
                    self.file_listbox.insert(tk.END, f"  {file_name}: {line_count} lineups")
                    total_lineups += line_count
                except Exception as e:
                    self.file_listbox.insert(tk.END, f"  Error reading {file_name}: {e}")
            
            self.file_listbox.insert(tk.END, "")
            self.file_listbox.insert(tk.END, f"🎯 TOTAL: {total_lineups} lineups available!")
            
        except Exception as e:
            self.file_listbox.insert(tk.END, f"Error loading files: {e}")
    
    def run(self):
        """Start the dashboard"""
        print("🎯 Test Dashboard starting...")
        self.root.mainloop()

if __name__ == "__main__":
    dashboard = TestDashboard()
    dashboard.run()
