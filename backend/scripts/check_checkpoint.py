
import sys

from psycopg.conninfo import make_conninfo
from langgraph.checkpoint.postgres import PostgresSaver

from app.core.config import settings
from app.investigations.agent import builder


THREAD_ID = "phase10-checkpoint-test-13"

CONFIG = {
    "configurable": {
        "thread_id": THREAD_ID,
    }
}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""

    if mode not in ("start", "inspect"):
        raise ValueError("Use: start or inspect")

    conninfo = make_conninfo(
        host=settings.postgres_host,
        port=settings.postgres_port,
        dbname=settings.postgres_db,
        user=settings.postgres_user,
        password=settings.postgres_password,
    )

    with PostgresSaver.from_conn_string(conninfo) as checkpointer:
        if mode == "start":
            checkpointer.setup()

        # Pause immediately before the first Gemini request.
        graph = builder.compile(
            checkpointer=checkpointer,
            interrupt_before=["gemini_decide"],
        )

        if mode == "start":
            graph.invoke(
                {
                    "incident_id": 13,
                    "events": [],
                    "tool_history": [],
                },
                config=CONFIG,
            )

        snapshot = graph.get_state(CONFIG)

        if not snapshot.values:
            raise RuntimeError("No saved checkpoint found")

        print("THREAD:", THREAD_ID)
        print("INCIDENT:", snapshot.values["incident_id"])
        print("NEXT NODE:", snapshot.next)
        print(
            "CHECKPOINT:",
            snapshot.config["configurable"]["checkpoint_id"],
        )

        print("\nPERSISTED EVENTS")

        for event in snapshot.values["events"]:
            print("-", event)

        print(
            "\nRETRIEVED CHUNKS:",
            len(snapshot.values["rag_context"]["chunks"]),
        )


if __name__ == "__main__":
    main()
