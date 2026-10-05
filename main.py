import asyncio
import logging
import random

from src.settings import Settings
from src.subscription_parser import SubscriptionParser
from src.connection_checker import ConnectionChecker
from src.exporter import Exporter
from src.geoip import GeoIPResolver


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(
    "vpn-parser"
)



async def collect_servers(
    parser: SubscriptionParser,
    subscriptions,
    timeout: float,
):

    servers = []


    for subscription in subscriptions:

        logger.info(
            "Loading group: %s",
            subscription.type,
        )


        for url in subscription.urls:

            try:

                logger.info(
                    "Downloading: %s",
                    url,
                )


                content = await parser.download(
                    url,
                    timeout,
                )


                configs = parser.parse_configs(
                    content,
                    subscription.type,
                    url,
                )


                servers.extend(
                    configs
                )


                logger.info(
                    "Loaded %s configs",
                    len(configs),
                )


            except Exception as error:

                logger.error(
                    "Failed %s: %s",
                    url,
                    error,
                )


    return servers





async def main():

    settings = Settings()


    parser = SubscriptionParser()


    subscriptions = parser.load_subscriptions()


    servers = await collect_servers(
        parser,
        subscriptions,
        settings.timeout,
    )


    print(
        f"Loaded servers: {len(servers)}"
    )


    if settings.shuffle_servers:

        random.shuffle(
            servers
        )



    geoip = GeoIPResolver(
        settings.geoip_db_path
    )


    try:

        checker = ConnectionChecker(
            max_workers=settings.max_concurrent_checks,
            timeout=settings.timeout,
            log_servers=settings.log_servers,
            geoip=geoip,
        )


        alive_servers = await checker.check(
            servers
        )


    finally:

        geoip.close()



    print(
        f"Alive servers: {len(alive_servers)}"
    )



    white_servers = [
        server
        for server in alive_servers
        if server.source_type == "white"
    ]


    black_servers = [
        server
        for server in alive_servers
        if server.source_type == "black"
    ]



    exporter = Exporter(
        max_lines_per_file=settings.max_lines_per_file,
    )


    if settings.shuffle_servers:

        random.shuffle(
            white_servers
        )

        random.shuffle(
            black_servers
        )


    if white_servers:

        exporter.export(
            white_servers,
            "white",
        )



    if black_servers:

        exporter.export(
            black_servers,
            "black",
        )



    print(
        "Export completed."
    )





if __name__ == "__main__":

    asyncio.run(
        main()
    )