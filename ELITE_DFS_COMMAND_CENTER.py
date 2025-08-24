"""
ELITE DFS COMMAND CENTER - Complete Professional Launch System
==============================================================

Launches your complete DFS ecosystem:
1. Real-time workflow monitoring 
2. Professional analytics dashboard
3. Ownership projection insights
4. Strategic opportunity alerts

Created: August 15, 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import time
import os
import sys
from datetime import datetime

class EliteDFSCommandCenter:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Elite DFS Command Center")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a1a')
        
        # System status
        self.workflow_running = False
        self.dashboard_running = False
        self.processes = {}
        
        # Colors
        self.colors = {
            'bg': '#1a1a1a',
            'card': '#2d2d2d',
            'accent': '#00d4aa',
            'warning': '#ff6b35', 
            'success': '#4caf50',
            'text': '#ffffff',
            'subtext': '#b0b0b0'
        }
        
        self.setup_gui()
        
    def setup_gui(self):
        """Create the command center interface"""
        
        # Title
        title_frame = tk.Frame(self.root, bg=self.colors['bg'])
        title_frame.pack(fill=tk.X, pady=20)
        
        title_label = tk.Label(title_frame,
                              text="🏆 ELITE DFS COMMAND CENTER",
                              font=('Arial', 24, 'bold'),
                              fg=self.colors['accent'],
                              bg=self.colors['bg'])
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame,
                                 text="Professional DFS Analytics & Automation Platform",
                                 font=('Arial', 12),
                                 fg=self.colors['subtext'],
                                 bg=self.colors['bg'])
        subtitle_label.pack(pady=(5, 0))
        
        # Status cards
        status_frame = tk.Frame(self.root, bg=self.colors['bg'])
        status_frame.pack(fill=tk.X, padx=40, pady=30)
        
        # Workflow status
        self.workflow_card = self.create_status_card(status_frame, 
                                                    "📊 DFS Workflow", 
                                                    "READY TO LAUNCH",
                                                    "Complete 5-phase optimization pipeline",
                                                    0)
        
        # Dashboard status  
        self.dashboard_card = self.create_status_card(status_frame,
                                                     "📈 Analytics Dashboard",
                                                     "READY TO LAUNCH", 
                                                     "Real-time ownership & opportunities",
                                                     1)
        
        # Control buttons
        control_frame = tk.Frame(self.root, bg=self.colors['bg'])
        control_frame.pack(fill=tk.X, padx=40, pady=30)
        
        # Launch everything button
        self.launch_all_btn = tk.Button(control_frame,
                                       text="🚀 LAUNCH COMPLETE SYSTEM",
                                       font=('Arial', 16, 'bold'),
                                       bg=self.colors['success'],
                                       fg='white',
                                       command=self.launch_complete_system,
                                       pady=15,
                                       cursor='hand2')
        self.launch_all_btn.pack(fill=tk.X, pady=(0, 15))
        
        # Individual control buttons
        button_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X)
        
        self.workflow_btn = tk.Button(button_frame,
                                     text="📊 Launch Workflow Only",
                                     font=('Arial', 12, 'bold'),
                                     bg=self.colors['accent'],
                                     fg='white',
                                     command=self.launch_workflow,
                                     pady=10,
                                     cursor='hand2')
        self.workflow_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.dashboard_btn = tk.Button(button_frame,
                                      text="📈 Launch Dashboard Only", 
                                      font=('Arial', 12, 'bold'),
                                      bg=self.colors['accent'],
                                      fg='white',
                                      command=self.launch_dashboard,
                                      pady=10,
                                      cursor='hand2')
        self.dashboard_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Stop button
        self.stop_btn = tk.Button(control_frame,
                                 text="⏹️ STOP ALL SYSTEMS",
                                 font=('Arial', 14, 'bold'),
                                 bg=self.colors['warning'],
                                 fg='white',
                                 command=self.stop_all_systems,
                                 pady=12,
                                 cursor='hand2')
        self.stop_btn.pack(fill=tk.X, pady=(15, 0))
        self.stop_btn.configure(state='disabled')
        
        # System info
        info_frame = tk.LabelFrame(self.root, 
                                  text="📋 System Information",
                                  font=('Arial', 12, 'bold'),
                                  fg=self.colors['text'],
                                  bg=self.colors['card'],
                                  relief=tk.RAISED,
                                  bd=2)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)
        
        info_text = f"""
