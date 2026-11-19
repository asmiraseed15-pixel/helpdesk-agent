from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

KB_DIR = Path("data/kb")
DB_DIR = "chroma_db"
COLLECTION = "it_kb"
MODEL_NAME = "all-MiniLM-L6-v2"


def parse_md(path: Path):
    """One .md file -> one chunk (symptoms + steps), actions/escalation in metadata."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    title, meta, sections = path.stem, {}, {}
    current = None

    for line in lines:
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            current = line[3:].strip()
            sections[current] = []
        elif current is None and ":" in line:
            key, value = line.split(":", 1)
            meta[key.strip().lower()] = value.strip()
        elif current is not None and line.strip():
            sections[current].append(line.strip())

    def sec(name):
        return "\n".join(sections.get(name, []))

    text = (
        f"{title}\n"
        f"Category: {meta.get('category', 'General')}\n"
        f"Keywords: {meta.get('keywords', '')}\n\n"
        f"Symptoms:\n{sec('Symptoms')}\n\n"
        f"Troubleshooting Steps:\n{sec('Troubleshooting Steps')}"
    )
    metadata = {
        "title": title,
        "category": meta.get("category", "General"),
        "severity": meta.get("severity", "Low"),
        "source": path.name,
        "actions": sec("Permitted Actions").replace("\n", " "),
        "escalate": sec("When to Escalate").replace("\n", " "),
    }
    return [(text, metadata)]
    chunks = []
    for section, body in sections.items():
        text = f"{title} - {section}\n" + "\n".join(body)
        metadata = {
            "title": title,
            "section": section,
            "category": meta.get("category", "General"),
            "severity": meta.get("severity", "Low"),
            "source": path.name,
        }
        chunks.append((text, metadata))
    return chunks


def main():
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=DB_DIR)

    # re-run safe: old collection delete panni fresh ah create
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    col = client.create_collection(COLLECTION, metadata={"hnsw:space": "cosine"})

    ids, docs, metas = [], [], []
    for file in sorted(KB_DIR.glob("*.md")):
        for i, (text, metadata) in enumerate(parse_md(file)):
            ids.append(f"{file.stem}_{i}")
            docs.append(text)
            metas.append(metadata)

    embeddings = model.encode(docs, normalize_embeddings=True).tolist()
    col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
    print(f"Done: {len(docs)} chunks from {len(list(KB_DIR.glob('*.md')))} files stored in '{DB_DIR}'")


if __name__ == "__main__":
    main()