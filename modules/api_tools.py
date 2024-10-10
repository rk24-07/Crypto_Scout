import requests
import os
from dotenv import load_dotenv
import pandas as pd
import numpy as np
from cachetools import TTLCache
import time

load_dotenv()  # Load variables from .env file

GITHUB_API_TOKEN = os.getenv('GITHUB_API_TOKEN')

# Cache for API responses to reduce requests to CoinGecko
cache = TTLCache(maxsize=100, ttl=600)  # Cache entries will expire after 600 seconds

def fetch_coingecko_data_with_cache(coin_id, days):
    """Fetch CoinGecko market data with caching to reduce repeated API calls."""
    cache_key = f"{coin_id}_{days}_market_data"
    
    # Check if the data is already in the cache
    if cache_key in cache:
        return cache[cache_key]
    
    # Fetch fresh data if not in cache
    data = fetch_coingecko_data(coin_id, days)
    if data:
        cache[cache_key] = data  # Cache the successful response
    return data


# Validate CoinGecko Coin ID
def validate_coin_id(coin_id):
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
    response = requests.get(url)
    return response.status_code == 200

# Fetch CoinGecko market chart data for the specified number of days
def fetch_coingecko_data(coin_id, days):
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
    params = {
        'vs_currency': 'usd',
        'days': str(days),  # Update the 'days' parameter dynamically
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from CoinGecko: {response.status_code}")
        return None


def fetch_coingecko_data_with_retry(coin_id, days, retries=3, delay=5):
    """Fetch CoinGecko data with retry logic to handle rate limits."""
    for attempt in range(retries):
        data = fetch_coingecko_data_with_cache(coin_id, days)
        if data:
            return data
        else:
            print(f"Rate limit reached, retrying in {delay} seconds... (Attempt {attempt + 1}/{retries})")
            time.sleep(delay)
            delay *= 2  # Exponential backoff
    return None


# Updated fetch_coin_details function to return coin details, GitHub repository URL and Number of Exchanges
def fetch_coin_details(coin_id):
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # Extract GitHub repository URL
        github_repo = data.get("links", {}).get("repos_url", {}).get("github", [None])[0]
       
        # Extract number of exchanges from 'tickers' field
        num_exchanges = len(data.get('tickers', []))
        
        return data, github_repo, num_exchanges
    else:
        print(f"Error fetching coin details from CoinGecko: {response.status_code}")
        return None, None, 0

# Fetch GitHub data
def fetch_github_data(repo_name):
    repo_url = f'https://api.github.com/repos/{repo_name}'
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {GITHUB_API_TOKEN}' if GITHUB_API_TOKEN else None,
    }
    headers = {k: v for k, v in headers.items() if v is not None}
    response = requests.get(repo_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from GitHub for repository: {repo_url}. Status code: {response.status_code}")
        return None
    

# Process GitHub data
def process_github_data(github_data):
    stars = github_data['stargazers_count']
    forks = github_data['forks_count']
    open_issues = github_data['open_issues_count']
    watchers = github_data['watchers_count']
    return stars, forks, open_issues, watchers





# Calculate market cap growth rate, volume growth rate, and volatility for a given time period
def calculate_growth_and_volatility(market_data):
    df = pd.DataFrame(market_data['prices'], columns=['timestamp', 'price'])
    df['volume'] = [v[1] for v in market_data['total_volumes']]
    df['market_cap'] = [m[1] for m in market_data['market_caps']]
    
    # Calculate growth rates
    market_cap_start = df['market_cap'].iloc[0]
    market_cap_end = df['market_cap'].iloc[-1]
    market_cap_growth = ((market_cap_end - market_cap_start) / market_cap_start) * 100

    volume_start = df['volume'].iloc[0]
    volume_end = df['volume'].iloc[-1]
    volume_growth = ((volume_end - volume_start) / volume_start) * 100

    # Calculate volatility (standard deviation of daily returns)
    df['price_change'] = df['price'].pct_change()
    volatility = df['price_change'].std() * np.sqrt(len(df)) * 100

    return market_cap_growth, volume_growth, volatility

def fetch_and_process_multiple_timeframes(coin_id):
    timeframes = [30, 60, 90]
    results = {
        'market_cap_growth': {},
        'volume_growth': {},
        'volatility': {},
        'volatility_to_volume_ratio': {},
        'num_exchanges': None
    }
    
    # Fetch coin details (including number of exchanges)
    _, _, num_exchanges = fetch_coin_details(coin_id)
    
    for days in timeframes:
        market_data = fetch_coingecko_data_with_cache(coin_id, days)
        
        if market_data is not None:
            market_cap_growth, volume_growth, volatility = calculate_growth_and_volatility(market_data)
            
            results['market_cap_growth'][f'{days}d'] = market_cap_growth if market_cap_growth is not None else 0
            results['volume_growth'][f'{days}d'] = volume_growth if volume_growth is not None else 0
            results['volatility'][f'{days}d'] = volatility if volatility is not None else 0
        else:
            results['market_cap_growth'][f'{days}d'] = 0
            results['volume_growth'][f'{days}d'] = 0
            results['volatility'][f'{days}d'] = 0
    
    if results['volatility']['30d'] is not None and results['volume_growth']['30d'] is not None:
        if results['volume_growth']['30d'] != 0:
            results['volatility_to_volume_ratio']['30d'] = results['volatility']['30d'] / results['volume_growth']['30d']
        else:
            results['volatility_to_volume_ratio']['30d'] = 0
    else:
        results['volatility_to_volume_ratio']['30d'] = 0
    
    results['num_exchanges'] = num_exchanges if num_exchanges is not None else 0
    
    return results

