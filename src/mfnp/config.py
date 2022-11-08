from pathlib import Path
import tomllib
from .logger import LoggerHandler

log = LoggerHandler.new(__name__)

workdir = Path(__file__).resolve().parents[1]
pyproject = tomllib.loads(Path(workdir, "pyproject.toml").read_text())
version = pyproject["project"]["version"]


log.info("Init completed")
