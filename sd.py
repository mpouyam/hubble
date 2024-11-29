from datetime import datetime, timedelta
import pytz

# Define trading sessions and their active currency pairs
TRADING_SESSIONS = {
    "Sydney": {
        "start": 21,  # Start time in UTC (9:00 PM)
        "end": 6,     # End time in UTC (6:00 AM)
        "pairs": {"AUD/USD", "NZD/USD", "AUD/JPY", "EUR/AUD", "GBP/AUD"}
    },
    "Tokyo": {
        "start": 0,   # Start time in UTC (12:00 AM)
        "end": 9,     # End time in UTC (9:00 AM)
        "pairs": {"USD/JPY", "EUR/JPY", "AUD/JPY", "NZD/JPY", "GBP/JPY"}
    },
    "London": {
        "start": 7,   # Start time in UTC (7:00 AM)
        "end": 16,    # End time in UTC (4:00 PM)
        "pairs": {"EUR/USD", "GBP/USD", "USD/CHF", "EUR/GBP", "EUR/CHF"}
    },
    "New York": {
        "start": 13,  # Start time in UTC (1:00 PM)
        "end": 22,    # End time in UTC (10:00 PM)
        "pairs": {"EUR/USD", "GBP/USD", "USD/JPY", "USD/CAD", "AUD/USD"}
    },
    "ALL": {
        "start": 0,   # Always active, 24 hours
        "end": 24,    # Until midnight of the next day
        "pairs": {"BTC/USD", "ETH/USD", "XRP/USD"}  # Example: Cryptocurrency pairs
    }
}

def is_symbol_active(symbol, timestamp, margin_minutes=0):
    """
    Check if the given symbol is active during its associated market session at the given timestamp.
    
    Parameters:
    - symbol (str): The currency pair to check (e.g., "EUR/USD").
    - timestamp (datetime): The timestamp in UTC to check.
    - margin_minutes (int): Minutes to extend the session's start and end times for flexibility.
    
    Returns:
    - str: The session name if the symbol is active, otherwise None.
    """
    # Ensure the timestamp is in UTC and timezone-aware
    if timestamp.tzinfo is None or timestamp.tzinfo != pytz.UTC:
        raise ValueError("The timestamp must be timezone-aware and in UTC.")

    # Iterate through each session
    for session_name, session_data in TRADING_SESSIONS.items():
        session_start = session_data["start"]
        session_end = session_data["end"]
        session_pairs = session_data["pairs"]

        # Check if the symbol belongs to the session
        if symbol not in session_pairs:
            continue

        # Handle the ALL session which is always active
        if session_name == "ALL":
            return session_name

        # Calculate session start and end times with margins
        utc = pytz.UTC
        start_time = (datetime.combine(timestamp.date(), datetime.min.time(), tzinfo=utc) + 
                      timedelta(hours=session_start) - timedelta(minutes=margin_minutes))
        end_time = (datetime.combine(timestamp.date(), datetime.min.time(), tzinfo=utc) + 
                    timedelta(hours=session_end) + timedelta(minutes=margin_minutes))

        # Handle sessions that span midnight
        if session_start > session_end:
            # If session spans midnight, the condition splits into two parts
            if timestamp >= start_time or timestamp <= end_time:
                return session_name
        else:
            # Regular session within the same calendar day
            if start_time <= timestamp <= end_time:
                return session_name

    return None

# Example usage
if __name__ == "__main__":
    # Convert Unix timestamp to a timezone-aware datetime object
    unix_timestamp = "1731682322"  # Example tick timestamp
    example_timestamp = datetime.fromtimestamp(int(unix_timestamp), pytz.UTC)  # Convert to UTC datetime
    symbol_to_check = "BTC/USD"
    print(example_timestamp)
    session = is_symbol_active(symbol_to_check, example_timestamp, margin_minutes=30)
    if session:
        print(f"The symbol {symbol_to_check} is active in the {session} session.")
    else:
        print(f"The symbol {symbol_to_check} is not active in any session.")
