import logging

import pytest
import sys

from testutils.logger_utils import configure_logging_from_toml



@pytest.fixture(name="logger_config", scope="session", autouse=True, )
def create_logger_config_fixture():
    """Fixture to configure the logger for tests."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - DockDNS - %(levelname)s - %(message)s',
        handlers=[handler]
    )

    configure_logging_from_toml('logger-config.toml')

    yield