🎯 ELITE DFS FEATURES:

📊 WORKFLOW SYSTEM:
   • 5-Phase optimization pipeline
   • Advanced ownership projections (0.5%-50% vs industry 95%)
   • Elite tournament optimization with deduplication
   • Late swap automation (30-second response)
   • Dynamic confirmed starters filtering

📈 ANALYTICS DASHBOARD:
   • Real-time ownership analysis & opportunities
   • Market inefficiency detection
   • Team stack optimization with weather integration
   • Live late swap alerts & recommendations  
   • Contest strategy & ROI projections

⚡ COMPETITIVE ADVANTAGES:
   • Professional-grade filtering (no more injured players)
   • Smart ownership curves (contrarian edge)
   • Lightning-fast late swaps (vs 15min industry standard)
   • Integrated weather/park factors
   • Multi-contest strategy optimization

🏆 SYSTEM STATUS: Ready for professional DFS domination
        """
        
        info_label = tk.Label(info_frame,
                             text=info_text.strip(),
                             font=('Consolas', 10),
                             fg=self.colors['text'],
                             bg=self.colors['card'],
                             justify=tk.LEFT,
                             anchor='nw')
        info_label.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)
        
        # Status monitoring
        self.start_status_monitoring()
        
    def create_status_card(self, parent, title, status, description, column):
        """Create a system status card"""
        card = tk.Frame(parent, bg=self.colors['card'], relief=tk.RAISED, bd=2)
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10 if column == 0 else (5, 10))
        
        # Title
        title_label = tk.Label(card, text=title,
                              font=('Arial', 14, 'bold'),
                              fg=self.colors['text'],
                              bg=self.colors['card'])
        title_label.pack(pady=(15, 5))
        
        # Status
        status_label = tk.Label(card, text=status,
                               font=('Arial', 12, 'bold'),
                               fg=self.colors['success'],
                               bg=self.colors['card'])
        status_label.pack()
        
        # Description
        desc_label = tk.Label(card, text=description,
                             font=('Arial', 10),
                             fg=self.colors['subtext'],
                             bg=self.colors['card'],
                             wraplength=200)
        desc_label.pack(pady=(5, 15))
        
        return {
            'card': card,
            'status_label': status_label
        }
        
    def launch_complete_system(self):
        """Launch both workflow and dashboard"""
        self.launch_workflow()
        time.sleep(2)  # Small delay
        self.launch_dashboard()
        
    def launch_workflow(self):
        """Launch the DFS workflow monitoring"""
        try:
            if not self.workflow_running:
                # Change to DAILY_RUNNERS directory and launch workflow
                cmd = 'cd "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\Scripts\\DAILY_RUNNERS" && COMPLETE_HYBRID_WORKFLOW.bat'
                
                process = subprocess.Popen(cmd, shell=True, cwd="C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\Scripts\\DAILY_RUNNERS")
                self.processes['workflow'] = process
                self.workflow_running = True
                
                # Update status
                self.workflow_card['status_label'].configure(text="🟢 RUNNING", fg=self.colors['success'])
                self.workflow_btn.configure(state='disabled')
                self.stop_btn.configure(state='normal')
                
                self.log_message("✅ DFS Workflow launched successfully")
                
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch workflow: {str(e)}")
            
    def launch_dashboard(self):
        """Launch the analytics dashboard"""
        try:
            if not self.dashboard_running:
                # Launch thread-safe dashboard in separate process
                cmd = f'python "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\Scripts\\SIMPLIFIED_ELITE_DFS_DASHBOARD.py"'
                
                process = subprocess.Popen(cmd, shell=True, cwd="C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\Scripts")
                self.processes['dashboard'] = process
                self.dashboard_running = True
                
                # Update status
                self.dashboard_card['status_label'].configure(text="🟢 RUNNING", fg=self.colors['success'])
                self.dashboard_btn.configure(state='disabled') 
                self.stop_btn.configure(state='normal')
                
                self.log_message("✅ Analytics Dashboard launched successfully (thread-safe version)")
                
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch dashboard: {str(e)}")
            
    def stop_all_systems(self):
        """Stop all running systems"""
        try:
            stopped_systems = []
            
            # Stop workflow
            if 'workflow' in self.processes and self.workflow_running:
                self.processes['workflow'].terminate()
                self.workflow_running = False
                self.workflow_card['status_label'].configure(text="⏹️ STOPPED", fg=self.colors['warning'])
                self.workflow_btn.configure(state='normal')
                stopped_systems.append("Workflow")
                
            # Stop dashboard
            if 'dashboard' in self.processes and self.dashboard_running:
                self.processes['dashboard'].terminate()
                self.dashboard_running = False
                self.dashboard_card['status_label'].configure(text="⏹️ STOPPED", fg=self.colors['warning'])
                self.dashboard_btn.configure(state='normal')
                stopped_systems.append("Dashboard")
                
            if not (self.workflow_running or self.dashboard_running):
                self.stop_btn.configure(state='disabled')
                
            if stopped_systems:
                self.log_message(f"⏹️ Stopped: {', '.join(stopped_systems)}")
            else:
                self.log_message("ℹ️ No systems were running")
                
        except Exception as e:
            messagebox.showerror("Stop Error", f"Error stopping systems: {str(e)}")
            
    def start_status_monitoring(self):
        """Start monitoring system status"""
        self.monitor_thread = threading.Thread(target=self.monitor_systems, daemon=True)
        self.monitor_thread.start()
        
    def monitor_systems(self):
        """Monitor running systems"""
        while True:
            try:
                # Check workflow process
                if 'workflow' in self.processes and self.workflow_running:
                    if self.processes['workflow'].poll() is not None:
                        # Process ended
                        self.workflow_running = False
                        self.root.after(0, lambda: self.workflow_card['status_label'].configure(
                            text="✅ COMPLETED", fg=self.colors['success']))
                        self.root.after(0, lambda: self.workflow_btn.configure(state='normal'))
                        
                # Check dashboard process  
                if 'dashboard' in self.processes and self.dashboard_running:
                    if self.processes['dashboard'].poll() is not None:
                        # Process ended
                        self.dashboard_running = False
                        self.root.after(0, lambda: self.dashboard_card['status_label'].configure(
                            text="⏹️ STOPPED", fg=self.colors['warning']))
                        self.root.after(0, lambda: self.dashboard_btn.configure(state='normal'))
                        
                # Update stop button state
                if not (self.workflow_running or self.dashboard_running):
                    self.root.after(0, lambda: self.stop_btn.configure(state='disabled'))
                    
            except Exception as e:
                print(f"Monitoring error: {str(e)}")
                
            time.sleep(2)
            
    def log_message(self, message):
        """Log a status message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def on_closing(self):
        """Handle window closing"""
        if self.workflow_running or self.dashboard_running:
            if messagebox.askokcancel("Quit", "Stop all systems and quit?"):
                self.stop_all_systems()
                time.sleep(1)
                self.root.destroy()
        else:
            self.root.destroy()
            
    def run(self):
        """Start the command center"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        print("🏆 Elite DFS Command Center Starting...")
        print("🎯 Professional DFS automation platform ready")
        print("📊 Use the interface to launch your complete system")
        
        self.root.mainloop()

if __name__ == "__main__":
    command_center = EliteDFSCommandCenter()
    command_center.run()
