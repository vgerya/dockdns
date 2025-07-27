from dataclasses import dataclass


@dataclass
class PiHoleConfig:
    url: str
    api_token: str
