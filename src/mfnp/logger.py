import logging


class LoggerHandler:
    def new(name: str, level: str = "debug"):
        """Create new logger object.

        Args:
            name (str): name of logger.
            level (str): set lever for logger, can be "info", "warn", "error" or "debug".

        Raises:
            ValueError: if logger level is unknown.

        Returns:
            obj: return logger object.
        """
        logger = logging.getLogger(name)
        if level == "info":
            logger.setLevel(logging.INFO)
        elif level == "warn":
            logger.setLevel(logging.WARNING)
        elif level == "error":
            logger.setLevel(logging.ERROR)
        elif level == "debug":
            logger.setLevel(logging.DEBUG)
        else:
            raise ValueError("Unknown logger level")
        return logger
