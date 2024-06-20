import requests

class HTTPClient:
    def __init__(self, base_url):
        self.base_url = base_url

    def get(self, endpoint, params=None, headers=None):
        url = f"{self.base_url}/{endpoint}"
        response = requests.get(url, params=params, headers=headers)
        return self._handle_response(response)

    def _handle_response(self, response):
        if response.status_code == 200:
            try:
                return response.json()
            except ValueError:
                return response.text
        else:
            response.raise_for_status()


class NewsService:
    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    def get_news(self, s_date=None , e_date=None):
        if s_date is not None:
            endpoint = f"/news"
        return self.http_client.get(endpoint)

# Example usage
if __name__ == "__main__":
    new_factory = HTTPClient("https://jsonplaceholder.typicode.com")
    news_service = NewsService(new_factory)
    response = news_service.get_post(1)
    print(response)
