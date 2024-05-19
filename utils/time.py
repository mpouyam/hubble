from datetime import datetime , timedelta
import pytz
from typing import List, Tuple

def now_time_iran():
    # Get the current time in UTC timezone
    current_time_utc = datetime.utcnow()  #- timedelta(hours=1)
    
    # Convert the UTC time to the desired timezone (Asia/Tehran)
    tehran_tz = pytz.timezone('Asia/Tehran')
    current_time_iran = current_time_utc.replace(tzinfo=pytz.utc).astimezone(tehran_tz)
    
    # Format the time string
    return current_time_iran.strftime("%Y-%m-%d %H:%M:%S")

def is_market_closed() -> bool:
    
    ny_timezone = pytz.timezone('America/New_York')
    # Get the current time in New York
    current_time = datetime.now(ny_timezone)

    # Check if it's a weekend
    if current_time.weekday() >= 5:  # Saturday (5) or Sunday (6)
        return True

    # Check if it's before 5 p.m. on Sunday
    if current_time.weekday() == 6 and current_time.hour < 17:  # Sunday and before 5 p.m.
        return True

    # Check if it's after 5 p.m. on Sunday
    if current_time.weekday() == 6 and current_time.hour >= 17:  # Sunday and after 5 p.m.
        return False

    # Market is open on weekdays
    return False


def format_datetime_tuple(dt: datetime) -> Tuple[int, int, int, int, int, int]:
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)

def split_into_weeks(
    sdate: str, edate: str
) -> List[Tuple[datetime, datetime]]:

    start_date = datetime.strptime(sdate, "%Y-%m-%d-%H-%M-%S")
    end_date = datetime.strptime(edate, "%Y-%m-%d-%H-%M-%S")



    if (end_date - start_date).days < 7:
        return [(start_date, end_date)]

    current_date = start_date
    weeks = []
    week = []
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Skip weekends
            week.append(current_date)
        if len(week) == 5 or (
            current_date.weekday() == 4 and current_date + timedelta(days=2) > end_date
        ):
            # Week is full or the end of the date range
            weeks.append((week[0], week[-1]))
            week = []
        current_date += timedelta(days=1)
    if week:
        weeks.append((week[0], week[-1]))
    
    

    
    weeks_formatted = [
        (format_datetime_tuple(start), format_datetime_tuple(end))
        for start, end in weeks
    ]
    
    return weeks_formatted


