#!/usr/bin/env python3
"""
Environment Configuration Setup
Creates a .env file with your current settings for secure configuration management.
"""

import os
from pathlib import Path

def create_env_file():
    """Create .env file with current hardcoded values"""
    
    script_dir = Path(__file__).parent
    env_file = script_dir / ".env"
    
    print("🔐 Creating environment configuration file...")
    
    # Current known values from your scripts
    current_values = {
        "OPENWEATHER_API_KEY": "eb27f1689074b1163c5cf5a1fde8fa91",
        "DEBUG_MODE": "false", 
        "ENABLE_DETAILED_LOGGING": "true",
        "USE_CACHED_DATA": "false",
        "ROLLING_WINDOW_DAYS": "5",
        "MIN_GAMES_FOR_ROLLING": "3",
        "DEFAULT_LINEUP_COUNT": "20",
        "FANDUEL_SALARY_CAP": "35000",
        "MAX_EXPOSURE_PCT": "40.0",
        "MIN_EXPOSURE_PCT": "5.0",
        "API_TIMEOUT_SECONDS": "10",
        "API_DELAY_SECONDS": "1",
        "MAX_CONCURRENT_REQUESTS": "5"
    }
    
    env_content = []
    env_content.append("# =====================================================================")
    env_content.append("# MLB MODEL ENVIRONMENT CONFIGURATION")
    env_content.append("# =====================================================================")
    env_content.append("# Auto-generated from migration_tool.py")
    env_content.append("# SECURITY NOTE: Keep this file secure and never commit to version control")
    env_content.append("# =====================================================================")
    env_content.append("")
    
    env_content.append("# Weather API Configuration")
    env_content.append(f"OPENWEATHER_API_KEY={current_values['OPENWEATHER_API_KEY']}")
    env_content.append("")
    
    env_content.append("# Model Settings")
    env_content.append(f"ROLLING_WINDOW_DAYS={current_values['ROLLING_WINDOW_DAYS']}")
    env_content.append(f"MIN_GAMES_FOR_ROLLING={current_values['MIN_GAMES_FOR_ROLLING']}")
    env_content.append(f"DEFAULT_LINEUP_COUNT={current_values['DEFAULT_LINEUP_COUNT']}")
    env_content.append("")
    
    env_content.append("# Debug and Testing")
    env_content.append(f"DEBUG_MODE={current_values['DEBUG_MODE']}")
    env_content.append(f"ENABLE_DETAILED_LOGGING={current_values['ENABLE_DETAILED_LOGGING']}")
    env_content.append(f"USE_CACHED_DATA={current_values['USE_CACHED_DATA']}")
    env_content.append("")
    
    env_content.append("# DFS Settings")
    env_content.append(f"FANDUEL_SALARY_CAP={current_values['FANDUEL_SALARY_CAP']}")
    env_content.append(f"MAX_EXPOSURE_PCT={current_values['MAX_EXPOSURE_PCT']}")
    env_content.append(f"MIN_EXPOSURE_PCT={current_values['MIN_EXPOSURE_PCT']}")
    env_content.append("")
    
    env_content.append("# Performance Settings")
    env_content.append(f"API_TIMEOUT_SECONDS={current_values['API_TIMEOUT_SECONDS']}")
    env_content.append(f"API_DELAY_SECONDS={current_values['API_DELAY_SECONDS']}")
    env_content.append(f"MAX_CONCURRENT_REQUESTS={current_values['MAX_CONCURRENT_REQUESTS']}")
    env_content.append("")
    
    env_content.append("# Optional Premium APIs (add your keys if using)")
    env_content.append("# SPORTSDATA_API_KEY=your_key_here")
    env_content.append("# FANDUEL_API_KEY=your_key_here")
    env_content.append("")
    
    env_content.append("# Custom Path Overrides (optional)")
    env_content.append("# CUSTOM_DATA_DIR=C:\\Your\\Custom\\Data\\Path")
    env_content.append("# CUSTOM_SLATE_DIR=C:\\Your\\Custom\\Slate\\Path")
    
    # Write to file
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(env_content))
    
    print(f"✅ Created environment file: {env_file}")
    print("\n📋 Next steps:")
    print("1. Review the generated .env file")
    print("2. Update any API keys or settings as needed")
    print("3. Add .env to your .gitignore file")
    print("4. Install python-dotenv: pip install python-dotenv")
    print("5. Run migration_tool.py to see what scripts need updating")
    
    # Create .gitignore entry
    gitignore_file = script_dir.parent / ".gitignore"
    gitignore_content = "\n# Environment configuration\n.env\n*.env\n"
    
    if gitignore_file.exists():
        with open(gitignore_file, 'r') as f:
            existing = f.read()
        if '.env' not in existing:
            with open(gitignore_file, 'a') as f:
                f.write(gitignore_content)
            print(f"📝 Updated {gitignore_file} to exclude .env files")
    else:
        with open(gitignore_file, 'w') as f:
            f.write(gitignore_content)
        print(f"📝 Created {gitignore_file}")

if __name__ == "__main__":
    create_env_file()
