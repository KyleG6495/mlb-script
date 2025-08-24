#!/usr/bin/env python3
"""
MLB Model Configuration Module
Centralizes all hardcoded values, paths, and settings for the MLB DFS/Betting system.
"""

import os
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════════
# 🗂️ BASE PATHS & DIRECTORIES
# ═══════════════════════════════════════════════════════════════════════════════

# Base project directory (parent of Scripts folder)
BASE_DIR = Path(__file__).resolve().parent.parent

# Core directories
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "Scripts"
FD_SLATE_DIR = BASE_DIR / "fd_current_slate"
DAILY_RUNNERS_DIR = SCRIPTS_DIR / "DAILY_RUNNERS"

# ═══════════════════════════════════════════════════════════════════════════════
# 🔑 API KEYS & CREDENTIALS
# ═══════════════════════════════════════════════════════════════════════════════

# OpenWeather API Configuration
OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', 'eb27f1689074b1163c5cf5a1fde8fa91')

# MLB Stats API Configuration
MLB_STATS_API_BASE = "https://statsapi.mlb.com/api/v1"
MLB_SCHEDULE_URL = f"{MLB_STATS_API_BASE}/schedule"

class MLBApiConfig:
    """MLB API Configuration and Settings"""
    BASE_URL = MLB_STATS_API_BASE
    SCHEDULE_URL = MLB_SCHEDULE_URL
    TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    
    # Common API endpoints
    PLAYER_STATS_URL = f"{BASE_URL}/people/{{player_id}}/stats"
    GAME_DETAILS_URL = f"{BASE_URL}/game/{{game_pk}}/feed/live"

# ═══════════════════════════════════════════════════════════════════════════════
# 📁 FILE PATHS & NAMES
# ═══════════════════════════════════════════════════════════════════════════════

