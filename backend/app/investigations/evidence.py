from datetime import (
    datetime,
    timezone,
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


def collect_incident_evidence(
    incident_id: int,
) -> dict:
    row = get_incident_by_id(
        incident_id
    )

    if row is None:
        raise ValueError(
            (
                f"Incident {incident_id} "
                "not found"
            )
        )

    incident = {
        "id":
            row[0],

        "fingerprint":
            row[1],

        "rule_key":
            row[2],

        "title":
            row[3],

        "service":
            row[4],

        "severity":
            row[5],

        "status":
            row[6],

        "trigger_value":
            row[7],

        "threshold":
            row[8],

        "first_detected_at":
            row[9].isoformat(),

        "last_seen_at":
            row[10].isoformat(),

        "resolved_at": (
            row[11].isoformat()
            if row[11]
            else None
        ),
    }

    collected_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    signals = {}

    for rule in INCIDENT_RULES:
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

        result = (
            connector.get_signal(
                signal_key=(
                    rule.key
                ),
                service=(
                    rule.service
                ),
            )
        )

        signal = {
            "title":
                rule.title,

            "service":
                rule.service,

            "connector":
                result.connector,

            "signal_key":
                rule.key,

            "threshold":
                rule.threshold,

            "operator":
                rule.operator.value,

            "readings":
                [],
        }

        for reading in (
            result.readings
        ):
            signal[
                "readings"
            ].append(
                {
                    "labels":
                        reading.labels,

                    "value":
                        reading.value,

                    "sample_time": (
                        reading
                        .observed_at
                        .isoformat()
                        if (
                            reading
                            .observed_at
                        )
                        else None
                    ),
                }
            )

        if (
            result.status
            == ConnectorStatus.OK
        ):
            signal[
                "data_status"
            ] = "AVAILABLE"

        elif (
            result.status
            == ConnectorStatus.NO_DATA
        ):
            signal[
                "data_status"
            ] = "NO_DATA"

        else:
            signal[
                "data_status"
            ] = "QUERY_ERROR"

            signal["error"] = (
                result.error
                or (
                    "Connector telemetry "
                    "query failed"
                )
            )

        signals[
            rule.key
        ] = signal

    return {
        "incident":
            incident,

        "evidence_collected_at":
            collected_at,

        "evidence_type":
            "CURRENT_METRIC_SNAPSHOT",

        "monitoring_signals":
            signals,
    }