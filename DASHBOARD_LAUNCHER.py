import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class DashboardLauncher:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏆 DFS Dashboard Launcher")
        self.root.geometry("600x500")
        self.root.configure(bg='#0f1419')
        
        self.colors = {
            'bg': '#0f1419',
            'card': '#1a1f2e',
            'accent': '#00d4aa',
            'text': '#ffffff',
            'success': '#00c851',
            'warning': '#ffbb33',
            'blue': '#007bff'
        }
        
        self.setup_gui()
        
    def setup_gui(self):
        # Header
        header_label = tk.Label(self.root, 
                               text="🏆 Elite DFS Dashboard Launcher",
                               bg=self.colors['bg'], fg=self.colors['accent'],
                               font=('Arial', 20, 'bold'))
        header_label.pack(pady=20)
        
        subtitle_label = tk.Label(self.root, 
                                 text="Choose the right dashboard for your needs",
                                 bg=self.colors['bg'], fg=self.colors['text'],
                                 font=('Arial', 12))
        subtitle_label.pack(pady=(0, 30))
        
        # Dashboard options
        self.create_dashboard_option(
            "🎯 USER FRIENDLY DASHBOARD",
            "⭐ RECOMMENDED FOR DAILY USE",
            "Simple color-coded recommendations (Green/Yellow/Red)\nEasy to read • Built-in help • Ready lineups",
            self.colors['success'],
            lambda: self.launch_dashboard("USER_FRIENDLY_ELITE_DFS_DASHBOARD.py")
        )
        
        self.create_dashboard_option(
            "📊 COMPLETE DASHBOARD", 
            "🔬 ADVANCED ANALYSIS",
            "All 8 tabs with every metric and analysis\nOwnership • Stacks • Opportunities • Contest Strategy",
            self.colors['blue'],
            lambda: self.launch_dashboard("COMPLETE_ELITE_DFS_DASHBOARD.py")
        )
        
        self.create_dashboard_option(
            "🐛 DEBUG DASHBOARD",
            "🔧 TROUBLESHOOTING",
            "System health monitoring and data verification\nUse when something seems wrong",
            self.colors['warning'],
            lambda: self.launch_dashboard("DEBUG_ELITE_DFS_DASHBOARD.py")
        )
        
        # Help section
        help_frame = tk.Frame(self.root, bg=self.colors['card'])
        help_frame.pack(fill=tk.X, padx=20, pady=20)
        
        help_label = tk.Label(help_frame,
                             text="💡 Not sure which to use? Start with USER FRIENDLY!",
                             bg=self.colors['card'], fg=self.colors['text'],
                             font=('Arial', 12, 'bold'))
        help_label.pack(pady=10)
        
        # Buttons
        button_frame = tk.Frame(self.root, bg=self.colors['bg'])
        button_frame.pack(pady=20)
        
        help_btn = tk.Button(button_frame, text="📖 Read Guide", 
                           bg=self.colors['blue'], fg='white',
                           font=('Arial', 12, 'bold'),
                           command=self.show_guide)
        help_btn.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Button(button_frame, text="❌ Close", 
                            bg=self.colors['warning'], fg='white',
                            font=('Arial', 12, 'bold'),
                            command=self.root.quit)
        close_btn.pack(side=tk.LEFT, padx=10)
        
    def create_dashboard_option(self, title, subtitle, description, color, command):
        frame = tk.Frame(self.root, bg=self.colors['card'], relief=tk.RAISED, bd=2)
        frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Title
        title_label = tk.Label(frame, text=title,
                              bg=self.colors['card'], fg=color,
                              font=('Arial', 14, 'bold'))
        title_label.pack(anchor=tk.W, padx=15, pady=(10, 0))
        
        # Subtitle  
        subtitle_label = tk.Label(frame, text=subtitle,
                                 bg=self.colors['card'], fg=self.colors['accent'],
                                 font=('Arial', 10, 'bold'))
        subtitle_label.pack(anchor=tk.W, padx=15)
        
        # Description
        desc_label = tk.Label(frame, text=description,
                             bg=self.colors['card'], fg=self.colors['text'],
                             font=('Arial', 10),
                             justify=tk.LEFT)
        desc_label.pack(anchor=tk.W, padx=15, pady=(5, 10))
        
        # Launch button
        launch_btn = tk.Button(frame, text="🚀 Launch Dashboard",
                              bg=color, fg='white',
                              font=('Arial', 11, 'bold'),
                              command=command)
        launch_btn.pack(anchor=tk.E, padx=15, pady=(0, 10))
        
    def launch_dashboard(self, dashboard_file):
        try:
            # Check if file exists
            if not os.path.exists(dashboard_file):
                messagebox.showerror("Error", f"Dashboard file not found: {dashboard_file}")
                return
                
            # Launch the dashboard
            subprocess.Popen([sys.executable, dashboard_file])
            
            # Show success message
            messagebox.showinfo("Dashboard Launched", 
                              f"✅ {dashboard_file} is starting up!\n\nCheck for the new window to appear.")
            
        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch dashboard:\n{str(e)}")
            
    def show_guide(self):
        guide_text = """
🎯 WHICH DASHBOARD TO USE:

🏆 USER FRIENDLY (Recommended):
• Perfect for daily lineup building
• Color-coded: Green=Tournament, Yellow=Cash, Red=Avoid
• Built-in help and explanations
• Ready-to-copy lineups

📊 COMPLETE DASHBOARD:
• All data and metrics available
• 8 detailed tabs with every analysis
• For research and deep dives
• Professional interface

🐛 DEBUG DASHBOARD:
• Technical monitoring
• Use when data seems wrong
• Shows system health status
• Troubleshooting tool

💡 RECOMMENDATION:
Use USER FRIENDLY 90% of the time.
Only use COMPLETE for research.
Only use DEBUG when something's broken.
        """
        
        messagebox.showinfo("📖 Dashboard Guide", guide_text)
        
    def run(self):
        print("🚀 Starting Dashboard Launcher...")
        self.root.mainloop()

if __name__ == "__main__":
    launcher = DashboardLauncher()
    launcher.run()
