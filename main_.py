#!/usr/bin/env python3
"""
DockDNS - Automatic DNS management for Docker containers with Pi-hole
Monitors Docker events and automatically creates/removes DNS records in Pi-hole.
"""

import hashlib
import json
import logging
import os
import socket
from typing import Optional, Dict, List

import docker
import fcntl
import requests
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - DockDNS - %(levelname)s - %(message)s')
logger = logging.getLogger('dockdns')


class PiHoleDNSManager:
    def __init__(self, pihole_url: str, api_token: Optional[str] = None):
        self.pihole_url = pihole_url.rstrip('/')
        self.api_token = api_token
        self.session = requests.Session()

    def add_dns_record(self, hostname: str, ip: str) -> bool:
        try:
            url = f"{self.pihole_url}/admin/scripts/pi-hole/php/customdns.php"
            data = {
                'action': 'add',
                'domain': hostname,
                'ip': ip
            }
            if self.api_token:
                data['auth'] = self.api_token

            response = self.session.post(url, data=data)
            response.raise_for_status()
            logger.info(f"Added DNS record: {hostname} -> {ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to add DNS record {hostname} -> {ip}: {e}")
            return False

    def remove_dns_record(self, hostname: str, ip: str) -> bool:
        try:
            url = f"{self.pihole_url}/admin/scripts/pi-hole/php/customdns.php"
            data = {
                'action': 'delete',
                'domain': hostname,
                'ip': ip
            }
            if self.api_token:
                data['auth'] = self.api_token

            response = self.session.post(url, data=data)
            response.raise_for_status()
            logger.info(f"Removed DNS record: {hostname} -> {ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove DNS record {hostname} -> {ip}: {e}")
            return False

    def get_dns_records(self) -> List[Dict[str, str]]:
        try:
            url = f"{self.pihole_url}/admin/scripts/pi-hole/php/customdns.php"
            params = {'action': 'get'}
            if self.api_token:
                params['auth'] = self.api_token

            response = self.session.get(url, params=params)
            response.raise_for_status()

            records = []
            for line in response.text.strip().split('\n'):
                if line and ' ' in line:
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        records.append({'ip': parts[0], 'domain': parts[1]})
            return records
        except Exception as e:
            logger.error(f"Failed to get DNS records: {e}")
            return []


