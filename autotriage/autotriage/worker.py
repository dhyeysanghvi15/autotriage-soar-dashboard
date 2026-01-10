from __future__ import annotations

import asyncio
import json

import structlog

from autotriage.core.pipeline.orchestrator import process_ingest
from autotriage.storage.db import get_db, init_db
from autotriage.storage.repositories.alerts_repo import AlertsRepository

log = structlog.get_logger(__name__)


async def worker_loop(poll_interval_s: float = 0.25) -> None:
    init_db()
    log.info("worker_started")
    while True:
        await asyncio.sleep(poll_interval_s)
        db = get_db()
        try:
            repo = AlertsRepository(db)
            row = repo.claim_next()
            if row is None:
                continue
            ingest_id = str(row["ingest_id"])
            raw = json.loads(str(row["raw_json"]))
            log.info("worker_processing", ingest_id=ingest_id)
            process_ingest(db, ingest_id, raw)
            repo.mark_processed(ingest_id)
            log.info("worker_processed", ingest_id=ingest_id)
        except Exception as e:  # noqa: BLE001
            try:
                if "ingest_id" in locals():
                    AlertsRepository(db).mark_failed(ingest_id, repr(e))
            except Exception:  # noqa: BLE001
                pass
            log.exception("worker_error")
        finally:
            db.close()
