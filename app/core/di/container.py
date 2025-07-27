from dependency_injector import containers, providers

from dns.manager.pihole.config import PiHoleConfig
from dns.manager.pihole.pihole_client import PiHoleClient


class Container(containers.DeclarativeContainer):
    config = providers.Configuration()

    config.pi_hole_url = config.from_env('PI_HOLE_URL', default='http://0.0.0.0:8080', as_=str)
    config.pi_hole_api_token = config.from_env('PI_HOLE_API_TOKEN', required=True, as_=str)

    pi_hole_client = providers.Singleton(
        PiHoleClient,
        pihole_config=PiHoleConfig(
            url=config.pi_hole_url(),
            api_token=config.pi_hole_api_token(),
        )
    )
