from __future__ import annotations

from fastapi import APIRouter

from autotriage.storage.db import with_db
from autotriage.storage.views.aggregates import overview_24h

router = APIRouter()


@router.get("/overview")
@with_db
def overview(db) -> dict[str, object]:
    return {"window": "24h", "stats": overview_24h(db)}

