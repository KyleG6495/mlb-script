#!/usr/bin/env python3
"""
MLB Configuration Migration Tool
Helps migrate existing scripts to use the centralized configuration system.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Import our config to reference paths
from config import SCRIPTS_DIR, DATA_DIR

class ConfigMigrator:
    def __init__(self):
        self.hardcoded_patterns = {
            # File paths
            'absolute_paths': r'["\']C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB[^"\']*["\']',
            'relative_data_paths': r'["\']\.\.\/data\/[^"\']*["\']',
            'fd_slate_paths': r'["\'][^"\']*fd_current_slate[^"\']*["\']',
            
            # API keys and URLs
            'openweather_key': r'eb27f1689074b1163c5cf5a1fde8fa91',
            'mlb_api_urls': r'["\']https://statsapi\.mlb\.com/api/v1[^"\']*["\']',
            
            # Hardcoded values
            'rolling_window': r'\b5\s*-?\s*game\b|\brolling.*5\b',
            'salary_cap': r'\b35000\b|\b50000\b',
            'timeout_values': r'timeout\s*=\s*\d+',
            'sleep_values': r'time\.sleep\s*\(\s*\d+\s*\)',
            
            # Team mappings
            'team_dict_start': r'team.*=\s*{',
            'coord_dict_start': r'coordinate.*=\s*{|TEAM_COORDINATES\s*=\s*{',
        }
    
    def scan_file(self, file_path: Path) -> Dict[str, List[Tuple[int, str]]]:
        """Scan a file for hardcoded values and return findings"""
        findings = {pattern_name: [] for pattern_name in self.hardcoded_patterns}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                for pattern_name, pattern in self.hardcoded_patterns.items():
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        findings[pattern_name].append((line_num, line.strip()))
            
            return findings
        
        except Exception as e:
            print(f"❌ Error scanning {file_path}: {e}")
            return findings
    
    def scan_directory(self, directory: Path) -> Dict[str, Dict[str, List[Tuple[int, str]]]]:
        """Scan all Python files in directory for hardcoded values"""
        all_findings = {}
        
        for py_file in directory.glob("**/*.py"):
            # Skip config files and test files
            if any(skip in py_file.name.lower() for skip in ['config', 'test', '__pycache__']):
                continue
                
            findings = self.scan_file(py_file)
            if any(findings.values()):  # Only include files with findings
                all_findings[str(py_file.relative_to(directory))] = findings
        
        return all_findings
    
    def generate_migration_report(self, findings: Dict) -> str:
        """Generate a comprehensive migration report"""
        report = []
        report.append("=" * 80)
        report.append("🔧 MLB MODEL CONFIGURATION MIGRATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        total_files = len(findings)
        total_issues = sum(
            len(issues) for file_findings in findings.values() 
            for issues in file_findings.values()
        )
        
        report.append(f"📊 SUMMARY:")
        report.append(f"   • Files to migrate: {total_files}")
        report.append(f"   • Total hardcoded items found: {total_issues}")
        report.append("")
        
        # Priority issues
        high_priority = ['openweather_key', 'absolute_paths', 'mlb_api_urls']
        medium_priority = ['relative_data_paths', 'fd_slate_paths', 'team_dict_start', 'coord_dict_start']
        
        report.append("🚨 HIGH PRIORITY ISSUES (Security & Critical Paths):")
        self._add_priority_section(report, findings, high_priority)
        
        report.append("⚠️  MEDIUM PRIORITY ISSUES (Hardcoded Paths & Values):")
        self._add_priority_section(report, findings, medium_priority)
        
        report.append("📝 DETAILED FINDINGS BY FILE:")
        report.append("-" * 50)
        
        for file_path, file_findings in findings.items():
            if any(file_findings.values()):
                report.append(f"\n📄 {file_path}")
                report.append("   " + "-" * (len(file_path) + 2))
                
                for pattern_name, issues in file_findings.items():
                    if issues:
                        pattern_display = pattern_name.replace('_', ' ').title()
                        report.append(f"   • {pattern_display}: {len(issues)} occurrences")
                        for line_num, line in issues[:3]:  # Show first 3
                            truncated_line = (line[:70] + "...") if len(line) > 70 else line
                            report.append(f"     Line {line_num}: {truncated_line}")
                        if len(issues) > 3:
                            report.append(f"     ... and {len(issues) - 3} more")
        
        report.append("\n" + "=" * 80)
        report.append("🛠️  RECOMMENDED MIGRATION STEPS:")
        report.append("=" * 80)
        
        steps = [
            "1. Review and update all API keys to use environment variables",
            "2. Replace absolute file paths with FilePaths from config.py",
            "3. Update team mappings to use TEAM_COORDINATES, TEAM_STANDARDIZED_MAP",
            "4. Replace hardcoded timeouts with WeatherDefaults.API_TIMEOUT",
            "5. Update rolling window references to ModelSettings.ROLLING_WINDOW_DAYS",
            "6. Replace salary caps with DFSSettings.FANDUEL_SALARY_CAP",
            "7. Update logging configurations to use LoggingConfig",
            "8. Test each migrated script thoroughly"
        ]
        
        for step in steps:
            report.append(step)
        
        report.append("\n📚 EXAMPLE MIGRATION:")
        report.append("Before: OPENWEATHER_API_KEY = 'eb27f1689074b1163c5cf5a1fde8fa91'")
        report.append("After:  from config import OPENWEATHER_API_KEY")
        report.append("")
        report.append("Before: INPUT_FILE = '../data/hitter_games.csv'")
        report.append("After:  INPUT_FILE = FilePaths.HITTER_GAMES")
        
        return "\n".join(report)
    
    def _add_priority_section(self, report: List[str], findings: Dict, priority_patterns: List[str]):
        """Add a priority section to the report"""
        found_issues = False
        for file_path, file_findings in findings.items():
            for pattern_name in priority_patterns:
                if file_findings.get(pattern_name):
                    if not found_issues:
                        found_issues = True
                    issues = file_findings[pattern_name]
                    pattern_display = pattern_name.replace('_', ' ').title()
                    report.append(f"   • {file_path}: {pattern_display} ({len(issues)} items)")
        
        if not found_issues:
            report.append("   ✅ No critical issues found!")
        report.append("")

def main():
    """Run the configuration migration analysis"""
    print("🔍 Starting MLB Model Configuration Migration Analysis...")
    
    migrator = ConfigMigrator()
    
    # Scan the Scripts directory
    print(f"📂 Scanning {SCRIPTS_DIR}...")
    findings = migrator.scan_directory(SCRIPTS_DIR)
    
    if not findings:
        print("✅ No hardcoded values found! Your scripts are already well-configured.")
        return
    
    # Generate and save report
    report = migrator.generate_migration_report(findings)
    
    # Save report to file
    report_file = SCRIPTS_DIR / "migration_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"📋 Migration report saved to: {report_file}")
    print("\n" + "="*60)
    print("🔧 QUICK SUMMARY:")
    print("="*60)
    
    total_files = len(findings)
    print(f"Files needing migration: {total_files}")
    
    # Count high priority issues
    high_priority_count = 0
    for file_findings in findings.values():
        for pattern in ['openweather_key', 'absolute_paths', 'mlb_api_urls']:
            high_priority_count += len(file_findings.get(pattern, []))
    
    if high_priority_count > 0:
        print(f"🚨 HIGH PRIORITY items: {high_priority_count}")
        print("   → These need immediate attention for security/functionality")
    
    print(f"\n📖 View full report: {report_file}")
    print("💡 Use the provided config.py and player_data_config.py to replace hardcoded values")

if __name__ == "__main__":
    main()
