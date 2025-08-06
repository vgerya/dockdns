import logging

import tomllib
from typing import List, Tuple


def flatten_loggers_recursively(d: dict, prefix: str = "") -> List[Tuple[str, str]]:
    result = []
    for key, value in d.items():
        new_prefix = f"{prefix}.{key}" if prefix else key
        if isinstance(value, dict):
            if "level" in value and len(value) == 1:
                # Found a logger
                result.append((new_prefix, value["level"]))
            else:
                result.extend(flatten_loggers_recursively(value, new_prefix))

    return result


def configure_logging_from_toml(config_path: str = "logger_config.toml"):
    try:
        with open(config_path, "rb") as file:
            config = tomllib.load(file)
            loggers = config.get("loggers", {})

            logger_tuples = flatten_loggers_recursively(loggers)

            for logger_name, level_str in logger_tuples:
                if logger_name.endswith(".level"):
                    logger_name = logger_name[:-1]

                level = logging.getLevelName(level_str.upper())
                logger = logging.getLogger(logger_name)
                logger.setLevel(level)
                print(f"Set logger level {logger_name}={level_str}")

    except FileNotFoundError:
        print(f"TOML file not found: {config_path}")
    except tomllib.TOMLDecodeError as e:
        print(f"Invalid TOML format: {e}")
    except Exception as e:
        print(f"Error configuring logging: {e}")
