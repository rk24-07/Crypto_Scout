class CryptoProject:
    def __init__(self, name, symbol=None, repo=None, data=None):
        self.name = name
        self.symbol = symbol
        self.repo = repo
        self.data = data

    def __repr__(self):
        # Customize what gets printed when using `st.write()`
        return f"CryptoProject(name={self.name}, repo={self.repo}, symbol={self.symbol})"
