from __future__ import annotations

from fastapi import APIRouter

from autotriage.config import load_effective_config

router = APIRouter()


@router.get("/config")
def get_config() -> dict[str, object]:
    cfg = load_effective_config()
    return {
        "version": cfg.version,
        "rules_dir": str(cfg.rules_dir),
        "data_dir": str(cfg.data_dir),
        "dedup_window_seconds": cfg.dedup_window_seconds,
        "correlation_window_seconds": cfg.correlation_window_seconds,
        "enabled_enrichers": cfg.enabled_enrichers,
    }
