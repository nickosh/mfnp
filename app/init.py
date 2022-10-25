from pathlib import Path

from .logger import LoggerHandler

log = LoggerHandler.new(__name__)

version = "v0.1.0"
workdir = Path(__file__).resolve().parents[1]


log.info("Init completed")
