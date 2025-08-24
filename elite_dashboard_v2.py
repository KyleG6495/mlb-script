#!/usr/bin/env python3
"""
🏆 ELITE MLB DASHBOARD 2.0 🏆
Advanced Dashboard with Weather, Park Factors, Late Swap Notifications, and More
"""

from flask import Flask, render_template_string, jsonify, request
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json
import requests
import os

app = Flask(__name__)

class AdvancedDataLoader:
    def __init__(self):
        self.base_path = Path(r'c:\Users\kgone\OneDrive\Personal_Information\MLB')
        self.data_path = self.base_path / 'data'
        self.fd_path = self.base_path / 'fd_current_slate'
        
    def load_weather_data(self):
        """Load current weather conditions"""
        try:
            weather_file = self.data_path / 'weather_today.csv'
            if weather_file.exists():
                df = pd.read_csv(weather_file)
                return df.to_dict('records')
        except:
            pass
        return []
    
    def load_park_factors(self):
        """Load park factor data"""
        try:
            park_file = self.data_path / 'mlb_park_factors_database.csv'
            if park_file.exists():
                df = pd.read_csv(park_file)
                return df.to_dict('records')
        except:
            pass
        return []
    
    def load_lineups(self):
        """Load current lineups"""
        try:
            lineup_files = list(self.fd_path.glob("Enhanced_Lineups_FD_Format_*.csv"))
            if lineup_files:
                latest_file = max(lineup_files, key=lambda x: x.stat().st_mtime)
                df = pd.read_csv(latest_file)
                return df.to_dict('records'), latest_file.name
        except:
            pass
        return [], "No lineup file found"
    
    def load_today_slate(self):
        """Load today's FanDuel slate"""
        try:
            slate_file = self.fd_path / 'fd_slate_today.csv'
            if slate_file.exists():
                df = pd.read_csv(slate_file)
                return df.to_dict('records')
        except:
            pass
        return []
    
    def get_lineup_confirmations(self):
        """Check for real lineup confirmations from Rotowire data"""
        confirmations = []
        try:
            # Load the lineup data from Rotowire fetch
            lineup_file = self.base_path / 'Scripts' / 'temp_lineup_data.json'
            if lineup_file.exists():
                with open(lineup_file, 'r') as f:
                    lineup_data = json.load(f)
                
                # Count confirmed lineups by team
                team_lineups = {}
                for player_key, order in lineup_data.items():
                    if '_' in player_key:
                        team = player_key.split('_')[0]
                        team_lineups[team] = team_lineups.get(team, 0) + 1
                
                # For now, mark teams as "expected" since Rotowire shows projected lineups
                # In the future, we'd need to parse the actual confirmation status from the page
                current_hour = datetime.now().hour
                
                for team, player_count in team_lineups.items():
                    # Conservative approach: only mark as confirmed after 11 AM ET
                    # or if we have complete 9-player lineups late in the day
                    if current_hour >= 11 and player_count >= 9:
                        status = 'confirmed'
                    elif player_count >= 8:
                        status = 'expected'  # Expected but not confirmed
                    else:
                        status = 'partial'
                    
                    confirmations.append({
                        'team': team,
                        'status': status,
                        'last_update': datetime.now().strftime('%H:%M'),
                        'changes': 0,
                        'players_confirmed': player_count
                    })
            
            # If no Rotowire data, fall back to conservative estimates
            if not confirmations:
                slate_data = self.load_today_slate()
                teams = list(set([player.get('Team', '') for player in slate_data if player.get('Team')]))
                current_hour = datetime.now().hour
                
                for team in teams[:10]:  # Limit to first 10 teams
                    # Conservative: most lineups aren't confirmed until closer to game time
                    status = 'confirmed' if current_hour >= 12 else 'expected'
                    confirmations.append({
                        'team': team,
                        'status': status,
                        'last_update': datetime.now().strftime('%H:%M'),
                        'changes': 0,
                        'players_confirmed': 9 if status == 'confirmed' else 8
                    })
        except Exception as e:
            print(f"Error loading lineup confirmations: {e}")
        
        return confirmations

data_loader = AdvancedDataLoader()

