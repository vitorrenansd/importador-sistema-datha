import sys
from configparser import ConfigParser
from pathlib import Path

config = ConfigParser()


def get_base_path():
    # PyInstaller (exe)
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    # desenvolvimento
    return Path(__file__).resolve().parent


config_path = get_base_path() / "config_importador.ini"

if not config_path.exists():
    raise FileNotFoundError(
        f"Arquivo de configuração não encontrado: {config_path}"
    )

config.read(config_path, encoding="utf-8")


def get_firebird_config():
    return {
        "host": config.get("FIREBIRD", "host"),
        "port": config.get("FIREBIRD", "port"),
        "database": config.get("FIREBIRD", "database"),
        "user": config.get("FIREBIRD", "user"),
        "password": config.get("FIREBIRD", "password"),
        "charset": config.get("FIREBIRD", "charset", fallback="UTF8"),
    }

def get_postgres_config():
    return {
        "host": config.get("POSTGRES", "host"),
        "port": config.getint("POSTGRES", "port"),
        "database": config.get("POSTGRES", "database"),
        "user": config.get("POSTGRES", "user"),
        "password": config.get("POSTGRES", "password"),
    }
