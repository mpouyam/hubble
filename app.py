from trading_platform import Platform, PlatformConfig
from publisher import Publisher, PublisherConfig
from strategies import Trader
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
    'period' : float(os.getenv('period'))
})
publisher = Publisher(publisher_config, platform)

# Initialize the logger
Beanlogger = logger('bean')
BeanRepository = JSONBoxRepository("bean_repo.json") 

# Initialize the strategy
beanStrategy = Trader(platform ,Beanlogger,BeanRepository , os.getenv('symbol'),)


# Add the strategy as a tick listener
publisher.add_tick_listener(beanStrategy)

# run publisher engine
publisher.start()

# make main thread running
print(int(os.getenv("http_port")))
if os.getenv("http_server"):
    HubbleHttpController(beanStrategy, port = int(os.getenv("http_port"))).run()
else:
    while True:
        time.sleep(0.1)
