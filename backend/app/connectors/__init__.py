from app.connectors.base import (
    Connector,
)
from app.connectors.benchmark import (
    BenchmarkConnector,
    benchmark_connector,
)
from app.connectors.models import (
    ActionResult,
    ConnectorStatus,
    LogResult,
    SignalReading,
    SignalResult,
)
from app.connectors.registry import (
    ConnectorRegistry,
    connector_registry,
)


connector_registry.register(
    benchmark_connector
)


__all__ = [
    "ActionResult",
    "BenchmarkConnector",
    "Connector",
    "ConnectorRegistry",
    "ConnectorStatus",
    "LogResult",
    "SignalReading",
    "SignalResult",
    "benchmark_connector",
    "connector_registry",
]