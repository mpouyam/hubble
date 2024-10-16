# from config import RulesConfig, TraderConfigCalculator
# from news import NewsManager, NewsService
from analyzer.signallers.sr_signaller.handler.sr_signal_handler import SRSignalHandler
from analyzer.signallers.sr_signaller.signal import SRSignal
from analyzer.signallers.sr_signaller.signaller.sr_signaller import SRSignaller, SRSignallerConfig
from trading_platform import Platform
from config import PlatformConfig
# from publisher import Publisher, PublisherConfig
# from strategy import TraderManager, Rules
# from type import Symbol , TraderSignal
# from utils import logger
# from repository import JSONBoxRepository
import time
from dotenv import load_dotenv
# from http_server import HubbleHttpController
import os
# from type import TraderSignalData , OrderDirection
load_dotenv(override=True)



path = os.getenv('path_to_mt')
login = int(os.getenv('login'))
password = os.getenv('password')
server = os.getenv('server')

# Initialize the trading_platform
platform_config = PlatformConfig({
    'path': path,
    'login': login,
    'password': password,
    'server': server,
})
platform = Platform().initialize(platform_config)


signaller = SRSignaller(
    SRSignallerConfig(
        'EURUSD',
        0.02,
        0.001,
        1,
        1,
        5
    ),
    platform
)

class TestSRSignalHandler(SRSignalHandler):
    def handle_signal(self, signal: SRSignal):
        print(signal)

signaller.subscribe_handler(TestSRSignalHandler())
signaller.start()


while True:
    time.sleep(2)
    print("still working!")