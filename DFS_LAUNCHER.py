#!/usr/bin/env python3
"""
SIMPLE DFS MONITOR LAUNCHER
===========================
Easy-to-start GUI for monitoring DFS workflow
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import os
import threading

def launch_workflow():
    """Launch the complete DFS workflow"""
    try:
        # Show that we're starting
        status_label.config(text="START: Starting DFS Workflow...", fg="yellow")
        start_button.config(state="disabled")
        
        # Change to the correct directory
        workflow_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
        
        def run_workflow():
            try:
                os.chdir(workflow_dir)
                result = subprocess.run(["cmd", "/c", "COMPLETE_HYBRID_WORKFLOW.bat"], 
                                      capture_output=True, text=True)
                
                if result.returncode == 0:
                    status_label.config(text="SUCCESS: Workflow Completed Successfully!", fg="green")
                else:
                    status_label.config(text="ERROR: Workflow had errors", fg="red")
                    
            except Exception as e:
                status_label.config(text=f"ERROR: Error: {str(e)}", fg="red")
            finally:
                start_button.config(state="normal")
        
        # Run in background thread
        thread = threading.Thread(target=run_workflow)
        thread.daemon = True
        thread.start()
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start workflow: {str(e)}")
        start_button.config(state="normal")

def open_data_folder():
    """Open the data folder to see results"""
    data_path = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    try:
        os.startfile(data_path)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open folder: {str(e)}")

def open_lineups_folder():
    """Open the FanDuel lineups folder"""
    fd_path = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate"
    try:
        os.startfile(fd_path)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open folder: {str(e)}")

# Create main window
root = tk.Tk()
root.title("LINEUP: DFS Workflow Launcher")
root.geometry("600x400")
root.configure(bg='#2d2d2d')

# Title
title_label = tk.Label(root, text="LINEUP: Professional DFS System", 
                      font=('Arial', 18, 'bold'), 
                      fg='#00ff00', bg='#2d2d2d')
title_label.pack(pady=20)

subtitle_label = tk.Label(root, text="Complete MLB DFS Optimization Workflow", 
                         font=('Arial', 12), 
                         fg='#cccccc', bg='#2d2d2d')
subtitle_label.pack(pady=5)

# Status
status_label = tk.Label(root, text="Ready to start workflow", 
                       font=('Arial', 14), 
                       fg='#ffffff', bg='#2d2d2d')
status_label.pack(pady=20)

# Main button
start_button = tk.Button(root, text="START: START COMPLETE DFS WORKFLOW", 
                        command=launch_workflow,
                        font=('Arial', 16, 'bold'),
                        bg='#00aa00', fg='white',
                        width=30, height=2)
start_button.pack(pady=20)

# Helper buttons frame
button_frame = tk.Frame(root, bg='#2d2d2d')
button_frame.pack(pady=20)

data_button = tk.Button(button_frame, text=" Open Data Folder", 
                       command=open_data_folder,
                       font=('Arial', 12),
                       bg='#0066aa', fg='white',
                       width=15)
data_button.pack(side=tk.LEFT, padx=10)

lineups_button = tk.Button(button_frame, text="DATA: Open Lineups Folder", 
                          command=open_lineups_folder,
                          font=('Arial', 12),
                          bg='#aa6600', fg='white',
                          width=15)
lineups_button.pack(side=tk.LEFT, padx=10)

# Instructions
instructions = tk.Text(root, height=8, width=70, 
                      bg='#1e1e1e', fg='#cccccc', 
                      font=('Arial', 10))
instructions.pack(pady=20, padx=20)

instructions.insert(tk.END, """TARGET: INSTRUCTIONS:

1. Click "START COMPLETE DFS WORKFLOW" to run all 5 phases:
    Phase 1: Enhanced Data Pipeline 
    Phase 2: Elite Championship Lineups
    Phase 3: Advanced Ownership Projections  
    Phase 4: Filtered Optimization
    Phase 5: Late Swap Monitoring

2. The status will update as the workflow runs

3. Use the folder buttons to view your results:
    Data Folder: All generated files and lineups
    Lineups Folder: FanDuel-ready submissions

4. Your lineups will be ready for tournament submission!""")

instructions.config(state=tk.DISABLED)

# Start the GUI
if __name__ == "__main__":
    print("START: Starting DFS Launcher GUI...")
    root.mainloop()
