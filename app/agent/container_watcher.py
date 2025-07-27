import threading

import docker
import time
from docker import DockerClient

from agent.dockdns_config import DockDNSConfig
from dns.manager.pihole.pihole_client import DNSRecord
from domain.container_wraper import ContainerWrapper


def get_dns_record(wrapper: ContainerWrapper) -> DNSRecord:
    """
    Extracts the DNS record from the container wrapper.
    """
    hostname = wrapper.target_hostname
    source_ip = wrapper.source_ip
    source_port = wrapper.source_port

    if not hostname or not source_ip or not source_port:
        raise ValueError(f"Invalid DNS record for {wrapper}")

    return DNSRecord(hostname, source_ip, source_port)


def process_container(wrapper: ContainerWrapper, config: DockDNSConfig):
    dns_record = get_dns_record(wrapper)

    if config.dry_run:
        print(f"[DRY RUN] Would process container {wrapper} with DNS record {dns_record}")
        # return

    # render_traefik_config(wrapper, dns_record)


def init_existing_containers(client: DockerClient, config: DockDNSConfig):
    print("[INIT] Checking existing containers...")
    for container in client.containers.list(filters={"status": "running"}):
        wrapper = ContainerWrapper(container.labels)
        if wrapper.disabled:
            print(f"[INIT] DockDNS disabled for {wrapper}. Skipping.")
            continue
        process_container(wrapper, config)


def destroy_container(wrapper: ContainerWrapper, config: DockDNSConfig):
    dns_record = get_dns_record(wrapper)

    if config.dry_run:
        print(f"[DRY RUN] Would destroy container {wrapper} with DNS record {dns_record}")
        # return

    # delete_traefik_config(wrapper)


class DockerWatcher:
    __running = True

    def __init__(self, dock_dn_config: DockDNSConfig):
        self.dock_dn_config = dock_dn_config
        self.__client: DockerClient = docker.DockerClient(base_url=dock_dn_config.docker_url)
        self.__thread = None

    def start(self):
        if self.__thread:
            print("[ERROR] Docker watcher is already running.")
            return
        self.__thread = threading.Thread(name="DockerWatcher", target=self.__watch_docker_events, daemon=True)
        self.__thread.start()

    def __watch_docker_events(self):
        init_existing_containers(self.__client, self.dock_dn_config)
        print("[START] Agent watching Docker events...")
        while self.__running:
            try:
                for event in self.__client.events(decode=True):
                    if event.get("Type") == "container":
                        action = event.get("Action")
                        container = self.__client.containers.get(event["id"])
                        wrapper = ContainerWrapper(container)
                        if action == "start":
                            process_container(wrapper, self.dock_dn_config)
                        elif action in ["die", "stop", "destroy"]:
                            destroy_container(wrapper, self.dock_dn_config)

                time.sleep(0.5)  # Polling interval
            except Exception as e:
                print(f"[ERROR] Main loop failed: {e}")
                time.sleep(5)

    def stop(self):
        print("[STOP] Stopping Docker watcher...")
        self.__running = False
        self.__thread.join()
        self.__thread = None
        print("[STOP] Docker watcher stopped.")
