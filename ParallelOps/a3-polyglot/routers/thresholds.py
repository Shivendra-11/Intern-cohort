"""Runtime threshold configuration for fraud verdict bands."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, model_validator

router = APIRouter()
BASE = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE / "config" / "thresholds.json"

_DEFAULTS = {"low_max": 30, "medium_max": 70, "high_min": 71}


class ThresholdConfig(BaseModel):
    low_max: int
    medium_max: int
    high_min: int

    @model_validator(mode="after")
    def _check_order(self) -> ThresholdConfig:
        if not (0 <= self.low_max < self.medium_max < self.high_min <= 100):
            raise ValueError(
                "thresholds must satisfy 0 <= low_max < medium_max < high_min <= 100"
            )
        return self


def _load() -> ThresholdConfig:
    if CONFIG_FILE.exists():
        return ThresholdConfig(**json.loads(CONFIG_FILE.read_text()))
    return ThresholdConfig(**_DEFAULTS)


def _save(cfg: ThresholdConfig) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(cfg.model_dump_json(indent=2) + "\n")


@router.get("/config/thresholds", response_model=ThresholdConfig, tags=["config"])
def get_thresholds() -> ThresholdConfig:
    return _load()


@router.put("/config/thresholds", response_model=ThresholdConfig, tags=["config"])
def put_thresholds(cfg: ThresholdConfig) -> ThresholdConfig:
    _save(cfg)
    return cfg
