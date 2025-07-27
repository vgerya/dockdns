from typing import Optional

from pydantic_settings import BaseSettings


class DockDNSConfig(BaseSettings):
    base_domain: str = 'docker'
    dry_run: bool = False

    traefik_output_dir = "/mnt/traefik-dynamic"
    traefik_template_path = "templates/traefik_router.tmpl"

    notifications_enabled: bool = True
    telegram_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None

    class Config:
        prefix = "DOCKDNS_"
        env_file = ".env"
