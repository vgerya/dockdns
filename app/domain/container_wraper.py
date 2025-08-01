import os
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
    def target_hostname(self) -> str:
        return self.labels_dict.get(ContainerLabelOptions.HOSTNAME.value) or self.name

    @property
    def source_port(self) -> int:
        return (self.labels_dict.get(ContainerLabelOptions.PORT.value)
                or next(iter(self.__container.attrs.get("Config", {}).get("ExposedPorts", {})), None)
                or 80
                )

    @property
    def source_ip(self) -> Optional[str]:
        try:
            ip = self.__container.attrs["NetworkSettings"]["IPAddress"]
            if not ip and self.__container.attrs["HostConfig"]["NetworkMode"] == "host":
                ip = os.popen("hostname -I").read().split()[0]

            import socket

            host_ip = socket.gethostbyname("host.docker.internal")

            print(host_ip)

            return ip.strip() if ip else None
        except Exception:
            return None

    def __str__(self):
        return (
            f"Container(name={self.name}, id={self.id}, image={self.__container.image}, "
            f"disabled={self.disabled}, target_hostname={self.target_hostname}, "
            f"source_port={self.source_port}, source_ip={self.source_ip})"
        )
