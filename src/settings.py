import json
from pathlib import Path
from typing import Any, Dict, Optional, Union


class Settings:


    DEFAULT_CONFIG_PATH = (
        Path(__file__).resolve().parent.parent
        / "files"
        / "settings.json"
    )


    REQUIRED_FIELDS = {
        "timeout": (int, float),
        "max_concurrent_checks": int,
        "max_lines_per_file": int,
        "geoip_db_path": str,
        "shuffle_servers": bool,
        "log_servers": bool,
    }


    def __init__(
        self,
        config_path: Optional[Union[Path, str]] = None,
    ) -> None:

        self.config_path = (
            Path(config_path)
            if config_path
            else self.DEFAULT_CONFIG_PATH
        )

        self._data = self._load()



    def _load(
        self,
    ) -> Dict[str, Any]:

        if not self.config_path.exists():

            raise FileNotFoundError(
                f"Settings file not found: {self.config_path}"
            )


        if not self.config_path.is_file():

            raise ValueError(
                f"Settings path is not a file: {self.config_path}"
            )


        try:

            with self.config_path.open(
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(file)


        except json.JSONDecodeError as error:

            raise ValueError(
                f"Invalid JSON: {self.config_path}"
            ) from error



        if not isinstance(data, dict):

            raise ValueError(
                "Settings root must be JSON object."
            )


        self._validate(
            data
        )


        return data



    def _validate(
        self,
        data: Dict[str, Any],
    ) -> None:


        missing = (
            set(self.REQUIRED_FIELDS)
            -
            set(data)
        )


        if missing:

            raise ValueError(
                "Missing settings: "
                +
                ", ".join(
                    sorted(missing)
                )
            )



        for field, expected in self.REQUIRED_FIELDS.items():

            value = data[field]


            if not isinstance(
                value,
                expected,
            ):

                if isinstance(
                    expected,
                    tuple,
                ):

                    expected_name = ", ".join(
                        item.__name__
                        for item in expected
                    )

                else:

                    expected_name = expected.__name__


                raise TypeError(
                    f"Invalid type for '{field}'. "
                    f"Expected {expected_name}, "
                    f"got {type(value).__name__}"
                )



        if data["timeout"] <= 0:

            raise ValueError(
                "'timeout' must be greater than zero"
            )


        if data["max_concurrent_checks"] <= 0:

            raise ValueError(
                "'max_concurrent_checks' must be greater than zero"
            )


        if data["max_lines_per_file"] <= 0:

            raise ValueError(
                "'max_lines_per_file' must be greater than zero"
            )


        if not data["geoip_db_path"].strip():

            raise ValueError(
                "'geoip_db_path' cannot be empty"
            )



    @property
    def timeout(
        self,
    ) -> float:

        return float(
            self._data["timeout"]
        )



    @property
    def max_concurrent_checks(
        self,
    ) -> int:

        return int(
            self._data["max_concurrent_checks"]
        )



    @property
    def max_lines_per_file(
        self,
    ) -> int:

        return int(
            self._data["max_lines_per_file"]
        )



    @property
    def geoip_db_path(
        self,
    ) -> Path:


        path = Path(
            self._data["geoip_db_path"]
        )


        if path.is_absolute():

            return path


        return (
            self.config_path.parent
            /
            path
        )



    @property
    def shuffle_servers(
        self,
    ) -> bool:

        return bool(
            self._data["shuffle_servers"]
        )



    @property
    def log_servers(
        self,
    ) -> bool:

        return bool(
            self._data["log_servers"]
        )