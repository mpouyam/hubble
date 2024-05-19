import sys
import os



# Now you can import the necessary modules
from trading_platform import PlatformConfig
from .platform_mock import PlatformMock
from .strategy_mock import TraderMock
from utils import logger
from repository import JSONBoxRepository
from dotenv import load_dotenv
load_dotenv()


def back_test(startDate: str , endDate:str , symbol:str , config: dict = None) : 
    # Initialize the platform
    platform_config = PlatformConfig({
        'path': os.getenv('path_to_mt'),
        'login': int(os.getenv('login')),
        'password': os.getenv('password'),
        'server': os.getenv('server'),
        'symbol': symbol,
    })
    platform = PlatformMock(platform_config)



    # Initialize the logger
    Beanlogger = logger('bean')


    repository_file_path = "backtest_repo.json"

    # Check if file exists, if not create it
    if not os.path.exists(repository_file_path):
        with open(repository_file_path, 'w'):
            pass  # Create an empty file if it doesn't exist

    # Initialize the logger
    BeanRepository = JSONBoxRepository("backtest_repo.json") 

    # Initialize the strategy
    beanStrategy = TraderMock(platform ,Beanlogger, BeanRepository , symbol)

    hist_data = platform.historic_data(startDate,endDate, symbol)
    for price in hist_data :
        # print(price)
        beanStrategy.on_tick(price)
