from pathlib import Path
from typing import Optional, Tuple
import ipaddress
import socket

import geoip2.database


class GeoIPResolver:


    def __init__(
        self,
        database_path: Path,
    ) -> None:

        self.database_path = Path(
            database_path
        )

        self.reader: Optional[
            geoip2.database.Reader
        ] = None

        self._load_database()



    def _load_database(self) -> None:

        if not self.database_path.exists():

            raise FileNotFoundError(
                f"GeoIP database not found: "
                f"{self.database_path}"
            )


        self.reader = geoip2.database.Reader(
            str(self.database_path)
        )



    def resolve(
        self,
        host: str,
    ) -> Tuple[
        Optional[str],
        Optional[str],
    ]:

        if not self.reader:

            return None, None


        ip = self._resolve_ip(
            host
        )


        if not ip:

            return None, None


        try:

            response = self.reader.country(
                ip
            )


            return (
                response.country.names.get("en")
                or response.country.name,
                response.country.iso_code,
            )


        except Exception:

            return None, None



    def _resolve_ip(
        self,
        host: str,
    ) -> Optional[str]:

        try:

            ipaddress.ip_address(
                host
            )

            return host


        except ValueError:

            pass


        try:

            addresses = socket.getaddrinfo(
                host,
                None,
                socket.AF_INET,
            )

            return addresses[0][4][0]


        except Exception:

            return None



    def close(self) -> None:

        if self.reader:

            self.reader.close()

            self.reader = None