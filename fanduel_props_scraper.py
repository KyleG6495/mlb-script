#!/usr/bin/env python3
"""
FanDuel Props Scraper
Scrapes current MLB prop betting lines from FanDuel
"""
import requests
import json
import pandas as pd
from datetime import datetime
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FanDuelPropsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
        })
        
    def get_mlb_props(self):
        """Scrape MLB prop betting lines from FanDuel"""
        try:
            # FanDuel API endpoint for MLB props
            url = "https://sportsbook.fanduel.com/api/content-managed-cms/query?market=US&language=en&includeMarkets=true&includeTabs=true&includePromotions=true&includeSeo=true&includeBanners=true&page=/baseball/mlb"
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logging.info("SUCCESS: Successfully fetched FanDuel data")
            
            # Parse the response to extract prop bets
            props = self.parse_props(data)
            return props
            
        except Exception as e:
            logging.error(f"ERROR: Error scraping FanDuel: {e}")
            return []
    
    def parse_props(self, data):
        """Parse the FanDuel API response to extract prop bets"""
        props = []
        
        try:
            # Navigate through the JSON structure to find events and markets
            attachments = data.get('attachments', {})
            events = attachments.get('events', {})
            markets = attachments.get('markets', {})
            
            for event_id, event in events.items():
                if not event.get('name', '').strip():
                    continue
                    
                game_name = event.get('name', '')
                
                # Get markets for this event
                event_markets = event.get('markets', [])
                
                for market_id in event_markets:
                    if market_id in markets:
                        market = markets[market_id]
                        market_name = market.get('name', '')
                        
                        # Look for prop bet markets
                        if self.is_prop_market(market_name):
                            runners = market.get('runners', [])
                            
                            for runner in runners:
                                prop = self.extract_prop_info(runner, market_name, game_name)
                                if prop:
                                    props.append(prop)
                                    
        except Exception as e:
            logging.error(f"ERROR: Error parsing props: {e}")
            
        return props
    
    def is_prop_market(self, market_name):
        """Check if a market is a prop bet we're interested in"""
        prop_keywords = [
            'hits', 'home runs', 'rbis', 'runs', 'total bases',
            'strikeouts', 'earned runs', 'walks', 'stolen bases'
        ]
        
        market_lower = market_name.lower()
        return any(keyword in market_lower for keyword in prop_keywords)
    
    def extract_prop_info(self, runner, market_name, game_name):
        """Extract prop bet information from a runner"""
        try:
            player_name = runner.get('runnerName', '')
            
            # Extract line value from runner name or market
            line_value = self.extract_line_value(runner.get('runnerName', ''), market_name)
            
            # Get odds
            odds = None
            winRunnerOdds = runner.get('winRunnerOdds', {})
            if winRunnerOdds:
                american_odds = winRunnerOdds.get('americanDisplayOdds', {})
                if american_odds:
                    odds = american_odds.get('americanOdds')
            
            # Determine bet type (Over/Under)
            runner_name_lower = runner.get('runnerName', '').lower()
            bet_type = 'OVER' if 'over' in runner_name_lower else 'UNDER' if 'under' in runner_name_lower else 'UNKNOWN'
            
            return {
                'player_name': self.clean_player_name(player_name),
                'market_name': market_name,
                'game': game_name,
                'line': line_value,
                'bet_type': bet_type,
                'odds': odds,
                'source': 'FanDuel',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"ERROR: Error extracting prop info: {e}")
            return None
    
    def extract_line_value(self, runner_name, market_name):
        """Extract the numerical line value from runner name or market name"""
        import re
        
        # Look for patterns like "Over 2.5", "Under 1.5", etc.
        pattern = r'(\d+\.?\d*)'
        
        # First try runner name
        matches = re.findall(pattern, runner_name)
        if matches:
            return float(matches[-1])  # Take the last number found
            
        # Then try market name
        matches = re.findall(pattern, market_name)
        if matches:
            return float(matches[-1])
            
        return None
    
    def clean_player_name(self, name):
        """Clean player name to remove extra text"""
        import re
        
        # Remove common prefixes/suffixes
        name = re.sub(r'(Over|Under|To Record|To Score)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'\d+\.?\d*\+?', '', name)  # Remove numbers
        name = re.sub(r'[^\w\s]', '', name)  # Remove special characters
        name = ' '.join(name.split())  # Clean whitespace
        
        return name.strip()
    
    def save_props(self, props, filename=None):
        """Save props to CSV file"""
        if not props:
            logging.warning("WARNING: No props to save")
            return None
            
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"../data/fanduel_props_{timestamp}.csv"
        
        df = pd.DataFrame(props)
        df.to_csv(filename, index=False)
        logging.info(f"SUCCESS: Saved {len(props)} props to {filename}")
        
        return filename

def main():
    """Main function to scrape FanDuel props"""
    logging.info("START: Starting FanDuel props scraper...")
    
    scraper = FanDuelPropsScraper()
    props = scraper.get_mlb_props()
    
    if props:
        filename = scraper.save_props(props)
        
        # Also save as today's file for the betting system
        today_file = "../data/fanduel_props_today.csv"
        scraper.save_props(props, today_file)
        
        # Show summary
        df = pd.DataFrame(props)
        print(f"\nDATA: FANDUEL PROPS SUMMARY:")
        print(f"Total props: {len(props)}")
        
        if 'market_name' in df.columns:
            print(f"\nProp types:")
            print(df['market_name'].value_counts().head(10))
            
        if 'player_name' in df.columns:
            print(f"\nTop players (by prop count):")
            print(df['player_name'].value_counts().head(10))
            
    else:
        logging.warning("WARNING: No props found - check if FanDuel has MLB games today")

if __name__ == "__main__":
    main()
