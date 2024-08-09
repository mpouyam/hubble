from configs import RulesConfig, TraderConfigCalculator
from news import NewsManager, NewsService
from platform import Platform, PlatformConfig
from publisher import Publisher, PublisherConfig
from strategy import TraderManager, Rules
from utils import logger
from repository import JSONBoxRepository
import time
from dotenv import load_dotenv
from http_server import HubbleHttpController
import os

load_dotenv()

# Initialize the platform
platform_config = PlatformConfig({
    'path': os.getenv('path_to_mt'),
    'login': int(os.getenv('login')),
    'password': os.getenv('password'),
    'server': os.getenv('server'),
    'symbol': os.getenv('symbol'),
})
platform = Platform().initialize(platform_config)

# Initialize the publisher
publisher_config = PublisherConfig({
    'symbol': os.getenv('symbol'),
    'max_stored_ticks': int(os.getenv('max_stored_ticks')),
    'max_subs': int(os.getenv('max_subs')),
    'period': float(os.getenv('period'))
})
publisher = Publisher(publisher_config, platform)

# Initialize the loggers
global_logger = logger('bean')

# Initialize the Repository
global_repository = JSONBoxRepository("bean_repo.json")

# Initialize the strategy
news_service = NewsService("sdfsdf", global_logger)
news_manager = NewsManager(news_service, global_logger)

bean_rules_config = RulesConfig({})
bean_rules = Rules("", news_manager, global_logger, bean_rules_config)

bean_config_calculator = TraderConfigCalculator()
bean_strategy = TraderManager(platform, global_logger, bean_rules, global_repository, bean_config_calculator)

# Add the strategy as a tick listener
publisher.add_tick_listener(bean_strategy)

# run publisher engine
publisher.start()

# make main thread running
if os.getenv("http_server"):
    HubbleHttpController(bean_strategy, port=int(os.getenv("http_port"))).run()
else:
    while True:
        time.sleep(0.1)
