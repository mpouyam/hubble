from datetime import datetime
from typing import List

from news import NewsService


class NewsManager:
    def __init__(self, news_service: NewsService, logger):
        self.logger = logger
        self.news_service = news_service
        # self.news = []
        # self.cache = {}

    def get_news_times(self, symbol: str, timestamp: int) -> List[float]:
        # TODO: cache news for a day , dont request every time
        # dt_object = datetime.utcfromtimestamp(timestamp)
        # date = dt_object.date()
        #
        # news_list = self.news_service.get_news(dt_object)
        # return news_list
        return [4.30]
