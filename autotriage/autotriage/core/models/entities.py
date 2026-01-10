from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class EntityType(StrEnum):
    user = "user"
    host = "host"
    src_ip = "src_ip"
    dst_ip = "dst_ip"
    domain = "domain"
    asn = "asn"
    rule_id = "rule_id"
    technique_id = "technique_id"


class Entity(BaseModel):
    type: EntityType
    value: str = Field(min_length=1, max_length=512)


class Edge(BaseModel):
    src: Entity
    dst: Entity
    type: str = Field(min_length=1, max_length=64)
