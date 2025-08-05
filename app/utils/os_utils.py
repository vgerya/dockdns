import logging
import os
import socket
from typing import Optional

logger = logging.getLogger('dockdns.os_utils')


def get_internal_docker_host() -> Optional[str]:
    internal_docker_host = socket.gethostbyname("host.docker.internal")

    logger.debug(f"host.docker.internal IP: {internal_docker_host}")

    return internal_docker_host

def get_system_ip_address() -> str:
    """
    Returns the system's hostname.
    """
    ip = os.popen("hostname -I").read().split()[0]

    logger.debug(f"hostname -I: {ip}")
    return ip