class FilePaths:
    """Centralized file path configuration"""
    
    # Base directories (computed properties for reuse)
    BASE_DIR = BASE_DIR
    DATA_DIR = DATA_DIR
    SCRIPTS_DIR = SCRIPTS_DIR
    FD_CURRENT_SLATE_DIR = FD_SLATE_DIR
    DAILY_RUNNERS_DIR = DAILY_RUNNERS_DIR
    
    # Core data files
    HITTER_GAMES = DATA_DIR / "hitter_games.csv"
    PITCHER_GAMES = DATA_DIR / "pitcher_games.csv"
    HITTER_BOXSCORES = DATA_DIR / "hitter_boxscores_full.csv"
    PITCHER_BOXSCORES = DATA_DIR / "pitcher_boxscores_full.csv"
    PITCHER_BOXSCORES_WITH_EARNED = DATA_DIR / "pitcher_boxscores_earned_runs.csv"
    
    # Game PK mapping files
    HITTER_GAMES_WITH_GAMEPK = DATA_DIR / "hitter_games_with_gamepk.csv"
    PITCHER_GAMES_WITH_GAMEPK = DATA_DIR / "pitcher_games_with_game_pk.csv"
    FAILED_HITTER_IDS = DATA_DIR / "failed_hitter_ids.json"
    FAILED_PITCHER_IDS = DATA_DIR / "failed_pitcher_ids.json"
    
    # Enhanced feature files
    HITTER_FEATURES_ENRICHED = DATA_DIR / "fd_hitter_features_enriched.csv"
    FD_HITTER_FEATURES_ENRICHED = DATA_DIR / "fd_hitter_features_enriched.csv"
    PITCHER_FEATURES_ENRICHED = DATA_DIR / "fd_pitcher_features_enriched.csv"
    HITTER_FEATURES_FINAL = DATA_DIR / "fd_hitter_features_final.csv"
    FD_HITTER_FEATURES_FINAL = DATA_DIR / "fd_hitter_features_final.csv"
    PITCHER_FEATURES_FINAL = DATA_DIR / "fd_pitcher_features_final.csv"
    
    # Prediction and model files
    PREDICTION_READY_FEATURES = DATA_DIR / "prediction_ready_features.csv"
    TOTAL_BASES_PIPELINE = DATA_DIR / "total_bases_pipeline.joblib"
    
    # Today's data files
    HITTER_FEATURES_TODAY = DATA_DIR / "fd_hitter_features_today.csv"
    FD_HITTER_FEATURES_TODAY = DATA_DIR / "fd_hitter_features_today.csv"
    PITCHER_FEATURES_TODAY = DATA_DIR / "today_pitcher_features.csv"
    TODAY_PITCHER_FEATURES = DATA_DIR / "today_pitcher_features.csv"
    TODAY_HITTER_FEATURES_MERGED = DATA_DIR / "today_hitter_features_merged.csv"
    WEATHER_TODAY = DATA_DIR / "weather_today.csv"
    
    # FanDuel slate files
    FD_SLATE_TODAY = FD_SLATE_DIR / "fd_slate_today.csv"
    FD_SLATE_STARTERS_ONLY = DATA_DIR / "fd_slate_starters_only.csv"
    
    # Rolling features
    HITTER_ROLLING_FEATURES = DATA_DIR / "hitter_rolling_5game_features.csv"
    HITTER_ROLLING_5GAME_FEATURES = DATA_DIR / "hitter_rolling_5game_features.csv"
    PITCHER_ROLLING_FEATURES = DATA_DIR / "pitcher_rolling_5game_features.csv"
    
    # Team mappings
    HITTER_TEAM_MAP = DATA_DIR / "hitter_team_map.csv"
    PITCHER_TEAM_MAP = DATA_DIR / "pitcher_team_map.csv"
    
    # Weather and park factors
    WEATHER_PARK_FACTORS = DATA_DIR / "merged_weather_park.csv"
    WEATHER_AND_PARK_FACTORS = DATA_DIR / "merged_weather_park.csv"
    MERGED_WEATHER_PARK = DATA_DIR / "merged_weather_park.csv"
    MLB_PARK_FACTORS = DATA_DIR / "mlb_park_factors_database.csv"
    
    # Model files
    BASE_HITTER_SCORES = DATA_DIR / "base_hitter_scores.csv"
    BASE_PITCHER_SCORES = DATA_DIR / "base_pitcher_scores.csv"
    PREDICTION_FEATURES = DATA_DIR / "prediction_features_enhanced_real_stats.csv"
    
    # Output directories for timestamped files
    @staticmethod
    def get_timestamped_path(base_name: str, extension: str = ".csv") -> Path:
        """Generate timestamped file path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return DATA_DIR / f"{base_name}_{timestamp}{extension}"

# ═══════════════════════════════════════════════════════════════════════════════
# ⚾ BASEBALL-SPECIFIC CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════════

class ModelSettings:
    """Machine Learning and Statistical Settings"""
    
    # Rolling window configurations
    ROLLING_WINDOW_DAYS = 5
    MIN_GAMES_FOR_ROLLING = 3
    
    # Feature engineering
    POSITION_MAPPING = {
        'C': 'Catcher',
        '1B': 'First Base',
        '2B': 'Second Base', 
        '3B': 'Third Base',
        'SS': 'Shortstop',
        'OF': 'Outfield',
        'LF': 'Left Field',
        'CF': 'Center Field',
        'RF': 'Right Field',
        'DH': 'Designated Hitter',
        'P': 'Pitcher'
    }
    
    # Statistical thresholds
    MIN_AT_BATS_THRESHOLD = 10
    MIN_INNINGS_PITCHED_THRESHOLD = 5.0
    OUTLIER_Z_SCORE_THRESHOLD = 3.0

class WeatherDefaults:
    """Default weather values when API fails"""
    TEMPERATURE = 75.0
    WIND_SPEED = 5.0
    CONDITION = "Clear Sky"
    API_TIMEOUT = 10
    API_DELAY_SECONDS = 1

# ═══════════════════════════════════════════════════════════════════════════════
# 🏟️ TEAM MAPPINGS & COORDINATES
# ═══════════════════════════════════════════════════════════════════════════════

# MLB Team Coordinates (for weather data)
TEAM_COORDINATES = {
    108: {'lat': 33.8003, 'lon': -117.8827},  # Los Angeles Angels
    109: {'lat': 33.4455, 'lon': -112.0667},  # Arizona Diamondbacks
    110: {'lat': 39.2839, 'lon': -76.6217},   # Baltimore Orioles
    111: {'lat': 42.3467, 'lon': -71.0972},   # Boston Red Sox
    112: {'lat': 41.9484, 'lon': -87.6553},   # Chicago Cubs
    113: {'lat': 39.0979, 'lon': -84.5081},   # Cincinnati Reds
    114: {'lat': 41.4962, 'lon': -81.6853},   # Cleveland Guardians
    115: {'lat': 39.7561, 'lon': -104.9941},  # Colorado Rockies
    116: {'lat': 42.3390, 'lon': -83.0485},   # Detroit Tigers
    117: {'lat': 29.7572, 'lon': -95.3555},   # Houston Astros
    118: {'lat': 39.0513, 'lon': -94.4803},   # Kansas City Royals
    119: {'lat': 34.0738, 'lon': -118.2400},  # Los Angeles Dodgers
    120: {'lat': 38.8730, 'lon': -77.0074},   # Washington Nationals
    121: {'lat': 40.7571, 'lon': -73.8458},   # New York Mets
    133: {'lat': 37.7516, 'lon': -122.2005},  # Oakland Athletics
    134: {'lat': 40.4469, 'lon': -80.0057},   # Pittsburgh Pirates
    135: {'lat': 32.7076, 'lon': -117.1570},  # San Diego Padres
    136: {'lat': 47.5911, 'lon': -122.3331},  # Seattle Mariners
    137: {'lat': 37.7786, 'lon': -122.3893},  # San Francisco Giants
    138: {'lat': 38.6226, 'lon': -90.1928},   # St. Louis Cardinals
    139: {'lat': 27.7682, 'lon': -82.6534},   # Tampa Bay Rays
    140: {'lat': 32.7511, 'lon': -97.0821},   # Texas Rangers
    141: {'lat': 43.6414, 'lon': -79.3890},   # Toronto Blue Jays
    142: {'lat': 44.9817, 'lon': -93.2783},   # Minnesota Twins
    143: {'lat': 39.9050, 'lon': -75.1665},   # Philadelphia Phillies
    144: {'lat': 33.8908, 'lon': -84.4679},   # Atlanta Braves
    145: {'lat': 41.8300, 'lon': -87.6339},   # Chicago White Sox
    146: {'lat': 25.7781, 'lon': -80.2196},   # Miami Marlins
    147: {'lat': 40.8296, 'lon': -73.9262},   # New York Yankees
    158: {'lat': 43.0280, 'lon': -87.9712}    # Milwaukee Brewers
}

# Team Name Standardization
TEAM_STANDARDIZED_MAP = {
    'minnesota twins': 'twins',
    'los angeles dodgers': 'dodgers',
    'houston astros': 'astros',
    'atlanta braves': 'braves',
    'kansas city royals': 'royals',
    'san francisco giants': 'giants',
    'los angeles angels': 'angels',
    'colorado rockies': 'rockies',
    'detroit tigers': 'tigers',
    'cincinnati reds': 'reds',
    'chicago cubs': 'cubs',
    'pittsburgh pirates': 'pirates',
    'philadelphia phillies': 'phillies',
    'st. louis cardinals': 'cardinals',
    'new york yankees': 'yankees',
    'arizona diamondbacks': 'diamondbacks',
    'new york mets': 'mets',
    'san diego padres': 'padres',
    'cleveland guardians': 'guardians',
    'oakland athletics': 'athletics',
    'boston red sox': 'redsox',
    'chicago white sox': 'whitesox',
    'toronto blue jays': 'bluejays',
    'miami marlins': 'marlins',
    'seattle mariners': 'mariners',
    'washington nationals': 'nationals',
    'milwaukee brewers': 'brewers',
    'tampa bay rays': 'rays',
    'texas rangers': 'rangers',
    'baltimore orioles': 'orioles',
    # Abbreviation mappings
    'tor': 'bluejays',
    'cws': 'whitesox',
    'pit': 'pirates'
}

# Team Name to Code Mapping (for API calls)
TEAM_NAME_TO_CODE = {
    'texas rangers': 'TEX',
    'pittsburgh pirates': 'PIT',
    'los angeles dodgers': 'LAD',
    'detroit tigers': 'DET',
    'san francisco giants': 'SF',
    'seattle mariners': 'SEA',
    'san diego padres': 'SD',
    'houston astros': 'HOU',
    'chicago white sox': 'CWS',
    'cleveland guardians': 'CLE',
    'oakland athletics': 'ATH',
    'colorado rockies': 'COL',
    'minnesota twins': 'MIN',
    'kansas city royals': 'KC',
    'atlanta braves': 'ATL',
    'cincinnati reds': 'CIN',
    'chicago cubs': 'CHC',
    'philadelphia phillies': 'PHI',
    'st. louis cardinals': 'STL',
    'new york yankees': 'NYY',
    'arizona diamondbacks': 'ARI',
    'new york mets': 'NYM',
    'boston red sox': 'BOS',
    'toronto blue jays': 'TOR',
    'miami marlins': 'MIA',
    'washington nationals': 'WSN',
    'milwaukee brewers': 'MIL',
    'tampa bay rays': 'TB',
    'baltimore orioles': 'BAL',
    'los angeles angels': 'LAA'
}

# ═══════════════════════════════════════════════════════════════════════════════
# 🎯 DFS & OPTIMIZATION SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

class DFSSettings:
    """DFS Optimization Configuration"""
    
    # Salary cap constraints
    FANDUEL_SALARY_CAP = 35000
    DRAFTKINGS_SALARY_CAP = 50000
    
    # Lineup requirements
    FANDUEL_ROSTER_POSITIONS = {
        'C': 1,
        '1B': 1,
        '2B': 1,
        '3B': 1,
        'SS': 1,
        'OF': 3,
        'P': 1
    }
    
    # Stack configurations
    MAX_PLAYERS_PER_TEAM = 5
    MIN_STACK_SIZE = 2
    MAX_STACK_SIZE = 5
    
    # Optimization settings
    DEFAULT_LINEUP_COUNT = 20
    MAX_EXPOSURE_PCT = 40.0
    MIN_EXPOSURE_PCT = 5.0
    
    # Contest types
    CONTEST_TYPES = {
        'GPP': {'variance_weight': 1.5, 'ceiling_weight': 2.0},
        'CASH': {'variance_weight': 0.5, 'ceiling_weight': 0.8},
        'TOURNAMENT': {'variance_weight': 2.0, 'ceiling_weight': 2.5}
    }

# ═══════════════════════════════════════════════════════════════════════════════
# 📊 LOGGING & OUTPUT SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════

class LoggingConfig:
    """Centralized logging configuration"""
    
    LEVEL = "INFO"
    FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    
    # Log file settings
    LOG_DIR = BASE_DIR / "logs"
    MAX_LOG_SIZE_MB = 10
    BACKUP_COUNT = 5

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        DATA_DIR,
        FD_SLATE_DIR,
        LoggingConfig.LOG_DIR,
        DATA_DIR / "backups",
        DATA_DIR / "backtest_analysis"
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

def get_today_str() -> str:
    """Get today's date as string in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")

def get_timestamp() -> str:
    """Get current timestamp string for file naming"""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

# Create directories on import
ensure_directories()

# Validate critical paths exist
if not SCRIPTS_DIR.exists():
    raise FileNotFoundError(f"Scripts directory not found: {SCRIPTS_DIR}")

# Export commonly used items
__all__ = [
    'FilePaths',
    'ModelSettings', 
    'WeatherDefaults',
    'DFSSettings',
    'LoggingConfig',
    'TEAM_COORDINATES',
    'TEAM_STANDARDIZED_MAP',
    'TEAM_NAME_TO_CODE',
    'OPENWEATHER_API_KEY',
    'MLB_STATS_API_BASE',
    'DATA_DIR',
    'BASE_DIR',
    'get_today_str',
    'get_timestamp'
]
