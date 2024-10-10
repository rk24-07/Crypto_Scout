import time
import streamlit as st
from app import load_repo_mappings, save_repo_mapping, get_or_prompt_repo_info
from modules.api_tools import fetch_github_data, process_github_data, fetch_and_process_multiple_timeframes, validate_coin_id
from modules.scoring_tool import calculate_project_score
from cachetools import TTLCache

# Cache to store API responses to reduce requests
cache = TTLCache(maxsize=100, ttl=600)

# Set the page configuration
st.set_page_config(page_title="Crypto Scout", page_icon=":crystal_ball:", layout="wide", initial_sidebar_state="expanded")

# Add custom CSS for better styling
st.markdown("""
    <style>
    .main {
        background: #1f3b73;
        color: #f5f5f5;
    }
    .block-container {
        font-family: Arial, sans-serif;
    }
    h1 {
        color: #ffa500;
    }
    h2, h3 {
        color: #ffb347;
    }
    .stTextInput label {
        color: #ffb347;
    }
    .stTextInput>div>input {
        background-color: #333333;
        color: #ffffff;
        border-radius: 10px;
        padding: 10px;
    }
    .stButton>button {
        background-color: #e67e22;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
    }
    .stButton>button:hover {
        background-color: #ff9900;
        color: #ffffff;
    }
    .github-link {
        color: #ffffff;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# Title
st.title(":crystal_ball: Crypto Scout - Early-Stage Project Scanner")

# Subtitle with brief description
st.subheader("Evaluate crypto projects with market cap, volume growth, volatility, and GitHub activity!")

st.write("""
    Enter the Coin ID and GitHub repository to receive an evaluation score based on market cap change, volume change, volatility, and GitHub metrics.
""")

# Input field for Coin ID
coin_id_1 = st.text_input(":moneybag: Enter the Coin ID for Project 1: (ex: 'bitcoin')", "")
repo_name_1 = None

# Load existing repo mappings
repo_mappings = load_repo_mappings()

if coin_id_1:
    # Validate the Coin ID first using CoinGecko
    if not validate_coin_id(coin_id_1):
        st.error(f"Invalid Coin ID '{coin_id_1}'. Please input a valid Coin ID.")
    else:
        repo_name_1, github_link = get_or_prompt_repo_info(coin_id_1)

        if repo_name_1:
            st.success(f"GitHub Repository found for {coin_id_1}: {repo_name_1}")
        else:
            if github_link:
                st.markdown(f"GitHub link from CoinGecko for **{coin_id_1}**: [GitHub Overview]({github_link})", unsafe_allow_html=True)
                st.markdown(f'<a href="{github_link}" target="_blank" class="github-link">GitHub Link: {github_link}</a>', unsafe_allow_html=True)
            repo_name_1 = st.text_input(":file_folder: Enter the GitHub Repository for Project 1 (owner/repo_name):", "")

            if repo_name_1:
                save_repo_mapping(coin_id_1, repo_name_1)

# Prompt for a second project to compare
compare = st.checkbox("🔄 Compare with another project?")

# If comparison is selected, input for the second project
coin_id_2 = ""
repo_name_2 = None
if compare:
    st.markdown("---")
    coin_id_2 = st.text_input(":moneybag: Enter the Coin ID for Project 2:", "")
    
    if coin_id_2:
        if not validate_coin_id(coin_id_2):
            st.error(f"Invalid Coin ID '{coin_id_2}'. Please input a valid Coin ID.")
        else:
            repo_name_2, github_link_2 = get_or_prompt_repo_info(coin_id_2)

            if repo_name_2:
                st.success(f"GitHub Repository found for {coin_id_2}: {repo_name_2}")
            else:
                if github_link_2:
                    st.markdown(f"GitHub link from CoinGecko for **{coin_id_2}**: [GitHub Overview]({github_link_2})", unsafe_allow_html=True)
                    st.markdown(f'<a href="{github_link_2}" target="_blank" class="github-link">GitHub Link: {github_link_2}</a>', unsafe_allow_html=True)
                repo_name_2 = st.text_input(":file_folder: Enter the GitHub Repository for Project 2 (owner/repo_name):", "")

                if repo_name_2:
                    save_repo_mapping(coin_id_2, repo_name_2)

# Fetching data and calculating scores
if st.button("Fetch Data and Calculate Score :rocket:"):
    if coin_id_1 and repo_name_1:
        data_1 = fetch_and_process_multiple_timeframes(coin_id_1)
        stars_1, forks_1, open_issues_1, watchers_1 = process_github_data(fetch_github_data(repo_name_1))

        # Ensure you're passing all the required arguments to calculate_project_score
        score_1 = calculate_project_score(
            market_cap_growth_30d=data_1['market_cap_growth'].get('30d', 0),
            market_cap_growth_60d=data_1['market_cap_growth'].get('60d', 0),
            market_cap_growth_90d=data_1['market_cap_growth'].get('90d', 0),
            volume_growth_30d=data_1['volume_growth'].get('30d', 0),
            volume_growth_60d=data_1['volume_growth'].get('60d', 0),
            volume_growth_90d=data_1['volume_growth'].get('90d', 0),
            volatility_volume_ratio=data_1['volatility_to_volume_ratio'].get('30d', 0),
            exchanges=data_1['num_exchanges'] if data_1['num_exchanges'] is not None else 0,
            stars=stars_1 if stars_1 is not None else 0,
            forks=forks_1 if forks_1 is not None else 0,
            open_issues=open_issues_1 if open_issues_1 is not None else 0,
            watchers=watchers_1 if watchers_1 is not None else 0
        )

        # Safeguard formatting for market cap growth and other metrics
        market_cap_growth_30d = data_1['market_cap_growth'].get('30d', 0) or 0
        market_cap_growth_60d = data_1['market_cap_growth'].get('60d', 0) or 0
        market_cap_growth_90d = data_1['market_cap_growth'].get('90d', 0) or 0

        volume_growth_30d = data_1['volume_growth'].get('30d', 0) or 0
        volume_growth_60d = data_1['volume_growth'].get('60d', 0) or 0
        volume_growth_90d = data_1['volume_growth'].get('90d', 0) or 0

        volatility_to_volume_ratio = data_1['volatility_to_volume_ratio'].get('30d', 0) or 0

        st.markdown(f"### :coin: Results for {coin_id_1}")
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(":bar_chart: Market Data")
            st.markdown(f"""
                **Market Cap Growth (30d, 60d, 90d):** 
                {market_cap_growth_30d:.2f}%, {market_cap_growth_60d:.2f}%, {market_cap_growth_90d:.2f}%  
                
                **Volume Growth (30d, 60d, 90d):** 
                {volume_growth_30d:.2f}%, {volume_growth_60d:.2f}%, {volume_growth_90d:.2f}%  
                
                **Volatility/Volume Ratio (30d):** 
                {volatility_to_volume_ratio:.2f}%  
                
                **Number of Exchanges:** {data_1['num_exchanges']}
            """)
        with col2:
            st.subheader(":file_folder: GitHub Data")
            st.markdown(f"""
                **Stars:** {stars_1:,}  
                **Forks:** {forks_1:,}  
                **Open Issues:** {open_issues_1:,}  
                **Watchers:** {watchers_1:,}
            """)
        st.markdown(f"## :star: Project Score: {score_1}/10")

    # Process the second project if selected and valid
    if compare and coin_id_2 and repo_name_2:
        data_2 = fetch_and_process_multiple_timeframes(coin_id_2)
        stars_2, forks_2, open_issues_2, watchers_2 = process_github_data(fetch_github_data(repo_name_2))

        score_2 = calculate_project_score(
            market_cap_growth_30d=data_2['market_cap_growth'].get('30d', 0),
            market_cap_growth_60d=data_2['market_cap_growth'].get('60d', 0),
            market_cap_growth_90d=data_2['market_cap_growth'].get('90d', 0),
            volume_growth_30d=data_2['volume_growth'].get('30d', 0),
            volume_growth_60d=data_2['volume_growth'].get('60d', 0),
            volume_growth_90d=data_2['volume_growth'].get('90d', 0),
            volatility_volume_ratio=data_2['volatility_to_volume_ratio'].get('30d', 0),
            exchanges=data_2['num_exchanges'],
            stars=stars_2,
            forks=forks_2,
            open_issues=open_issues_2,
            watchers=watchers_2
        )

        # Display results side by side in a table
        st.markdown(f"### :coin: Comparison Results for {coin_id_1} and {coin_id_2}")
        comparison_table = f"""
        <table>
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>{coin_id_1.upper()}</th>
                    <th>{coin_id_2.upper()}</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td><strong>Market Cap Growth (30d, 60d, 90d)</strong></td>
                    <td>{data_1['market_cap_growth']['30d'] if data_1['market_cap_growth']['30d'] is not None else 0:.2f}%, 
                        {data_1['market_cap_growth']['60d'] if data_1['market_cap_growth']['60d'] is not None else 0:.2f}%, 
                        {data_1['market_cap_growth']['90d'] if data_1['market_cap_growth']['90d'] is not None else 0:.2f}%</td>
                    <td>{data_2['market_cap_growth']['30d'] if data_2['market_cap_growth']['30d'] is not None else 0:.2f}%, 
                        {data_2['market_cap_growth']['60d'] if data_2['market_cap_growth']['60d'] is not None else 0:.2f}%, 
                        {data_2['market_cap_growth']['90d'] if data_2['market_cap_growth']['90d'] is not None else 0:.2f}%</td>
                </tr>
                <tr>
                    <td><strong>Volume Growth (30d, 60d, 90d)</strong></td>
                    <td>{data_1['volume_growth']['30d'] if data_1['volume_growth']['30d'] is not None else 0:.2f}%, 
                        {data_1['volume_growth']['60d'] if data_1['volume_growth']['60d'] is not None else 0:.2f}%, 
                        {data_1['volume_growth']['90d'] if data_1['volume_growth']['90d'] is not None else 0:.2f}%</td>
                    <td>{data_2['volume_growth']['30d'] if data_2['volume_growth']['30d'] is not None else 0:.2f}%, 
                        {data_2['volume_growth']['60d'] if data_2['volume_growth']['60d'] is not None else 0:.2f}%, 
                        {data_2['volume_growth']['90d'] if data_2['volume_growth']['90d'] is not None else 0:.2f}%</td>
                </tr>
                <tr>
                    <td><strong>Volatility/Volume Ratio (30d)</strong></td>
                    <td>{data_1['volatility_to_volume_ratio']['30d'] if data_1['volatility_to_volume_ratio']['30d'] is not None else 0:.2f}%</td>
                    <td>{data_2['volatility_to_volume_ratio']['30d'] if data_2['volatility_to_volume_ratio']['30d'] is not None else 0:.2f}%</td>
                </tr>
                <tr>
                    <td><strong>Number of Exchanges</strong></td>
                    <td>{data_1['num_exchanges']}</td>
                    <td>{data_2['num_exchanges']}</td>
                </tr>
                <tr>
                    <td><strong>Stars</strong></td>
                    <td>{stars_1:,}</td>
                    <td>{stars_2:,}</td>
                </tr>
                <tr>
                    <td><strong>Forks</strong></td>
                    <td>{forks_1:,}</td>
                    <td>{forks_2:,}</td>
                </tr>
                <tr>
                    <td><strong>Open Issues</strong></td>
                    <td>{open_issues_1:,}</td>
                    <td>{open_issues_2:,}</td>
                </tr>
                <tr>
                    <td><strong>Watchers</strong></td>
                    <td>{watchers_1:,}</td>
                    <td>{watchers_2:,}</td>
                </tr>
                <tr>
                    <td><strong>Project Score</strong></td>
                    <td>{score_1}/10</td>
                    <td>{score_2}/10</td>
                </tr>
            </tbody>
        </table>
        """
        st.markdown(comparison_table, unsafe_allow_html=True)


# Footer with contact information
st.markdown("---")
st.write("""
    Built with :heart: for the crypto community.
    For more information or questions, please contact us at [support@cryptoscout.com](mailto:support@cryptoscout.com).
""")

