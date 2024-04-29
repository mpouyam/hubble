import json
from trading_platform import Platform, PlatformConfig
from publisher import Publisher, PublisherConfig
from strategies import BeanStrategy
from utils import logger
import time 

f = open("config.json")
conf = json.load(f)
f.close()


# Initialize the platform
platform_config = PlatformConfig({
    'path': conf['path'],
    'login': conf['login'],
    'password': conf['password'],
    'server': conf['server'],
    'symbol': conf['symbol'],
})
platform = Platform().initialize(platform_config)

# Initialize the publisher
publisher_config = PublisherConfig({
    'symbol': conf['symbol'],
    'max_stored_ticks': conf['max_stored_ticks'],
    'max_subs': conf['max_subs'],
    'period' : conf['period']
})
publisher = Publisher(publisher_config, platform)

# Initialize the logger
Beanlogger = logger('bean')

# Initialize the strategy
beanStrategy = BeanStrategy(platform ,Beanlogger,conf['symbol'])


# Add the strategy as a tick listener
publisher.add_tick_listener(beanStrategy)

# run publisher engine
publisher.start()

# run strategy
beanStrategy.run()

# make main thread running
while True:
    time.sleep(0.1)
