from trading_platform import Platform, PlatformConfig
import time 
from dotenv import load_dotenv
from publisher import TickListener, Publisher, PublisherConfig
import os 
from analyzer import CandleRangeSignaller, CandleRangeSignallerConfig
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


class TestStrategy(TickListener):

    def __init__(self, symbol):
        self.symbol = symbol

    def on_tick(self, tick) -> None:
        print(tick)

    def get_symbol(self) -> str:
        return self.symbol

# publisher.add_tick_listener(TestStrategy("GBPUSD_o"))
# publisher.start()
candle_range_signaller = CandleRangeSignaller(
    "USDSEK",
    platform,
    lambda x: print("Callback Called"),
    CandleRangeSignallerConfig().set_count(2)
).start()


while True:
#     # print("Main Thread Working!")
    time.sleep(5)
#     publisher_config.set_symbol("USDSEK")
#     publisher_config.set_period(3)
#     publisher.change_config(publisher_config)
#     print("Publisher Config Changed")
#     while True:

#         time.sleep(2)

