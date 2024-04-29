import logging
import colorlog
import pytz
from datetime import datetime

def logger(name):
    """
    Sets up a logger with colored output and timestamp.
    """
    formatter = IranTimeFormatter(
        '%(log_color)s%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',   # SL touches
            'ERROR': 'red',
            'CRITICAL': 'blue',    # TP touched
            'STATE': 'white'
        }
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = colorlog.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


class IranTimeFormatter(colorlog.ColoredFormatter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.iran_tz = pytz.timezone('Asia/Tehran')

    def formatTime(self, record, datefmt=None):
        ct = datetime.fromtimestamp(record.created, self.iran_tz)
        if datefmt:
            s = ct.strftime(datefmt)
        else:
            try:
                s = ct.isoformat(timespec='milliseconds')
            except TypeError:
                s = ct.isoformat()
        return s