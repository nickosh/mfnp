import logging as pylogger
import sys

from dearpygui_ext.logger import mvLogger as uiLogger

pylogger.basicConfig(stream=sys.stdout, level=pylogger.DEBUG)


def singleton(cls, *args, **kw):
    instances: dict = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


@singleton
class LoggerHandler(object):
    def __init__(
        self, name: str = "mainlogger", level: str = "debug", uilog: uiLogger = None
    ):
        """Create new logger object.

        Args:
            name (str): name of logger.
            level (str): set lever for logger, can be "info", "warn", "error" or "debug".
            parent (str): set parent dearpygui window

        Raises:
            ValueError: if logger level is unknown.

        Returns:
            obj: return logger object.
        """
        self.pylog: pylogger = pylogger.getLogger(name)
        self.uilog: uiLogger = uilog
        if level == "info":
            self.pylog.setLevel(pylogger.INFO)
        elif level == "warn":
            self.pylog.setLevel(pylogger.WARNING)
        elif level == "error":
            self.pylog.setLevel(pylogger.ERROR)
        elif level == "debug":
            self.pylog.setLevel(pylogger.DEBUG)
        else:
            raise ValueError("Unknown logger level")

    def debug(self, message: str):
        self.pylog.debug(message)
        self.uilog.log_debug(message)

    def info(self, message: str):
        self.pylog.info(message)
        self.uilog.log_info(message)

    def warning(self, message: str):
        self.pylog.warning(message)
        self.uilog.log_warning(message)

    def error(self, message: str):
        self.pylog.error(message)
        self.uilog.log_error(message)

    def critical(self, message: str):
        self.pylog.critical(message)
        self.uilog.log_critical(message)
