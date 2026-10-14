from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)

from app.connectors import (
    ConnectorStatus,
    connector_registry,
)
from app.incidents.repository import (
    get_incident_by_id,
)
from app.incidents.rules import (
    INCIDENT_RULES,
)


class GetIncidentArgs(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid"
    )

    incident_id: int = Field(
        ge=1
    )


class GetMetricArgs(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid"
    )

    rule_key: str = Field(
        min_length=1,
        max_length=128,
    )


class GetServiceLogsArgs(
    BaseModel
):
    model_config = ConfigDict(
        extra="forbid"
    )

    service: str = Field(
        min_length=1,
        max_length=128,
    )

    tail: int = Field(
        default=50,
        ge=1,
        le=100,
    )

    since_minutes: int = Field(
        default=30,
        ge=1,
        le=60,
    )


RULES_BY_KEY = {
    rule.key:
        rule
    for rule
    in INCIDENT_RULES
}


def get_incident(
    incident_id: int,
) -> dict:
    row = get_incident_by_id(
        incident_id
    )

    if row is None:
        return {
            "tool_status":
                "NOT_FOUND",

            "incident_id":
                incident_id,
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

    incident = dict(
        zip(
            fields,
            row,
        )
    )

    for field in (
        "first_detected_at",
        "last_seen_at",
        "resolved_at",
    ):
        value = (
            incident[
                field
            ]
        )

        incident[field] = (
            value.isoformat()
            if value
            else None
        )

    return {
        "tool_status":
            "OK",

        "incident":
            incident,
    }


def get_metric(
    rule_key: str,
) -> dict:
    rule = (
        RULES_BY_KEY.get(
            rule_key
        )
    )

    if rule is None:
        raise ValueError(
            (
                "Unknown or disallowed "
                f"rule: {rule_key}"
            )
        )

    connector = (
        connector_registry.resolve(
            connector_key=(
                rule.connector_key
            ),
            service=(
                rule.service
            ),
        )
    )

    result = connector.get_signal(
        signal_key=rule.key,
        service=rule.service,
    )

    if (
        result.status
        == ConnectorStatus.ERROR
    ):
        return {
            "tool_status":
                "QUERY_ERROR",

            "connector":
                result.connector,

            "rule_key":
                rule.key,

            "service":
                rule.service,

            "error":
                (
                    result.error
                    or (
                        "Connector telemetry "
                        "query failed"
                    )
                ),
        }

    readings = [
        {
            "value":
                reading.value,

            "labels":
                reading.labels,

            "sample_time": (
                reading
                .observed_at
                .isoformat()
                if reading.observed_at
                else None
            ),
        }
        for reading
        in result.readings
    ]

    return {
        "tool_status": (
            "OK"
            if (
                result.status
                == ConnectorStatus.OK
            )
            else "NO_DATA"
        ),

        "connector":
            result.connector,

        "rule_key":
            rule.key,

        "service":
            rule.service,

        "threshold":
            rule.threshold,

        "operator":
            rule.operator.value,

        "readings":
            readings,
    }


def get_service_logs(
    service: str,
    tail: int = 50,
    since_minutes: int = 30,
) -> dict:
    connector = (
        connector_registry
        .resolve_service(
            service
        )
    )

    result = connector.get_logs(
        service=service,
        tail=tail,
        since_minutes=(
            since_minutes
        ),
    )

    status_map = {
        ConnectorStatus.OK:
            "OK",

        ConnectorStatus.NO_DATA:
            "NO_DATA",

        ConnectorStatus.ERROR:
            "TOOL_ERROR",
    }

    response = {
        "tool_status":
            status_map[
                result.status
            ],

        "connector":
            result.connector,

        "service":
            result.service,

        "logs":
            result.logs,

        **result.metadata,
    }

    if result.error:
        response["error"] = (
            result.error
        )

    return response


def execute_tool(
    name: str,
    arguments: dict,
) -> dict:
    if (
        name
        == "get_incident"
    ):
        args = (
            GetIncidentArgs
            .model_validate(
                arguments
            )
        )

        return get_incident(
            args.incident_id
        )

    if (
        name
        == "get_metric"
    ):
        args = (
            GetMetricArgs
            .model_validate(
                arguments
            )
        )

        return get_metric(
            args.rule_key
        )

    if (
        name
        == "get_service_logs"
    ):
        args = (
            GetServiceLogsArgs
            .model_validate(
                arguments
            )
        )

        return get_service_logs(
            service=(
                args.service
            ),
            tail=(
                args.tail
            ),
            since_minutes=(
                args.since_minutes
            ),
        )

    raise ValueError(
        (
            "Unknown or disallowed "
            f"tool: {name}"
        )
    )