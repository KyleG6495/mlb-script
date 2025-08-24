#!/usr/bin/env python3
"""
REAL-TIME DFS WORKFLOW MONITOR
=============================
GUI that monitors actual DFS script execution with live progress tracking
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import subprocess
import threading
import time
import os
import queue
import re
from datetime import datetime

class DFSWorkflowMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("LINEUP: Real-Time DFS Workflow Monitor")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e1e1e')
        
        # Process tracking
        self.current_process = None
        self.output_queue = queue.Queue()
        self.running = False
        
        # Progress tracking
        self.current_phase = tk.StringVar(value="Ready to start...")
        self.current_step = tk.StringVar(value="Click 'Start Complete Workflow' to begin")
        self.total_progress = tk.DoubleVar(value=0)
        self.step_progress = tk.DoubleVar(value=0)
        
        # Statistics
        self.players_loaded = tk.StringVar(value="0")
        self.players_filtered = tk.StringVar(value="0")
        self.lineups_generated = tk.StringVar(value="0")
        self.ownership_projections = tk.StringVar(value="0")
        self.late_swaps = tk.StringVar(value="0")
        
        self.setup_gui()
        self.monitor_output()
        
    def setup_gui(self):
        """Setup the monitoring GUI"""
        
        # Title
        title_frame = tk.Frame(self.root, bg='#1e1e1e')
        title_frame.pack(fill=tk.X, padx=10, pady=5)
        
        title_label = tk.Label(title_frame, 
                              text="LINEUP: Professional DFS Workflow Monitor", 
                              font=('Arial', 20, 'bold'),
                              fg='#00ff00', bg='#1e1e1e')
        title_label.pack()
        
        subtitle_label = tk.Label(title_frame, 
                                 text="Real-time monitoring of complete DFS optimization pipeline", 
                                 font=('Arial', 12),
                                 fg='#cccccc', bg='#1e1e1e')
        subtitle_label.pack()
        
        # Status panel
        status_frame = tk.LabelFrame(self.root, text="DATA: Current Status", 
                                    bg='#2d2d2d', fg='#ffffff', 
                                    font=('Arial', 12, 'bold'))
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Phase and step
        tk.Label(status_frame, text="Phase:", font=('Arial', 11, 'bold'), 
                fg='#ffffff', bg='#2d2d2d').grid(row=0, column=0, sticky=tk.W, padx=10, pady=2)
        tk.Label(status_frame, textvariable=self.current_phase, font=('Arial', 11), 
                fg='#00ff00', bg='#2d2d2d').grid(row=0, column=1, sticky=tk.W, padx=10, pady=2)
        
        tk.Label(status_frame, text="Step:", font=('Arial', 11, 'bold'), 
                fg='#ffffff', bg='#2d2d2d').grid(row=1, column=0, sticky=tk.W, padx=10, pady=2)
        tk.Label(status_frame, textvariable=self.current_step, font=('Arial', 11), 
                fg='#ffff00', bg='#2d2d2d').grid(row=1, column=1, sticky=tk.W, padx=10, pady=2)
        
        # Progress bars
        progress_frame = tk.LabelFrame(self.root, text="PROGRESS: Progress Tracking", 
                                      bg='#2d2d2d', fg='#ffffff', 
                                      font=('Arial', 12, 'bold'))
        progress_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Overall progress
        tk.Label(progress_frame, text="Overall Workflow Progress:", 
                font=('Arial', 11), fg='#ffffff', bg='#2d2d2d').pack(anchor=tk.W, padx=10, pady=(5,0))
        
        self.overall_progress = ttk.Progressbar(progress_frame, 
                                               variable=self.total_progress,
                                               maximum=100, length=500)
        self.overall_progress.pack(padx=10, pady=5, fill=tk.X)
        
        # Step progress  
        tk.Label(progress_frame, text="Current Step Progress:", 
                font=('Arial', 11), fg='#ffffff', bg='#2d2d2d').pack(anchor=tk.W, padx=10, pady=(5,0))
        
        self.step_progress_bar = ttk.Progressbar(progress_frame, 
                                                variable=self.step_progress,
                                                maximum=100, length=500)
        self.step_progress_bar.pack(padx=10, pady=5, fill=tk.X)
        
        # Statistics panel
        stats_frame = tk.LabelFrame(self.root, text="DATA: Live Statistics", 
                                   bg='#2d2d2d', fg='#ffffff', 
                                   font=('Arial', 12, 'bold'))
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        stats_grid = tk.Frame(stats_frame, bg='#2d2d2d')
        stats_grid.pack(fill=tk.X, padx=10, pady=5)
        
        # Row 1
        tk.Label(stats_grid, text=" Players Loaded:", 
                font=('Arial', 10), fg='#ffffff', bg='#2d2d2d').grid(row=0, column=0, sticky=tk.W, padx=5)
        tk.Label(stats_grid, textvariable=self.players_loaded,
                font=('Arial', 10, 'bold'), fg='#66ff66', bg='#2d2d2d').grid(row=0, column=1, sticky=tk.W, padx=5)
        
        tk.Label(stats_grid, text="FILTER: Players Filtered:", 
                font=('Arial', 10), fg='#ffffff', bg='#2d2d2d').grid(row=0, column=2, sticky=tk.W, padx=5)
        tk.Label(stats_grid, textvariable=self.players_filtered,
                font=('Arial', 10, 'bold'), fg='#ff6666', bg='#2d2d2d').grid(row=0, column=3, sticky=tk.W, padx=5)
        
        tk.Label(stats_grid, text="LINEUP: Lineups Generated:", 
                font=('Arial', 10), fg='#ffffff', bg='#2d2d2d').grid(row=0, column=4, sticky=tk.W, padx=5)
        tk.Label(stats_grid, textvariable=self.lineups_generated,
                font=('Arial', 10, 'bold'), fg='#66ffff', bg='#2d2d2d').grid(row=0, column=5, sticky=tk.W, padx=5)
        
        # Row 2
        tk.Label(stats_grid, text="OWNERSHIP: Ownership Projections:", 
                font=('Arial', 10), fg='#ffffff', bg='#2d2d2d').grid(row=1, column=0, sticky=tk.W, padx=5)
        tk.Label(stats_grid, textvariable=self.ownership_projections,
                font=('Arial', 10, 'bold'), fg='#6666ff', bg='#2d2d2d').grid(row=1, column=1, sticky=tk.W, padx=5)
        
        tk.Label(stats_grid, text="SWAP: Late Swaps:", 
                font=('Arial', 10), fg='#ffffff', bg='#2d2d2d').grid(row=1, column=2, sticky=tk.W, padx=5)
        tk.Label(stats_grid, textvariable=self.late_swaps,
                font=('Arial', 10, 'bold'), fg='#ffff66', bg='#2d2d2d').grid(row=1, column=3, sticky=tk.W, padx=5)
        
        # Output log
        log_frame = tk.LabelFrame(self.root, text="INFO: Real-Time System Output", 
                                 bg='#2d2d2d', fg='#ffffff', 
                                 font=('Arial', 12, 'bold'))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, 
                                                 height=20, 
                                                 bg='#000000', 
                                                 fg='#00ff00',
                                                 font=('Consolas', 9),
                                                 wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Control panel
        control_frame = tk.Frame(self.root, bg='#1e1e1e')
        control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_button = tk.Button(control_frame, text="START: Start Complete Workflow", 
                                     command=self.start_workflow,
                                     bg='#00aa00', fg='white', 
                                     font=('Arial', 12, 'bold'),
                                     width=20)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = tk.Button(control_frame, text=" Stop Process", 
                                    command=self.stop_workflow,
                                    bg='#aa0000', fg='white', 
                                    font=('Arial', 12, 'bold'),
                                    width=15)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = tk.Button(control_frame, text=" Clear Log", 
                                     command=self.clear_log,
                                     bg='#555555', fg='white', 
                                     font=('Arial', 12),
                                     width=12)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        # Status indicator
        self.status_indicator = tk.Label(control_frame, text=" READY", 
                                        font=('Arial', 12, 'bold'),
                                        fg='#00ff00', bg='#1e1e1e')
        self.status_indicator.pack(side=tk.RIGHT, padx=10)
        
    def start_workflow(self):
        """Start the complete DFS workflow"""
        if self.running:
            return
            
        self.running = True
        self.start_button.configure(state='disabled')
        self.status_indicator.configure(text=" RUNNING", fg='#ffff00')
        
        # Start workflow in separate thread
        workflow_thread = threading.Thread(target=self.run_workflow)
        workflow_thread.daemon = True
        workflow_thread.start()
        
    def stop_workflow(self):
        """Stop the workflow process"""
        self.running = False
        if self.current_process:
            self.current_process.terminate()
        self.start_button.configure(state='normal')
        self.status_indicator.configure(text=" STOPPED", fg='#ff0000')
        self.add_log_message(" Workflow stopped by user", "WARNING")
        
    def clear_log(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
        
    def run_workflow(self):
        """Execute the complete DFS workflow with monitoring"""
        try:
            self.add_log_message("START: Starting Professional DFS Workflow Monitor", "SUCCESS")
            self.update_progress("STEP: Initialization", "Starting workflow...", 5, 0)
            
            # Change to the correct directory
            workflow_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
            os.chdir(workflow_dir)
            
            # Execute the complete workflow batch file
            cmd = ["cmd", "/c", "COMPLETE_HYBRID_WORKFLOW.bat"]
            
            self.current_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor output
            while self.current_process.poll() is None and self.running:
                output = self.current_process.stdout.readline()
                if output:
                    self.output_queue.put(output.strip())
                    
            # Get any remaining output
            if self.current_process.returncode == 0:
                self.add_log_message("SUCCESS: Complete workflow finished successfully!", "SUCCESS")
                self.status_indicator.configure(text=" COMPLETE", fg='#00ff00')
                self.update_progress("SUCCESS: Complete", "All systems operational!", 100, 100)
            else:
                self.add_log_message("ERROR: Workflow completed with errors", "ERROR")
                self.status_indicator.configure(text=" ERROR", fg='#ff0000')
                
        except Exception as e:
            self.add_log_message(f"ERROR: Error running workflow: {str(e)}", "ERROR")
            self.status_indicator.configure(text=" ERROR", fg='#ff0000')
        finally:
            self.running = False
            self.start_button.configure(state='normal')
            
    def monitor_output(self):
        """Monitor output queue and update GUI"""
        try:
            while True:
                output = self.output_queue.get_nowait()
                self.process_output(output)
                self.add_log_message(output, "INFO")
        except queue.Empty:
            pass
            
        # Schedule next check
        self.root.after(100, self.monitor_output)
        
    def process_output(self, output):
        """Process output to extract progress and statistics"""
        
        # Phase detection
        if "PHASE 1" in output or "DATA PIPELINE" in output:
            self.update_progress("DATA: Phase 1: Data Pipeline", "Processing data...", 10, 50)
        elif "PHASE 2" in output or "Enhanced Elite System" in output:
            self.update_progress("LINEUP: Phase 2: Elite System", "Building lineups...", 30, 25)
        elif "PHASE 3" in output or "Ownership Edge" in output:
            self.update_progress("OWNERSHIP: Phase 3: Ownership Edge", "Calculating ownership...", 50, 60)
        elif "PHASE 4" in output or "Filtered Optimization" in output:
            self.update_progress("BASEBALL: Phase 4: Optimization", "Running filters...", 70, 80)
        elif "PHASE 5" in output or "Late Swap" in output:
            self.update_progress("SWAP: Phase 5: Late Swap", "Monitoring lineups...", 90, 40)
            
        # Step detection
        if "Step 1:" in output:
            self.current_step.set("Loading enhanced projections...")
        elif "Step 2:" in output:
            self.current_step.set("Building championship lineups...")
        elif "Step 3:" in output:
            self.current_step.set("Creating ownership projections...")
        elif "Step 4:" in output:
            self.current_step.set("Elite tournament optimization...")
        elif "Step 5:" in output:
            self.current_step.set("Running filtered optimizer...")
        elif "Step 6:" in output:
            self.current_step.set("Formatting for FanDuel...")
        elif "Step 7:" in output:
            self.current_step.set("Late swap monitoring...")
            
        # Statistics extraction
        if "Loaded" in output and "player" in output:
            numbers = re.findall(r'\d+', output)
            if numbers:
                self.players_loaded.set(numbers[0])
                
        if "filtered" in output.lower() and "player" in output:
            numbers = re.findall(r'\d+', output)
            if numbers:
                self.players_filtered.set(numbers[0])
                
        if "lineup" in output.lower() and ("generated" in output or "created" in output):
            numbers = re.findall(r'\d+', output)
            if numbers:
                self.lineups_generated.set(numbers[0])
                
        if "ownership" in output.lower() and "projection" in output:
            numbers = re.findall(r'\d+', output)
            if numbers:
                self.ownership_projections.set(numbers[0])
                
        if "swap" in output.lower() and ("executed" in output or "emergency" in output):
            current = self.late_swaps.get()
            self.late_swaps.set(str(int(current) + 1))
            
    def update_progress(self, phase, step, total_pct, step_pct):
        """Update progress indicators"""
        self.current_phase.set(phase)
        self.current_step.set(step)
        self.total_progress.set(total_pct)
        self.step_progress.set(step_pct)
        
    def add_log_message(self, message, level="INFO"):
        """Add message to log with color coding"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color coding
        colors = {
            "INFO": "#00ff00",
            "WARNING": "#ffff00",
            "ERROR": "#ff0000", 
            "SUCCESS": "#00ffff"
        }
        
        color = colors.get(level, "#00ff00")
        
        self.log_text.tag_configure(level, foreground=color)
        formatted_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, formatted_message, level)
        self.log_text.see(tk.END)

def main():
    """Main function"""
    root = tk.Tk()
    app = DFSWorkflowMonitor(root)
    
    # Initial messages
    app.add_log_message("LINEUP: Professional DFS Workflow Monitor Ready", "SUCCESS")
    app.add_log_message("TIP: This will run your complete HYBRID workflow with real-time monitoring", "INFO")
    app.add_log_message("DATA: Progress bars and statistics will update as scripts execute", "INFO")
    app.add_log_message("START: Click 'Start Complete Workflow' to begin monitoring", "INFO")
    
    root.mainloop()

if __name__ == "__main__":
    main()
