from config import RulesConfig
from news import NewsService
from type import Symbol , ImpactLevel
from datetime import datetime, time
import pytz

class TradeDecisionService:
    def __init__(self, news_service: NewsService , config: RulesConfig , logger):
        self.news_service = news_service
        self.config = config
        self.logger = logger

    def is_safe_to_trade(self, symbol: Symbol, current_time: datetime) -> bool:

        is_working_hour = self.__is_working_hour(current_time)
        if not is_working_hour:
            self.logger.error("Signal Received But Not Good For Trade : IT'S NOT WORKING HOUR")
            return False
        
        is_news_time = self.__is_news_time(symbol ,current_time)
        if is_news_time:
            self.logger.error("Signal Received But Not Good For Trade : IT'S NEW'S HOUR")
            return False
        
        return True
        
    def __is_working_hour(self, tick_time: int) -> bool:
        gmt_tz = pytz.timezone('GMT')
        tick_time_gmt = datetime.fromtimestamp(tick_time , gmt_tz)
        start_hour, end_hour = self.config.default_working_hours

        start_hour_int = int(start_hour)
        start_minute = int(round((start_hour - start_hour_int) * 100))
        
        end_hour_int = int(end_hour)
        end_minute = int(round((end_hour - end_hour_int) * 100))

        start_time = datetime.combine(tick_time_gmt.date(), time(hour=start_hour_int, minute=start_minute),gmt_tz)
        end_time = datetime.combine(tick_time_gmt.date(), time(hour=end_hour_int, minute=end_minute),gmt_tz)

        return start_time <= tick_time_gmt <= end_time

    def __is_news_time(self,symbol, timestamp: int = None) -> bool:
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
            if news.impact == ImpactLevel.LOW:
                low_impact_count += 1
            elif news.impact == ImpactLevel.MEDIUM:
                medium_impact_count += 1
            elif news.impact == ImpactLevel.HIGH:
                high_impact_count += 1

        # Decision logic: trade is not safe if the combined impact is too high
        if high_impact_count >= 1 or medium_impact_count >= 2:
            is_news_time = True
        
        return is_news_time 


