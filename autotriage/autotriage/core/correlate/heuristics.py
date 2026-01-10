from __future__ import annotations

from collections.abc import Iterable

from autotriage.core.models.entities import Entity, EntityType


def correlation_entities(entities: Iterable[Entity]) -> list[Entity]:
    keep = {
        EntityType.user,
        EntityType.host,
        EntityType.src_ip,
        EntityType.dst_ip,
        EntityType.domain,
        EntityType.rule_id,
        EntityType.technique_id,
    }
    out: list[Entity] = []
    for e in entities:
        if e.type in keep and e.value:
            out.append(e)
    return out
