class Symbol:
    def __init__(self, name: str, point: float,base: str , quote: str):
        self.name = name
        self.point = point
        self.related_countries = [base , quote , "ALL"]

    def get_point(self) -> float:
        return self.point
    
    def get_name(self) -> str:
        return self.name
    
    def is_news_relevant(self, country: str) -> bool:
        """Check if the news event affects the symbol based on country relevance."""
        return country in self.related_countries
