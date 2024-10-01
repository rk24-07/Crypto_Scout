import requests

class APIClient:
    def fetch_data(self):
        pass  # Placeholder for API call functions

def search_github_repo(project_name):
    """Search for a GitHub repository by project name using the GitHub API."""
    url = f"https://api.github.com/search/repositories?q={project_name}+in:name"
    headers = {"Accept": "application/vnd.github.v3+json"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()
            if data['total_count'] > 0:
                # Return the top repository URL
                return data['items'][0]['html_url']
            else:
                return None
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching GitHub repository: {e}")
        return None

