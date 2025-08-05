from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class DockDNSConfig(BaseSettings):
    base_domain: str = 'docker'
    dry_run: bool = False
    dns_ip: Optional[str] = None

    docker_url: str = "unix:///var/run/docker.sock"

    traefik_templates_path: str = "app/templates/traefik_router.tmpl"
    traefik_output_dir: str = "/mnt/traefik-dynamic-config"

    notifications_enabled: bool = True
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    model_config = SettingsConfigDict(
        env_prefix="DOCKDNS_",
        env_file=".env",
    )
