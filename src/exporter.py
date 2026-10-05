import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from src.models import Server


class Exporter:

    def __init__(
        self,
        output_dir: Path = None,
        max_lines_per_file: int = 300,
    ) -> None:

        self.output_dir = (
            output_dir
            or (
                Path(__file__)
                .resolve()
                .parent.parent
                / "output"
            )
        )

        self.max_lines_per_file = max_lines_per_file

    def export(
        self,
        servers: List[Server],
        group: str,
    ) -> None:

        if group not in (
            "white",
            "black",
        ):
            raise ValueError(
                "Group must be white or black"
            )

        base = self.output_dir / group

        # Полностью очищаем старый результат этой группы.
        if base.exists():
            shutil.rmtree(base)

        self._prepare_dirs(base)

        # ==========================================================
        # FULL
        # ==========================================================

        self._write_file(
            base / "full.txt",
            servers,
            f"VPN {group.upper()} — Full",
        )

        self._write_split_files(
            base,
            "full",
            servers,
            f"VPN {group.upper()}",
        )

        # ==========================================================
        # RU / NON-RU
        # ==========================================================

        ru_servers = [
            server
            for server in servers
            if (
                server.country_code
                and server.country_code.upper() == "RU"
            )
        ]

        non_ru_servers = [
            server
            for server in servers
            if (
                not server.country_code
                or server.country_code.upper() != "RU"
            )
        ]

        # ----------------------------------------------------------
        # NON-RU
        # ----------------------------------------------------------

        non_ru_dir = base / "non-ru"

        self._write_file(
            non_ru_dir / "full.txt",
            non_ru_servers,
            "VPN NON-RU — Full",
        )

        self._write_split_files(
            non_ru_dir,
            "full",
            non_ru_servers,
            "VPN NON-RU",
        )

        # ==========================================================
        # PROTOCOLS
        # ==========================================================

        self._export_protocols(
            base,
            servers,
        )

        # ==========================================================
        # COUNTRIES
        # ==========================================================

        self._export_countries(
            base,
            servers,
        )

    def _prepare_dirs(
        self,
        base: Path,
    ) -> None:

        (
            base / "protocols"
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

        (
            base / "countries"
        ).mkdir(
            parents=True,
            exist_ok=True,
        )

    def _write_file(
        self,
        path: Path,
        servers: List[Server],
        title: str,
    ) -> None:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with path.open(
            "w",
            encoding="utf-8",
        ) as file:

            self._write_header(
                file,
                servers,
                title,
            )

            for server in servers:
                file.write(
                    server.config
                    +
                    "\n"
                )

    def _write_split_files(
        self,
        directory: Path,
        name: str,
        servers: List[Server],
        title: str,
    ) -> None:

        if not servers:
            return

        directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        chunks = [
            servers[i:i + self.max_lines_per_file]
            for i in range(
                0,
                len(servers),
                self.max_lines_per_file,
            )
        ]

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):

            self._write_file(
                directory
                /
                f"{name}_{index}.txt",
                chunk,
                f"{title} — #{index}",
            )

    def _export_protocols(
        self,
        base: Path,
        servers: List[Server],
    ) -> None:

        groups: Dict[str, List[Server]] = {}

        for server in servers:

            protocol = (
                server.protocol
                or "unknown"
            ).lower()

            groups.setdefault(
                protocol,
                [],
            ).append(
                server
            )

        # ==========================================================
        # OTHER
        # Все протоколы, кроме VLESS
        # ==========================================================

        other_servers = [
            server
            for server in servers
            if (
                (server.protocol or "unknown").lower()
                != "vless"
            )
        ]

        other_dir = (
            base
            / "protocols"
            / "other"
        )

        self._write_file(
            other_dir / "full.txt",
            other_servers,
            "VPN OTHER — Full",
        )

        self._write_split_files(
            other_dir,
            "full",
            other_servers,
            "VPN OTHER",
        )

        # ==========================================================
        # ОТДЕЛЬНЫЕ ПРОТОКОЛЫ
        # ==========================================================

        for protocol, items in sorted(
            groups.items()
        ):

            protocol_dir = (
                base
                / "protocols"
                / protocol
            )

            self._write_split_files(
                protocol_dir,
                protocol,
                items,
                f"VPN {protocol.upper()}",
            )

    def _export_countries(
        self,
        base: Path,
        servers: List[Server],
    ) -> None:

        groups: Dict[str, List[Server]] = {}

        for server in servers:

            country = (
                server.country_code
                or "UNKNOWN"
            ).upper()

            groups.setdefault(
                country,
                [],
            ).append(
                server
            )

        for country, items in sorted(
            groups.items()
        ):

            self._write_split_files(
                base
                / "countries"
                / country,

                country.lower(),

                items,

                f"VPN {country}",
            )

    def _write_header(
        self,
        file,
        servers: List[Server],
        title: str,
    ) -> None:

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )

        headers = [
            "# announce: ⚡ Проверяйте сервер кнопкой скорости или молнией. Чем меньше задержка (ms), тем лучше отклик; n/a означает, что проверка не удалась.",
            f"# profile-title: {title}",
            "# profile-update-interval: 1",
            f"# generated-at: {now}",
            f"# servers-count: {len(servers)}",
            "",
        ]

        file.write(
            "\n".join(headers)
        )
        file.write("\n")