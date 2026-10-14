import json
import subprocess

from datetime import (
    datetime,
    timezone,
)
from math import isfinite
from pathlib import Path

from app.connectors.base import Connector
from app.connectors.models import (
    ActionResult,
    ConnectorStatus,
    LogResult,
    SignalReading,
    SignalResult,
)
from app.monitoring.prometheus import (
    PrometheusError,
    prometheus_client,
)


BENCHMARK_SERVICES = {
    "benchmark-api",
    "benchmark-redis",
    "benchmark-postgresql",
}


BENCHMARK_CONTAINERS = {
    "benchmark-api":
        "aegisops-benchmark-api",

    "benchmark-redis":
        "aegisops-benchmark-redis",

    "benchmark-postgresql":
        "aegisops-benchmark-db",
}


BENCHMARK_SIGNALS = {
    "postgresql_unavailable": {
        "service":
            "benchmark-postgresql",

        "promql":
            (
                'benchmark_dependency_up'
                '{dependency="postgresql"}'
            ),
    },

    "redis_unavailable": {
        "service":
            "benchmark-redis",

        "promql":
            (
                'benchmark_dependency_up'
                '{dependency="redis"}'
            ),
    },

    "http_5xx_rate_high": {
        "service":
            "benchmark-api",

        "promql":
            """
            sum(
                rate(
                    benchmark_http_requests_total{
                        status=~"5.."
                    }[5m]
                )
            )
            """,
    },

    "api_latency_high": {
        "service":
            "benchmark-api",

        "promql":
            """
            histogram_quantile(
                0.95,
                sum by (le) (
                    rate(
                        benchmark_http_request_duration_seconds_bucket[5m]
                    )
                )
            )
            """,
    },
}


BENCHMARK_ACTIONS = {
    "restart_benchmark_redis": {
        "target_service":
            "benchmark-redis",

        "compose_service":
            "benchmark-redis",
    },

    "restart_benchmark_postgresql": {
        "target_service":
            "benchmark-postgresql",

        "compose_service":
            "benchmark-db",
    },

    "restart_benchmark_api": {
        "target_service":
            "benchmark-api",

        "compose_service":
            "benchmark-api",
    },
}


