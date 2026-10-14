from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ConnectorStatus(str, Enum):
    OK = "OK"
    NO_DATA = "NO_DATA"
    ERROR = "ERROR"


@dataclass(frozen=True)
class SignalReading:
    value: float
    labels: dict[str, str] = field(
        default_factory=dict
    )
    observed_at: datetime | None = None


@dataclass(frozen=True)
class SignalResult:
    connector: str
    signal_key: str
    service: str
    status: ConnectorStatus
    readings: tuple[SignalReading, ...] = ()
    error: str | None = None

    @property
    def first_value(self) -> float | None:
        if not self.readings:
            return None

        return self.readings[0].value


@dataclass(frozen=True)
class LogResult:
    connector: str
    service: str
    status: ConnectorStatus
    logs: str = ""
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    error: str | None = None


@dataclass(frozen=True)
class ActionResult:
    connector: str
    action_key: str
    target_service: str
    success: bool
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""