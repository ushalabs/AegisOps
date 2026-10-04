
from datetime import datetime, timezone
from math import isfinite
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
import json
import subprocess

from app.incidents.repository import get_incident_by_id
from app.incidents.rules import INCIDENT_RULES
from app.monitoring.prometheus import (
    PrometheusError,
    prometheus_client,
)


class GetIncidentArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    incident_id: int = Field(ge=1)


class GetMetricArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rule_key: Literal[
        "postgresql_unavailable",
        "redis_unavailable",
        "http_5xx_rate_high",
        "api_latency_high",
    ]

class GetServiceLogsArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    service: Literal[
        "benchmark-api",
        "benchmark-redis",
        "benchmark-postgresql",
    ]
    tail: int = Field(default=50, ge=1, le=100)
    since_minutes: int = Field(default=30, ge=1, le=60)


BENCHMARK_CONTAINERS = {
    "benchmark-api": "aegisops-benchmark-api",
    "benchmark-redis": "aegisops-benchmark-redis",
    "benchmark-postgresql": "aegisops-benchmark-db",
}

RULES_BY_KEY = {
    rule.key: rule
    for rule in INCIDENT_RULES
}


def get_incident(incident_id: int) -> dict:
    row = get_incident_by_id(incident_id)

    if row is None:
        return {
            "tool_status": "NOT_FOUND",
            "incident_id": incident_id,
        }

    fields = [
        "id",
        "fingerprint",
        "rule_key",
        "title",
        "service",
        "severity",
        "status",
        "trigger_value",
        "threshold",
        "first_detected_at",
        "last_seen_at",
        "resolved_at",
    ]

    incident = dict(zip(fields, row))

    for field in (
        "first_detected_at",
        "last_seen_at",
        "resolved_at",
    ):
        value = incident[field]
        incident[field] = value.isoformat() if value else None

    return {
        "tool_status": "OK",
        "incident": incident,
    }


def get_metric(rule_key: str) -> dict:
    rule = RULES_BY_KEY[rule_key]

    try:
        results = prometheus_client.query(rule.promql)
    except PrometheusError as exc:
        return {
            "tool_status": "QUERY_ERROR",
            "rule_key": rule_key,
            "error": str(exc),
        }

    readings = []

    for result in results:
        try:
            timestamp, raw_value = result["value"]
            value = float(raw_value)

            if not isfinite(value):
                continue

            sample_time = datetime.fromtimestamp(
                float(timestamp),
                tz=timezone.utc,
            ).isoformat()

        except (
            KeyError,
            ValueError,
            TypeError,
            OverflowError,
        ):
            continue

        readings.append({
            "value": value,
            "labels": result.get("metric", {}),
            "sample_time": sample_time,
        })

    return {
        "tool_status": "OK" if readings else "NO_DATA",
        "rule_key": rule_key,
        "service": rule.service,
        "threshold": rule.threshold,
        "operator": rule.operator.value,
        "readings": readings,
    }


def execute_tool(
    name: str,
    arguments: dict,
) -> dict:
    if name == "get_incident":
        args = GetIncidentArgs.model_validate(arguments)
        return get_incident(args.incident_id)

    if name == "get_metric":
        args = GetMetricArgs.model_validate(arguments)
        return get_metric(args.rule_key)

    if name == "get_service_logs":
        args = GetServiceLogsArgs.model_validate(arguments)

        return get_service_logs(
            service=args.service,
            tail=args.tail,
            since_minutes=args.since_minutes,
        )
    raise ValueError(f"Unknown or disallowed tool: {name}")


def get_service_logs(
    service: str,
    tail: int = 50,
    since_minutes: int = 30,
) -> dict:
    container = BENCHMARK_CONTAINERS[service]

    def run_docker(*arguments):
        return subprocess.run(
            ["docker", *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=8,
            check=False,
        )

    try:
        inspection = run_docker(
            "inspect",
            "--format",
            "{{json .State}}",
            container,
        )

        if inspection.returncode != 0:
            return {
                "tool_status": "TOOL_ERROR",
                "service": service,
                "error": "Docker container inspection failed",
            }

        state = json.loads(inspection.stdout.strip())

        result = run_docker(
            "logs",
            "--timestamps",
            "--since",
            f"{since_minutes}m",
            "--tail",
            str(tail),
            container,
        )

        if result.returncode != 0:
            return {
                "tool_status": "TOOL_ERROR",
                "service": service,
                "error": "Docker log retrieval failed",
            }

    except (
        OSError,
        subprocess.TimeoutExpired,
        ValueError,
    ) as exc:
        return {
            "tool_status": "TOOL_ERROR",
            "service": service,
            "error": type(exc).__name__,
        }

    lines = result.stdout.splitlines()
    log_text = "\n".join(lines[-tail:])[-8000:]

    return {
        "tool_status": "OK" if log_text else "NO_DATA",
        "service": service,
        "container": container,
        "container_state": {
            "status": state.get("Status"),
            "running": state.get("Running"),
            "exit_code": state.get("ExitCode"),
            "oom_killed": state.get("OOMKilled"),
            "started_at": state.get("StartedAt"),
            "finished_at": state.get("FinishedAt"),
        },
        "logs": log_text,
    }
