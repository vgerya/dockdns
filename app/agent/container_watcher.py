import logging
import threading

import docker
import time
from docker import DockerClient

from agent.dockdns_config import DockDNSConfig
from dns.manager.pihole.pihole_client import DNSRecord
from dns.manager.reverse_proxy.traefik_client import render_traefik_config
from domain.container_wraper import ContainerWrapper, ContainerLabelOptions
from utils import os_utils

logger = logging.getLogger('dockdns.main')


def get_dns_record(wrapper: ContainerWrapper, config: DockDNSConfig, ) -> DNSRecord:
    """
    Extracts the DNS record from the container wrapper or configs/labels.
    """
    source_ip = (
            config.dns_ip
            or wrapper.network_settings_ip_address
            or (os_utils.get_system_ip_address() if wrapper.is_network_host_mode() else None)
            or os_utils.get_internal_docker_host()
    )
    if not source_ip:
        raise ValueError(f"Container {wrapper} does not have a valid source IP.")

    source_port = wrapper.labeled_port or wrapper.exposed_ports[0] if wrapper.exposed_ports else None
    if not source_port:
        raise ValueError(
            f"Container {wrapper} does not have a valid source port. "
            f"Port must be defined either in exposed ports or via '{ContainerLabelOptions.PORT}' label.",
        )

    hostname = wrapper.labeled_hostname or wrapper.name

    if not hostname or not source_ip or not source_port:
        raise ValueError(f"Invalid DNS record for {wrapper}")

    return DNSRecord(hostname, source_ip, int(source_port))


def process_container(
        wrapper: ContainerWrapper,
        config: DockDNSConfig,
):
    dns_record = get_dns_record(wrapper, config)

    if config.dry_run:
        logger.info(f"[DRY RUN] Would process container {wrapper} with DNS record {dns_record}")
        # return

    render_traefik_config(
        container=wrapper,
        dns_record=dns_record,
        dockdns_config=config,
    )


def init_existing_containers(client: DockerClient, config: DockDNSConfig,):
    logger.info("[INIT] Checking existing containers...")
    for container in client.containers.list(filters={"status": "running"}):
        try:
            wrapper = ContainerWrapper(container.labels)
            if wrapper.disabled:
                logger.info(f"[INIT] DockDNS disabled for {wrapper}. Skipping.")
                continue
            process_container(
                wrapper=wrapper,
                config=config,
            )
        except Exception as e:
            logger.error(f"[INIT] Error processing container {container.id}: {e}", exc_info=True)


def destroy_container(wrapper: ContainerWrapper, config: DockDNSConfig):
    dns_record = get_dns_record(wrapper, config)

    if config.dry_run:
        logger.info(f"[DRY RUN] Would destroy container {wrapper} with DNS record {dns_record}")
        # return

    # delete_traefik_config(wrapper)


class DockerWatcher:
    __running = True

    def __init__(self, dock_dn_config: DockDNSConfig):
        self.dock_dn_config = dock_dn_config
        self.__client: DockerClient = docker.DockerClient(base_url=dock_dn_config.docker_url, timeout=0.5, )
        self.__thread = None

    def start(self):
        if self.__thread:
            logger.error("[ERROR] Docker watcher is already running.")
            return
        self.__thread = threading.Thread(name="DockerWatcherThread", target=self.__watch_docker_events, daemon=True, )
        self.__thread.start()

    def __watch_docker_events(self):
        init_existing_containers(self.__client, self.dock_dn_config)
        logger.info(f"[START] Agent watching Docker events, config={self.dock_dn_config}...")
        while self.__running:
            try:
                for event in self.__client.events(decode=True):
                    if event.get("Type") == "container":
                        action = event.get("Action")
                        container = self.__client.containers.get(event["id"])
                        wrapper = ContainerWrapper(container)
                        if action == "start":
                            process_container(
                                wrapper=wrapper,
                                config=self.dock_dn_config,
                            )
                        elif action in ["die", "stop", "destroy"]:
                            destroy_container(wrapper, self.dock_dn_config)

                time.sleep(0.5)  # Polling interval
            except Exception as e:
                logger.error(f"[ERROR] Error in main loop: {e}. Continue to work...", exc_info=True)
        logger.info("[STOP] Agent stopped watching Docker events.")

    def stop(self):
        logger.info("[STOP] Stopping Docker watcher...")
        self.__running = False
        self.__thread.join()
        self.__thread = None
        logger.info("[STOP] Docker watcher stopped.")
