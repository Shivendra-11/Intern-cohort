"""Threshold validation with an untested edge branch (ISS-003)."""
from __future__ import annotations

from pydantic import BaseModel, model_validator


class ThresholdConfig(BaseModel):
    low_max: int
    medium_max: int
    high_min: int

    @model_validator(mode="after")
    def _check_order(self) -> ThresholdConfig:
        if not (0 <= self.low_max < self.medium_max < self.high_min <= 100):
            raise ValueError("invalid threshold ordering")
        return self


def validate_thresholds(data: dict) -> ThresholdConfig:
    return ThresholdConfig(**data)
