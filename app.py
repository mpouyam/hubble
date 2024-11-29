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

""" TRADE CONFIG """
sl_limit = 4
tp_limit = 16
static_vol = {}
static_tp = {
    1: 4
}
static_sl = {}
growth_factor = 1.3
pause_times = 3
max_order = 20

# Initialize the trading_platform
platform_config = PlatformConfig({
    'path': path,
    'login': login,
    'password': password,
    'server': server,
})
platform = Platform().initialize(platform_config)

# Initialize the loggers
global_logger = logger('bean')
# Initialize the Repository
global_repository = JSONBoxRepository("repo.json")

# Initialize the strategy
news_service = NewsService(news_service_base_url)

trade_decision_service = TradeDecisionService(news_service, global_logger)



'''GBPUSD'''
GBPUSD = "GBPUSD_o"
# validate symbol
gbpusd_info = platform.get_symbol_info(GBPUSD)
verified_gbpusd_symbol = Symbol(
    GBPUSD,
    gbpusd_info[2],
    gbpusd_info[0],
    gbpusd_info[1]
)

# Initialize the publisher
gbpusd_publisher_config = PublisherConfig({
    'symbol': verified_gbpusd_symbol.get_name(),
    'max_stored_ticks': max_stored_ticks,
    'max_subs': max_subs,
    'period': period
})
gbpusd_publisher = Publisher(gbpusd_publisher_config, platform)

gbpusd_config_calculator = TraderConfigCalculator({
    'symbol': verified_gbpusd_symbol.name,
    'point': verified_gbpusd_symbol.point,
    'sl_limit': sl_limit,
    'tp_limit': tp_limit,
    'static_vol': static_vol,
    'static_tp': static_tp,
    'static_sl': static_sl,
    'growth_factor': growth_factor,
    'pause_times': pause_times,
    'max_order': max_order
})

gbp_strategy = TraderManager(platform, verified_gbpusd_symbol, global_logger, trade_decision_service, global_repository,
                              gbpusd_config_calculator)

# Add the strategy as a tick listener , run publisher engine
gbpusd_publisher.add_tick_listener(gbp_strategy)
gbpusd_publisher.start()

gbpsignaller = SRSignaller(
    SRSignallerConfig(
        verified_gbpusd_symbol.get_name(),
        0.0002,
        0.0002,
        1,
        "1h",
        3
    ),
    platform
)
gbpsignaller.subscribe_handler(gbp_strategy)
gbpsignaller.start()

gbpsignaller2 = SRSignaller(
    SRSignallerConfig(
        verified_gbpusd_symbol.get_name(),
        0.0002,
        0.0002,
        1,
        "1h",
        3
    ),
    platform
)
gbpsignaller2.subscribe_handler(gbp_strategy)
gbpsignaller2.start()


'''EURUSD'''
EURUSD = "EURUSD_o"
# validate symbol
eurusd_info = platform.get_symbol_info(EURUSD)
verified_eurusd_symbol = Symbol(
    EURUSD,
    eurusd_info[2],
    eurusd_info[0],
    eurusd_info[1]
)

# Initialize the publisher
eurusd_publisher_config = PublisherConfig({
    'symbol': verified_eurusd_symbol.get_name(),
    'max_stored_ticks': max_stored_ticks,
    'max_subs': max_subs,
    'period': period
})
eurusd_publisher = Publisher(eurusd_publisher_config, platform)

eurusd_config_calculator = TraderConfigCalculator({
    'symbol': verified_eurusd_symbol.name,
    'point': verified_eurusd_symbol.point,
    'sl_limit': sl_limit,
    'tp_limit': tp_limit,
    'static_vol': static_vol,
    'static_tp': static_tp,
    'static_sl': static_sl,
    'growth_factor': growth_factor,
    'pause_times': pause_times,
    'max_order': max_order
})

eurusd_strategy = TraderManager(platform, verified_eurusd_symbol, global_logger, trade_decision_service, global_repository,
                              eurusd_config_calculator)

# Add the strategy as a tick listener , run publisher engine
eurusd_publisher.add_tick_listener(eurusd_strategy)
eurusd_publisher.start()

eurusdsignaller = SRSignaller(
    SRSignallerConfig(
        verified_eurusd_symbol.get_name(),
        0.0002,
        0.0002,
        1,
        "1h",
        5
    ),
    platform
)
eurusdsignaller.subscribe_handler(eurusd_strategy)
eurusdsignaller.start()

