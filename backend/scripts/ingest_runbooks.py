
from pathlib import Path

from app.knowledge.repository import upsert_documents


RUNBOOK_DIR = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "runbooks"
)


def main():
    documents = []

    for path in sorted(RUNBOOK_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")

        title = content.splitlines()[0].removeprefix("# ").strip()

        documents.append({
            "source_key": f"runbook:{path.stem}",
            "title": title,
            "content": content,
            "metadata": {
                "file_path": f"docs/runbooks/{path.name}",
                "environment": "benchmark",
            },
        })

    if not documents:
        print("No Markdown runbooks found")
        return

    document_ids = upsert_documents(
        documents,
        source_type="runbook",
    )

    for document_id, document in zip(
        document_ids,
        documents,
    ):
        print(f"Stored {document_id}: {document['title']}")


if __name__ == "__main__":
    main()