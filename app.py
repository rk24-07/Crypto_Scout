import os
import json
from dotenv import load_dotenv
from firebase_setup import db 
from modules.api_tools import fetch_and_process_multiple_timeframes, fetch_coin_details, fetch_github_data, validate_coin_id
from modules.scoring_tool import calculate_project_score


load_dotenv()  # Load variables from .env file

REPO_MAPPING_FILE = "repo_mappings.json"

# Load existing mappings if available
def load_repo_mappings():
    if os.path.exists(REPO_MAPPING_FILE):
        with open(REPO_MAPPING_FILE, 'r') as file:
            return json.load(file)
    return {}

# Save new mappings
def save_repo_mapping(coin_id, github_repo):
    mappings = load_repo_mappings()
    mappings[coin_id] = github_repo
    with open(REPO_MAPPING_FILE, 'w') as file:
        json.dump(mappings, file)

# Store project data in Firestore
def store_project_data(project_name, score, market_cap_growth, volume_growth, volatility_data, exchanges, github_metrics):
    projects_ref = db.collection('crypto_projects')
    
    # Combine all the data into a single dictionary
    project_data = {
        'name': project_name,
        'score': score,
        'market_cap_growth_30d': market_cap_growth.get('market_cap_growth_30d'),
        'market_cap_growth_60d': market_cap_growth.get('market_cap_growth_60d'),
        'market_cap_growth_90d': market_cap_growth.get('market_cap_growth_90d'),
        'volume_growth_30d': volume_growth.get('volume_growth_30d'),
        'volume_growth_60d': volume_growth.get('volume_growth_60d'),
        'volume_growth_90d': volume_growth.get('volume_growth_90d'),
        'volatility_volume_ratio': volatility_data.get('volatility_volume_ratio'),
        'num_exchanges': exchanges,
        'stars': github_metrics.get('stars'),
        'forks': github_metrics.get('forks'),
        'open_issues': github_metrics.get('open_issues'),
        'watchers': github_metrics.get('watchers')
    }
    
    # Add the project data to Firestore
    projects_ref.add(project_data)
    

# Retrieve Project Data
def retrieve_project_data(project_name):
    projects_ref = db.collection('crypto_projects')
    query = projects_ref.where('name', '==', project_name)
    results = query.stream()
    

# New Function to Get GitHub Info or Prompt User
def get_or_prompt_repo_info(coin_id):
    repo_mappings = load_repo_mappings()
    if coin_id in repo_mappings:
        return repo_mappings[coin_id], None

    # Check if coin_id is valid before proceeding
    if not validate_coin_id(coin_id):
        print(f"Invalid Coin ID '{coin_id}'. Please input a valid one.")
        return None, None

    # If valid, try to get GitHub overview link from CoinGecko
    _, github_link, _ = fetch_coin_details(coin_id)
    return None, github_link

