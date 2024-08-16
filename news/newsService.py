import datetime
from typing import List

import requests


class NewsService:
    def __init__(self, base_url: str, logger):
        self.logger = logger
        self.base_url = base_url

    def get_news(self, date: datetime.datetime) -> List[int]:
        news_list = []
        try:
            response = requests.get(f"{self.base_url}/get-news")

            if response.status_code == 200:
                news_list = response.json()
            else:
                print('Error:', response.status_code)

        except requests.exceptions.RequestException as e:
            print('Error:', e)

        finally:
            return news_list
