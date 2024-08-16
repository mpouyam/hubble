from dataclasses import dataclass
from enum import StrEnum

from .box import BoxSignalData


@dataclass
class TraderSignalData(BoxSignalData):
    pass

    # # private method
    # def __is_working_hours(self) -> bool:
    #     # Define the GMT timezone
    #     gmt_tz = pytz.timezone('GMT')
    #
    #     # Convert self.clock (which is a timestamp) to a datetime object in GMT timezone
    #     timestamp_time = datetime.fromtimestamp(self.clock, tz=gmt_tz)
    #
    #     # Get the current day of the week (Monday=0, Sunday=6)
    #     current_day = timestamp_time.weekday()
    #
    #     # Get working hours for the current day, or default if not specified
    #     working_hours = self.config["trader_config"]["working_hours"].get(
    #         current_day,
    #         self.config["trader_config"]["default_working_hours"]
    #     )
    #
    #     # Parse start and end hours as floats
    #     start_hour, end_hour = working_hours
    #
    #     # Extract hour and minute from start_hour and end_hour
    #     start_hour_int = int(start_hour)
    #     start_minute = int(round((start_hour - start_hour_int) * 100))
    #     end_hour_int = int(end_hour)
    #     end_minute = int(round((end_hour - end_hour_int) * 100))
    #
    #     # Define start and end times for the current day's working hours
    #     start_time = datetime.combine(timestamp_time.date(), time(hour=start_hour_int, minute=start_minute))
    #     end_time = datetime.combine(timestamp_time.date(), time(hour=end_hour_int, minute=end_minute))
    #
    #     # Localize start_time and end_time to GMT timezone
    #     start_time = gmt_tz.localize(start_time)
    #     end_time = gmt_tz.localize(end_time)
    #
    #     # Check if the timestamp_time is within working hours
    #     return start_time <= timestamp_time <= end_time
    #
    # def __default_configs(self) -> Config:
    #     return {
    #         "trader_config": {
    #             "default_working_hours": (7.00, 21.00),
    #             "working_hours": {},
    #             "default_not_working_hours": (13.00, 17.00),
    #             "not_working_hours": {},
    #         },
    #         "orders_config": {
    #             "symbol": "GBPUSD_o",
    #             "first_order_signal": "BUY",
    #             "pip_unit": None,
    #             "try_count": 9,
    #             "tp_limit": 6,
    #             "sl_limit": 1,
    #             "base_lot": 0.1,
    #             "growth_factor": 1.3,
    #             "static_vol": {
    #                 1: 0.01,
    #                 2: 0.01,
    #                 3: 0.01,
    #                 4: 0.02,
    #                 5: 0.02,
    #                 6: 0.03,
    #                 7: 0.04,
    #                 8: 0.05,
    #                 9: 0.06,
    #                 10: 0.08,
    #                 11: 0.1
    #             },
    #             "static_tp": {},
    #             "static_sl": {},
    #         }
    #     }
    #


class TraderSignal(StrEnum):
    RUN = "RUN"
    SHUT_DOWN = "SHUT_DOWN"
    ON = "ON"


