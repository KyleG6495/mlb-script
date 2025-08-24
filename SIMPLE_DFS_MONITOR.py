#!/usr/bin/env python3
"""
SIMPLE DFS PROGRESS MONITOR
===========================
Shows progress of DFS workflow in terminal with colors and updates
"""

import subprocess
import time
import re
import os
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    """Print the header"""
    print(f"\n{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}LINEUP: PROFESSIONAL DFS WORKFLOW MONITOR{Colors.END}")
    print(f"{Colors.BOLD}{Colors.GREEN}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}Real-time monitoring of your complete DFS optimization system{Colors.END}")
    print(f"{Colors.YELLOW}Starting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")

def print_progress_bar(current, total, prefix="", suffix="", length=50):
    """Print a progress bar"""
    percent = f"{100 * (current / float(total)):.1f}"
    filled_length = int(length * current // total)
    bar = '' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{Colors.GREEN}{bar}{Colors.END}| {percent}% {suffix}', end='', flush=True)

def monitor_workflow():
    """Monitor the DFS workflow execution"""
    
    print_header()
    
    # Statistics tracking
    stats = {
        'players_loaded': 0,
        'players_filtered': 0,
        'lineups_generated': 0,
        'ownership_calculated': 0,
        'swaps_executed': 0
    }
    
    # Phase tracking
    phases = [
        "DATA: Phase 1: Data Pipeline",
        "LINEUP: Phase 2: Enhanced Elite System", 
        "OWNERSHIP: Phase 3: Ownership Edge System",
        "BASEBALL: Phase 4: Filtered Optimization",
        "SWAP: Phase 5: Late Swap Monitoring"
    ]
    
    current_phase = 0
    
    try:
        # Change to workflow directory
        workflow_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\DAILY_RUNNERS"
        os.chdir(workflow_dir)
        
        print(f"{Colors.BLUE} Working directory: {workflow_dir}{Colors.END}")
        print(f"{Colors.YELLOW}START: Starting COMPLETE_HYBRID_WORKFLOW.bat...{Colors.END}\n")
        
        # Start the process
        process = subprocess.Popen(
            ["cmd", "/c", "COMPLETE_HYBRID_WORKFLOW.bat"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        # Monitor output
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
                
            if output:
                line = output.strip()
                
                # Update current phase
                if "PHASE 1" in line or "DATA PIPELINE" in line:
                    current_phase = 0
                elif "PHASE 2" in line or "Enhanced Elite" in line:
                    current_phase = 1
                elif "PHASE 3" in line or "Ownership Edge" in line:
                    current_phase = 2
                elif "PHASE 4" in line or "Filtered" in line:
                    current_phase = 3
                elif "PHASE 5" in line or "Late Swap" in line:
                    current_phase = 4
                
                # Extract statistics
                if "Loaded" in line and "player" in line:
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        stats['players_loaded'] = int(numbers[0])
                        
                if "filtered" in line.lower() and "player" in line:
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        stats['players_filtered'] = int(numbers[0])
                        
                if "lineup" in line.lower() and ("generated" in line or "created" in line):
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        stats['lineups_generated'] = int(numbers[0])
                        
                if "ownership" in line.lower():
                    numbers = re.findall(r'\d+', line)
                    if numbers:
                        stats['ownership_calculated'] = int(numbers[0])
                        
                if "swap" in line.lower() and "executed" in line:
                    stats['swaps_executed'] += 1
                
                # Print current phase
                if current_phase < len(phases):
                    phase_progress = (current_phase + 1) / len(phases) * 100
                    print(f"\n{Colors.BOLD}{phases[current_phase]}{Colors.END}")
                    print_progress_bar(current_phase + 1, len(phases), "Overall Progress:", f"({phase_progress:.0f}%)")
                
                # Print statistics
                print(f"\n{Colors.CYAN}DATA: Live Statistics:{Colors.END}")
                print(f"    Players Loaded: {Colors.GREEN}{stats['players_loaded']}{Colors.END}")
                print(f"   FILTER: Players Filtered: {Colors.RED}{stats['players_filtered']}{Colors.END}")
                print(f"   LINEUP: Lineups Generated: {Colors.BLUE}{stats['lineups_generated']}{Colors.END}")
                print(f"   OWNERSHIP: Ownership Calculated: {Colors.PURPLE}{stats['ownership_calculated']}{Colors.END}")
                print(f"   SWAP: Late Swaps: {Colors.YELLOW}{stats['swaps_executed']}{Colors.END}")
                
                # Print the actual output with color coding
                if "ERROR" in line or "error" in line:
                    print(f"{Colors.RED}ERROR: {line}{Colors.END}")
                elif "SUCCESS" in line or "SUCCESS:" in line or "Complete" in line:
                    print(f"{Colors.GREEN}SUCCESS: {line}{Colors.END}")
                elif "WARNING" in line or "WARNING:" in line:
                    print(f"{Colors.YELLOW}WARNING: {line}{Colors.END}")
                elif "Step" in line:
                    print(f"{Colors.BLUE}STEP: {line}{Colors.END}")
                else:
                    print(f"{Colors.WHITE}{line}{Colors.END}")
        
        # Process completed
        return_code = process.wait()
        
        print(f"\n{Colors.BOLD}{'='*80}{Colors.END}")
        if return_code == 0:
            print(f"{Colors.GREEN}COMPLETE: WORKFLOW COMPLETED SUCCESSFULLY!{Colors.END}")
            print(f"{Colors.CYAN}SUCCESS: All 5 phases completed without errors{Colors.END}")
            print(f"{Colors.YELLOW} Check your data folder for the generated lineups{Colors.END}")
        else:
            print(f"{Colors.RED}ERROR: WORKFLOW COMPLETED WITH ERRORS (Code: {return_code}){Colors.END}")
            
        print(f"{Colors.BOLD}{'='*80}{Colors.END}")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW} Workflow stopped by user{Colors.END}")
        if process:
            process.terminate()
    except Exception as e:
        print(f"{Colors.RED}ERROR: Error: {str(e)}{Colors.END}")

if __name__ == "__main__":
    monitor_workflow()
