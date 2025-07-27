import os
from dataclasses import dataclass

from jinja2 import Template

from agent.dockdns_config import DockDNSConfig
from domain.container_wraper import ContainerWrapper


@dataclass
class TraefikConfig:
    template_path: str
    output_dir: str
    dry_run: bool


def yaml_path(container: ContainerWrapper, config: TraefikConfig, ):
    return f"{config.output_dir}/{container.target_hostname}_{container.id[:12]}.yaml"


def render_traefik_config(hostname, ip, port, container, config: TraefikConfig, dockdns_config: DockDNSConfig):
    with open(config.template_path) as f:
        template = Template(f.read())
    rendered = template.render(hostname=hostname, ip=ip, port=port)
    output_path = yaml_path(hostname, container)
    if dockdns_config.dry_run:
        print(f"[DRY RUN] Would write {output_path}:{rendered}")
    else:
        with open(output_path, "w") as f:
            f.write(rendered)
        print(f"[TRAEFIK] Wrote config to {output_path}")
        # send_telegram(f"[Traefik] \U0001F195 Added route: {hostname} → {ip}:{port}")


def delete_traefik_config(container: ContainerWrapper, config: TraefikConfig, dockdns_config: DockDNSConfig,):
    path = yaml_path(container, config, )
    if os.path.exists(path):
        if dockdns_config.dry_run:
            print(f"[DRY RUN] Would delete {path}")
        else:
            os.remove(path)
            print(f"[TRAEFIK] Removed config: {path}")
            # send_telegram(f"[Traefik] ❌ Removed route: {hostname}")
