import base64
import json
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

import aiohttp

from src.models import Server, Subscription


class SubscriptionParser:


    DEFAULT_CONFIG_PATH = (
        Path(__file__)
        .resolve()
        .parent.parent
        /
        "files"
        /
        "subscriptions.json"
    )


    def __init__(
        self,
        config_path: Optional[
            Union[Path, str]
        ] = None,
    ) -> None:

        self.config_path = (
            Path(config_path)
            if config_path
            else self.DEFAULT_CONFIG_PATH
        )



    def load_subscriptions(
        self,
    ) -> List[Subscription]:

        if not self.config_path.exists():

            raise FileNotFoundError(
                f"Subscriptions file not found: "
                f"{self.config_path}"
            )


        with self.config_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )


        if not isinstance(
            data,
            list,
        ):

            raise ValueError(
                "Subscriptions file must contain array"
            )


        result = []


        for item in data:

            if not isinstance(
                item,
                dict,
            ):
                continue


            sub_type = item.get(
                "type"
            )

            urls = item.get(
                "urls"
            )


            if not isinstance(
                sub_type,
                str,
            ):
                continue


            if not isinstance(
                urls,
                list,
            ):
                continue


            result.append(
                Subscription(
                    type=sub_type,
                    urls=urls,
                )
            )


        return result



    async def download(
        self,
        url: str,
        timeout: float = 10,
    ) -> str:

        client_timeout = aiohttp.ClientTimeout(
            total=timeout
        )


        async with aiohttp.ClientSession(
            timeout=client_timeout,
        ) as session:


            async with session.get(
                url
            ) as response:

                response.raise_for_status()

                content = await response.read()


        return self._decode_content(
            content
        )



    def parse_configs(
        self,
        content: str,
        source_type: str,
        source_url: str,
    ) -> List[Server]:

        servers = []


        for line in content.splitlines():

            line = line.strip()


            if not line:
                continue


            if line.startswith("#"):
                continue


            server = self._parse_config(
                line,
                source_type,
                source_url,
            )


            if server:

                servers.append(
                    server
                )


        return servers



    @staticmethod
    def _parse_config(
        config: str,
        source_type: str,
        source_url: str,
    ) -> Optional[Server]:

        try:

            parsed = urlparse(
                config
            )


            if not parsed.scheme:

                return None


            host = parsed.hostname
            port = parsed.port


            if not host or not port:

                return None


            return Server(
                config=config,
                protocol=parsed.scheme.lower(),
                host=host,
                port=port,
                source_type=source_type,
                source_url=source_url,
            )


        except Exception:

            return None



    @staticmethod
    def _decode_content(
        content: bytes,
    ) -> str:

        text = content.decode(
            "utf-8",
            errors="ignore",
        ).strip()


        if "://" in text:

            return text


        try:

            decoded = base64.b64decode(
                content,
                validate=True,
            )


            return decoded.decode(
                "utf-8",
                errors="ignore",
            ).strip()


        except Exception:

            return text