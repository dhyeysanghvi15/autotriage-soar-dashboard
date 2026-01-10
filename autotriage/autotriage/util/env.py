from __future__ import annotations

import os
from pathlib import Path


def env_int(name: str, default: int) -> int:
    val = os.getenv(name)
    return default if val is None or val == "" else int(val)


def env_path(name: str, default: Path) -> Path:
    val = os.getenv(name)
    return default if val is None or val == "" else Path(val)


def env_str_list(name: str, default: list[str]) -> list[str]:
    val = os.getenv(name)
    if val is None or val.strip() == "":
        return list(default)
    return [s.strip() for s in val.split(",") if s.strip()]


def env_str(name: str, default: str) -> str:
    val = os.getenv(name)
    return default if val is None or val.strip() == "" else val.strip()
