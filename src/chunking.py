"""
Text chunking module.
Splits article text into overlapping chunks for embedding and retrieval.

Strategy: Fixed-size word-based chunks with overlap.
- Chunk size: 500 words
- Overlap: 100 words
- This balances between capturing enough context per chunk and keeping
  chunks small enough for meaningful semantic search.
"""

import json
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")


def ensure_dirs():
    os.makedirs(PROCESSED_DIR, exist_ok=True)


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Split text into chunks of approximately `chunk_size` words
    with `overlap` words of overlap between consecutive chunks.

    Returns a list of text chunks.
    """
    words = text.split()

    if len(words) <= chunk_size:
        return [text.strip()] if text.strip() else []

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk.strip())

        # Move forward by (chunk_size - overlap) words
        start += chunk_size - overlap

    return chunks


def chunk_article(article: dict, chunk_size: int = 500, overlap: int = 100) -> list[dict]:
    """
    Chunk a single article and return a list of chunk dictionaries
    with metadata attached to each chunk.
    """
    text = article["text"]
    raw_chunks = chunk_text(text, chunk_size, overlap)

    chunks = []
    for i, chunk_text_content in enumerate(raw_chunks):
        chunks.append({
            "entity_name": article["name"],
            "entity_type": article["type"],
            "source_url": article["url"],
            "chunk_index": i,
            "total_chunks": len(raw_chunks),
            "text": chunk_text_content,
        })

    return chunks


def save_processed_chunks(entity_name: str, chunks: list[dict]):
    """Save processed chunks to data/processed/ as a JSON file."""
    ensure_dirs()

    safe_name = entity_name.lower().replace(" ", "_").replace(".", "")
    filename = f"{safe_name}_chunks.json"
    filepath = os.path.join(PROCESSED_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    return filepath


def load_all_processed_chunks() -> list[dict]:
    """Load all processed chunks from data/processed/ directory."""
    ensure_dirs()
    all_chunks = []

    for filename in sorted(os.listdir(PROCESSED_DIR)):
        if filename.endswith("_chunks.json"):
            filepath = os.path.join(PROCESSED_DIR, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                all_chunks.extend(chunks)

    return all_chunks
