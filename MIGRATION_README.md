# MLB Model Configuration Migration Guide

## 🎯 Overview

Your MLB model has been analyzed and a comprehensive configuration system has been created to eliminate all hardcoded values. This guide will help you migrate your existing scripts to use the new centralized configuration.

## 📁 New Configuration Files

### 1. `config.py` - Main Configuration
Contains all file paths, API settings, team mappings, and model parameters.

### 2. `player_data_config.py` - Player Data
Contains all manual player ID mappings and team corrections.

### 3. `.env.template` - Environment Template
Template for creating your environment configuration file.

## 🚀 Quick Start Migration

### Step 1: Set Up Environment Configuration
```bash
# Run the setup script to create your .env file
python setup_env.py
```

### Step 2: Analyze Current Scripts
```bash
# Scan all scripts for hardcoded values
python migration_tool.py
```

### Step 3: Install Dependencies (if needed)
```bash
pip install python-dotenv
```

## 🔧 Migration Examples

### Before (Hardcoded):
```python
OPENWEATHER_API_KEY = 'eb27f1689074b1163c5cf5a1fde8fa91'
INPUT_FILE = "../data/hitter_games.csv"
FDSLATE_PATH = "C:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate/fd_slate_today.csv"
```

### After (Configured):
```python
from config import OPENWEATHER_API_KEY, FilePaths
INPUT_FILE = FilePaths.HITTER_GAMES
FDSLATE_PATH = FilePaths.FD_SLATE_TODAY
```

## 📊 Configuration Categories

### 🔑 API Keys & Security
- **OpenWeather API**: Now in environment variables
- **MLB Stats API**: Centralized base URL
- **Other APIs**: Template ready for addition

### 📁 File Paths
- **Data Files**: `FilePaths.HITTER_GAMES`, `FilePaths.PITCHER_GAMES`
- **Features**: `FilePaths.HITTER_FEATURES_FINAL`, etc.
- **FanDuel Slate**: `FilePaths.FD_SLATE_TODAY`
- **Output Files**: Timestamped path generation

### ⚾ Baseball Data
- **Team Coordinates**: `TEAM_COORDINATES` (for weather)
- **Team Mappings**: `TEAM_STANDARDIZED_MAP`, `TEAM_NAME_TO_CODE`
- **Player IDs**: `ALL_HITTER_MANUAL_IDS`, `ALL_PITCHER_MANUAL_IDS`

### 🎛️ Model Settings
- **Rolling Windows**: `ModelSettings.ROLLING_WINDOW_DAYS`
- **Thresholds**: `ModelSettings.MIN_AT_BATS_THRESHOLD`
- **Weather Defaults**: `WeatherDefaults.TEMPERATURE`

### 💰 DFS Settings
- **Salary Caps**: `DFSSettings.FANDUEL_SALARY_CAP`
- **Exposures**: `DFSSettings.MAX_EXPOSURE_PCT`
- **Lineups**: `DFSSettings.DEFAULT_LINEUP_COUNT`

## 🛠️ Migration Patterns

### 1. Update Imports
```python
# Add to top of each script
from config import (
    FilePaths, 
    OPENWEATHER_API_KEY,
    TEAM_COORDINATES,
    WeatherDefaults,
    LoggingConfig
)
from player_data_config import ALL_HITTER_MANUAL_IDS
```

### 2. Replace File Paths
```python
# Old
INPUT_FILE = "../data/hitter_games.csv"

# New  
INPUT_FILE = FilePaths.HITTER_GAMES
```

### 3. Replace API Configuration
```python
# Old
OPENWEATHER_API_KEY = 'hardcoded_key'
timeout = 10

# New
from config import OPENWEATHER_API_KEY, WeatherDefaults
timeout = WeatherDefaults.API_TIMEOUT
```

### 4. Replace Team Data
```python
# Old
TEAM_COORDINATES = {108: {'lat': 33.8003, 'lon': -117.8827}, ...}

# New
from config import TEAM_COORDINATES
# (no local definition needed)
```

### 5. Replace Player IDs
```python
# Old
manual_ids = {"Player Name": 123456, ...}

# New
from player_data_config import ALL_HITTER_MANUAL_IDS
manual_ids = ALL_HITTER_MANUAL_IDS
```

### 6. Update Logging
```python
# Old
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# New
from config import LoggingConfig
logging.basicConfig(
    level=getattr(logging, LoggingConfig.LEVEL),
    format=LoggingConfig.FORMAT,
    datefmt=LoggingConfig.DATE_FORMAT
)
```

## 🔒 Security Best Practices

### Environment Variables
1. **Never commit .env files** to version control
2. **Use different .env files** for development/production
3. **Rotate API keys** regularly
4. **Validate environment** variables on startup

### File Organization
```
MLB/
├── Scripts/
│   ├── config.py              # Main configuration
│   ├── player_data_config.py  # Player data
│   ├── .env                   # Your environment (don't commit!)
│   ├── .env.template          # Template (safe to commit)
│   └── your_scripts.py
├── data/
└── fd_current_slate/
```

## 📈 Benefits of Migration

### ✅ Eliminated Hardcoding
- **No more API keys** in source code
- **No absolute paths** that break on other machines
- **No hardcoded values** scattered across files

### 🔧 Easy Maintenance
- **Single source of truth** for all configuration
- **Environment-specific** settings via .env
- **Type-safe access** to configuration values

### 🚀 Better Development
- **Team collaboration** without path conflicts
- **Easy testing** with different configurations
- **Professional code structure**

## 🐛 Troubleshooting

### Import Errors
```python
# If you get import errors, ensure Scripts directory is in Python path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))
from config import FilePaths
```

### Path Issues
```python
# Use absolute paths from config
from config import DATA_DIR
full_path = DATA_DIR / "your_file.csv"
```

### Missing .env
```python
# Config will use defaults if .env is missing
# Run setup_env.py to create your .env file
```

## 📞 Next Steps

1. **Run `setup_env.py`** to create your environment file
2. **Run `migration_tool.py`** to analyze your scripts
3. **Update your most critical scripts first** (those with API keys)
4. **Test each migrated script** thoroughly
5. **Update your batch files** to use new script names

## 🎯 Priority Migration Order

1. **Security Critical**: Scripts with API keys
2. **Data Pipeline**: Core data processing scripts
3. **Model Scripts**: Feature engineering and ML
4. **Optimization**: DFS lineup generation
5. **Analysis**: Backtesting and reporting

Your MLB model will be much more maintainable and professional after this migration! 🚀
