import logging, os
from logging.handlers import RotatingFileHandler
from datetime import datetime
from zoneinfo import ZoneInfo

class AppLogger:
    _initialized = False

    @classmethod
    def setup(cls):
        open("app.log", "w").close()
        
        if cls._initialized:
            return

        class WIBFormatter(logging.Formatter):
            def formatTime(self, record, datefmt=None):
                dt = datetime.fromtimestamp(
                    record.created,
                    ZoneInfo("Asia/Jakarta")
                )
                return dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S")

        handler = RotatingFileHandler(
            "app.log",
            maxBytes=1 * 1024 * 1024,  # 1 MB
            backupCount=0             # 1 file saja
        )

        formatter = WIBFormatter(
            "%(asctime)s | %(levelname)s | %(message)s"
        )

        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

        cls._initialized = True
