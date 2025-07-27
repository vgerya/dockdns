import hashlib
import json
import logging
import os
import socket
from dataclasses import dataclass
from typing import Dict

import fcntl
import time

from dns.manager.pihole.pihole_client import DNSRecord

logger = logging.getLogger('dns.manager.dns_state')


def _generate_instance_id(self) -> str:
    hostname = socket.gethostname()
    docker_host = os.getenv('DOCKER_HOST', 'unix:///var/run/docker.sock')
    unique_string = f"{hostname}-{docker_host}-{self.base_domain}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:8]


@dataclass
class SharedState:
    hostname: str
    base_domain: str
    env_prefix: str
    last_seen: time
    records: list[DNSRecord]


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
