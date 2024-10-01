import os
from dotenv import load_dotenv
import pandas as pd
import requests
import numpy as np
from firebase_setup import db

load_dotenv()  # Load variables from .env file

def main():
    print("Welcome to the Crypto Scout Tool!")

if __name__ == "__main__":
    main()

import requests

# Fetch CoinGecko market chart data for the past 30 days (Updated)
def fetch_coingecko_data(coin_id):
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart'
    params = {
        'vs_currency': 'usd',
        'days': '30',  # CHANGED: Last 30 days for volume and volatility
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from CoinGecko: {response.status_code}")
        return None

# Fetch additional details like the number of exchanges the coin is listed on
def fetch_coin_details(coin_id):
    url = f'https://api.coingecko.com/api/v3/coins/{coin_id}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching coin details from CoinGecko: {response.status_code}")
        return None

# Process CoinGecko data for 30-day period (Updated)
def process_coingecko_data(market_data, coin_details):
    # Create a DataFrame from CoinGecko data
    df = pd.DataFrame(market_data['prices'], columns=['timestamp', 'price'])
    df['volume'] = [v[1] for v in market_data['total_volumes']]

    # Calculate Average Volume over Last 30 Days (CHANGED)
    average_volume_30_days = df['volume'].mean()  # CHANGED: Calculate average instead of sum over 30 days

    # Calculate 30-Day Volatility (standard deviation of daily returns) (CHANGED)
    df['price_change'] = df['price'].pct_change()  # Calculate daily returns
    volatility_30_days = df['price_change'].std() * np.sqrt(30) * 100     # CHANGED: Volatility over 30 days instead of 7

    # Extract the number of exchanges the coin is listed on
    num_exchanges = len(coin_details['tickers'])  # Number of exchange listings
    
    # Print the values for testing purposes
    print(f"Average Daily Volume (Last 30 Days): {average_volume_30_days}")  # CHANGED
    print(f"Volatility (Last 30 Days): {volatility_30_days}")  # CHANGED
    print(f"Number of Exchanges Listed: {num_exchanges}")

    return average_volume_30_days, volatility_30_days, num_exchanges
    

GITHUB_API_TOKEN = os.getenv('GITHUB_API_TOKEN')

def fetch_github_data(repo_name):
    repo_url = f'https://api.github.com/repos/{repo_name}'

    # Replace 'your_github_token_here' if you're not using dotenv
    headers = {
        'Authorization': f'token {GITHUB_API_TOKEN}',
    }
    response = requests.get(repo_url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching data from GitHub: {response.status_code}")
        return None

# Process GitHub data
def process_github_data(github_data):
    
        stars = github_data['stargazers_count']
        forks = github_data['forks_count']
        open_issues = github_data['open_issues_count']
        watchers = github_data['watchers_count']

        return stars, forks, open_issues, watchers


# Calculate the project score based on evaluated criteria
def calculate_project_score(volume, volatility, exchanges, stars, forks, open_issues, watchers):
    # Calculate score for each criterion (0-10 scale)
    volume_score = 10 if volume > 50_000_000 else 8 if volume > 10_000_000 else 6 if volume > 1_000_000 else 4 if volume > 100_000 else 2
    volatility_score = 10 if volatility < 0.1 else 8 if volatility < 0.3 else 6 if volatility < 0.5 else 4 if volatility < 0.7 else 2
    exchanges_score = 10 if exchanges > 5 else 8 if exchanges >= 3 else 6 if exchanges == 2 else 4 if exchanges == 1 else 2
    stars_score = 10 if stars > 500 else 8 if stars >= 200 else 6 if stars >= 50 else 4 if stars >= 10 else 2
    forks_score = 10 if forks > 100 else 8 if forks >= 50 else 6 if forks >= 10 else 4 if forks >= 5 else 2
    open_issues_score = 10 if open_issues < 20 else 8 if open_issues < 50 else 6 if open_issues < 100 else 4 if open_issues < 200 else 2
    watchers_score = 10 if watchers > 200 else 8 if watchers >= 100 else 6 if watchers >= 50 else 4 if watchers >= 10 else 2

    # Define weights for each criterion
    weights = {
        'volume': 0.15,
        'volatility': 0.10,
        'exchanges': 0.10,
        'stars': 0.20,
        'forks': 0.10,
        'open_issues': 0.10,
        'watchers': 0.25
    }

    # Calculate weighted scores
    weighted_score = (
        volume_score * weights['volume'] +
        volatility_score * weights['volatility'] +
        exchanges_score * weights['exchanges'] +
        stars_score * weights['stars'] +
        forks_score * weights['forks'] +
        open_issues_score * weights['open_issues'] +
        watchers_score * weights['watchers']
    )

    return weighted_score


# Function to store project data in Firestore
def store_project_data(project_name, score, average_volume, volatility, num_exchanges, stars, forks, open_issues, watchers):
    # Reference to the "crypto_projects" collection
    projects_ref = db.collection('crypto_projects')
    
    # Data to be stored
    project_data = {
        'name': project_name,
        'score': score,
        'average_volume': average_volume,
        'volatility': volatility,
        'num_exchanges': num_exchanges,
        'stars': stars,
        'forks': forks,
        'open_issues': open_issues,
        'watchers': watchers
    }
    
    # Add a new document to the collection
    projects_ref.add(project_data)
    print(f"Stored project data for: {project_name}")

# Updated Function to Retrieve Project Data
def retrieve_project_data(project_name):
    # Reference to the "crypto_projects" collection
    projects_ref = db.collection('crypto_projects')

    # Query the documents by project name
    query = projects_ref.where('name', '==', project_name)
    results = query.stream()

    # Iterate through the results and print data
    for doc in results:
        data = doc.to_dict()
        print(f"Project ID: {doc.id}")
        print(f"Name: {data['name']}")
        print(f"Score: {data['score']:.2f}")
        print(f"30-Day Average Volume: {data['average_volume']}")
        print(f"30-Day Volatility: {data['volatility']:.2f}")
        print(f"Number of Exchanges: {data['num_exchanges']}")
        print(f"GitHub Stars: {data['stars']}")
        print(f"GitHub Forks: {data['forks']}")
        print(f"Open Issues: {data['open_issues']}")
        print(f"Watchers: {data['watchers']}\n")

def main():
    # Example coin ID (you can later prompt for user input)
    coin_id = 'bittensor'
    repo_name = 'opentensor/bittensor'
    
    # Fetch CoinGecko market chart data for the past 30 days (CHANGED)
    market_data = fetch_coingecko_data(coin_id)
    
    # Fetch CoinGecko details (for number of exchanges)
    coin_details = fetch_coin_details(coin_id)
    
    # Fetch GitHub data (example: bitcoin repository)
    github_data = fetch_github_data(repo_name)
  
 # If data is fetched successfully, process and calculate scores
    if market_data and coin_details and github_data:
        average_volume, volatility, num_exchanges = process_coingecko_data(market_data, coin_details)
        stars, forks, open_issues, watchers = process_github_data(github_data)
        
        # Calculate the final score
        final_score = calculate_project_score(average_volume, volatility, num_exchanges, stars, forks, open_issues, watchers)

        # Store the project data in Firestore
        store_project_data("Bittensor", final_score, average_volume, volatility, num_exchanges, stars, forks, open_issues, watchers)
        
        # Print the final score
        print("\nFinal Project Score (out of 10):")
        print(f"{final_score:.2f}")

        # Retrieve the stored project data
        retrieve_project_data("Bittensor")

if __name__ == "__main__":
    main()


