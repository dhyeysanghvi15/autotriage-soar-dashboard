from __future__ import annotations

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from autotriage.storage.db import db_dependency
from autotriage.storage.views.aggregates import overview_24h

router = APIRouter()


@router.get("/overview")
def overview(db: Annotated[sqlite3.Connection, Depends(db_dependency)]) -> dict[str, object]:
    return {"window": "24h", "stats": overview_24h(db)}