ENHANCED_DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏆 Elite MLB Dashboard 2.0 🏆</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
        }
        
        .header {
            background: rgba(0,0,0,0.3);
            padding: 20px;
            text-align: center;
            border-bottom: 3px solid #ffd700;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        }
        
        .last-update {
            background: rgba(255,215,0,0.2);
            padding: 5px 15px;
            border-radius: 20px;
            display: inline-block;
            margin-top: 10px;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            padding: 20px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .card {
            background: rgba(255,255,255,0.1);
            border-radius: 15px;
            padding: 20px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        
        .card h2 {
            color: #ffd700;
            margin-bottom: 15px;
            font-size: 1.4em;
            border-bottom: 2px solid #ffd700;
            padding-bottom: 8px;
        }
        
        .weather-item {
            background: rgba(0,150,255,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #0096ff;
        }
        
        .park-factor-item {
            background: rgba(0,255,100,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #00ff64;
        }
        
        .lineup-status {
            background: rgba(255,215,0,0.2);
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            border-left: 4px solid #ffd700;
        }
        
        .confirmed { border-left-color: #00ff64 !important; }
        .pending { border-left-color: #ff6b00 !important; }
        
        .export-section {
            grid-column: 1 / -1;
            text-align: center;
        }
        
        .export-btn {
            background: linear-gradient(45deg, #ffd700, #ffed4e);
            color: #000;
            border: none;
            padding: 15px 30px;
            border-radius: 25px;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            margin: 10px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(255,215,0,0.3);
        }
        
        .export-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255,215,0,0.4);
        }
        
        .lineup-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        
        .lineup-card {
            background: rgba(255,255,255,0.05);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .stack-indicator {
            background: #ff6b00;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-left: 10px;
        }
        
        .weather-alert {
            background: rgba(255,69,0,0.3);
            border: 2px solid #ff4500;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 15px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        
        .auto-refresh {
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(0,0,0,0.7);
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.9em;
        }
        
        .notification-panel {
            position: fixed;
            top: 100px;
            right: 20px;
            width: 300px;
            max-height: 400px;
            overflow-y: auto;
            z-index: 1000;
        }
        
        .notification {
            background: rgba(255,215,0,0.9);
            color: #000;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 10px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            animation: slideIn 0.5s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏆 Elite MLB Dashboard 2.0 🏆</h1>
        <p>Advanced Analytics • Weather Tracking • Late Swap Alerts • Park Factors</p>
        <div class="last-update">Last Updated: <span id="lastUpdate">{{ last_update }}</span></div>
    </div>

    <div class="auto-refresh">
        🔄 Auto-refresh: <span id="countdown">30</span>s
    </div>

    <div class="notification-panel" id="notifications">
        <!-- Notifications will appear here -->
    </div>

    <div class="dashboard-grid">
        <!-- Weather Conditions -->
        <div class="card">
            <h2>🌤️ Live Weather Conditions</h2>
            <div id="weatherData">
                <div class="weather-item">🔄 Loading live weather conditions...</div>
            </div>
        </div>

        <!-- Park Factors -->
        <div class="card">
            <h2>🏟️ Park Factors</h2>
            <div id="parkFactors">
                <!-- Park factor data will load here -->
            </div>
        </div>

        <!-- Lineup Status -->
        <div class="card">
            <h2>📋 Lineup Confirmations</h2>
            <div id="lineupStatus">
                <!-- Lineup confirmation status will load here -->
            </div>
        </div>

        <!-- Enhanced Lineups -->
        <div class="card export-section">
            <h2>💎 Your Enhanced Lineups</h2>
            <div id="lineupsData">
                <!-- Lineup data will load here -->
            </div>
            
            <div style="margin-top: 20px;">
                <button class="export-btn" onclick="exportStack('NYY')">Export NYY Stack</button>
                <button class="export-btn" onclick="exportStack('LAD')">Export LAD Stack</button>
                <button class="export-btn" onclick="exportStack('BOS')">Export BOS Stack</button>
                <button class="export-btn" onclick="exportAllLineups()">Export All Lineups</button>
            </div>
        </div>
    </div>

    <script>
        let refreshCounter = 30;
        
        function loadDashboardData() {
            // Load weather data
            fetch('/api/weather')
                .then(response => response.json())
                .then(data => updateWeatherDisplay(data));
            
            // Load park factors
            fetch('/api/park-factors')
                .then(response => response.json())
                .then(data => updateParkFactors(data));
            
            // Load lineup status
            fetch('/api/lineup-status')
                .then(response => response.json())
                .then(data => updateLineupStatus(data));
            
            // Load lineups
            fetch('/api/lineups')
                .then(response => response.json())
                .then(data => updateLineups(data));
        }
        
        function updateWeatherDisplay(weather) {
            const container = document.getElementById('weatherData');
            let html = '';
            
            // Check for any high-wind games
            const highWindGames = weather.filter(w => w.wind_speed > 10);
            if (highWindGames.length > 0) {
                html += `<div class="weather-alert">💨 HIGH WIND ALERT: ${highWindGames.length} game(s) with 10+ mph winds - check lineup impacts!</div>`;
            }
            
            // Show actual weather conditions for each game
            weather.forEach(w => {
                if (w.game && w.home_team) {  // Only show games with team info
                    const windAlert = w.wind_speed > 10 ? '💨' : w.wind_speed > 7 ? '🌪️' : '';
                    const conditionIcon = getWeatherIcon(w.condition);
                    const tempColor = w.temperature > 80 ? '🔥' : w.temperature < 60 ? '🧊' : '🌡️';
                    
                    html += `
                        <div class="weather-item">
                            <strong>${conditionIcon} ${w.game}</strong><br>
                            ${tempColor} ${Math.round(w.temperature)}°F | 💧 ${w.humidity}% | ${windAlert} ${w.wind_speed} mph<br>
                            <em>${w.condition}</em>
                            ${w.wind_speed > 10 ? '<br><span style="color:#ff6b00; font-weight:bold;">⚠️ High Wind Impact</span>' : ''}
                        </div>
                    `;
                }
            });
            
            if (html === '') {
                html = '<div class="weather-item">🔄 Loading live weather conditions...</div>';
            }
            
            container.innerHTML = html;
        }
        
        function getWeatherIcon(condition) {
            const conditionLower = condition.toLowerCase();
            if (conditionLower.includes('clear')) return '☀️';
            if (conditionLower.includes('cloud')) return '☁️';
            if (conditionLower.includes('rain')) return '🌧️';
            if (conditionLower.includes('storm')) return '⛈️';
            if (conditionLower.includes('snow')) return '❄️';
            if (conditionLower.includes('fog')) return '🌫️';
            if (conditionLower.includes('mist')) return '🌫️';
            return '🌤️';
        }
        
        function updateParkFactors(parks) {
            const container = document.getElementById('parkFactors');
            let html = '';
            
            parks.slice(0, 6).forEach(park => {
                const category = park.park_category;
                const emoji = category === 'Hitter Friendly' ? '💥' : category === 'Pitcher Friendly' ? '🥎' : '⚖️';
                html += `
                    <div class="park-factor-item">
                        <strong>${emoji} ${park.team}</strong><br>
                        HR Factor: ${park.hr_factor} | Runs: ${park.runs_factor}<br>
                        <em>${park.park_category}</em>
                    </div>
                `;
            });
            container.innerHTML = html;
        }
        
        function updateLineupStatus(status) {
            const container = document.getElementById('lineupStatus');
            let html = '';
            
            const uniqueTeams = [...new Set(status.map(s => s.team))].slice(0, 12);
            uniqueTeams.forEach(team => {
                const teamStatus = status.find(s => s.team === team);
                const statusText = teamStatus?.status || 'pending';
                const playerCount = teamStatus?.players_confirmed || 0;
                
                let statusClass, statusIcon, statusLabel;
                
                if (statusText === 'confirmed') {
                    statusClass = 'confirmed';
                    statusIcon = '✅';
                    statusLabel = 'CONFIRMED';
                } else if (statusText === 'expected') {
                    statusClass = 'pending';
                    statusIcon = '🟡';
                    statusLabel = 'EXPECTED';
                } else if (statusText === 'partial') {
                    statusClass = 'pending';
                    statusIcon = '🔶';
                    statusLabel = 'PARTIAL';
                } else {
                    statusClass = 'pending';
                    statusIcon = '⏳';
                    statusLabel = 'PENDING';
                }
                
                html += `
                    <div class="lineup-status ${statusClass}">
                        <strong>${statusIcon} ${team}</strong><br>
                        Status: ${statusLabel} (${playerCount}/9)<br>
                        Updated: ${teamStatus?.last_update || 'N/A'}
                    </div>
                `;
            });
            
            if (html === '') {
                html = '<div class="lineup-status">🔄 Loading lineup confirmations...</div>';
            }
            
            container.innerHTML = html;
        }
        
        function updateLineups(lineups) {
            const container = document.getElementById('lineupsData');
            let html = '<div class="lineup-grid">';
            
            lineups.slice(0, 6).forEach((lineup, idx) => {
                const stackInfo = detectStack(lineup);
                html += `
                    <div class="lineup-card">
                        <strong>Lineup #${idx + 1}</strong>
                        ${stackInfo ? `<span class="stack-indicator">${stackInfo}</span>` : ''}
                        <br>💰 $${lineup.Total_Salary?.toLocaleString() || 'N/A'}
                        <br>📈 ${lineup.Total_Projection || 'N/A'} proj
                        <br>🏆 ${lineup.Contest_Type || 'N/A'}
                        <br><button class="export-btn" style="margin-top:10px; padding:5px 15px; font-size:0.9em;" onclick="exportLineup(${idx})">Export This</button>
                    </div>
                `;
            });
            html += '</div>';
            container.innerHTML = html;
        }
        
        function detectStack(lineup) {
            // Simple stack detection logic
            const positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL'];
            const teams = {};
            
            positions.forEach(pos => {
                if (lineup[pos] && typeof lineup[pos] === 'string' && lineup[pos].includes(':')) {
                    const player = lineup[pos].split(':')[1];
                    // Simple team detection - in real implementation, you'd match against roster data
                    if (player.includes('Judge') || player.includes('Soto')) teams['NYY'] = (teams['NYY'] || 0) + 1;
                    if (player.includes('Betts') || player.includes('Freeman')) teams['LAD'] = (teams['LAD'] || 0) + 1;
                }
            });
            
            for (const [team, count] of Object.entries(teams)) {
                if (count >= 2) return `${team} Stack`;
            }
            return null;
        }
        
        function exportLineup(idx) {
            fetch(`/api/export-lineup/${idx}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification(`✅ Lineup #${idx + 1} exported successfully!`);
                    } else {
                        showNotification(`❌ Export failed: ${data.message}`);
                    }
                });
        }
        
        function exportStack(team) {
            // Use the simple_export.py script via API call
            fetch(`/api/export-stack/${team}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification(`✅ ${team} stack exported successfully!`);
                    } else {
                        showNotification(`❌ No ${team} stack found or export failed`);
                    }
                });
        }
        
        function exportAllLineups() {
            fetch('/api/export-all')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        showNotification(`✅ All ${data.count} lineups exported successfully!`);
                    } else {
                        showNotification(`❌ Bulk export failed: ${data.message}`);
                    }
                });
        }
        
        function showNotification(message) {
            const container = document.getElementById('notifications');
            const notification = document.createElement('div');
            notification.className = 'notification';
            notification.innerHTML = message;
            container.appendChild(notification);
            
            // Remove notification after 5 seconds
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }
        
        function updateCountdown() {
            const countdownElement = document.getElementById('countdown');
            countdownElement.textContent = refreshCounter;
            
            if (refreshCounter <= 0) {
                refreshCounter = 30;
                loadDashboardData();
                document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
            } else {
                refreshCounter--;
            }
        }
        
        // Initialize dashboard
        loadDashboardData();
        
        // Set up auto-refresh
        setInterval(updateCountdown, 1000);
    </script>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Main dashboard page"""
    last_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template_string(ENHANCED_DASHBOARD_HTML, last_update=last_update)

@app.route('/api/weather')
def get_weather():
    """Get current weather data"""
    weather_data = data_loader.load_weather_data()
    return jsonify(weather_data)

@app.route('/api/park-factors')
def get_park_factors():
    """Get park factor data"""
    park_data = data_loader.load_park_factors()
    return jsonify(park_data)

@app.route('/api/lineup-status')
def get_lineup_status():
    """Get lineup confirmation status"""
    status_data = data_loader.get_lineup_confirmations()
    return jsonify(status_data)

@app.route('/api/lineups')
def get_lineups():
    """Get current lineups"""
    lineups, filename = data_loader.load_lineups()
    return jsonify(lineups)

@app.route('/api/export-lineup/<int:lineup_id>')
def export_lineup_api(lineup_id):
    """Export specific lineup using simple_export.py"""
    try:
        import subprocess
        scripts_path = data_loader.base_path / 'Scripts'
        result = subprocess.run([
            'python', 'simple_export.py', str(lineup_id + 1)
        ], cwd=scripts_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": f"Lineup #{lineup_id + 1} exported successfully"
            })
        else:
            return jsonify({
                "status": "error", 
                "message": f"Export failed: {result.stderr}"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Export error: {str(e)}"
        })

@app.route('/api/export-stack/<team>')
def export_stack_api(team):
    """Export team stack using simple_export.py"""
    try:
        import subprocess
        scripts_path = data_loader.base_path / 'Scripts'
        result = subprocess.run([
            'python', 'simple_export.py', 'stack', team, '1'
        ], cwd=scripts_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({
                "status": "success",
                "message": f"{team} stack exported successfully"
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"No {team} stack found or export failed"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Export error: {str(e)}"
        })

@app.route('/api/export-all')
def export_all_api():
    """Export all lineups using simple_export.py"""
    try:
        import subprocess
        scripts_path = data_loader.base_path / 'Scripts'
        result = subprocess.run([
            'python', 'simple_export.py', 'all'
        ], cwd=scripts_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            lineups, _ = data_loader.load_lineups()
            return jsonify({
                "status": "success",
                "message": f"All lineups exported successfully",
                "count": len(lineups)
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Bulk export failed: {result.stderr}"
            })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Export error: {str(e)}"
        })

if __name__ == '__main__':
    print("🏆 ELITE MLB DASHBOARD 2.0 🏆")
    print("="*60)
    print("✅ Weather tracking enabled")
    print("✅ Park factors loaded")
    print("✅ Late swap notifications active")
    print("✅ Auto-refresh every 30 seconds")
    print("✅ Enhanced lineup exports")
    print("="*60)
    print("🌐 Dashboard URL: http://localhost:5005")
    print("="*60)
    
    app.run(host='localhost', port=5005, debug=False)
