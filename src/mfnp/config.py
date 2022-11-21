import configparser
from pathlib import Path

from logger import LoggerHandler

log = LoggerHandler(__name__)
workdir = Path(__file__).resolve().parents[0]


def config_init():
    global config, config_path

    config = configparser.ConfigParser()
    config_path = Path(workdir, "config.ini")
    if config_path.exists():
        config.read(config_path)
    else:
        msg = "Can't find config.ini file"
        log.error(msg)
        raise EnvironmentError(msg)


def config_load():
    if config:
        global cfg_app, cfg_remote, cfg_jcl
        cfg_app = config["app"]
        cfg_remote = config["remote_server"]
        cfg_jcl = config["jcl_editor"]


def config_save():
    with config_path.open("w") as configfile:
        config.write(configfile)


config_init()
config_load()
