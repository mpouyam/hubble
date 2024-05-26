class NullLogger:
    """
    Null logger implementation that does not log anything.
    """
    def __init__(self, name):
        pass

    def debug(self, msg, *args, **kwargs):
        pass

    def info(self, msg, *args, **kwargs):
        pass

    def warning(self, msg, *args, **kwargs):
        pass

    def error(self, msg, *args, **kwargs):
        pass

    def critical(self, msg, *args, **kwargs):
        pass

# Usage:
# Replace calls to logger() with NullLogger() in your test environment.
# Example:
# my_logger = NullLogger('test_logger')
