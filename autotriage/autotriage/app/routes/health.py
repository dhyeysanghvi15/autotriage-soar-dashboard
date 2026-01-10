from __future__ import annotations

from fastapi import APIRouter

from autotriage.storage.db import get_db
from autotriage.version import __version__

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}


@router.get("/readyz")
def readyz() -> dict[str, str]:
    db = get_db()
    try:
        db.execute("SELECT 1")
    finally:
        db.close()
    return {"status": "ok", "db": "ok"}

