from pathlib import Path
from pkg_resources import get_distribution

APP_WORKDIR = Path(__file__).resolve().parents[0]
APP_VERSION = get_distribution("mfnp").version
