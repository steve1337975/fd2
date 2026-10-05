import asyncio
import time
from typing import List, Optional

from src.models import Server
from src.geoip import GeoIPResolver


class ConnectionChecker:


    def __init__(
        self,
        max_workers: int = 100,
        timeout: float = 5,
        log_servers: bool = False,
        geoip: Optional[GeoIPResolver] = None,
    ) -> None:

        self.max_workers = max_workers
        self.timeout = timeout
        self.log_servers = log_servers
        self.geoip = geoip

        self.queue = asyncio.Queue()
        self.result: List[Server] = []

        self.lock = asyncio.Lock()



    async def check(
        self,
        servers: List[Server],
    ) -> List[Server]:

        self.result.clear()


        for server in servers:

            await self.queue.put(
                server
            )


        workers = [
            asyncio.create_task(
                self._worker()
            )
            for _ in range(
                min(
                    self.max_workers,
                    len(servers),
                )
            )
        ]


        await self.queue.join()


        for _ in workers:

            await self.queue.put(
                None
            )


        await asyncio.gather(
            *workers
        )


        return self.result



    async def _worker(self):

        while True:

            server = await self.queue.get()


            if server is None:

                self.queue.task_done()
                break


            try:

                await self._check_server(
                    server
                )


            except Exception as error:

                self._log(
                    server,
                    "ERROR",
                    str(error),
                )


            finally:

                self.queue.task_done()



    async def _check_server(
        self,
        server: Server,
    ) -> None:


        start = time.perf_counter()


        try:

            _, writer = await asyncio.wait_for(
                asyncio.open_connection(
                    server.host,
                    server.port,
                ),
                timeout=self.timeout,
            )


            elapsed = (
                time.perf_counter()
                -
                start
            ) * 1000


            writer.close()

            try:

                await writer.wait_closed()

            except Exception:

                pass



            server.tcp_ok = True

            server.tcp_connect_time = round(
                elapsed,
                2,
            )


            if self.geoip:

                country, code = self.geoip.resolve(
                    server.host
                )

                server.country = country
                server.country_code = code



            async with self.lock:

                self.result.append(
                    server
                )


            self._log(
                server,
                "OK",
                (
                    f"{server.tcp_connect_time} ms | "
                    f"{server.country or 'UNKNOWN'} "
                    f"({server.country_code or '--'})"
                ),
            )



        except asyncio.TimeoutError:

            self._log(
                server,
                "TIMEOUT",
                f">{self.timeout}s",
            )



        except ConnectionRefusedError:

            self._log(
                server,
                "REFUSED",
                "connection refused",
            )



        except Exception as error:

            self._log(
                server,
                "ERROR",
                str(error),
            )



    def _log(
        self,
        server: Server,
        status: str,
        info: Optional[str] = None,
    ) -> None:


        if not self.log_servers:

            return


        print(
            f"[{status}] "
            f"{server.protocol.upper():7} "
            f"{server.host}:{server.port} | "
            f"{info or ''}"
        )