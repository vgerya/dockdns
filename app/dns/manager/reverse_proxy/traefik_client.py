import logging
import os
from datetime import datetime

from jinja2 import Template

from agent.dockdns_config import DockDNSConfig
from dns.manager.pihole.pihole_client import DNSRecord
from domain.container_wraper import ContainerWrapper

logger = logging.getLogger('dns.manager.traefik_client')


def yaml_path(container: ContainerWrapper, config: DockDNSConfig, ):
    return f"{config.traefik_output_dir}/{container.labeled_hostname}_{container.id[:12]}.yaml"


def create_traefik_config(
        dns_record: DNSRecord,
        dockdns_config: DockDNSConfig,
) -> str:
    with open(dockdns_config.traefik_templates_path) as f:
        template = Template(f.read())

        target_hostname = (
                dns_record.hostname +
                ("." if not dockdns_config.base_domain.startswith(".") else "") +
                dockdns_config.base_domain
        )

        return template.render(
            hostname=target_hostname,
            ip=dns_record.ip,
            port=dns_record.port,
            timestamp=datetime.now().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
        )

def render_traefik_config(
    container: ContainerWrapper,
    dns_record: DNSRecord,
    dockdns_config: DockDNSConfig,
):
    rendered = create_traefik_config(dns_record, dockdns_config)

    output_path = yaml_path(container,dockdns_config,)

    if dockdns_config.dry_run:
        logger.info(f"[DRY RUN] Would write {output_path}:{rendered}")
        return

    with open(output_path, "w") as f:
        f.write(rendered)

    logger.info(f"[TRAEFIK] Wrote config to {output_path}")
    # send_telegram(f"[Traefik] \U0001F195 Added route: {hostname} → {ip}:{port}")


def delete_traefik_config(container: ContainerWrapper, dockdns_config: DockDNSConfig, ):
    path = yaml_path(container, dockdns_config, )
    if os.path.exists(path):
        if dockdns_config.dry_run:
            logger.info(f"[DRY RUN] Would delete {path}")
            return

        os.remove(path)
        logger.info(f"[TRAEFIK] Removed config: {path}")
        # send_telegram(f"[Traefik] ❌ Removed route: {hostname}")
