from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ScoringRules:
    weights: dict[str, float]


def load_scoring_rules(rules_dir: Path) -> ScoringRules:
    data = yaml.safe_load((rules_dir / "scoring.yml").read_text(encoding="utf-8")) or {}
    weights = {str(k): float(v) for k, v in (data.get("weights") or {}).items()}
    return ScoringRules(weights=weights)