eurusdsignaller2 = SRSignaller(
    SRSignallerConfig(
        verified_eurusd_symbol.get_name(),
        0.0002,
        0.0002,
        1,
        "1h",
        3
    ),
    platform
)
eurusdsignaller2.subscribe_handler(eurusd_strategy)
eurusdsignaller2.start()


'''AUDJPY'''
AUDJPY = "AUDJPY_o"
# validate symbol
audjpy_info = platform.get_symbol_info(AUDJPY)
verified_audjpy_symbol = Symbol(
    AUDJPY,
    audjpy_info[2],
    audjpy_info[0],
    audjpy_info[1]
)

# Initialize the publisher
audjpy_publisher_config = PublisherConfig({
    'symbol': verified_audjpy_symbol.get_name(),
    'max_stored_ticks': max_stored_ticks,
    'max_subs': max_subs,
    'period': period
})
audjpy_publisher = Publisher(audjpy_publisher_config, platform)

audjpy_config_calculator = TraderConfigCalculator({
    'symbol': verified_audjpy_symbol.name,
    'point': verified_audjpy_symbol.point,
    'sl_limit': sl_limit,
    'tp_limit': tp_limit,
    'static_vol': static_vol,
    'static_tp': static_tp,
    'static_sl': static_sl,
    'growth_factor': growth_factor,
    'pause_times': pause_times,
    'max_order': max_order
})

audjpy_strategy = TraderManager(platform, verified_audjpy_symbol, global_logger, trade_decision_service, global_repository,
                              audjpy_config_calculator)

# Add the strategy as a tick listener , run publisher engine
audjpy_publisher.add_tick_listener(audjpy_strategy)
audjpy_publisher.start()

audjpysignaller = SRSignaller(
    SRSignallerConfig(
        verified_audjpy_symbol.get_name(),
        0.0002,
        0.0002,
        1,
        "1h",
        5
    ),
    platform
)
audjpysignaller.subscribe_handler(audjpy_strategy)
audjpysignaller.start()

audjpysignaller2 = SRSignaller(
    SRSignallerConfig(
        verified_audjpy_symbol.get_name(),
        0.0002,
        0.0002,
        1,
        "1h",
        3
    ),
    platform
)
audjpysignaller2.subscribe_handler(audjpy_strategy)
audjpysignaller2.start()


# '''BTCUSD'''
# BTCUSD = "BTCUSD"
# # validate symbol
# btcusd_info = platform.get_symbol_info(BTCUSD)
# verified_btcusd_symbol = Symbol(
#     BTCUSD,
#     btcusd_info[2],
#     btcusd_info[0],
#     btcusd_info[1]
# )

# # Initialize the publisher
# btcusd_publisher_config = PublisherConfig({
#     'symbol': verified_btcusd_symbol.get_name(),
#     'max_stored_ticks': max_stored_ticks,
#     'max_subs': max_subs,
#     'period': period
# })
# btcusd_publisher = Publisher(btcusd_publisher_config, platform)

# btcusd_config_calculator = TraderConfigCalculator({
#     'symbol': verified_btcusd_symbol.name,
#     'point': verified_btcusd_symbol.point,
#     'sl_limit': 500,
#     'tp_limit': 2500,
#     'static_vol': {1:0.01},
#     'static_tp': {1:1200},
#     'static_sl': static_sl,
#     'growth_factor': growth_factor,
#     'pause_times': pause_times,
#     'max_order': max_order
# })

# btc_strategy = TraderManager(platform, verified_btcusd_symbol, global_logger, trade_decision_service, global_repository,
#                               btcusd_config_calculator)

# # Add the strategy as a tick listener , run publisher engine
# btcusd_publisher.add_tick_listener(btc_strategy)
# btcusd_publisher.start()

# btcsignaller = SRSignaller(
#     SRSignallerConfig(
#         verified_btcusd_symbol.get_name(),
#         0.2,
#         0.2,
#         4,
#         "1h",
#         5
#     ),
#     platform
# )
# btcsignaller.subscribe_handler(btc_strategy)
# btcsignaller.start()

# btcsignaller2 = SRSignaller(
#     SRSignallerConfig(
#         verified_btcusd_symbol.get_name(),
#         0.2,
#         0.2,
#         1,
#         "1h",
#         3
#     ),
#     platform
# )
# btcsignaller2.subscribe_handler(btc_strategy)
# btcsignaller2.start()


# make main thread running
if os.getenv("http_server"):
    HubbleHttpController(gbp_strategy, port=int(os.getenv("http_port"))).run()
else:
    while True:
        time.sleep(2)
