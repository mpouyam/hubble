from datetime import datetime, time, timedelta

from config import RulesConfig
from news import NewsManager
import pytz


class Rules:
    def __init__(self, news_manager: NewsManager, logger, config: RulesConfig):
        self.logger = logger
        self.news_manager = news_manager
        self.config = config

    def should_work(self, timestamp: int) -> bool:
        should_work = True #TODO: make it false

        market_is_open = self.__is_market_open(timestamp)

        if market_is_open:
            is_working_hour = self.__is_working_hour(timestamp)
            if is_working_hour:
                is_news_time = self.__is_news_time(timestamp)
                if not is_news_time:
                    should_work = True

        return should_work

    @staticmethod
    def __is_market_open(timestamp: int) -> bool:
        is_close = True

        current_time_utc = datetime.utcfromtimestamp(timestamp)
        ny_timezone = pytz.timezone('America/New_York')
        current_time_ny = current_time_utc.replace(tzinfo=pytz.utc).astimezone(ny_timezone)
        weekday = current_time_ny.weekday()
        hour = current_time_ny.hour

        if weekday >= 5:  # Saturday (5) or Sunday (6)
            is_close = False

        if weekday == 6 and hour < 17:  # Sunday and before 5 p.m.
            is_close = False

        return is_close

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

    def __is_news_time(self, timestamp: int = None) -> bool:
        before_news_minutes = self.config.before_news_minute
        after_news_minutes = self.config.after_news_minute
        news_times = self.news_manager.get_news_times(timestamp)

        for timee in news_times:
            news_time = self.__float_to_time(timee)
            non_work_start = news_time - timedelta(minutes=before_news_minutes)
            non_work_end = news_time + timedelta(minutes=after_news_minutes)

            # Check if timestamp is within the buffer period
            if non_work_start <= news_time <= non_work_end:
                return False

        return True

    @staticmethod
    def __float_to_time(float_time: float) -> datetime:
        """Convert a float time to a datetime object."""
        hours = int(float_time)
        minutes = int((float_time - hours) * 100)
        return datetime(year=1, month=1, day=1, hour=hours, minute=minutes)
