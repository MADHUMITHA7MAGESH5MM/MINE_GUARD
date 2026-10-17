"""
MINEGUARD - Unified Incident Schema
Canonical field names across database, backend models, and frontend charts.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum
import json
import uuid
from datetime import datetime


class MineType(str, Enum):
    UNDERGROUND = "Underground"
    OPENCAST = "Opencast"


class Shift(str, Enum):
    RELAY_1 = "Relay-1"
    RELAY_2 = "Relay-2"
    RELAY_3_NIGHT = "Relay-3 / Night"


class WorkerType(str, Enum):
    DEPARTMENTAL = "Departmental"
    CONTRACTUAL = "Contractual"


class TARPLevel(str, Enum):
    GREEN = "Green"
    YELLOW = "Yellow"
    ORANGE = "Orange"
    RED = "Red"


class CauseCode(str, Enum):
    FALL_OF_ROOF = "Fall of Roof"
    FALL_OF_SIDES = "Fall of Sides"
    DUMPERS = "Dumpers"
    WHEELED_TRACKLESS = "Wheeled Trackless"
    GAS_EXPLOSION = "Gas Explosion"
    MINE_FLOODING = "Mine Flooding"
    MACHINERY_ACCIDENT = "Machinery Accident"
    OTHER = "Other"


@dataclass
class IncidentSchema:
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    narrative: str = ""
    mine_type: str = MineType.UNDERGROUND.value
    cause_code: str = CauseCode.OTHER.value
    workplace: str = ""
    shift: str = Shift.RELAY_1.value
    worker_type: str = WorkerType.DEPARTMENTAL.value
    sif_score: float = 0.0
    tarp_level: str = TARPLevel.GREEN.value
    sif_label: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    mine_id: Optional[str] = None
    hazards: List[str] = field(default_factory=list)
    failed_controls: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "narrative": self.narrative,
            "mine_type": self.mine_type,
            "cause_code": self.cause_code,
            "workplace": self.workplace,
            "shift": self.shift,
            "worker_type": self.worker_type,
            "sif_score": self.sif_score,
            "tarp_level": self.tarp_level,
            "sif_label": self.sif_label,
            "timestamp": self.timestamp,
            "mine_id": self.mine_id,
            "hazards": self.hazards,
            "failed_controls": self.failed_controls,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> "IncidentSchema":
        return cls(**data)

    def validate(self) -> bool:
        assert self.mine_type in [e.value for e in MineType], "Invalid mine_type"
        assert self.shift in [e.value for e in Shift], "Invalid shift"
        assert self.worker_type in [e.value for e in WorkerType], "Invalid worker_type"
        assert self.tarp_level in [e.value for e in TARPLevel], "Invalid tarp_level"
        assert 0.0 <= self.sif_score <= 1.0, "sif_score must be between 0.0 and 1.0"
        assert self.sif_label in [0, 1], "sif_label must be 0 or 1"
        return True


def get_tarp_level(sif_score: float) -> str:
    if sif_score >= 0.85:
        return TARPLevel.RED.value
    elif sif_score >= 0.60:
        return TARPLevel.ORANGE.value
    elif sif_score >= 0.35:
        return TARPLevel.YELLOW.value
    else:
        return TARPLevel.GREEN.value


if __name__ == "__main__":
    incident = IncidentSchema(
        narrative="Roof fall at 3rd panel due to inadequate support installation",
        mine_type=MineType.UNDERGROUND.value,
        cause_code=CauseCode.FALL_OF_ROOF.value,
        workplace="Depillaring Face",
        shift=Shift.RELAY_2.value,
        worker_type=WorkerType.CONTRACTUAL.value,
        sif_score=0.92,
        tarp_level=get_tarp_level(0.92),
        sif_label=1,
        mine_id="Mine_A",
        hazards=["roof instability"],
        failed_controls=["no roof bolting"],
    )
    incident.validate()
    print(incident.to_json())
