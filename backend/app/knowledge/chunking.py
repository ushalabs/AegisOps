
import re


def chunk_markdown(
    markdown: str,
    max_words: int = 100,
    overlap: int = 20,
) -> list[dict]:
    if max_words <= 0 or not 0 <= overlap < max_words:
        raise ValueError("Invalid chunk size or overlap")

    title = "Untitled"
    sections = []
    current_heading = "Introduction"
    current_lines = []

    for line in markdown.splitlines():
        stripped = line.strip()

        if stripped.startswith("# ") and title == "Untitled":
            title = stripped[2:].strip()
            continue

        heading = re.match(r"^#{2,3}\s+(.+)$", stripped)

        if heading:
            if current_lines:
                sections.append((
                    current_heading,
                    "\n".join(current_lines).strip(),
                ))

            current_heading = heading.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((
            current_heading,
            "\n".join(current_lines).strip(),
        ))

    chunks = []

    for heading, content in sections:
        words = content.split()

        if not words:
            continue

        start = 0

        while start < len(words):
            end = min(start + max_words, len(words))
            chunk_text = " ".join(words[start:end])

            chunks.append({
                "chunk_index": len(chunks),
                "heading": heading,
                "content": (
                    f"# {title}\n"
                    f"## {heading}\n\n"
                    f"{chunk_text}"
                ),
            })

            if end == len(words):
                break

            start = end - overlap

    return chunks