# Updated Coin Data Processing in app.py
def process_coin_data(coin_id):
    # Fetch or prompt for GitHub repository
    repo_name, github_link = get_or_prompt_repo_info(coin_id)

    if repo_name is None and github_link is None:
        print(f"Invalid Coin ID '{coin_id}'. Please input a valid Coin ID.")
        return

    if not repo_name:
        if github_link:
            print(f"GitHub link for {coin_id} from CoinGecko: {github_link}")
        while True:
            repo_name = input("Please enter the GitHub repository in the format 'owner/repo_name' (e.g., 'bitcoin/bitcoin'): ").strip()
            if '/' in repo_name and len(repo_name.split('/')) == 2:
                break
            else:
                print("Invalid GitHub repository format provided. Please use the format 'owner/repo_name'.")

        save_repo_mapping(coin_id, repo_name)

    # Fetch market data and process multiple timeframes from CoinGecko
    market_data = fetch_and_process_multiple_timeframes(coin_id)
    if not market_data:
        print(f"Failed to fetch market data for coin '{coin_id}'. Skipping processing.")
        return

    # Group related metrics for market cap and volume growth rates
    market_cap_growth = {
        'market_cap_growth_30d': market_data['market_cap_growth'].get('30d'),
        'market_cap_growth_60d': market_data['market_cap_growth'].get('60d'),
        'market_cap_growth_90d': market_data['market_cap_growth'].get('90d')
    }

    volume_growth = {
        'volume_growth_30d': market_data['volume_growth'].get('30d'),
        'volume_growth_60d': market_data['volume_growth'].get('60d'),
        'volume_growth_90d': market_data['volume_growth'].get('90d')
    }

    volatility_data = {
        'volatility_volume_ratio': market_data['volatility_to_volume_ratio'].get('30d')
    }

    # Get the number of exchanges
    exchanges = market_data['num_exchanges']

    # Fetch GitHub data for the project's repo
    github_data = fetch_github_data(repo_name)
    if not github_data:
        print(f"Error fetching data from GitHub for repository: {repo_name}. Skipping processing.")
        return

    # Group GitHub metrics
    github_metrics = {
        'stars': github_data['stargazers_count'],
        'forks': github_data['forks_count'],
        'open_issues': github_data['open_issues_count'],
        'watchers': github_data['watchers_count']
    }

    # Calculate the final project score using the fetched data
    final_score = calculate_project_score(
        **market_cap_growth,       # Unpack market cap growth rates
        **volume_growth,           # Unpack volume growth rates
        **volatility_data,         # Unpack volatility-to-volume ratio
        exchanges=exchanges,       # Directly pass exchanges
        **github_metrics           # Unpack GitHub metrics
    )

    
     # Display the market data, GitHub metrics, and score
    print(f"\nMarket Data for {coin_id}:")
    print(f"30d Market Cap Growth: {market_cap_growth['market_cap_growth_30d']:.2f}%")
    print(f"60d Market Cap Growth: {market_cap_growth['market_cap_growth_60d']:.2f}%")
    print(f"90d Market Cap Growth: {market_cap_growth['market_cap_growth_90d']:.2f}%")

    print(f"30d Volume Growth: {volume_growth['volume_growth_30d']:.2f}%")
    print(f"60d Volume Growth: {volume_growth['volume_growth_60d']:.2f}%")
    print(f"90d Volume Growth: {volume_growth['volume_growth_90d']:.2f}%")

    print(f"Volatility/Volume Ratio (30d): {volatility_data['volatility_volume_ratio']:.2f}")
    print(f"Number of Exchanges: {exchanges}")

    print("\nGitHub Metrics:")
    print(f"Stars: {github_metrics['stars']}")
    print(f"Forks: {github_metrics['forks']}")
    print(f"Open Issues: {github_metrics['open_issues']}")
    print(f"Watchers: {github_metrics['watchers']}")

    
  # Display the market data, GitHub metrics, and score
    print(f"\nMarket Data for {coin_id}:")
    print(f"30d Market Cap Growth: {market_cap_growth['market_cap_growth_30d']:.2f}%")
    print(f"60d Market Cap Growth: {market_cap_growth['market_cap_growth_60d']:.2f}%")
    print(f"90d Market Cap Growth: {market_cap_growth['market_cap_growth_90d']:.2f}%")

    print(f"30d Volume Growth: {volume_growth['volume_growth_30d']:.2f}%")
    print(f"60d Volume Growth: {volume_growth['volume_growth_60d']:.2f}%")
    print(f"90d Volume Growth: {volume_growth['volume_growth_90d']:.2f}%")

    print(f"Volatility/Volume Ratio (30d): {volatility_data['volatility_volume_ratio']:.2f}")
    print(f"Number of Exchanges: {exchanges}")

    print("\nGitHub Metrics:")
    print(f"Stars: {github_metrics['stars']}")
    print(f"Forks: {github_metrics['forks']}")
    print(f"Open Issues: {github_metrics['open_issues']}")
    print(f"Watchers: {github_metrics['watchers']}")

    # Print the final project score
    print("\nFinal Project Score (out of 10):")
    print(f"{final_score:.2f}")

    # Retrieve and display project data (optional, if using Firestore)
    retrieve_project_data(coin_id)

# Main function for user interaction
def main():
    print("Welcome to the Crypto Scout Tool!")
    coin_id = input("Enter the Coin ID: ")
    process_coin_data(coin_id)

if __name__ == "__main__":
    main()
