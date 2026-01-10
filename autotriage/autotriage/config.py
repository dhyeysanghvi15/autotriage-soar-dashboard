from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from autotriage.util.env import env_int, env_path, env_str, env_str_list


@dataclass(frozen=True)
class AppConfig:
    version: str
    db_path: Path
    data_dir: Path
    rules_dir: Path
    dedup_window_seconds: int
    correlation_window_seconds: int
    enabled_enrichers: list[str]
    log_level: str


def load_effective_config() -> AppConfig:
    load_dotenv()
    project_root = Path(__file__).resolve().parents[1]
    return AppConfig(
        version="0.1.0",
        db_path=env_path("AUTOTRIAGE_DB_PATH", project_root / "var" / "autotriage.db"),
        data_dir=env_path("AUTOTRIAGE_DATA_DIR", project_root / "data"),
        rules_dir=env_path("AUTOTRIAGE_RULES_DIR", project_root / "autotriage" / "rules"),
        dedup_window_seconds=env_int("AUTOTRIAGE_DEDUP_WINDOW_SECONDS", 600),
        correlation_window_seconds=env_int("AUTOTRIAGE_CORRELATION_WINDOW_SECONDS", 3600),
        enabled_enrichers=env_str_list(
            "AUTOTRIAGE_ENABLED_ENRICHERS",
            ["allowlist", "asset_context", "ip_reputation", "geo_asn", "whois"],
        ),
        log_level=env_str("AUTOTRIAGE_LOG_LEVEL", "INFO"),
    )