class BenchmarkConnector(
    Connector
):
    @property
    def key(self) -> str:
        return "benchmark"

    def supports_service(
        self,
        service: str,
    ) -> bool:
        return (
            service
            in BENCHMARK_SERVICES
        )

    def get_signal(
        self,
        *,
        signal_key: str,
        service: str,
    ) -> SignalResult:
        signal = (
            BENCHMARK_SIGNALS.get(
                signal_key
            )
        )

        if signal is None:
            raise ValueError(
                (
                    "Unsupported benchmark "
                    f"signal: {signal_key}"
                )
            )

        expected_service = (
            signal[
                "service"
            ]
        )

        if (
            service
            != expected_service
        ):
            raise ValueError(
                (
                    f"Signal '{signal_key}' "
                    "belongs to service "
                    f"'{expected_service}', "
                    f"not '{service}'."
                )
            )

        try:
            results = (
                prometheus_client.query(
                    signal[
                        "promql"
                    ]
                )
            )

        except PrometheusError as exc:
            return SignalResult(
                connector=self.key,
                signal_key=signal_key,
                service=service,
                status=(
                    ConnectorStatus.ERROR
                ),
                error=str(exc),
            )

        readings = []

        for result in results:
            try:
                (
                    timestamp,
                    raw_value,
                ) = result["value"]

                value = float(
                    raw_value
                )

                if not isfinite(
                    value
                ):
                    continue

                observed_at = (
                    datetime.fromtimestamp(
                        float(
                            timestamp
                        ),
                        tz=timezone.utc,
                    )
                )

            except (
                KeyError,
                IndexError,
                ValueError,
                TypeError,
                OverflowError,
            ):
                continue

            labels = {
                str(key):
                    str(value)
                for key, value
                in result.get(
                    "metric",
                    {},
                ).items()
            }

            readings.append(
                SignalReading(
                    value=value,
                    labels=labels,
                    observed_at=(
                        observed_at
                    ),
                )
            )

        if not readings:
            return SignalResult(
                connector=self.key,
                signal_key=signal_key,
                service=service,
                status=(
                    ConnectorStatus.NO_DATA
                ),
            )

        return SignalResult(
            connector=self.key,
            signal_key=signal_key,
            service=service,
            status=(
                ConnectorStatus.OK
            ),
            readings=tuple(
                readings
            ),
        )

    def get_logs(
        self,
        *,
        service: str,
        tail: int = 50,
        since_minutes: int = 30,
    ) -> LogResult:
        if not self.supports_service(
            service
        ):
            raise ValueError(
                (
                    "Unsupported benchmark "
                    f"service: {service}"
                )
            )

        if not (
            1 <= tail <= 100
        ):
            raise ValueError(
                (
                    "tail must be between "
                    "1 and 100"
                )
            )

        if not (
            1
            <= since_minutes
            <= 60
        ):
            raise ValueError(
                (
                    "since_minutes must "
                    "be between 1 and 60"
                )
            )

        container = (
            BENCHMARK_CONTAINERS[
                service
            ]
        )

        try:
            inspection = (
                self._run_docker(
                    "inspect",
                    "--format",
                    "{{json .State}}",
                    container,
                    timeout=8,
                )
            )

            if (
                inspection.returncode
                != 0
            ):
                return LogResult(
                    connector=self.key,
                    service=service,
                    status=(
                        ConnectorStatus.ERROR
                    ),
                    error=(
                        "Docker container "
                        "inspection failed"
                    ),
                )

            state = json.loads(
                inspection
                .stdout
                .strip()
            )

            result = (
                self._run_docker(
                    "logs",
                    "--timestamps",
                    "--since",
                    (
                        f"{since_minutes}m"
                    ),
                    "--tail",
                    str(tail),
                    container,
                    timeout=8,
                )
            )

            if (
                result.returncode
                != 0
            ):
                return LogResult(
                    connector=self.key,
                    service=service,
                    status=(
                        ConnectorStatus.ERROR
                    ),
                    error=(
                        "Docker log "
                        "retrieval failed"
                    ),
                )

        except (
            OSError,
            subprocess.TimeoutExpired,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            return LogResult(
                connector=self.key,
                service=service,
                status=(
                    ConnectorStatus.ERROR
                ),
                error=(
                    type(exc).__name__
                ),
            )

        lines = (
            result.stdout
            .splitlines()
        )

        log_text = (
            "\n".join(
                lines[-tail:]
            )
        )[-8000:]

        return LogResult(
            connector=self.key,
            service=service,
            status=(
                ConnectorStatus.OK
                if log_text
                else ConnectorStatus.NO_DATA
            ),
            logs=log_text,
            metadata={
                "container":
                    container,

                "container_state": {
                    "status":
                        state.get(
                            "Status"
                        ),

                    "running":
                        state.get(
                            "Running"
                        ),

                    "exit_code":
                        state.get(
                            "ExitCode"
                        ),

                    "oom_killed":
                        state.get(
                            "OOMKilled"
                        ),

                    "started_at":
                        state.get(
                            "StartedAt"
                        ),

                    "finished_at":
                        state.get(
                            "FinishedAt"
                        ),
                },
            },
        )

    def execute_action(
        self,
        *,
        action_key: str,
        target_service: str,
    ) -> ActionResult:
        action = (
            BENCHMARK_ACTIONS.get(
                action_key
            )
        )

        if action is None:
            raise ValueError(
                (
                    "Unsupported benchmark "
                    f"action: {action_key}"
                )
            )

        expected_target = (
            action[
                "target_service"
            ]
        )

        if (
            target_service
            != expected_target
        ):
            raise ValueError(
                (
                    f"Action '{action_key}' "
                    "is restricted to "
                    f"'{expected_target}', "
                    f"not '{target_service}'."
                )
            )

        repo_root = (
            Path(__file__)
            .resolve()
            .parents[3]
        )

        command = [
            "docker",
            "compose",
            "--project-directory",
            str(repo_root),
            "restart",
            action[
                "compose_service"
            ],
        ]

        try:
            completed = (
                subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=90,
                    check=False,
                )
            )

        except subprocess.TimeoutExpired:
            return ActionResult(
                connector=self.key,
                action_key=action_key,
                target_service=(
                    target_service
                ),
                success=False,
                exit_code=None,
                stderr=(
                    "Docker remediation "
                    "timed out."
                ),
            )

        except OSError as exc:
            return ActionResult(
                connector=self.key,
                action_key=action_key,
                target_service=(
                    target_service
                ),
                success=False,
                exit_code=None,
                stderr=str(exc),
            )

        return ActionResult(
            connector=self.key,
            action_key=action_key,
            target_service=(
                target_service
            ),
            success=(
                completed.returncode
                == 0
            ),
            exit_code=(
                completed.returncode
            ),
            stdout=(
                completed.stdout
                .strip()
            ),
            stderr=(
                completed.stderr
                .strip()
            ),
        )

    @staticmethod
    def _run_docker(
        *arguments: str,
        timeout: int,
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [
                "docker",
                *arguments,
            ],
            stdout=(
                subprocess.PIPE
            ),
            stderr=(
                subprocess.STDOUT
            ),
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )


benchmark_connector = (
    BenchmarkConnector()
)