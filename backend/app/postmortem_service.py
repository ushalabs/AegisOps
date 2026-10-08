from app.core.config import settings
from app.postmortem import (
    build_incident_timeline,
    build_incident_memory_text,
    save_incident_memory,
    save_incident_postmortem,
)
from app.postmortem_gemini import (
    generate_postmortem_with_gemini,
)

from app.postmortem import (
    build_incident_timeline,
    build_incident_memory_text,
    get_postmortem_by_incident,
    get_incident_memory_by_incident,
    save_incident_memory,
    save_incident_postmortem,
)

def generate_and_store_postmortem(
    incident_id: int,
) -> dict:

    existing_postmortem = (
    get_postmortem_by_incident(
        incident_id
    )
)
    existing_postmortem = (
        get_postmortem_by_incident(
            incident_id
        )
    )

    existing_memory = (
        get_incident_memory_by_incident(
            incident_id
        )
    )

    if (
        existing_postmortem is not None
        and existing_memory is not None
    ):
        return {
            "incident_id": incident_id,
            "postmortem_id":
                existing_postmortem["id"],
            "memory_id":
                existing_memory["id"],
            "reused": True,
        }

    facts = build_incident_timeline(
        incident_id
    )

    incident = facts["incident"]

    if incident["status"] != "RESOLVED":
        raise ValueError(
            "Postmortems can only be generated "
            "for RESOLVED incidents."
        )

    recovered = any(
        record["status"] == "RECOVERED"
        for record
        in facts["recovery_verifications"]
    )

    if not recovered:
        raise ValueError(
            "Incident does not have a confirmed "
            "recovery verification."
        )

    report = generate_postmortem_with_gemini(
        facts
    )

    postmortem = save_incident_postmortem(
        incident_id=incident_id,
        timeline=facts["timeline"],
        report=report,
        model=settings.gemini_model,
    )

    memory_text = build_incident_memory_text(
        incident,
        report,
    )

    memory = save_incident_memory(
        incident_id=incident_id,
        postmortem_id=postmortem["id"],
        memory_text=memory_text,
        metadata={
            "service":
                incident["service"],
            "rule_key":
                incident["rule_key"],
            "severity":
                incident["severity"],
        },
    )

    return {
        "incident_id": incident_id,
        "postmortem_id":
            postmortem["id"],
        "memory_id":
            memory["id"],
        "service":
            incident["service"],
        "rule_key":
            incident["rule_key"],
        "reused": False,
    }