class DockerEventMonitor:
    def __init__(
            self, dns_manager: PiHoleDNSManager, dns_label: str = 'dns.hostname',
            base_domain: str = '', docker_host_ip: Optional[str] = None,
            instance_id: Optional[str] = None, state_dir: str = '/shared-state',
            env_prefix: str = '',
    ):
        self.client = docker.from_env()
        self.dns_manager = dns_manager
        self.dns_label = dns_label
        self.base_domain = base_domain
        self.docker_host_ip = docker_host_ip or self._get_docker_host_ip()
        self.instance_id = instance_id or self._generate_instance_id()
        self.env_prefix = env_prefix or self._generate_env_prefix()
        self.state_dir = state_dir
        self.state_file = os.path.join(state_dir, 'dockdns-shared-state.json')
        self.container_dns_records: Dict[str, tuple] = {}
        self._load_state()

    def _generate_instance_id(self) -> str:
        hostname = socket.gethostname()
        docker_host = os.getenv('DOCKER_HOST', 'unix:///var/run/docker.sock')
        unique_string = f"{hostname}-{docker_host}-{self.base_domain}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:8]

    def _generate_env_prefix(self) -> str:
        hostname = socket.gethostname()
        # Clean hostname for DNS compatibility (remove special chars, lowercase)
        clean_hostname = ''.join(c for c in hostname if c.isalnum() or c == '-').lower().strip('-')
        if len(clean_hostname) > 10:
            clean_hostname = clean_hostname[:10]
        return clean_hostname or 'env'

    def _get_docker_host_ip(self) -> str:
        try:
            docker_host = os.getenv('DOCKER_HOST', 'unix:///var/run/docker.sock')
            if docker_host.startswith('tcp://'):
                host = docker_host.replace('tcp://', '').split(':')[0]
                return host
            else:
                return socket.gethostbyname(socket.gethostname())
        except Exception:
            return '127.0.0.1'

    def _load_shared_state(self) -> Dict:
        """Load the shared state file with file locking"""
        try:
            os.makedirs(self.state_dir, exist_ok=True)
            if not os.path.exists(self.state_file):
                return {'instances': {}, 'last_updated': time.time()}

            with open(self.state_file, 'r') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_SH)
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load shared state from {self.state_file}: {e}")
            return {'instances': {}, 'last_updated': time.time()}

    def _save_shared_state(self, shared_state: Dict):
        """Save the shared state file with file locking"""
        try:
            os.makedirs(self.state_dir, exist_ok=True)
            shared_state['last_updated'] = time.time()

            with open(self.state_file, 'w') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                json.dump(shared_state, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save shared state to {self.state_file}: {e}")

    def _load_state(self):
        """Load this instance's records from shared state"""
        try:
            shared_state = self._load_shared_state()
            instance_data = shared_state.get('instances', {}).get(self.instance_id, {})

            self.container_dns_records = {}
            for container_id, record_data in instance_data.get('records', {}).items():
                self.container_dns_records[container_id] = tuple(record_data)

            logger.info(f"Loaded {len(self.container_dns_records)} DNS records for instance {self.instance_id}")
        except Exception as e:
            logger.warning(f"Failed to load state for instance {self.instance_id}: {e}")

    def _save_state(self):
        """Save this instance's records to shared state"""
        try:
            shared_state = self._load_shared_state()

            if 'instances' not in shared_state:
                shared_state['instances'] = {}

            shared_state['instances'][self.instance_id] = {
                'hostname': socket.gethostname(),
                'base_domain': self.base_domain,
                'env_prefix': self.env_prefix,
                'last_seen': time.time(),
                'records': {k: list(v) for k, v in self.container_dns_records.items()}
            }

            self._save_shared_state(shared_state)
        except Exception as e:
            logger.warning(f"Failed to save state for instance {self.instance_id}: {e}")

    def get_container_hostname(self, container) -> Optional[str]:
        labels = container.labels or {}

        if self.dns_label in labels:
            hostname = labels[self.dns_label]
        else:
            container_name = container.name
            if not container_name or container_name.startswith('/'):
                return None
            hostname = container_name.lstrip('/')

        # Add environment prefix to avoid conflicts across Docker environments
        if self.env_prefix and not hostname.startswith(f"{self.env_prefix}-"):
            hostname = f"{self.env_prefix}-{hostname}"

        if self.base_domain and '{container-name}' in self.base_domain:
            hostname = self.base_domain.replace('{container-name}', hostname)
        elif self.base_domain and '{env-prefix}' in self.base_domain:
            hostname = self.base_domain.replace('{env-prefix}', self.env_prefix).replace(
                '{container-name}',
                hostname.replace(f"{self.env_prefix}-", ""),
            )
        elif self.base_domain:
            hostname = f"{hostname}.{self.base_domain}"

        return hostname

    def get_container_ip(self, container) -> Optional[str]:
        try:
            container.reload()
            network_mode = container.attrs.get('HostConfig', {}).get('NetworkMode', '')

            if network_mode == 'host':
                return self.docker_host_ip

            networks = container.attrs['NetworkSettings']['Networks']
            for network_name, network_info in networks.items():
                if network_info.get('IPAddress'):
                    return network_info['IPAddress']

        except Exception as e:
            logger.error(f"Failed to get IP for container {container.name}: {e}")
        return None

    def handle_container_start(self, container):
        hostname = self.get_container_hostname(container)
        if not hostname:
            logger.debug(f"No hostname found for container {container.name}")
            return

        ip = self.get_container_ip(container)
        if not ip:
            logger.warning(f"No IP found for container {container.name}")
            return

        if self.dns_manager.add_dns_record(hostname, ip):
            self.container_dns_records[container.id] = (hostname, ip)
            self._save_state()

    def handle_container_stop(self, container_id: str):
        if container_id in self.container_dns_records:
            hostname, ip = self.container_dns_records[container_id]
            if self.dns_manager.remove_dns_record(hostname, ip):
                del self.container_dns_records[container_id]
                self._save_state()

    def cleanup_stale_dns_records(self):
        logger.info(f"Cleaning up stale DNS records for instance {self.instance_id}...")
        try:
            running_containers = self.client.containers.list(filters={'status': 'running'})
            current_container_ids = {c.id for c in running_containers}

            stale_records = []
            for container_id, (hostname, ip) in list(self.container_dns_records.items()):
                if container_id not in current_container_ids:
                    stale_records.append((container_id, hostname, ip))

            for container_id, hostname, ip in stale_records:
                logger.info(f"Removing stale DNS record managed by this instance: {hostname} -> {ip}")
                if self.dns_manager.remove_dns_record(hostname, ip):
                    del self.container_dns_records[container_id]

            if stale_records:
                self._save_state()
                logger.info(f"Cleaned up {len(stale_records)} stale DNS records")

            self._cleanup_inactive_instances()

        except Exception as e:
            logger.error(f"Failed to cleanup stale DNS records: {e}")

    def _cleanup_inactive_instances(self):
        """Remove DNS records from instances that haven't been seen for too long"""
        try:
            shared_state = self._load_shared_state()
            current_time = time.time()
            inactive_threshold = 300  # 5 minutes

            inactive_instances = []
            for instance_id, instance_data in shared_state.get('instances', {}).items():
                if instance_id == self.instance_id:
                    continue

                last_seen = instance_data.get('last_seen', 0)
                if current_time - last_seen > inactive_threshold:
                    inactive_instances.append(instance_id)

            if inactive_instances:
                logger.info(f"Found {len(inactive_instances)} inactive instances, cleaning up their DNS records")

                for instance_id in inactive_instances:
                    instance_data = shared_state['instances'][instance_id]
                    for container_id, record_data in instance_data.get('records', {}).items():
                        hostname, ip = record_data
                        logger.info(f"Removing DNS record from inactive instance {instance_id}: {hostname} -> {ip}")
                        self.dns_manager.remove_dns_record(hostname, ip)

                    del shared_state['instances'][instance_id]

                self._save_shared_state(shared_state)
                logger.info(f"Cleaned up {len(inactive_instances)} inactive instances")

        except Exception as e:
            logger.error(f"Failed to cleanup inactive instances: {e}")

    def sync_existing_containers(self):
        logger.info("Syncing existing running containers...")
        try:
            containers = self.client.containers.list(filters={'status': 'running'})
            for container in containers:
                self.handle_container_start(container)
        except Exception as e:
            logger.error(f"Failed to sync existing containers: {e}")

    def monitor_events(self):
        logger.info("Starting Docker event monitoring...")
        self.cleanup_stale_dns_records()
        self.sync_existing_containers()

        try:
            for event in self.client.events(decode=True):
                if event.get('Type') == 'container':
                    action = event.get('Action')
                    container_id = event.get('id')

                    if action == 'start':
                        try:
                            container = self.client.containers.get(container_id)
                            self.handle_container_start(container)
                        except docker.errors.NotFound:
                            logger.warning(f"Container {container_id} not found")

                    elif action in ['stop', 'die', 'kill']:
                        self.handle_container_stop(container_id)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.error(f"Error monitoring events: {e}")
            raise


def main():
    pihole_url = os.getenv('PIHOLE_URL', 'http://pihole.local')
    api_token = os.getenv('PIHOLE_API_TOKEN')
    dns_label = os.getenv('DNS_LABEL', 'dns.hostname')
    base_domain = os.getenv('BASE_DOMAIN', '')
    docker_host_ip = os.getenv('DOCKER_HOST_IP')
    instance_id = os.getenv('INSTANCE_ID')
    state_dir = os.getenv('STATE_DIR', '/shared-state')
    env_prefix = os.getenv('ENV_PREFIX', '')

    if not pihole_url:
        logger.error("PIHOLE_URL environment variable is required")
        return 1

    logger.info("🚀 Starting DockDNS - Automatic DNS for Docker containers")
    logger.info(f"📡 Pi-hole server: {pihole_url}")
    logger.info(f"🏷️  DNS label: {dns_label}")
    logger.info(f"💾 Shared state directory: {state_dir}")
    if base_domain:
        logger.info(f"🌐 Base domain: {base_domain}")
    if docker_host_ip:
        logger.info(f"🖥️  Docker host IP: {docker_host_ip}")

    dns_manager = PiHoleDNSManager(pihole_url, api_token)
    monitor = DockerEventMonitor(
        dns_manager,
        dns_label,
        base_domain,
        docker_host_ip,
        instance_id,
        state_dir,
        env_prefix,
    )

    logger.info(f"🆔 Service instance ID: {monitor.instance_id}")
    logger.info(f"🏢 Environment prefix: {monitor.env_prefix}")

    try:
        monitor.monitor_events()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1

    return 0


if __name__ == '__main__':
    exit(main())