import logging
from dataclasses import dataclass
from typing import List

import requests

from dns.manager.pihole.config import PiHoleConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - DockDNS - %(levelname)s - %(message)s')
logger = logging.getLogger('dns.manager.pihole_client')


@dataclass
class DNSRecord:
    hostname: str
    ip: str
    port: int


class PiHoleClient:
    def __init__(self, pihole_config: PiHoleConfig):
        self.pihole_config = pihole_config
        self.session = requests.Session()

    def add_dns_record(self, dns_record: DNSRecord) -> bool:
        try:
            url = f"{self.pihole_config.url}/admin/scripts/pi-hole/php/customdns.php"
            data = {
                'action': 'add',
                'domain': dns_record.hostname,
                'ip': dns_record.ip
            }
            if self.pihole_config.api_token:
                data['auth'] = self.pihole_config.api_token

            response = self.session.post(url, data=data)
            response.raise_for_status()
            logger.info(f"Added DNS record: {dns_record}")
            return True
        except Exception as e:
            logger.error(f"Failed to add DNS record {dns_record}: {e}", exc_info=True)
            return False

    def remove_dns_record(self, hostname: str, ip: str) -> bool:
        try:
            url = f"{self.pihole_config.url}/admin/scripts/pi-hole/php/customdns.php"
            data = {
                'action': 'delete',
                'domain': hostname,
                'ip': ip
            }
            if self.pihole_config.api_token:
                data['auth'] = self.pihole_config.api_token

            response = self.session.post(url, data=data)
            response.raise_for_status()
            logger.info(f"Removed DNS record: {hostname} -> {ip}")
            return True
        except Exception as e:
            logger.error(f"Failed to remove DNS record {hostname} -> {ip}: {e}")
            return False

    def get_dns_records(self) -> List[DNSRecord]:
        try:
            url = f"{self.pihole_config.url}/admin/scripts/pi-hole/php/customdns.php"
            params = {'action': 'get'}
            if self.pihole_config.api_token:
                params['auth'] = self.pihole_config.api_token

            response = self.session.get(url, params=params)
            response.raise_for_status()

            records = []
            for line in response.text.strip().split('\n'):
                if line and ' ' in line:
                    parts = line.split(' ', 1)
                    if len(parts) == 2:
                        records.append(DNSRecord(ip=parts[0], hostname=parts[1]))
            return records
        except Exception as e:
            logger.error(f"Failed to get DNS records: {e}", exc_info=True)
            return []




