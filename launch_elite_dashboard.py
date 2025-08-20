import os
import sys
import subprocess
import webbrowser
import time

print("🏆 ELITE MLB DASHBOARD LAUNCHER 🏆")
print("=" * 50)

# Set environment variable to skip Streamlit email collection
os.environ['STREAMLIT_EMAIL_ENABLED'] = 'false'

# Change to the Scripts directory
scripts_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
os.chdir(scripts_dir)

print("🚀 Starting Elite Dashboard...")
print("📊 Professional DFS & Prop Betting Interface")
print("⚾ Ready for tonight's 7:15 PM slate")
print("=" * 50)

try:
    # Start Streamlit with configuration to skip email
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        "ELITE_MLB_DASHBOARD.py",
        "--server.port", "8503",
        "--server.address", "localhost",
        "--server.headless", "true",
        "--global.disableWatchdogWarning", "true"
    ]
    
    print("🔄 Launching dashboard server...")
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait a few seconds for server to start
    time.sleep(5)
    
    # Open browser
    dashboard_url = "http://localhost:8503"
    print(f"🌐 Opening dashboard at: {dashboard_url}")
    webbrowser.open(dashboard_url)
    
    print("✅ Elite Dashboard is now running!")
    print("💡 Close this window to stop the dashboard")
    print("=" * 50)
    
    # Keep the process running
    process.wait()
    
except KeyboardInterrupt:
    print("\n🛑 Dashboard stopped by user")
except Exception as e:
    print(f"❌ Error starting dashboard: {e}")
    print("🔧 Try running manually: streamlit run ELITE_MLB_DASHBOARD.py")

input("Press Enter to exit...")
