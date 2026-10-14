from abc import ABC, abstractmethod

from app.connectors.models import (
    ActionResult,
    LogResult,
    SignalResult,
)


class Connector(ABC):
    @property
    @abstractmethod
    def key(self) -> str:
        """
        Stable connector identifier.

        Examples:
        benchmark
        aws
        velora
        """
        raise NotImplementedError

    @abstractmethod
    def supports_service(
        self,
        service: str,
    ) -> bool:
        """
        Return whether this connector owns the
        supplied service.
        """
        raise NotImplementedError

    @abstractmethod
    def get_signal(
        self,
        *,
        signal_key: str,
        service: str,
    ) -> SignalResult:
        """
        Retrieve current telemetry for a
        deterministic incident signal.

        The connector gathers the telemetry.
        AegisOps core decides whether that
        telemetry represents an incident.
        """
        raise NotImplementedError

    @abstractmethod
    def get_logs(
        self,
        *,
        service: str,
        tail: int = 50,
        since_minutes: int = 30,
    ) -> LogResult:
        """
        Retrieve bounded diagnostic evidence for
        an allowlisted service.
        """
        raise NotImplementedError

    @abstractmethod
    def execute_action(
        self,
        *,
        action_key: str,
        target_service: str,
    ) -> ActionResult:
        """
        Execute a predefined remediation action.

        Connectors must never accept arbitrary
        shell commands from the model.
        """
        raise NotImplementedError