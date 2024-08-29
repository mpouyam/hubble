import os
import json
from datetime import datetime
from typing import Tuple

from config import TraderConfigCalculator, RulesConfig
from news import NewsService, NewsManager
from platform import PlatformConfig
from type import Symbol
from .platform_mock import PlatformMock
from .logger_mock import NullLogger
from strategy import TraderManager, Rules
from repository import JSONBoxRepository
from dotenv import load_dotenv

load_dotenv()


def back_test(startDate: Tuple, endDate: Tuple, config):
    config = {key: value.__dict__ for key, value in config.items()}
    symbol = config["orders_config"]["symbol"]

    """ ACCOUNT CONFIG """
    path = os.getenv('path_to_mt')
    login = int(os.getenv('login'))
    password = os.getenv('password')
    server = os.getenv('server')

    """ NEWS CONFIG """
    news_service_base_url = 'http://localhost:8000'

    """ RULES CONFIG """
    default_working_hours = config["orders_config"]["start_time"], config["orders_config"]["end_time"]
    before_news_minute = config["orders_config"]["before_news_minute"]
    after_news_minute = config["orders_config"]["after_news_minute"]

    """ TRADE CONFIG """
    sl_limit = config["orders_config"]["sl_limit"]
    tp_limit = config["orders_config"]["tp_limit"]
    static_vol = {}
    static_tp = {
        1: 6
    }
    static_sl = {}
    growth_factor = config["orders_config"]["growth_factor"]
    pause_times = config["orders_config"]["pause_times"]
    max_order = config["orders_config"]["max_order"]

    # Initialize the platform
    platform_config = PlatformConfig({
        'path': path,
        'login': login,
        'password': password,
        'server': server,
    })

    platform = PlatformMock(platform_config)

    # validate symbol
    symbol_info = platform.get_symbol_info(symbol)
    verified_symbol = Symbol(
        name=symbol,
        point=symbol_info[2],
        quote=symbol_info[1],
        base=symbol_info[0]
    )

    # Initialize the logger
    logger = NullLogger('bean')

    # Construct the output file name
    output_folder = "backtest_result"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file_name = f"{config["orders_config"]["symbol"]}_{startDate}_{endDate}_{config["orders_config"]["sl_limit"]}_{config["orders_config"]["tp_limit"]}_{datetime.now().timestamp()}.json"
    output_file_path = os.path.join(output_folder, output_file_name)

    # Check if file exists, if not create it
    if not os.path.exists(output_file_path):
        with open(output_file_path, 'w'):
            pass  # Create an empty file if it doesn't exist

    # Initialize the logger
    repo = JSONBoxRepository(output_file_path)

    # Initialize the strategy
    news_service = NewsService(news_service_base_url, logger)
    news_manager = NewsManager(news_service, logger)

    bean_rules_config = RulesConfig(
        symbol=verified_symbol,
        default_working_hours=default_working_hours,
        before_news_minute=before_news_minute,
        after_news_minute=after_news_minute
    )
    bean_rules = Rules(news_manager, logger, bean_rules_config)

    # Initialize the strategy
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

    bean_strategy = TraderManager(platform, logger, bean_rules, repo, bean_config_calculator)

    hist_data = platform.historic_data(startDate, endDate, symbol)
    for tick in hist_data:
        tick = (tick[0], tick[1], tick[2], tick[3])
        bean_strategy.on_tick(tick)

    result = analyzer(output_file_path)
    return result


def analyzer(file_path: str):
    # Step 1: Read the JSON file
    with open(file_path, mode="r+", encoding='utf-8', errors='ignore') as file:
        data = json.load(file)

    box_durations = []
    order_durations = []
    all_orders_count = 0
    active_index_map = {}

    for item in data:
        box_start_time = datetime.fromisoformat(item['started_at'])
        box_end_time = datetime.fromisoformat(item['ended_at'])
        box_duration = (box_end_time - box_start_time).total_seconds() / 60  # Convert to minutes
        box_durations.append(box_duration)

        if item['active_index'] > 20:
            if item['active_index'] not in active_index_map:
                active_index_map[item['active_index']] = []
            active_index_map[item['active_index']].append(item['started_at'])

        for order in item['orders']:
            all_orders_count += 1
            order_start_time = datetime.fromisoformat(order['started_at'])
            order_end_time = datetime.fromisoformat(order['ended_at'])
            order_duration = (order_end_time - order_start_time).total_seconds() / 60  # Convert to minutes
            order_durations.append(order_duration)

    # Step 3: Calculate max, min, and average durations
    max_box_duration = max(box_durations)
    avg_box_duration = sum(box_durations) / len(box_durations)

    max_order_duration = max(order_durations)
    avg_order_duration = sum(order_durations) / len(order_durations)

    # Step 4: Calculate total number of boxes and max/min order number
    box_total_number = len(data)
    avg_order_number = all_orders_count / box_total_number

    result = {
        "MAX_BOX_DURATION": round(max_box_duration),
        "AVG_BOX_DURATION": round(avg_box_duration),
        "MAX_ORDER_DURATION": round(max_order_duration),
        "AVG_ORDER_DURATION": round(avg_order_duration),
        "BOX_TOTAL_NUMBER": round(box_total_number),
        "AVG_ORDER_NUMBER": round(avg_order_number),
        "ACTIVE_INDEX_MAP": active_index_map
    }

    # Output the result
    return result
