# from datetime import datetime, timedelta
# from dateutil import parser
# import pytz
# import requests
# import os
# import json
# from type import ImpactLevel , Symbol

# # --- Domain Entities ---
# class EconomicNewsEvent:
#     def __init__(self, title: str, country: str, date: datetime, impact: str):
#         self.title = title
#         self.country = country
#         self.date = date
        
#         # Convert the impact string to the appropriate ImpactLevel enum, with a fallback
#         try:
#             self.impact = ImpactLevel(impact)  # Map the string to the ImpactLevel enum
#         except ValueError:
#             self.impact = None  # Handle the case where the impact string is not valid

#     def is_within_time_margin(self, current_time: datetime, margin_minutes: int = 30) -> bool:
#         """Check if the current time falls within the margin window of this news event."""
#         margin_start = self.date - timedelta(minutes=margin_minutes)
#         margin_end = self.date + timedelta(minutes=margin_minutes)
#         return margin_start <= current_time <= margin_end

# # --- News Service ---
# class NewsService:
#     CACHE_FILE = 'news_cache.json'
#     CACHE_EXPIRY_HOURS = 24 * 7  # 7 days

#     def __init__(self, api_url: str):
#         self.api_url = api_url

#     def _load_cached_news(self):
#         """Load cached news data if it's still valid."""
#         if os.path.exists(self.CACHE_FILE):
#             with open(self.CACHE_FILE, 'r') as cache_file:
#                 cached_data = json.load(cache_file)
#                 cache_timestamp = datetime.fromisoformat(cached_data['timestamp'])
#                 if datetime.now() - cache_timestamp < timedelta(hours=self.CACHE_EXPIRY_HOURS):
#                     return cached_data['news']
#         return None

#     def _cache_news(self, news_data):
#         """Cache the news data with a timestamp."""
#         with open(self.CACHE_FILE, 'w') as cache_file:
#             json.dump({
#                 'timestamp': datetime.now().isoformat(),
#                 'news': news_data
#             }, cache_file)

#     def fetch_news(self):
#         """Fetch the news, either from cache or by calling the API."""
#         cached_news = self._load_cached_news()
#         if cached_news:
#             return cached_news

#         response = requests.get(self.api_url)
#         if response.status_code == 200:
#             news_data = response.json()
#             self._cache_news(news_data)
#             return news_data
#         else:
#             raise Exception(f"Failed to fetch news: {response.status_code}")

#     def get_relevant_news(self, symbol: Symbol, current_time: datetime):
#         """Get relevant news based on the symbol and current time."""
#         all_news = self.fetch_news()
#         relevant_news = []
        
#         # Filter news based on the related countries and time window
#         for news_item in all_news:
#             news_event = EconomicNewsEvent(
#                 title=news_item['title'],
#                 country=news_item['country'],
#                 date=parser.isoparse(news_item['date']).astimezone(pytz.UTC),  # Parse and convert to UTC
#                 impact=news_item.get('impact', '')  # Fetch the 'impact' field safely
#             )
#             if symbol.is_news_relevant(news_event) and news_event.is_within_time_margin(current_time):
#                 relevant_news.append(news_event)
        
#         return relevant_news





from datetime import datetime, timedelta
from dateutil import parser
import pytz
import requests
import os
import json
from type import ImpactLevel, Symbol

# --- Domain Entities ---
class EconomicNewsEvent:
    def __init__(self, title: str, country: str, date: datetime, impact: str):
        self.title = title
        self.country = country
        self.date = date
        
        # Convert the impact string to the appropriate ImpactLevel enum, with a fallback
        try:
            self.impact = ImpactLevel(impact)  # Map the string to the ImpactLevel enum
        except ValueError:
            self.impact = None  # Handle the case where the impact string is not valid

    def is_within_time_margin(self, current_time: datetime, margin_minutes: int = 30) -> bool:
        """Check if the current time falls within the margin window of this news event."""
        margin_start = self.date - timedelta(minutes=margin_minutes)
        margin_end = self.date + timedelta(minutes=margin_minutes)
        return margin_start <= current_time <= margin_end

# --- News Service ---
class NewsService:
    CACHE_FILE = 'news_cache.json'
    
    def __init__(self, api_url: str):
        self.api_url = api_url

    def _load_cached_news(self):
        """Load cached news data if it's still valid based on data range."""
        if os.path.exists(self.CACHE_FILE):
            with open(self.CACHE_FILE, 'r') as cache_file:
                cached_data = json.load(cache_file)
                
                # Check the last date in the cached data to determine if cache is still valid
                date_range = cached_data.get('date_range', {})
                if 'end_date' in date_range:
                    end_date = datetime.fromisoformat(date_range['end_date']).replace(tzinfo=pytz.UTC)
                    # Set expiration at midnight after the last news day
                    expiration_date = end_date + timedelta(days=1)
                    
                    if datetime.now(pytz.UTC) < expiration_date:
                        return cached_data['news']
                    
        return None

    def _cache_news(self, news_data):
        """Cache the news data with a timestamp and date range."""
        # Calculate date range based on the data
        dates = [parser.isoparse(item['date']).astimezone(pytz.UTC) for item in news_data]
        start_date = min(dates).isoformat()
        end_date = max(dates).isoformat()
        
        # Cache data along with start and end dates
        with open(self.CACHE_FILE, 'w') as cache_file:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'news': news_data,
                'date_range': {
                    'start_date': start_date,
                    'end_date': end_date
                }
            }, cache_file)

    def fetch_news(self):
        """Fetch the news, either from cache or by calling the API."""
        cached_news = self._load_cached_news()
        if cached_news:
            return cached_news

        response = requests.get(self.api_url)
        if response.status_code == 200:
            news_data = response.json()
            self._cache_news(news_data)
            return news_data
        else:
            raise Exception(f"Failed to fetch news: {response.status_code}")

    def get_relevant_news(self, symbol: Symbol, current_time: datetime):
        """Get relevant news based on the symbol and current time."""
        all_news = self.fetch_news()
        relevant_news = []
        
        # Filter news based on the related countries and time window
        for news_item in all_news:
            news_event = EconomicNewsEvent(
                title=news_item['title'],
                country=news_item['country'],
                date=parser.isoparse(news_item['date']).astimezone(pytz.UTC),  # Parse and convert to UTC
                impact=news_item.get('impact', '')  # Fetch the 'impact' field safely
            )
            if symbol.is_news_relevant(news_event) and news_event.is_within_time_margin(current_time):
                relevant_news.append(news_event)
        
        return relevant_news
