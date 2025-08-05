import pytest

from domain.container_wraper import ContainerWrapper
from agent.dockdns_config import DockDNSConfig

class DummyContainer:
    def __init__(self, name="test", id="abc123", labels=None, attrs=None, image="img"):
        self.name = name
        self.id = id
        self.labels = labels or {}
        self.attrs = attrs or {"Config": {"ExposedPorts": {"80/tcp": {}}}, "NetworkSettings": {"IPAddress": "1.2.3.4"}, "HostConfig": {"NetworkMode": "bridge"}}
        self.image = image

@pytest.fixture
def config():
    return DockDNSConfig()

@pytest.fixture
def container():
    return DummyContainer()

@pytest.fixture
def wrapper(container):
    return ContainerWrapper(container)
