from dataclasses import dataclass
from typing import Optional


@dataclass
class Subscription:

    type: str
    urls: list


@dataclass
class Server:

    config: str

    protocol: str

    host: str

    port: int


    # Source information

    source_type: Optional[str] = None
    source_url: Optional[str] = None


    # Geo information

    country: Optional[str] = None
    country_code: Optional[str] = None


    # Check result

    http_ok: bool = False
    http_ping: Optional[float] = None