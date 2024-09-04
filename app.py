from config import RulesConfig, TraderConfigCalculator
from news import NewsManager, NewsService
from platform import Platform, PlatformConfig
from publisher import Publisher, PublisherConfig
from strategy import TraderManager, Rules
from type import Symbol , TraderSignal
from utils import logger
from repository import JSONBoxRepository
import time
from dotenv import load_dotenv
from http_server import HubbleHttpController
import os
from type import TraderSignalData , OrderDirection
load_dotenv(override=True)

# LOAD CONFIGS :
symbol = os.getenv('symbol')

""" ACCOUNT CONFIG """
path = os.getenv('path_to_mt')
login = int(os.getenv('login'))
password = os.getenv('password')
server = os.getenv('server')

""" PUBLISHER CONFIG """
max_stored_ticks = int(os.getenv('max_stored_ticks'))
max_subs = int(os.getenv('max_subs'))
period = float(os.getenv('period'))

""" NEWS CONFIG """
news_service_base_url = os.getenv('news_url')

""" RULES CONFIG """
default_working_hours = (float(os.getenv('start_working_at')), float(os.getenv('stop_working_at')))
before_news_minute = int(os.getenv('before_news_minute'))
after_news_minute = int(os.getenv('after_news_minute'))

""" TRADE CONFIG """
sl_limit = int(os.getenv('sl_limit'))
tp_limit = int(os.getenv('tp_limit'))
static_vol = {}
static_tp = {
    1: 6
}
static_sl = {}
growth_factor = float(os.getenv('growth_factor'))
pause_times = int(os.getenv('pause_times'))
max_order = int(os.getenv('max_order'))

# Initialize the platform
platform_config = PlatformConfig({
    'path': path,
    'login': login,
    'password': password,
    'server': server,
})
platform = Platform().initialize(platform_config)

# validate symbol
symbol_info = platform.get_symbol_info(symbol)
verified_symbol = Symbol(
    name=symbol,
    point=symbol_info[2],
    quote=symbol_info[1],
    base=symbol_info[0]
)

# Initialize the publisher
publisher_config = PublisherConfig({
    'symbol': symbol,
    'max_stored_ticks': max_stored_ticks,
    'max_subs': max_subs,
    'period': period
})
publisher = Publisher(publisher_config, platform)

# Initialize the loggers
global_logger = logger('bean')

# Initialize the Repository
global_repository = JSONBoxRepository("repo.json")

# Initialize the strategy
news_service = NewsService(news_service_base_url, global_logger)
news_manager = NewsManager(news_service, global_logger)

bean_rules_config = RulesConfig(
    symbol=verified_symbol,
    default_working_hours=default_working_hours,
    before_news_minute=before_news_minute,
    after_news_minute=after_news_minute
)
bean_rules = Rules(news_manager, global_logger, bean_rules_config)

bean_config_calculator = TraderConfigCalculator({
    'symbol': verified_symbol.name,
    'point': verified_symbol.point,
    'sl_limit': sl_limit,
    'tp_limit': tp_limit,
    'static_vol': static_vol,
    'static_tp': static_tp,
    'static_sl': static_sl,
    'growth_factor': growth_factor,
    'pause_times': pause_times,
    'max_order': max_order
})

bean_strategy = TraderManager(platform, global_logger, bean_rules, global_repository, bean_config_calculator)

# Add the strategy as a tick listener
publisher.add_tick_listener(bean_strategy)

# run publisher engine
publisher.start()

# make main thread running
# if os.getenv("http_server"):
#     HubbleHttpController(bean_strategy, port=int(os.getenv("http_port"))).run()
# else:
while True:

    time.sleep(2)
    bean_strategy.on_signal(
        TraderSignal.RUN,
        TraderSignalData(direction= OrderDirection.BUY)
    )
