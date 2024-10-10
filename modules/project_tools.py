# project_tools.py

class CryptoProject:
    def __init__(self, name, symbol=None, repo=None, market_cap_growth=None, volume_growth=None, exchanges=None, stars=None, forks=None, open_issues=None, watchers=None):
        # Initialize project details
        self.name = name
        self.symbol = symbol
        self.repo = repo
        
        # Initialize market cap growth and volume growth as dictionaries
        self.market_cap_growth = market_cap_growth if market_cap_growth else {'30d': None, '60d': None, '90d': None}
        self.volume_growth = volume_growth if volume_growth else {'30d': None, '60d': None, '90d': None}
        
        # Other project metrics
        self.exchanges = exchanges
        self.stars = stars
        self.forks = forks
        self.open_issues = open_issues
        self.watchers = watchers

    def __repr__(self):
        return (
            f"CryptoProject(name={self.name}, symbol={self.symbol}, repo={self.repo}, "
            f"market_cap_growth={self.market_cap_growth}, volume_growth={self.volume_growth}, "
            f"exchanges={self.exchanges}, stars={self.stars}, forks={self.forks}, "
            f"open_issues={self.open_issues}, watchers={self.watchers})"
        )

