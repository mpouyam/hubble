import os
import time

from dotenv import load_dotenv

from analyzer.signallers.sr_signaller.signaller.sr_signaller import SRSignaller, SRSignallerConfig
from configs import RulesConfig, TraderConfigCalculator
from http_server import HubbleHttpController
from internal_types import Symbol
from news import NewsService
from publisher import Publisher, PublisherConfig
from repository import JSONBoxRepository
from strategy import TraderManager, TradeDecisionService
from trading_platform import Platform, PlatformConfig
from utils import logger

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
    1: 3
}
static_sl = {}
growth_factor = float(os.getenv('growth_factor'))
pause_times = int(os.getenv('pause_times'))
max_order = int(os.getenv('max_order'))

# Initialize the trading_platform
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
    symbol,
    symbol_info[2],
    symbol_info[0],
    symbol_info[1]
)

# Initialize the publisher
publisher_config = PublisherConfig({
    'symbol': verified_symbol.get_name(),
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
news_service = NewsService(news_service_base_url)

bean_rules_config = RulesConfig(
    symbol=verified_symbol,
    default_working_hours=default_working_hours,
    before_news_minute=before_news_minute,
    after_news_minute=after_news_minute
)

trade_decision_service = TradeDecisionService(news_service, bean_rules_config, global_logger)

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

bean_strategy = TraderManager(platform, verified_symbol, global_logger, trade_decision_service, global_repository,
                              bean_config_calculator)

# Add the strategy as a tick listener
publisher.add_tick_listener(bean_strategy)

# run publisher engine
publisher.start()

signaller = SRSignaller(
    SRSignallerConfig(
        verified_symbol.get_name(),
        0.0002,
        0.0002,
        4,
        "1m",
        25
    ),
    platform
)

signaller.subscribe_handler(bean_strategy)
signaller.start()

signaller2 = SRSignaller(
    SRSignallerConfig(
        verified_symbol.get_name(),
        0.0002,
        0.0002,
        4,
        "5m",
        22
    ),
    platform
)

signaller2.subscribe_handler(bean_strategy)
signaller2.start()

signaller3 = SRSignaller(
    SRSignallerConfig(
        verified_symbol.get_name(),
        0.0002,
        0.0002,
        2,
        "1h",
        3
    ),
    platform
)

signaller3.subscribe_handler(bean_strategy)
signaller3.start()

# make main thread running
if os.getenv("http_server"):
    HubbleHttpController(bean_strategy, port=int(os.getenv("http_port"))).run()
else:
    while True:
        time.sleep(2)
