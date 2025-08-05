import inspect
from enum import Enum
from typing import Optional


class ContainerLabelOptions(Enum):
    DISABLED = "dockdns.disabled"
    HOSTNAME = "dockdns.target.hostname"
    PORT = "dockdns.source.port"


class ContainerWrapper:
    def __init__(self, container):
        self.__container = container

    @property
    def id(self):
        return self.__container.id

    @property
    def name(self):
        return self.__container.name

    @property
    def labels_dict(self):
        return self.__container.labels

    @property
    def attrs(self):
        return self.__container.attrs

    @property
    def disabled(self) -> bool:
        return self.labels_dict.get(ContainerLabelOptions.DISABLED.value, "false").lower() == "true"

    @property
    def labeled_hostname(self) -> str:
        return self.labels_dict.get(ContainerLabelOptions.HOSTNAME.value)

    @property
    def labeled_port(self) -> Optional[str]:
        return self.labels_dict.get(ContainerLabelOptions.PORT.value)

    @property
    def exposed_ports(self) -> list[str]:
        return self.__container.attrs.get("Config", {}).get("ExposedPorts", []) or []

    @property
    def network_settings_ip_address(self) -> Optional[str]:
        return self.__container.attrs.get("NetworkSettings", {}).get("IPAddress")

    def is_network_host_mode(self):
        return self.__container.attrs.get("HostConfig", {}).get("NetworkMode") == "host"

    def __str__(self):
        members = inspect.getmembers(self.__class__, lambda x: isinstance(x, property))
        properties = [f"{name}={getattr(self, name)}" for name, _ in members]
        return f"ContainerWrapper({', '.join(properties)})"
