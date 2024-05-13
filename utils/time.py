from datetime import datetime
import pytz

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
