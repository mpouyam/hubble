from datetime import datetime
import pytz


def now_time_iran(timestamp=None):
    # Get the current time in UTC timezone if no timestamp is provided
    if timestamp is None:
        current_time_utc = datetime.utcnow()  # - timedelta(hours=3)

    else:
        # Convert the provided timestamp to datetime object
        current_time_utc = datetime.utcfromtimestamp(timestamp)  # - timedelta(hours=3)

    # Convert the UTC time to the desired timezone (Asia/Tehran)
    # tehran_tz = pytz.timezone('Asia/Tehran')
    current_time_iran = current_time_utc.replace(tzinfo=pytz.utc)  # .astimezone(tehran_tz)

    # Format the time string
    return current_time_iran.strftime("%Y-%m-%d %H:%M:%S")


def format_gmt_time(timestamp=None):
    # Define GMT and Tehran timezones
    gmt_tz = pytz.timezone('GMT')

    # Get the current time in GMT timezone if no timestamp is provided
    if timestamp is None:
        current_time_gmt = datetime.now(gmt_tz)
    else:
        # Convert the provided timestamp to datetime object in GMT
        current_time_gmt = datetime.fromtimestamp(timestamp, tz=gmt_tz)

    # Format the time string
    return current_time_gmt.strftime("%Y-%m-%d %H:%M:%S")


def format_datetime_tuple(dt: datetime):
    return (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
