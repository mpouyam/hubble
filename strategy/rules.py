from datetime import datetime, timedelta

import pytz

from internal_types import Symbol, NewsImpactLevel
from news import NewsService

# Define trading sessions and their active currency pairs
TRADING_SESSIONS = {

    "Tokyo": {
        "start": 0,   # Start time in UTC (12:00 AM)
        "end": 9,     # End time in UTC (9:00 AM)
        "pairs": {"AUDJPY_o"}
    },
    "London": {
        "start": 7,   # Start time in UTC (7:00 AM)
        "end": 16,    # End time in UTC (4:00 PM)
        "pairs": {"EURUSD_o", "GBPUSD_o"}
    },
    "New York": {
        "start": 13,  # Start time in UTC (1:00 PM)
        "end": 22,    # End time in UTC (10:00 PM)
        "pairs": {"EURUSD_o", "GBPUSD_o"}
    },
    "ALL": {
        "start": 0,   # Always active, 24 hours
        "end": 24,    # Until midnight of the next day
        "pairs": {"BTCUSD", "ETHUSD"}  # Example: Cryptocurrency pairs
    }
}

class TradeDecisionService:
    def __init__(self, news_service: NewsService, logger):
        self.news_service = news_service
        self.logger = logger

    ''' PUBLIC '''
    def is_safe_to_trade(self, symbol: Symbol, current_time: int) -> bool:        
        is_market_active = self.__is_market_active(symbol.get_name() , current_time)
        if not is_market_active:
            self.logger.error("Signal Received But Not Good For Trade : IT'S NOT MARKET HOUR")
            return False

        is_news_time = self.__is_news_time(symbol, current_time)
        if is_news_time:
            self.logger.error("Signal Received But Not Good For Trade : IT'S NEW'S HOUR")
            return False

        return True


    ''' PRIVATE '''
    def __is_market_active(self,symbol:str, timestamp:int , margin_minutes=60) -> bool:
        """
        Check if the given symbol is active during its associated market session at the given timestamp.
        
        Parameters:
        - symbol (str): The currency pair to check (e.g., "EUR/USD").
        - timestamp (datetime): The timestamp in UTC to check.
        - margin_minutes (int): Minutes to extend the session's start and end times for flexibility.
        
        Returns:
        - str: The session name if the symbol is active, otherwise None.
        """
        timestamp = datetime.fromtimestamp(timestamp, pytz.UTC)  # Convert to UTC datetime

        # Ensure the timestamp is in UTC and timezone-aware
        if timestamp.tzinfo is None or timestamp.tzinfo != pytz.UTC:
            raise ValueError("The timestamp must be timezone-aware and in UTC.")

        # Iterate through each session
        for _, session_data in TRADING_SESSIONS.items():
            session_start = session_data["start"]
            session_end = session_data["end"]
            session_pairs = session_data["pairs"]

            # Check if the symbol belongs to the session
            if symbol not in session_pairs:
                continue

            # Calculate session start and end times with margins
            utc = pytz.UTC
            start_time = (datetime.combine(timestamp.date(), datetime.min.time(), tzinfo=utc) + 
                        timedelta(hours=session_start) - timedelta(minutes=margin_minutes))
            end_time = (datetime.combine(timestamp.date(), datetime.min.time(), tzinfo=utc) + 
                        timedelta(hours=session_end) + timedelta(minutes=margin_minutes))
            is_related_market_open = False
            # Handle sessions that span midnight
            if session_start > session_end:
                # If session spans midnight, the condition splits into two parts
                if timestamp >= start_time or timestamp <= end_time:
                    is_related_market_open = True
            else:
                # Regular session within the same calendar day
                if start_time <= timestamp <= end_time:
                    is_related_market_open = True

        return is_related_market_open

    # def __is_working_hour(self, tick_time: int) -> bool:
    #     gmt_tz = pytz.timezone('GMT')
    #     tick_time_gmt = datetime.fromtimestamp(tick_time, gmt_tz)
    #     start_hour, end_hour = self.config.default_working_hours

    #     start_hour_int = int(start_hour)
    #     start_minute = int(round((start_hour - start_hour_int) * 100))

    #     end_hour_int = int(end_hour)
    #     end_minute = int(round((end_hour - end_hour_int) * 100))

    #     start_time = datetime.combine(tick_time_gmt.date(), time(hour=start_hour_int, minute=start_minute), gmt_tz)
    #     end_time = datetime.combine(tick_time_gmt.date(), time(hour=end_hour_int, minute=end_minute), gmt_tz)

    #     return start_time <= tick_time_gmt <= end_time

    def __is_news_time(self, symbol, timestamp: int = None) -> bool:
        """Evaluate if it's safe to trade based on recent news events and their impacts."""

        is_news_time = False

        gmt_tz = pytz.timezone('GMT')
        tick_time_gmt = datetime.fromtimestamp(timestamp , gmt_tz)
        relevant_news = self.news_service.get_relevant_news(symbol, tick_time_gmt)

        # Count impact levels within a 1-hour window
        low_impact_count = 0
        medium_impact_count = 0
        high_impact_count = 0

        for news in relevant_news:
            if news.impact is None:
                continue
            if news.impact == NewsImpactLevel.LOW:
                low_impact_count += 1
            elif news.impact == NewsImpactLevel.MEDIUM:
                medium_impact_count += 1
            elif news.impact == NewsImpactLevel.HIGH:
                high_impact_count += 1
        # Decision logic: trade is not safe if the combined impact is too high
        if high_impact_count >= 1 or medium_impact_count >= 2:
            is_news_time = True

        return is_news_time
