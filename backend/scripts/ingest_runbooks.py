
from pathlib import Path

from app.knowledge.repository import upsert_documents
from app.knowledge.chunking import chunk_markdown
from app.knowledge.repository import (
    upsert_documents,
    replace_document_chunks,
)


RUNBOOK_DIR = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "runbooks"
)


def main():
    documents = []

    for path in sorted(RUNBOOK_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")

        title = next(
        (
            line.strip()[2:].strip()
            for line in content.splitlines()
            if line.strip().startswith("# ")
        ),
        path.stem.replace("-", " ").title(),
        )

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
        chunks = chunk_markdown(
            document["content"],
        )

        count = replace_document_chunks(
            document_id=document_id,
            chunks=chunks,
        )

        print(
            f"Stored document {document_id}: "
            f"{document['title']} ({count} chunks)"
        )


if __name__ == "__main__":
    main()