# Import functions from api_tool.py
from modules.api_tools import fetch_and_process_multiple_timeframes, fetch_github_data, process_github_data

# General function to assign a score based on value and upper/lower bounds for linear scaling
def assign_linear_score(value, min_value, max_value):
    """
    Assign a score based on a linear scale between min_value and max_value.

    """
    if value is None:
        return 0  # Fallback to 0 if the value is None

    if value >= max_value:
        return 10
    elif value <= min_value:
        return 0
    else:
        # Calculate score based on the linear position between min_value and max_value
        return (value - min_value) / (max_value - min_value) * 10

# Reverse scoring for metrics like open issues (fewer is better)
def assign_reverse_linear_score(value, min_value, max_value):
    if value <= min_value:
        return 10.00  # Best score for fewer open issues
    elif value >= max_value:
        return 0.00  # Worst score for many open issues
    else:
        return round(10 - ((value - min_value) / (max_value - min_value)) * 10, 2)  # Inverse linear scale

# Harmonized scoring for growth rates (Market Cap and Volume) between -50% and 50%
def assign_growth_score_harmonized(growth_rate):
    return assign_linear_score(growth_rate, -50, 50)  # Growth rates between -50% and 50%

# Harmonized scoring for volatility-to-volume ratio between 0 and 2.0
def assign_volatility_to_volume_score_harmonized(ratio):
    return assign_linear_score(ratio, 0, 2.0)  # Volatility-to-volume ratio between 0 and 2.0

# Calculate the weighted growth rate (Market Cap or Volume) based on the 30d, 60d, and 90d growth rates
def calculate_weighted_growth_rate(growth_30d, growth_60d, growth_90d):
    """
    Calculate a weighted growth rate using 30d, 60d, and 90d growth rates.
    If any of the growth rates are None, treat them as 0.
    """
    # Replace None values with 0
    growth_30d = growth_30d if growth_30d is not None else 0
    growth_60d = growth_60d if growth_60d is not None else 0
    growth_90d = growth_90d if growth_90d is not None else 0

    # Calculate weighted average
    weighted_growth = (growth_30d * 0.20) + (growth_60d * 0.40) + (growth_90d * 0.40)
    return weighted_growth

# Calculate individual scores for each metric
def calculate_metric_scores(volume_growth_30d, volume_growth_60d, volume_growth_90d, 
                            market_cap_growth_30d, market_cap_growth_60d, market_cap_growth_90d, 
                            volatility_volume_ratio, exchanges, stars, forks, open_issues, watchers):
    
    # Calculate weighted growth rates for market cap and volume
    weighted_market_cap_growth = calculate_weighted_growth_rate(market_cap_growth_30d, market_cap_growth_60d, market_cap_growth_90d)
    weighted_volume_growth = calculate_weighted_growth_rate(volume_growth_30d, volume_growth_60d, volume_growth_90d)
    
    # Assign harmonized scores based on the weighted growth rates and volatility/volume ratio
    market_cap_growth_score = assign_growth_score_harmonized(weighted_market_cap_growth)
    volume_growth_score = assign_growth_score_harmonized(weighted_volume_growth)
    volatility_score = assign_volatility_to_volume_score_harmonized(volatility_volume_ratio)

    # Harmonized scoring for exchanges, stars, forks, and watchers
    exchanges_score = assign_linear_score(exchanges, 1, 10)          # Assume 1 to 10 exchanges is typical
    stars_score = assign_linear_score(stars, 0, 500)                 # Scale from 0 to 500 stars
    forks_score = assign_linear_score(forks, 0, 100)                 # Scale from 0 to 100 forks
    watchers_score = assign_linear_score(watchers, 0, 200)           # Scale from 0 to 200 watchers

    # Reverse scoring for open issues (fewer open issues is better)
    open_issues_score = assign_reverse_linear_score(open_issues, 0, 100)  # Scale from 0 to 100 open issues (fewer is better)

    # Return all scores as a dictionary
    return {
        'market_cap_growth_score': market_cap_growth_score,
        'volume_growth_score': volume_growth_score,
        'volatility_score': volatility_score,
        'exchanges_score': exchanges_score,
        'stars_score': stars_score,
        'forks_score': forks_score,
        'open_issues_score': open_issues_score,
        'watchers_score': watchers_score,
    }


# Calculate the overall project score
def calculate_project_score(market_cap_growth_30d, market_cap_growth_60d, market_cap_growth_90d,
                            volume_growth_30d, volume_growth_60d, volume_growth_90d,
                            volatility_volume_ratio, exchanges, stars, forks, open_issues, watchers):
    # Calculate individual scores for each metric
    scores = calculate_metric_scores(volume_growth_30d, volume_growth_60d, volume_growth_90d, 
                                     market_cap_growth_30d, market_cap_growth_60d, market_cap_growth_90d, 
                                     volatility_volume_ratio, exchanges, stars, forks, open_issues, watchers)
    
    # Define weights for each criterion
    weights = {
        'market_cap_growth_score': 0.15,
        'volume_growth_score': 0.20,
        'volatility_score': 0.10,
        'exchanges_score': 0.05,
        'stars_score': 0.10,
        'forks_score': 0.15,
        'open_issues_score': 0.05,
        'watchers_score': 0.20
    }

    # Calculate weighted score
    weighted_score = (
        scores['market_cap_growth_score'] * weights['market_cap_growth_score'] +
        scores['volume_growth_score'] * weights['volume_growth_score'] +
        scores['volatility_score'] * weights['volatility_score'] +
        scores['exchanges_score'] * weights['exchanges_score'] +
        scores['stars_score'] * weights['stars_score'] +
        scores['forks_score'] * weights['forks_score'] +
        scores['open_issues_score'] * weights['open_issues_score'] +
        scores['watchers_score'] * weights['watchers_score']
    )

    return round(weighted_score, 2)  # Round the final score to two decimal places






