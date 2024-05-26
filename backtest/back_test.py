import os



# Now you can import the necessary modules
from trading_platform import PlatformConfig
from .platform_mock import PlatformMock
from .strategy_mock import TraderMock
from .logger_mock import NullLogger
from strategies import Config
from repository import JSONBoxRepository
from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict

   
def back_test(startDate: str , endDate:str , config: Config) : 
    config = {key: value.__dict__ for key, value in config.items()}
    symbol = config["orders_config"]["symbol"]

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
    Beanlogger = NullLogger('bean')


    repository_file_path = "backtest_repo.json"

    # Check if file exists, if not create it
    if not os.path.exists(repository_file_path):
        with open(repository_file_path, 'w'):
            pass  # Create an empty file if it doesn't exist

    # Initialize the logger
    BeanRepository = JSONBoxRepository(repository_file_path) 

    # Initialize the strategy
    beanStrategy = TraderMock(platform ,Beanlogger, BeanRepository , config)

    hist_data = platform.historic_data(startDate,endDate, symbol)
    for tick in hist_data :
        tick = (tick[0] ,tick[1],tick[2],tick[3] )
        beanStrategy.on_tick(tick)
